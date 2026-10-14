"""Read Zoom's Chat button and toast text through its accessibility tree."""
import re
from collections import deque
from pathlib import Path

import pyatspi
from gi.repository import Atspi


def name(node):
    try:
        return node.name or ""
    except Exception:
        return ""


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


def same_process_family(app, pid):
    try:
        app_pid = app.get_process_id()
        return (app_pid == pid or bool(process_scopes(app_pid) & process_scopes(pid))
                or bool(zoom_ancestors(app_pid) & zoom_ancestors(pid)))
    except Exception:
        return False


def bounds(node):
    try:
        rect = node.queryComponent().getExtents(pyatspi.DESKTOP_COORDS)
        return tuple(rect) if rect and rect.width > 0 and rect.height > 0 else None
    except Exception:
        return None


def same_bounds(node, geometry):
    rect = bounds(node)
    return rect is not None and all(abs(a - b) <= 2 for a, b in zip(rect, geometry))


def children(node):
    try:
        return [node.getChildAtIndex(i) for i in range(min(node.childCount, 256))]
    except Exception:
        return []


def descendants(node):
    pending = deque((child, 1) for child in children(node))
    for _ in range(512):
        if not pending:
            return
        child, depth = pending.popleft()
        yield child
        if depth < 3:
            pending.extend((item, depth + 1) for item in children(child))


def showing(node):
    try:
        return node.getState().contains(pyatspi.STATE_SHOWING)
    except Exception:
        return False


def toast_text(frame):
    for node in descendants(frame):
        try:
            if node.getRole() != pyatspi.ROLE_LABEL or not name(node).startswith("From "):
                continue
            text = node.queryText()
            value = text.getText(0, text.characterCount).replace("\r\n", "\n")
            header, separator, message = value.partition("\n")
            match = re.fullmatch(r"From (.+?) to (.+)", header)
            if match and separator and message.strip():
                return {"sender": match[1], "recipient": match[2],
                        "message": message.lstrip("\n")}
        except Exception:
            continue
    return {}


def read_popup(parent_x11_geom, popup_x11_geom, pid=None):
    """Return the meeting-relative Chat anchor and this toast's sender/message.

    Flatpak exposes the D-Bus proxy PID; verify its app scope/process family.
    Cached hidden frames are accepted only with an unambiguous geometry match.
    """
    Atspi.set_timeout(500, 1500)
    desktop = pyatspi.Registry.getDesktop(0)
    meetings = []
    for app in children(desktop):
        if name(app).lower() != "zoom" or (pid is not None and not same_process_family(app, pid)):
            continue
        frames = children(app)
        meetings.extend((frame, frames) for frame in frames
                        if name(frame) == "Meeting" and same_bounds(frame, parent_x11_geom))
    if len(meetings) != 1:
        return {}
    meeting, frames = meetings[0]
    origin = bounds(meeting)
    if origin is None:
        return {}
    result = {}
    for node in descendants(meeting):
        if name(node) == "Chat" and node.getRole() == pyatspi.ROLE_PUSH_BUTTON:
            rect = bounds(node)
            if rect:
                result["anchor"] = {"x": rect[0] + rect[2] / 2 - origin[0],
                                    "y": rect[1] - origin[1]}
                break
    candidates = [(frame, toast_text(frame)) for frame in frames
                  if name(frame) == "Zoom Workplace" and same_bounds(frame, popup_x11_geom)]
    candidates = [(frame, data) for frame, data in candidates if data]
    visible = [(frame, data) for frame, data in candidates if showing(frame)]
    if len(visible or candidates) == 1:
        result.update((visible or candidates)[0][1])
    return result
