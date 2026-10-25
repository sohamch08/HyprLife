#!/usr/bin/env python3
"""Forward Zoom toast name-change events, which carry the full message text."""
from collections import deque
import html
import json
from pathlib import Path
import subprocess
import time

from Xlib import X, Xatom, display, error

from zoom_chat_accessibility import Gio, GLib, Reader, parse_text, same_bounds


EVENT = "object:property-change:accessible-name"
REGISTRY = ("org.a11y.atspi.Registry", "/org/a11y/atspi/registry")


def clients():
    return json.loads(subprocess.check_output(["hyprctl", "-j", "clients"], timeout=2))


class Notifications:
    def __init__(self):
        self.reader = Reader()
        self.x11 = display.Display()
        self.loop = GLib.MainLoop()
        self.owners, self.meetings, self.frames, self.verified = {}, {}, {}, {}
        self.pending = deque(maxlen=128)
        self.busy = False
        self.reader.connection.signal_subscribe(
            None, "org.a11y.atspi.Event.Object", "PropertyChange", None, "accessible-name",
            Gio.DBusSignalFlags.NONE, self.on_event)
        self.reader.connection.connect("closed", lambda *args: self.loop.quit())

    def register(self, bus, method):
        args = GLib.Variant("(sass)", (EVENT, [], bus)) if method == "RegisterEvent" else GLib.Variant("(ss)", (EVENT, bus))
        self.reader.connection.call_sync(*REGISTRY, "org.a11y.atspi.Registry", method,
                                         args, None, Gio.DBusCallFlags.NONE, 1000, None)

    def refresh(self):
        if self.busy:
            return True
        self.busy = True
        try:
            self.meetings = {w["address"]: w for w in clients()
                             if w["mapped"] and w["class"] == "zoom" and w["title"] == "Meeting"}
            pids = {w["pid"] for w in self.meetings.values()}
            for bus, pid in list(self.owners.items()):
                if pid not in pids:
                    self.register(bus, "DeregisterEvent")
                    del self.owners[bus]
                    self.frames = {k: v for k, v in self.frames.items() if k[0] != bus}
                    self.verified = {k: v for k, v in self.verified.items() if k[0] != bus}
            for pid in pids:
                for bus, _ in self.reader.applications(pid):
                    if bus not in self.owners:
                        self.register(bus, "RegisterEvent")
                        self.owners[bus] = pid
                        print("Listening for Zoom chat message events.", flush=True)
        except (GLib.Error, OSError, subprocess.SubprocessError, ValueError) as exc:
            print(f"zoom-chat-notifications: discovery: {exc}", flush=True)
        finally:
            self.busy = False
        return True

    def on_event(self, connection, sender, path, interface, member, parameters):
        if sender not in self.owners:
            return
        values = parameters.unpack()
        if len(values) < 4 or values[0] != "accessible-name" or not isinstance(values[3], str):
            return
        contents = parse_text(values[3])
        if contents:
            # Save the event payload immediately. Later accessibility calls
            # may stall or the toast may disappear; neither loses this text.
            self.pending.append({"ref": (sender, path), "pid": self.owners[sender],
                                 "contents": contents, "received": time.monotonic(), "retry": 0})

    def native_toast(self, window, pid):
        """Confirm the native utility window belongs to this running meeting."""
        try:
            if window.get_wm_class() != ("zoom", "zoom") or window.get_wm_name() != "Zoom Workplace":
                return None
            types = window.get_full_property(self.x11.intern_atom("_NET_WM_WINDOW_TYPE"), Xatom.ATOM)
            if types is None or self.x11.intern_atom("_NET_WM_WINDOW_TYPE_UTILITY") not in types.value:
                return None
            parent = window.get_wm_transient_for()
            if (parent is None or parent.get_wm_class() != ("zoom", "zoom") or parent.get_wm_name() != "Meeting"
                    or parent.get_attributes().map_state != X.IsViewable):
                return None
            prop = parent.get_full_property(self.x11.intern_atom("_NET_WM_PID"), Xatom.CARDINAL)
            status = Path(f"/proc/{pid}/status").read_text().splitlines()
            namespace_ids = next((set(map(int, line.split()[1:])) for line in status if line.startswith("NSpid:")), {pid})
            if prop is None or int(prop.value[0]) not in namespace_ids:
                return None
            rect = parent.get_geometry()
            geometry = (rect.x, rect.y, rect.width, rect.height)
            meetings = [w for w in self.meetings.values() if w["pid"] == pid
                        and same_bounds(w["at"] + w["size"], geometry)]
            if len(meetings) != 1:
                return None
            rect = window.get_geometry()
            return {"xid": window.id, "meeting": meetings[0]["address"],
                    "meeting_id": meetings[0]["stableId"], "geometry": (rect.x, rect.y, rect.width, rect.height)}
        except (error.XError, OSError, ValueError):
            return None

    def verify(self, ref, pid):
        cached = self.verified.get(ref)
        if cached:
            current = self.native_toast(self.x11.create_resource_object("window", cached["xid"]), pid)
            if current and current["meeting"] == cached["meeting"] and current["meeting_id"] == cached["meeting_id"]:
                return True
            self.verified.pop(ref, None)
        frame = self.frames.get(ref)
        if frame is None:
            parent = ref
            for _ in range(4):
                reply = self.reader.query([parent], Reader.PROPERTIES, "Get",
                                          GLib.Variant("(ss)", (Reader.ACCESSIBLE, "Parent"))).get(parent)
                if not reply:
                    return False
                parent = tuple(reply[0])
                if parent[0] != ref[0] or parent[1].endswith("/root"):
                    return False
                if self.reader.names([parent]).get(parent) == "Zoom Workplace":
                    frame = self.frames[ref] = parent
                    break
        if frame is None:
            return False
        rect = self.reader.rectangles([frame]).get(frame)
        if not rect:
            return False
        native = [info for w in self.x11.screen().root.query_tree().children
                  if (info := self.native_toast(w, pid))]
        matches = [info for info in native if same_bounds(info["geometry"], rect)]
        # Qt can retain its pre-placement coordinates after Hyprland moves the
        # toast. Only accept a size match when there is exactly one such toast.
        if not matches:
            matches = [info for info in native if tuple(info["geometry"][2:]) == tuple(rect[2:])]
        if len(matches) != 1:
            return False
        self.verified[ref] = matches[0]
        return True

    def drain(self):
        if self.busy or not self.pending:
            return True
        item = self.pending.popleft()
        if time.monotonic() < item["retry"]:
            self.pending.append(item)
            return True
        self.busy = True
        try:
            if item["pid"] not in self.owners.values():
                return True
            if self.verify(item["ref"], item["pid"]):
                contents = item["contents"]
                body = f"<b>{html.escape(contents['sender'])}</b>: {html.escape(contents['message'])}"
                subprocess.run(["notify-send", "-a", "Zoom", "-i", "Zoom", "--", "Zoom Chat", body],
                               check=True, timeout=2, stdout=subprocess.DEVNULL)
                print("Delivered Zoom chat notification with sender and message.", flush=True)
            elif time.monotonic() - item["received"] < 12:
                item["retry"] = time.monotonic() + 0.2
                self.pending.append(item)
            else:
                print("Skipped a chat event whose toast could not be verified.", flush=True)
        except (GLib.Error, error.XError, OSError, subprocess.SubprocessError) as exc:
            print(f"zoom-chat-notifications: delivery: {exc}", flush=True)
        finally:
            self.busy = False
        return True

    def run(self):
        self.refresh()
        GLib.timeout_add_seconds(2, self.refresh)
        GLib.timeout_add(100, self.drain)
        self.loop.run()
        self.x11.close()
        self.reader.close()
        raise SystemExit(1)  # systemd reconnects if the accessibility bus restarts


if __name__ == "__main__":
    Notifications().run()
