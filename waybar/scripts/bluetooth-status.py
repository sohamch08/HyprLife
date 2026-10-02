#!/usr/bin/env python3
"""Waybar Bluetooth status with icons for the user's named audio devices."""

import html
import json
from pathlib import Path

from gi.repository import Gio, GLib

ADAPTER = "org.bluez.Adapter1"
DEVICE = "org.bluez.Device1"
BATTERY = "org.bluez.Battery1"
ICONS = {
    "on": "\U00104136",
    "off": "\U00104138",
    "connected": "\U00104137",
    "headphone": "\U00104217",
    "earbuds": "\U00104bdb",
}


def device_icon(device):
    names = " ".join(str(device.get(key, "")) for key in ("Alias", "Name")).casefold()
    if any(name in names for name in ("earbud", "nord buds")):
        return ICONS["earbuds"]
    if "headphone" in names or "wh-ch720n" in names:
        return ICONS["headphone"]
    return ICONS["connected"]


def render(objects, blocked=False):
    adapters = [
        (path, data[ADAPTER]) for path, data in objects.items() if ADAPTER in data
    ]
    adapter_path, adapter = next(
        ((path, data) for path, data in adapters if data.get("Powered")),
        adapters[0] if adapters else ("", {}),
    )
    devices = [
        (data[DEVICE], data.get(BATTERY, {}).get("Percentage"))
        for data in objects.values()
        if DEVICE in data
        and data[DEVICE].get("Connected")
        and data[DEVICE].get("Adapter") == adapter_path
    ]
    if blocked or not adapters:
        state, label, icon = "disabled", "dis", ICONS["off"]
    elif not adapter.get("Powered"):
        state, label, icon = "off", "off", ICONS["off"]
    elif devices:
        state = "connected"
        # Prefer the named audio devices over mice/keyboards when several are connected.
        device, _ = next(
            (item for item in devices if device_icon(item[0]) != ICONS["connected"]),
            devices[-1],
        )
        label = device_icon(device)
        icon = ICONS["connected"]
    else:
        state, label, icon = "on", "on", ICONS["on"]

    tooltip = [f"{adapter.get('Alias', 'Bluetooth')}: {state}"]
    if state == "connected":
        tooltip.extend(
            f"{device.get('Alias', device.get('Name', 'Device'))}\t{device.get('Address', '')}"
            + (f"\t{battery}%" if battery is not None else "")
            for device, battery in devices
        )

    def icon_span(glyph):
        return f"<span font_family='Material Terminal Rounded' size='16pt' rise='-5120'>{glyph}</span>"

    status = icon_span(label) if state == "connected" else html.escape(label)
    return {
        "text": f"{icon_span(icon)} {status}",
        "tooltip": html.escape("\n".join(tooltip)),
        "class": state,
    }


def bluetooth_blocked():
    for entry in Path("/sys/class/rfkill").glob("rfkill*"):
        try:
            if (entry / "type").read_text().strip() == "bluetooth":
                if any(
                    (entry / flag).read_text().strip() == "1"
                    for flag in ("soft", "hard")
                ):
                    return True
        except OSError:
            # Adapters can disappear while their status is being read.
            continue
    return False


def main():
    try:
        bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        objects = bus.call_sync(
            "org.bluez",
            "/",
            "org.freedesktop.DBus.ObjectManager",
            "GetManagedObjects",
            None,
            GLib.VariantType.new("(a{oa{sa{sv}}})"),
            Gio.DBusCallFlags.NONE,
            5000,
            None,
        ).unpack()[0]
        result = render(objects, bluetooth_blocked())
    except GLib.Error as error:
        result = render({})
        result["tooltip"] = html.escape(f"Bluetooth unavailable: {error.message}")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
