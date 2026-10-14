#!/usr/bin/env python3
"""Identify Zoom chat notifications by their X11 type and meeting parent.

Hyprland does not expose the X11 transient parent to Lua. Match the mapped
windows conservatively, then return the result to the waiting Lua callback.
"""
import html
import json
import subprocess
import sys
import time

from Xlib import X, Xatom, display, error

from zoom_chat_accessibility import read_popup


def geometry(window):
    rect = window.get_geometry()
    return (rect.x, rect.y, rect.width, rect.height)


def same_geometry(client, rect):
    return all(abs(a - b) <= 2 for a, b in zip(client["at"] + client["size"], rect))


def classify(address, stable_id):
    clients = json.loads(subprocess.check_output(["hyprctl", "-j", "clients"], timeout=3))
    generic = [w for w in clients if w["mapped"] and w["class"] == "zoom"
               and w["title"] == "Zoom Workplace" and w["xwayland"]]
    target = next((w for w in generic if w["address"] == address
                   and int(w["stableId"], 16) == stable_id), None)
    if target is None:
        return None
    connection = display.Display()
    try:
        candidates = []
        for window in connection.screen().root.query_tree().children:
            try:
                if (window.get_wm_class() == ("zoom", "zoom")
                        and window.get_wm_name() == "Zoom Workplace"
                        and window.get_attributes().map_state == X.IsViewable):
                    candidates.append((window, geometry(window)))
            except error.BadWindow:
                continue
        matches = [(w, rect) for w, rect in candidates if same_geometry(target, rect)]
        if len(matches) == 1:
            window, rect = matches[0]
            if sum(same_geometry(w, rect) for w in generic) != 1:
                return None
        elif not matches and len(candidates) == len(generic) == 1:
            # A newly mapped surface may still have its pre-layout geometry.
            window, _ = candidates[0]
        else:
            return None
        types = window.get_full_property(connection.intern_atom("_NET_WM_WINDOW_TYPE"), Xatom.ATOM)
        utility = connection.intern_atom("_NET_WM_WINDOW_TYPE_UTILITY")
        parent = window.get_wm_transient_for()
        if (types is None or utility not in types.value or parent is None
                or parent.get_wm_class() != ("zoom", "zoom")
                or parent.get_wm_name() != "Meeting"
                or parent.get_attributes().map_state != X.IsViewable):
            return None
        meetings = [w for w in clients if w["mapped"] and w["class"] == "zoom"
                    and w["title"] == "Meeting" and w["pid"] == target["pid"] and w["xwayland"]]
        parent_rect = geometry(parent)
        exact = [w for w in meetings if same_geometry(w, parent_rect)]
        if len(exact) == 1:
            meeting = exact[0]
        elif not exact and len(meetings) == 1:
            meeting = meetings[0]
        else:
            return None
        return {"meeting": meeting, "parent_geometry": parent_rect,
                "popup_geometry": geometry(window)}
    finally:
        connection.close()


def lua_string(value):
    """Quote UTF-8 data without treating chat contents as Lua source."""
    return '"' + ''.join(f"\\{b:03d}" for b in value.encode("utf-8")) + '"'


def main():
    address, stable_id = sys.argv[1], int(sys.argv[2])
    notify = len(sys.argv) > 3 and sys.argv[3] == "notify"
    info, contents = None, {}
    try:
        info = classify(address, stable_id)
        if info:
            # Qt can map its reused toast before updating its accessible label.
            time.sleep(0.1)
            contents = read_popup(info["parent_geometry"], info["popup_geometry"], info["meeting"]["pid"])
            if notify and not contents.get("message"):
                time.sleep(0.1)
                contents = read_popup(info["parent_geometry"], info["popup_geometry"], info["meeting"]["pid"])
    except Exception as exc:
        print(f"zoom-chat-popup: {exc}", file=sys.stderr)
    result = lua_string(info["meeting"]["address"]) if info else "nil"
    center_offset, bottom_inset = "nil", "nil"
    if info and contents.get("anchor"):
        meeting = info["meeting"]
        parent = info["parent_geometry"]
        anchor = contents["anchor"]
        center_offset = str(anchor["x"] * meeting["size"][0] / parent[2] - meeting["size"][0] / 2)
        bottom_inset = str(meeting["size"][1] - anchor["y"] * meeting["size"][1] / parent[3])
    callback = ("if hyprlifeZoomPopupClassified then hyprlifeZoomPopupClassified("
                f"{lua_string(address)},{stable_id},{result},{center_offset},{bottom_inset}) end")
    subprocess.run(["hyprctl", "eval", callback], check=True, timeout=3,
                   stdout=subprocess.DEVNULL)
    if notify and info and contents.get("sender") and contents.get("message"):
        clients = json.loads(subprocess.check_output(["hyprctl", "-j", "clients"], timeout=3))
        if not any(w["address"] == address and w["mapped"]
                   and int(w["stableId"], 16) == stable_id and "zoom-chat" in w["tags"] for w in clients):
            return
        subprocess.run(["notify-send", "-a", "Zoom", "-i", "Zoom", "--",
                        "Zoom Chat", f"<b>{html.escape(contents['sender'])}</b>: {html.escape(contents['message'])}"],
                       check=True, timeout=3)


if __name__ == "__main__":
    main()
