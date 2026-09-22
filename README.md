# My Hyprland with other things config

## Tools and themes

| Tool / theme | Used for | Repository |
| --- | --- | --- |
| hyprlock | Screen locking | [hyprwm/hyprlock](https://github.com/hyprwm/hyprlock) |
| awww | Animated wallpapers | [LGFae/awww (Codeberg)](https://codeberg.org/LGFae/awww) · [Former GitHub repository: swww](https://github.com/LGFae/swww) |
| hyprsunset | Blue-light filtering | [hyprwm/hyprsunset](https://github.com/hyprwm/hyprsunset) |
| wifi-manager | Wi-Fi and network controls | [Vijay-papanaboina/wifi-manager](https://github.com/Vijay-papanaboina/wifi-manager) |
| blurs | Bluetooth applet | [cachebag/blurs](https://github.com/cachebag/blurs) |
| skwd-wall | Wallpaper selection and management | [liixini/skwd-wall](https://github.com/liixini/skwd-wall) |
| fastfetch | System information in the terminal | [fastfetch-cli/fastfetch](https://github.com/fastfetch-cli/fastfetch) |
| rofi | Application launcher and menus | [davatorium/rofi](https://github.com/davatorium/rofi) |
| rofi-themes | Rofi launcher and power-menu themes | [adi1090x/rofi](https://github.com/adi1090x/rofi) |
| swaync | Notifications and control center | [ErikReider/SwayNotificationCenter](https://github.com/ErikReider/SwayNotificationCenter) |
| HyprNova | Source of the SwayNC `nova-dark` theme | [zDyant/HyprNova](https://github.com/zDyant/HyprNova) |

## External system configuration log

This log records desktop-portal service changes outside HyprLife. It excludes the repository's configuration files and application source edits.

### 2026-09-20 — Desktop portal startup on plain Hyprland

#### Problem

`xdg-desktop-portal.service` failed to start because Fedora's packaged service contains:

```ini
Requisite=graphical-session.target
```

The default, non-UWSM Hyprland session had an inactive `graphical-session.target`. PipeWire and WirePlumber were running, and the necessary portal packages were already installed.

#### Ineffective drop-in attempt

Created:

```text
/home/soham/.config/systemd/user/xdg-desktop-portal.service.d/override.conf
```

Contents:

```ini
[Unit]
Requisite=
```

This did **not** remove the dependency. Systemd dependency lists cannot be cleared with an empty assignment in a drop-in. This file was still present at the last inspection; it is not the working fix.

#### Working full user override

Created a full user service override using:

```bash
systemctl --user edit --full xdg-desktop-portal.service
```

File:

```text
/home/soham/.config/systemd/user/xdg-desktop-portal.service
```

Removed `Requisite=graphical-session.target`, leaving:

```ini
[Unit]
Description=Portal service
PartOf=graphical-session.target
After=graphical-session.target

[Service]
Type=dbus
BusName=org.freedesktop.portal.Desktop
ExecStart=/usr/libexec/xdg-desktop-portal
Slice=session.slice
```

The packaged file at `/usr/lib/systemd/user/xdg-desktop-portal.service` was not edited. No override was created for `xdg-desktop-portal-hyprland.service` during this session.

#### Applying and verifying

Commands used during troubleshooting:

```bash
systemctl --user daemon-reload
systemctl --user restart xdg-desktop-portal-hyprland.service
systemctl --user restart xdg-desktop-portal.service
systemctl --user status xdg-desktop-portal xdg-desktop-portal-hyprland
```

After the full override, the user reported success. Both portal services were confirmed active when this log was created.

#### Persistence and limitations

- The full user override persists across reboots.
- It shadows future changes to the packaged service file and should be reviewed after relevant package updates.
- This is a workaround for the unmanaged session; it does not activate `graphical-session.target` or provide UWSM session lifecycle management.
- Actual screen sharing and portal activation after a fresh login/reboot still need verification.
- No portal packages were removed. The existing system backend preference remains `hyprland;gtk`.

#### Undoing these overrides

To return to the packaged service, remove only the two user files listed above, then run `systemctl --user daemon-reload`. This restores the original graphical-session requirement, so the startup failure can return if that target remains inactive.

Reference: [systemd unit and drop-in documentation](https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml).
