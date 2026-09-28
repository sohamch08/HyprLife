# Configurable tray icons

Foreground: `#f5af67`, matching `#tray` in `waybar/style.css`.

Choose another foreground with `--color`; quote colors beginning with `#`.
Both `#RGB` and `#RRGGBB` are accepted, with or without the leading `#`.
Omitting the option keeps the original orange default.

```sh
# Generate SVGs in a separate folder without installing or changing the desktop.
python3 ~/.config/waybar/scripts/install-tray-theme.py /tmp/my-tray-theme --color '#89b4fa'

# Install that color into the host overlay and existing supported Flatpak profiles.
python3 ~/.config/waybar/scripts/install-tray-theme.py --color '#89b4fa'
```

An explicit destination always generates only there, even with `--color`.
The destination must be absent or already marked by this generator.
Generated app icons are in `status/24/`, including `chatgpt-tray.svg`, `claude.svg`,
`zoom.svg`, Steam, and all three OBS states. Network states are in `status/16/`,
`status/22/`, and `status/24/`. Aliases, lock strokes, and pause symbols use the
selected color; dark badge backings, opacity, geometry, and transparent fills
are preserved. Source SVG files in this repository are not overwritten.

Changing generated SVG colors does not edit Waybar CSS or configuration.
For a matching live tray, also set the `#tray` foreground in `waybar/style.css`.
The current ChatGPT and Claude overrides point to repository source assets;
point those entries in `waybar/config.jsonc` at the generated
`~/.local/share/icons/breeze-dark/status/24/chatgpt-tray.svg` and `claude.svg`
(using full absolute paths). Zoom and Steam already use generated alias paths.
Restart Waybar and the affected applications to clear cached icons.

Install the icon-theme overlay after linking the Waybar configuration:

```sh
python3 ~/.config/waybar/scripts/install-tray-theme.py
systemctl --user restart waybar.service
```

The installer adds an overlay at `~/.local/share/icons/breeze-dark`, retaining
the installed Breeze Dark index and theme fallback. It requires the system
Breeze, Papirus, and network-manager-applet icon packages. It refuses to replace
an existing unmanaged user theme.
Run it again after updating Breeze's theme layout. To uninstall, remove that
directory only if its `.hyprlife-tray-overlay` marker identifies this installer.

NetworkManager has no fixed icon override. Its real signal-strength, disconnected,
disabled, Ethernet, secure Wi-Fi, mobile/roaming, and VPN icons are recolored
while retaining their paths and opacity. All 33 connection-animation frames
(three stages, eleven frames each) and 14 VPN-animation frames are included.
Breeze artwork is preferred; missing states use Papirus or the applet's own
vector artwork. Dynamically requested `-secure` variants receive a lock badge
when no dedicated artwork exists. The installer checks every packaged nm-applet
icon name before writing the theme, failing if any state is missing. This
preserves changing signal bars and animations. Named OBS idle/active icons are included too.
The overlay is visible to other applications using Breeze Dark, not just Waybar.

The installer discovers the installed Papirus `16x16/apps` symlinks resolving to
`Zoom.svg`, `obs.svg`, and `steam.svg` and maps all of them to the corresponding
orange tray artwork. This covers `us.zoom.Zoom`, `zoom-desktop`, `zoom-icon`,
`com.obsproject.Studio`, `com.valvesoftware.Steam`, `steam-icon`, `steam-launcher`,
and `steampowered`, as well as the base names. Steam game icons are excluded by
checking each symlink's actual target. Waybar's known Zoom/Steam tray IDs use
the installed `us.zoom.Zoom.svg` and `com.valvesoftware.Steam.svg` aliases
directly: Steam advertises a private `IconThemePath` containing its white icon,
which takes precedence if only a theme name is configured.
Zoom's square outline and the larger OBS/Steam artwork are preserved.

Claude, Zoom, and Steam also have explicit Waybar overrides for apps that
supply pixels instead of theme names. Claude's observed ID is
`Claude_status_icon_1`; Zoom's is `zoom`; OBS's is `obs`; Steam's is `steam`.
Fixed app overrides don't show native unread/status artwork. The stock Waybar
0.15.0 loses these overrides on `NewIcon` updates. The user-local patched build
preserves them; see `waybar/patches/README.md` for the fix, rebuild instructions,
and rollback. NetworkManager and OBS have no fixed override and retain their
native state changes.

OBS uses native theme lookups instead of a fixed Waybar override. The installer
also installs `obs-tray`, `obs-tray-active`, and `obs-tray-paused` into its Flatpak
data directory, `~/.var/app/com.obsproject.Studio/data/icons/hicolor`. Restart OBS
after the first installation. This lets `QIcon::fromTheme` find all three states
instead of falling back to bundled bitmaps. The host theme contains the same
names, so Waybar keeps the orange color when recording starts, pauses, or stops.
The paused artwork adds a pause badge to the Papirus idle icon. App-local
themes are marked with `.hyprlife-tray-icons` (the earlier `.hyprlife-obs-tray`
marker is also accepted). The installer won't replace an unmanaged theme.
Installed Zoom and Steam Flatpaks receive their respective names and aliases
in their own data directories too. These aliases help native theme lookups;
they cannot force an app that supplies bundled bitmaps to use a theme instead.

Sources:

- `obs-tray.svg`, `obs-tray-active.svg`, `steam_tray_mono.svg`: recolored from
  the installed Papirus 24px panel icons. `zoom.svg` uses the camera path from
  Papirus's `Zoom.svg`. GPL-3.0; see `LICENSE-Papirus`.
- `claude.svg`: recolored from
  https://github.com/simple-icons/simple-icons/blob/develop/icons/claude.svg
  (Simple Icons, CC0).
- Generated network icons come from `/usr/share/icons/breeze-dark`; the
  installed license is `/usr/share/licenses/breeze-icon-theme/COPYING-ICONS`.
  Additional network states come from Papirus (GPL-3.0) and the applet's hicolor
  SVGs (`/usr/share/licenses/network-manager-applet/COPYING`).
- Waybar update handling:
  https://github.com/Alexays/Waybar/blob/0.15.0/src/modules/sni/item.cpp
  and https://github.com/Alexays/Waybar/blob/master/src/modules/sni/item.cpp.

Validation: resolved and rendered all 105 icon names shipped by the installed
nm-applet package through GTK at 16, 22, and 24px, with no missing sources or
non-orange foreground pixels. The installer also covers `nm-device-wireless`.
Temporary SNI `NewIcon` updates tested signal-strength changes, disconnected,
Ethernet, all three connecting stages, VPN connecting, and secured Ethernet
without changing the real network connection.
Claude, Zoom, and OBS were visually checked in the running tray.
An actual Qt tray test inside OBS's Flatpak verified the emitted icon names in
the sequence idle → recording → paused → idle, without making a recording.
All 11 installed Papirus application aliases were checked through GTK at the
configured tray size and resolve to the orange overlay.
