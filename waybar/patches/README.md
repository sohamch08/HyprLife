# Persistent tray overrides for Waybar 0.15

Waybar 0.15.0 applies `tray.icons` while reading an item's ID, but later
`NewIcon` signals replace its IconName/IconPixmap with the app's original icon.
Zoom emits such updates during startup, so a configuration-only override is
insufficient. Icon-theme aliases do not fix an app supplying bitmap pixels.

`0001-preserve-custom-tray-icons.patch` backports the upstream behavior: after
successfully applying an explicit override, ignore IconName/IconPixmap changes
for that item. Items without overrides retain their native state transitions,
including NetworkManager and OBS.

Reference: https://github.com/Alexays/Waybar/blob/master/src/modules/sni/item.cpp
(`has_custom_icon_` handling in `setProperty` and `setCustomIcon`).
Waybar source is MIT licensed. The patch applies to the official 0.15.0 archive.

The installed binary is `~/.local/libexec/waybar-tray-fix`. The system Waybar
package remains installed. A user-service drop-in selects the patched binary:
`systemd/user/waybar.service.d/20-tray-icon-fix.conf`.

To rebuild after installing the normal Waybar development dependencies:

```sh
sh ~/.config/waybar/scripts/build-tray-fixed-waybar.sh
systemctl --user restart waybar.service
```

The initial build used RPM headers extracted under `/tmp`, without installing
system packages. It retained the packaged runtime module dependencies. The
temporary header root required its top-level include path to be searched with
`-idirafter`, so standard C++ headers precede the extracted C headers.

Regression check: `python3 ~/.config/waybar/tests/tray-override-regression.py check`
adds a temporary item with the configured `Zoom` ID, then sends new bitmap and
icon-name values. It saves three tray-area screenshots under `/tmp` and exits
after four seconds. The stock build changed the override into a red square;
the patched build kept the same orange camera outline through both updates.
Real Zoom startup was also checked after activation. Native network state
updates continue to work because those items have no fixed override.

To revert, remove only the `20-tray-icon-fix.conf` link from
`~/.config/systemd/user/waybar.service.d`, run `systemctl --user daemon-reload`,
then restart `waybar.service`. Keep the drop-in disabled if using the unpatched
system package, or after a future Waybar update supplies this fix itself.
