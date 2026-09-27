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
| cliphist | Clipboard history | [sentriz/cliphist](https://github.com/sentriz/cliphist) |
| Waybar | Desktop status bar | [Alexays/Waybar](https://github.com/Alexays/Waybar) |
| Alacritty | Terminal emulator | [alacritty/alacritty](https://github.com/alacritty/alacritty) |
| Yazi | Terminal file manager | [sxyazi/yazi](https://github.com/sxyazi/yazi) |
| Neovim (nvim) | Text editor with my personal configuration | [sohamch08/neovim-config](https://github.com/sohamch08/neovim-config) |
| Zsh | Shell with my personal configuration | [sohamch08/zsh](https://github.com/sohamch08/zsh) |

## UWSM session setup

Use the **Hyprland (uwsm-managed)** login session. Environment settings live in
`uwsm/env` (toolkits/XCursor) and `uwsm/env-hyprland` (Hyprland-specific settings),
using POSIX shell `export` syntax. Link this repository's `uwsm` directory to
`~/.config/uwsm`, just like the existing `hypr`, `rofi`, and `waybar` links.
UWSM supplies the XDG session identity variables automatically.

Enable the packaged user services once:

```bash
systemctl --user enable waybar.service swaync.service hyprsunset.service
```

These services start with the graphical session. NetworkManager uses its
packaged XDG autostart entry; GNOME Keyring uses the display manager's
PAM integration and D-Bus activation. The already-enabled `mpd-mpris.service`
starts MPD through the dependency described below. The remaining Hyprland
autostarts (Polkit and clipboard watchers), application keybindings, and Rofi
application launches use `uwsm app --`.

Blueman's tray applet is disabled by the `Hidden=true` override in
`autostart/blueman.desktop`, linked to `~/.config/autostart/blueman.desktop`.
Bluetooth itself remains enabled. Remove that user override to restore the
packaged applet autostart.

The power menus log out with `uwsm stop`. The bar restart shortcut restarts
`waybar.service` and `swaync.service` through systemd. Environment edits take
full effect at the next login; a Hyprland config reload does not reread them.

References: [Hyprland environment variables](https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/),
[UWSM session and application management](https://wiki.hypr.land/useful-utilities/uwsm/),
and [UWSM launcher integration](https://github.com/Vladimir-csp/uwsm#3-applications-and-slices).

## External system configuration log

This log records user-service changes outside HyprLife and any repository files used to reproduce them.

### 2026-09-26 — UWSM migration and portal override removal

Linked `~/.config/uwsm` to `/home/soham/projects/HyprLife/uwsm`, enabled the three
desktop services above, and switched their running processes plus nm-applet to
systemd management. Published the migrated environment to the current session
with `uwsm finalize` and the explicit variable names, which also registers them
for cleanup. Future sessions load the files through UWSM automatically.

The active UWSM session now provides `graphical-session.target`. Backed up and
removed the two obsolete portal overrides listed in the September 20 entry:

```text
~/.local/state/hyprlife/backups/uwsm-migration-20260926/xdg-desktop-portal.service
~/.local/state/hyprlife/backups/uwsm-migration-20260926/xdg-desktop-portal.service.d/override.conf
```

Reloaded systemd and restarted the portal using the packaged unit, including its
`Requisite=graphical-session.target`. Both the main and Hyprland portal services
started successfully. Hyprland reported no configuration errors; Waybar,
SwayNC, Hyprsunset, nm-applet, and MPD/MPRIS were active with zero restarts when
checked. A fresh login and an actual screen-sharing session remain to be tested.

### 2026-09-26 — MPD media bridge restart notifications under UWSM

`mpd-mpris.service` was enabled with `Restart=always`, but the MPD server was
inactive. The bridge failed to connect to `127.0.0.1:6600` every five seconds,
and UWSM's `fumon` reported repeated failure/recovery notifications.

Installed `systemd/user/mpd-mpris.service.d/10-mpd-dependency.conf` from this
repository at `~/.config/systemd/user/mpd-mpris.service.d/10-mpd-dependency.conf`.
The drop-in requires and starts `mpd.service` before the bridge, restarts only
on failure, and limits starts to three per minute. MPD does not need separate
enablement because the already-enabled bridge pulls it in.

To apply this drop-in on an installation with the existing `mpd-mpris.service`:

```bash
install -D -m 644 systemd/user/mpd-mpris.service.d/10-mpd-dependency.conf \
  ~/.config/systemd/user/mpd-mpris.service.d/10-mpd-dependency.conf
systemctl --user daemon-reload
systemctl --user reset-failed mpd-mpris.service
systemctl --user restart mpd-mpris.service
```

To undo, remove only this drop-in and reload the user systemd manager.

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
