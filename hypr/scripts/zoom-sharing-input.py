#!/usr/bin/env python3
"""Remove Zoom's TOOLTIP hint only from its interactive sharing controls.

Hyprland 0.56 routes override-redirect tooltips to the previously focused
window. allows_input alone cannot override that hit-test path. Run when
sharing controls open and on config reload; no background polling is needed.
Requires python3-xlib (available on this machine).
"""
import json
import subprocess

from Xlib import Xatom, display, error

CONTROL_TITLES = {"as_toolbar", "as_preview"}


def place_controls():
    """Apply placement after Hyprland finishes mapping/clamping new windows."""
    windows = json.loads(subprocess.check_output(["hyprctl", "-j", "clients"]))
    monitors = {m["id"]: m for m in json.loads(
        subprocess.check_output(["hyprctl", "-j", "monitors"]))}
    controls = [w for w in windows if w["class"] == "zoom"
                and w["title"] in CONTROL_TITLES and w["mapped"]]
    for w in controls:
        monitor = monitors.get(w["monitor"])
        if monitor is None:
            continue
        top = monitor["y"]
        if w["title"] == "as_preview":
            toolbar = next((t for t in controls if t["title"] == "as_toolbar"
                            and t["pid"] == w["pid"] and t["monitor"] == w["monitor"]), None)
            if toolbar is None:
                continue
            top += toolbar["size"][1]
        selector = json.dumps("address:" + w["address"])
        command = (f"local w=hl.get_window({selector}); if w then "
                   "if not w.pinned then hl.dispatch(hl.dsp.window.pin({action='set',window=w})) end; "
                   f"hl.dispatch(hl.dsp.window.move({{x={w['at'][0]},y={top},relative=false,window=w}})) end")
        subprocess.run(["hyprctl", "eval", command], check=True,
                       stdout=subprocess.DEVNULL)


def main():
    connection = display.Display()
    try:
        type_atom = connection.intern_atom("_NET_WM_WINDOW_TYPE")
        tooltip = connection.intern_atom("_NET_WM_WINDOW_TYPE_TOOLTIP")
        normal = connection.intern_atom("_NET_WM_WINDOW_TYPE_NORMAL")
        for window in connection.screen().root.query_tree().children:
            try:
                if window.get_wm_class() != ("zoom", "zoom"):
                    continue
                if window.get_wm_name() not in CONTROL_TITLES:
                    continue
                prop = window.get_full_property(type_atom, Xatom.ATOM)
                if prop is None or tooltip not in prop.value:
                    continue
                types = [atom for atom in prop.value if atom != tooltip]
                if normal not in types:
                    types.append(normal)
                window.change_property(type_atom, Xatom.ATOM, 32, types,
                                       onerror=lambda *_: None)
            except error.BadWindow:
                # A transient Zoom window may close during enumeration.
                continue
        connection.sync()
    finally:
        connection.close()
    place_controls()


if __name__ == "__main__":
    main()
