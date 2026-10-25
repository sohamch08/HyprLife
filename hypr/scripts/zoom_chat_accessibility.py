"""Accessibility bus helpers for the Zoom chat event listener."""
import re
from pathlib import Path

import gi
gi.require_version("Atspi", "2.0")
from gi.repository import Atspi, Gio, GLib


def process_scopes(pid):
    try:
        paths = [line.split(":", 2)[2] for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines()]
        # A login session or user-wide cgroup does not identify one app instance.
        return {path for path in paths
                if Path(path).name.startswith("app-") and path.endswith(".scope")}
    except (OSError, IndexError):
        return set()


def zoom_ancestors(pid):
    ancestors = set()
    for _ in range(32):
        if pid <= 1:
            break
        try:
            status = dict(line.split(":", 1) for line in Path(f"/proc/{pid}/status").read_text().splitlines() if ":" in line)
            if status["Name"].strip().lower() in {"zoom", "zoomlauncher"}:
                ancestors.add(pid)
            parent = int(status["PPid"].strip())
            if parent == pid:
                break
            pid = parent
        except (OSError, KeyError, ValueError):
            break
    return ancestors


def same_process_family(app_pid, pid):
    try:
        return (app_pid == pid or bool(process_scopes(app_pid) & process_scopes(pid))
                or bool(zoom_ancestors(app_pid) & zoom_ancestors(pid)))
    except Exception:
        return False


class Reader:
    """Query Zoom directly; stale libatspi cache entries can time out serially."""
    ACCESSIBLE = "org.a11y.atspi.Accessible"
    PROPERTIES = "org.freedesktop.DBus.Properties"
    DBUS = ("org.freedesktop.DBus", "/org/freedesktop/DBus")

    def __init__(self):
        session = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        address = session.call_sync(
            "org.a11y.Bus", "/org/a11y/bus", "org.a11y.Bus", "GetAddress", None,
            None, Gio.DBusCallFlags.NONE, 800, None).unpack()[0]
        self.connection = Gio.DBusConnection.new_for_address_sync(
            address, Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT
            | Gio.DBusConnectionFlags.MESSAGE_BUS_CONNECTION, None, None)

    def close(self):
        self.connection.close_sync(None)

    def batch(self, jobs):
        results = {}
        loop = GLib.MainLoop()
        remaining = len(jobs)

        def done(connection, result, key):
            nonlocal remaining
            try:
                results[key] = connection.call_finish(result).unpack()
            except GLib.Error:
                results[key] = None
            remaining -= 1
            if remaining == 0:
                loop.quit()

        for key, (ref, interface, method, args) in jobs.items():
            self.connection.call(*ref, interface, method, args, None,
                                 Gio.DBusCallFlags.NONE, 800, None, done, key)
        if remaining:
            loop.run()
        return results

    def query(self, refs, interface, method, args=None):
        return self.batch({tuple(ref): (tuple(ref), interface, method, args) for ref in refs})

    def children(self, refs):
        replies = self.query(refs, self.ACCESSIBLE, "GetChildren")
        return {ref: [tuple(child) for child in value[0]][:256] if value else []
                for ref, value in replies.items()}

    def names(self, refs):
        replies = self.query(refs, self.PROPERTIES, "Get",
                             GLib.Variant("(ss)", (self.ACCESSIBLE, "Name")))
        return {ref: value[0] if value else "" for ref, value in replies.items()}

    def rectangles(self, refs):
        replies = self.query(refs, "org.a11y.atspi.Component", "GetExtents",
                             GLib.Variant("(u)", (int(Atspi.CoordType.SCREEN),)))
        return {ref: value[0] for ref, value in replies.items() if value}

    def applications(self, pid):
        registry = ("org.a11y.atspi.Registry", "/org/a11y/atspi/accessible/root")
        apps = self.children([registry]).get(registry, [])
        owners = self.batch({app: (self.DBUS, "org.freedesktop.DBus", "GetConnectionUnixProcessID",
                                  GLib.Variant("(s)", (app[0],))) for app in apps})
        return [app for app in apps if owners.get(app) and same_process_family(owners[app][0], pid)]


def parse_text(value):
    header, separator, message = value.replace("\r\n", "\n").partition("\n")
    match = re.fullmatch(r"From (.+?) to (.+)", header)
    if match and separator and message.strip():
        return {"sender": match[1], "recipient": match[2], "message": message.lstrip("\n")}
    return {}


def same_bounds(rect, geometry):
    return (rect is not None and geometry is not None and len(rect) == len(geometry) == 4
            and all(abs(a - b) <= 2 for a, b in zip(rect, geometry)))
