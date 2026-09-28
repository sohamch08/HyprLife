# Tray icon changes: detailed record and rollback guide

Recorded on **2026-09-27**, for `/home/soham/projects/HyprLife`.

This report describes the changes made during the tray troubleshooting conversation, including the approaches that did not fully work, the final configuration, the files written outside the repository, verification performed, and how to undo the work. **Writing this report has not undone anything.**

## 1. Current result

The setup has three distinct parts:

1. **Orange artwork and CSS**, using `#f5af67`.
2. **Icon-theme entries and aliases**, including state-specific NetworkManager and OBS icons.
3. **A user-local patched Waybar**, which prevents applications such as Zoom from replacing explicit tray-icon overrides when they publish a new icon.

At the time this report was written, `waybar.service` was active and executing:

```text
/home/soham/.local/libexec/waybar-tray-fix
```

The packaged executable, `/usr/bin/waybar`, remains installed. The installed package was `waybar-0.15.0-2.fc44.x86_64`. The custom executable still reports `Waybar v0.15.0`; its path, not the version string alone, distinguishes it.

The final custom executable's SHA-256 was:

```text
01c7efc23b6da2f59bce271ffa19a4bd5ea1fcc2c1b8a025ef7e4dc98d4fd111
```

This is not a universal recoloring engine for every future application. Known apps have explicit overrides or matching theme entries. A new app with a different tray ID, a private icon path, or embedded bitmap artwork can still require configuration.

## 2. What was already present, and what is preserved

The repository already supplied your live Waybar configuration through this symlink:

```text
/home/soham/.config/waybar -> /home/soham/projects/HyprLife/waybar
```

Consequently, editing repository files changed the live configuration. I did not create that symlink.

Important pre-existing or user-authored details:

- The Telegram file override in `waybar/config.jsonc` was already commented out when I first inspected it. Its referenced file did not exist. I kept that comment rather than restoring the old Git version of the line.
- You subsequently added `show-passive-items: true`. It appeared inside the `icons` map; I moved it to the correct level directly under `tray`. The rollback preserves this preference.
- Your KDE Connect launcher now contains `Exec=sh -c "kdeconnect-indicator & exec kdeconnect-app"`. I provided the instructions for that change, but did not write the launcher myself. The rollback leaves it in place, with a separate optional undo procedure below.
- At report time, `hypr/modules/windowrules.lua` had an unrelated modification. It is not part of this tray work and the rollback does not touch it.
- The existing Spotify entry, tray size, tray spacing, and unrelated modules were retained.

**Do not use `git reset --hard`, `git clean -fd`, or a blanket `git restore` to undo this work.** Those operations could also remove your own changes. The supplied rollback edits the specific tray additions and backs up the affected files.

## 3. Why the original icons were missing or inconsistent

### 3.1 Telegram was present but effectively invisible

Telegram had registered an active StatusNotifierItem on the session D-Bus. It supplied a symbolic icon name. Your CSS grouped `#tray` with other modules and assigned both its background and foreground the same almost-black color, `#080303`.

Symbolic icons can inherit that foreground color. Telegram therefore appeared black against the black tray background.

I added this dedicated rule in `waybar/style.css`:

```css
#tray {
  /* Symbolic tray icons inherit this foreground color. */
  color: #f5af67;
}
```

That made Telegram visible and established the requested orange color for symbolic tray artwork. A trailing blank line in the stylesheet also changed; that is formatting only.

### 3.2 KDE Connect's indicator had lost its registration

`kdeconnect-indicator` was running. Its secondary D-Bus connection exposed an active StatusNotifierItem, but the item was absent from the watcher's registered list.

I used the indicator's normal Qt quit method and relaunched `kdeconnect-indicator` through UWSM. Its registration returned and the icon became visible. This was a process restart, not a persistent daemon or networking reconfiguration.

The evidence established the missing registration and the successful restart. It did not establish a definitive underlying cause for why that registration had been lost.

KDE Connect has separate processes:

| Process | Role |
| --- | --- |
| `kdeconnect-app` | Main application window |
| `kdeconnect-indicator` | Tray icon and menu |
| `kdeconnectd` | Background device communication |

Your `Mod+Shift+Q` binding invokes `hl.dsp.window.kill()`. Killing the main application's window does not automatically terminate the independent indicator. The indicator, rather than the daemon alone, owns the tray icon.

### 3.3 Apps do not all supply the same kind of icon

A tray app can publish a theme name, an absolute image path, or raw pixels through `IconName`/`IconPixmap`. It can also advertise a private `IconThemePath` and issue `NewIcon` signals when its state changes.

That distinction explains why a single foreground-color rule worked for Telegram but did not automatically recolor every other app. Existing icons in Papirus are useful only if the relevant icon name is requested and the consuming application can find that theme entry.

## 4. The initial approaches and their limitations

Several intermediate changes were useful but insufficient. They were followed by the fixes below.

| Intermediate approach | What it achieved | Why it was insufficient |
| --- | --- | --- |
| Set the tray foreground to orange | Made Telegram's symbolic icon visible | Does not recolor arbitrary bitmap pixels |
| Override `nm-applet` with one Wi-Fi symbol | Produced an orange Wi-Fi icon initially | Lost signal-strength detail, and later updates replaced it |
| Add static app-icon overrides | Made known apps orange after a bar reload | Stock Waybar 0.15 could overwrite them after `NewIcon` |
| Add standard app-name aliases | Made the relevant artwork discoverable | Did not force Zoom to stop sending its own bitmap |
| Override OBS with one idle icon | Made OBS orange initially | Did not correctly preserve recording and paused states |
| Refer to Steam by a theme name | Found the right host-theme asset in GTK tests | Steam advertised a private icon directory that took priority in Waybar |

The final setup removes the fixed NetworkManager and OBS overrides. It uses state-specific artwork for those applications and a Waybar fix for apps that need a fixed override.

## 5. Final Waybar configuration

The configured tray size remains **21 pixels**, with **10 pixels of spacing**. Enlarging OBS and Steam changed the artwork's internal padding, not these global tray settings.

The relevant final override mappings are:

| Tray ID / key | Configured artwork |
| --- | --- |
| `chatgpt` | `/home/soham/.config/waybar/assets/chatgpt-tray.svg` |
| `claude`, `Claude`, `Claude_status_icon_1` | `/home/soham/.config/waybar/assets/tray/claude.svg` |
| `zoom`, `Zoom` | `/home/soham/.local/share/icons/breeze-dark/status/24/us.zoom.Zoom.svg` |
| `steam`, `Steam` | `/home/soham/.local/share/icons/breeze-dark/status/24/com.valvesoftware.Steam.svg` |
| `KDE Connect Indicator` | `kdeconnect-tray-symbolic` |
| `nm-applet` | No fixed override; uses its real state-specific icon names |
| `obs` | No fixed override; uses idle, recording, and paused theme names |

The actual observed Claude tray ID was `Claude_status_icon_1`. Zoom's was `zoom`, OBS's was `obs`, and Steam's was `steam`.

ChatGPT used Electron's generic `chrome_status_icon_1` ID. Waybar has special handling for that ID, taking the lowercased tooltip text as the override key; that is why `chatgpt` is used in the configuration.

`show-passive-items` is enabled directly under `tray`, so an otherwise valid passive item is not hidden merely because its status is passive. This affects all passive tray items, not just KDE Connect.

## 6. SVG artwork changes

### ChatGPT

I extracted an existing OpenAI logo SVG from the installed application's archive at `/usr/lib/chatgpt/resources/app.asar`, specifically its `openai-logo-regular-ceb75a1754fa.svg` asset. I changed its visible fixed fill to orange and saved it as:

```text
/home/soham/projects/HyprLife/waybar/assets/chatgpt-tray.svg
```

The application archive itself was not modified. The result is a recolored local vector asset, not an AI-generated image.

### Claude

I downloaded the Claude vector from Simple Icons and recolored it to orange. It is stored as `waybar/assets/tray/claude.svg`. This was necessary because the application supplied its own tray image rather than a host theme name.

### Zoom

I used the camera path from the installed Papirus `24x24/apps/Zoom.svg` and recolored it. At your request, I added a rounded-square outline around it:

```xml
<rect x="2" y="2" width="20" height="20" rx="4"
      fill="none" stroke="#f5af67" stroke-width="1.4"/>
```

The SVG uses a `0 0 24 24` viewBox. The resulting source asset is `waybar/assets/tray/zoom.svg`.

### OBS

The idle and recording artwork came from Papirus's `obs-tray.svg` and `obs-tray-active.svg`. Both were recolored.

To make the idle icon larger, its viewBox was narrowed to `3 3 18 18` while keeping a 24-by-24 output size. That enlarges the visible idle artwork by about one third. The active icon uses `3 3 19 19` to leave room for its recording label.

I also created `obs-tray-paused.svg` from the idle vector with an added pause badge. Its viewBox leaves space for the badge. Thus the orange idle, recording, and paused icons remain distinguishable.

### Steam

The source was Papirus's monochrome panel icon, `steam_tray_mono.svg`. I recolored it and changed its viewBox to `3 3 18 18`, enlarging its visible artwork by about one third without changing the tray's spacing.

### Licenses and attribution

- Papirus-derived assets retain a copy of the installed GPL license in `waybar/assets/tray/LICENSE-Papirus`.
- The Claude source is from [Simple Icons](https://github.com/simple-icons/simple-icons/blob/develop/icons/claude.svg), whose project uses CC0.
- The generated Breeze-based network artwork comes from the installed theme; its local license is `/usr/share/licenses/breeze-icon-theme/COPYING-ICONS`.
- NetworkManager's fallback SVGs come from its installed hicolor resources; see `/usr/share/licenses/network-manager-applet/COPYING`.
- Waybar's source is MIT licensed. The small local patch is kept separately from the downloaded source tree.

## 7. NetworkManager: full state coverage

The original fixed `nm-applet` override was removed. The installer now provides orange versions of the names that NetworkManager actually requests.

Coverage includes:

- Disconnected and networking-disabled states.
- Wired/Ethernet states, including secure variants.
- Wi-Fi signal levels, including zero signal.
- Secure Wi-Fi variants.
- All **33 connection-animation frames**: three stages with eleven frames each.
- All **14 VPN connecting-animation frames**.
- VPN active/locked variants.
- Mobile network technologies, signal levels, and roaming icons.
- Related Bluetooth and network icons.

The installer first uses Breeze artwork where available, supplements missing states from Papirus panel and animation directories, then uses the applet's own hicolor SVGs where needed. It preserves path geometry and opacity, so dim signal bars and animations continue to convey state.

When a dynamically requested `-secure` name has no dedicated artwork, the installer creates a lock-badged version of the base icon. The badge uses an orange outline and a dark backing for legibility.

The installed package exposed **105 packaged icon names**. The installer also covers `nm-device-wireless`, giving **106 required names** in its coverage check. It checks that those names exist at 16, 22, and 24 pixels before writing the theme. The full overlay contains additional related icons and aliases beyond that required set.

This covers the installed applet version and the discovered states. It cannot guarantee names introduced by a future version; rerunning the installer after updates will recheck the installed resources.

## 8. The theme installer and where it writes

The installer is:

```text
/home/soham/projects/HyprLife/waybar/scripts/install-tray-theme.py
```

A normal invocation writes the host overlay and, where the corresponding app directories exist, app-local Flatpak themes:

```bash
python3 /home/soham/projects/HyprLife/waybar/scripts/install-tray-theme.py
systemctl --user restart waybar.service
```

An alternate destination generates only the host overlay for inspection and does not install the Flatpak themes:

```bash
python3 /home/soham/projects/HyprLife/waybar/scripts/install-tray-theme.py /tmp/tray-theme-preview
```

### Host overlay

```text
/home/soham/.local/share/icons/breeze-dark
```

The installer copies the system Breeze Dark index and writes matching icon entries under the user theme path. The existing system theme and its fallback remain available. Its ownership marker is:

```text
.hyprlife-tray-overlay
```

The installer refuses to overwrite an existing destination without that marker. It does not delete unrelated system theme files or modify `/usr/share/icons`.

**Scope:** this is a user icon-theme overlay, not a Waybar-only rendering filter. Other applications using the same Breeze Dark theme and icon names can also see the orange versions. The generated app aliases may also be used outside the tray.

### Flatpak app-local themes

The following were actually created:

```text
/home/soham/.var/app/com.obsproject.Studio/data/icons/hicolor
/home/soham/.var/app/us.zoom.Zoom/data/icons/hicolor
```

Their current marker is `.hyprlife-tray-icons`. The OBS directory also retains the earlier `.hyprlife-obs-tray` marker, which the installer accepts for compatibility.

The installer supports a Steam Flatpak directory if one exists, but none was installed during this work. Native Steam was the observed running application. The rollback described here removes only the OBS and Zoom app-local themes actually created in this session.

App-local themes make named icons discoverable inside the sandbox. They do not compel an application to stop publishing bundled bitmap pixels.

### Color selection

The script now offers a **`--color` option**, added after the original report at your request. It accepts three- or six-digit hex colors, with or without `#`, and defaults to the original `#f5af67`.

```bash
# Generate only, without changing the installed themes:
python3 /home/soham/projects/HyprLife/waybar/scripts/install-tray-theme.py /tmp/my-tray-theme --color '#89b4fa'

# Install into the host theme and supported existing Flatpak profiles:
python3 /home/soham/projects/HyprLife/waybar/scripts/install-tray-theme.py --color '#89b4fa'
```

Every generated network and application SVG uses the selected foreground, including aliases, connection states, lock symbols, and OBS badges. Dark badge backings and opacity are preserved. ChatGPT is now included as `status/24/chatgpt-tray.svg`, increasing the host SVG count from 1,128 to 1,129 with the same installed source packages. Invalid colors are rejected before any files are written. An explicit destination suppresses Flatpak installation regardless of other options.

The generator does not overwrite repository source artwork or edit Waybar CSS/configuration. To match the entire running tray, separately set the `#tray` CSS foreground and point the existing ChatGPT/Claude file overrides to the generated files in `~/.local/share/icons/breeze-dark/status/24/` using absolute paths. Zoom and Steam already reference the generated aliases. Restart Waybar and affected apps afterward.

Validation of this addition generated all 1,129 SVGs in temporary directories with a custom six-digit color, a short hex color, and the default orange. Every SVG parsed and contained only the chosen foreground plus any preserved dark badge backing. Flatpak alias/state generation was checked against temporary app profiles. No installed theme was recolored during those tests.

## 9. Papirus aliases from your pasted listing

The installer now discovers symlinks in the installed Papirus `16x16/apps` directory by comparing their resolved targets. It does not assume that every file containing the word `steam` belongs to the Steam client's tray icon.

The eleven relevant names were:

| App | Names and aliases |
| --- | --- |
| Zoom | `Zoom`, `us.zoom.Zoom`, `zoom-desktop`, `zoom-icon` |
| OBS | `obs`, `com.obsproject.Studio` |
| Steam | `steam`, `com.valvesoftware.Steam`, `steam-icon`, `steam-launcher`, `steampowered` |

All eleven were installed as mappings to the corresponding orange artwork and checked through GTK at the configured tray size.

The many `steam_icon_<number>` files in the pasted output were game icons and were excluded. `preferences-desktop-accessibility-zoom.svg` was also excluded because it is unrelated to the Zoom meeting app.

Steam advertised this private icon search path:

```text
/home/soham/.local/share/Steam/public
```

A plain theme-name override still allowed Waybar to select Steam's private white icon. The final Steam override therefore points directly to the installed orange `com.valvesoftware.Steam.svg` alias. Steam's own installation files were not modified.

## 10. OBS's native state-icon fix

Before the application-side fix, OBS published an empty `IconName` and a bitmap. Its Flatpak runtime could not find the themed state icons and therefore used bundled resource images.

I installed these three names in its own hicolor theme:

```text
obs-tray
obs-tray-active
obs-tray-paused
```

I then removed OBS's fixed Waybar override. This allows its `QIcon::fromTheme` calls to use named artwork and lets recording/paused/idle transitions remain visible.

Before restarting OBS, I checked the tray menu and logs. The menu offered **Start Recording** and **Start Streaming**, indicating those outputs were stopped. I used its normal **Exit** menu action and reopened it. Later, the process exited with status 137 during the session. I did not establish the cause of that termination. Logs during that interval showed a brief recording start and stop; I did not issue a Start Recording action.

For verification after that, I used a small Qt tray test inside the same Flatpak runtime. It did not capture audio or video. It confirmed that all three names could be loaded and emitted the actual D-Bus sequence:

```text
obs-tray → obs-tray-active → obs-tray-paused → obs-tray
```

The resulting recording and pause icons were visually checked in the tray.

## 11. The Waybar bug and the durable override fix

### The failure

Stock Waybar 0.15.0 applied the configured custom icon when it read an item's ID. Later, when the app emitted `NewIcon`, Waybar read its new `IconName` and `IconPixmap` and replaced the custom artwork.

Zoom did this during startup. That is why its orange icon could look correct immediately after reloading Waybar and then turn blue when the app started or updated its icon. The earlier alias changes did not solve this behavior.

### The patch

The patch is:

```text
/home/soham/projects/HyprLife/waybar/patches/0001-preserve-custom-tray-icons.patch
```

It adapts the upstream `has_custom_icon_` behavior in [Waybar's item implementation](https://github.com/Alexays/Waybar/blob/master/src/modules/sni/item.cpp):

1. Add a boolean field recording whether a custom icon was successfully applied.
2. Set it after loading an explicit image override or selecting an explicit theme-name override.
3. Ignore subsequent `IconName` and `IconPixmap` updates for that item when the flag is set.
4. Continue processing normal updates for items that have no explicit override.

Thus Zoom, Steam, Claude, and ChatGPT keep their configured artwork. NetworkManager and OBS can still change icons because their fixed overrides were removed.

A consequence of intentionally fixed overrides is that native unread-count or other icon artwork may no longer be displayed for those apps. This patch preserves the selected artwork rather than attempting to recolor arbitrary incoming pixels.

### How it was built

The configured repositories offered the same installed Waybar version, so I built a local patched executable from the official 0.15.0 source archive.

Source archive SHA-256:

```text
21c2bbef88c40473c355003582f9331d2f9b8a01efdcce0935edfc5f6b023a3e
```

I downloaded development RPMs and extracted their headers into a temporary build root. **Those packages were downloaded, not installed into the operating system.** Some 32-bit dependencies were also downloaded during the first dependency request; only 64-bit and noarch packages were extracted for the build.

The temporary root reused installed runtime libraries through links. Its top-level header directory had to be searched with `-idirafter` so C++ standard headers were found before the extracted C headers. That resolved a build issue involving PipeWire math declarations without changing system headers.

The first working build lacked the packaged radio-status feature setting. I corrected that with `-Drfkill=enabled`, rebuilt, and activated the final version. The final startup no longer showed the missing-rfkill-support warning.

The binary was staged through Meson's install process before being copied to the user executable directory. This removed temporary build-library search paths. `readelf` and `ldd` checks found no remaining `/tmp` runtime dependencies or missing shared libraries.

### Rebuild helper

```text
/home/soham/projects/HyprLife/waybar/scripts/build-tray-fixed-waybar.sh
```

This script downloads and verifies the pinned source archive, applies the patch, builds it, stages the installation, and installs the result at:

```text
/home/soham/.local/libexec/waybar-tray-fix
```

Unlike the one-time temporary-header procedure, this helper expects the ordinary Waybar development dependencies to already be available. It does not install those dependencies itself.

```bash
sh /home/soham/projects/HyprLife/waybar/scripts/build-tray-fixed-waybar.sh
systemctl --user restart waybar.service
```

The helper builds with two jobs by default; `BUILD_JOBS` can change that. It disables test-suite/man-page generation, systemd-unit installation, Cava, and sndio, and explicitly enables the dependencies used by your main tray/network/audio setup and rfkill. Other optional modules depend on the available build dependencies. Rebuilding on a different machine can therefore produce a different optional module set.

The installed binary is not automatically replaced by a future distribution Waybar update. When a packaged version includes the fix, the service override can be removed to return to the maintained package.

## 12. How systemd selects the patched binary

Repository file:

```text
/home/soham/projects/HyprLife/systemd/user/waybar.service.d/20-tray-icon-fix.conf
```

Contents:

```ini
[Service]
# User-local Waybar 0.15 with the upstream custom-icon update fix backported.
ExecStart=
ExecStart=%h/.local/libexec/waybar-tray-fix
```

The empty `ExecStart=` clears the packaged command, and the following line supplies the user-local executable. `%h` expands to your home directory.

Installed symlink:

```text
/home/soham/.config/systemd/user/waybar.service.d/20-tray-icon-fix.conf
  -> /home/soham/projects/HyprLife/systemd/user/waybar.service.d/20-tray-icon-fix.conf
```

I ran `systemctl --user daemon-reload` and restarted `waybar.service` to activate it. Existing unrelated service drop-ins, including runtime CPU/IO weight settings, were not edited.

Your existing bar-restart shortcut invokes a script that restarts `waybar.service`, so it now starts this selected executable as well.

## 13. Repository file inventory

All paths below are relative to `/home/soham/projects/HyprLife`.

| File or directory | Change / purpose |
| --- | --- |
| `waybar/config.jsonc` | App overrides, explanatory comments, correctly placed passive-item setting |
| `waybar/style.css` | Orange `#tray` foreground rule |
| `waybar/assets/chatgpt-tray.svg` | Extracted and recolored ChatGPT vector |
| `waybar/assets/tray/claude.svg` | Orange Claude logo |
| `waybar/assets/tray/zoom.svg` | Orange camera with rounded-square outline |
| `waybar/assets/tray/obs-tray.svg` | Enlarged orange idle OBS icon |
| `waybar/assets/tray/obs-tray-active.svg` | Enlarged orange active/recording OBS icon |
| `waybar/assets/tray/obs-tray-paused.svg` | Orange OBS icon with pause badge |
| `waybar/assets/tray/steam_tray_mono.svg` | Enlarged orange Steam icon |
| `waybar/assets/tray/LICENSE-Papirus` | License for Papirus-derived artwork |
| `waybar/assets/tray/README.md` | Theme installation, sources, and limitations |
| `waybar/scripts/install-tray-theme.py` | Generates/installs host and app-local theme entries |
| `waybar/scripts/build-tray-fixed-waybar.sh` | Rebuilds the local patched executable |
| `waybar/patches/0001-preserve-custom-tray-icons.patch` | Persistent override fix |
| `waybar/patches/README.md` | Patch explanation, rebuild, and limited rollback |
| `waybar/tests/tray-override-regression.py` | Temporary StatusNotifierItem regression test |
| `systemd/user/waybar.service.d/20-tray-icon-fix.conf` | Selects local patched executable |
| `maintenance/undo-tray-changes.py` | Durable backup-first rollback script added with this report |
| `docs/tray-theming-and-rollback.md` | This report |

No Git commit or push was made as part of this work.

## 14. Persistent changes outside the repository

| Path | What was written | Undo behavior |
| --- | --- | --- |
| `~/.local/share/icons/breeze-dark` | Marked user theme overlay | Back up and remove the marked directory |
| `~/.var/app/com.obsproject.Studio/data/icons/hicolor` | Marked OBS-local icons and aliases | Back up and remove the marked directory |
| `~/.var/app/us.zoom.Zoom/data/icons/hicolor` | Marked Zoom-local icons and aliases | Back up and remove the marked directory |
| `~/.local/libexec/waybar-tray-fix` | Patched executable | Back up and remove it after removing its service selection |
| `~/.config/systemd/user/waybar.service.d/20-tray-icon-fix.conf` | Symlink selecting the patched executable | Back up and remove only this drop-in |

I did not change the system icon files, install system development packages, replace `/usr/bin/waybar`, change the system-wide service, edit Telegram account settings, or change your actual network connection. Temporary Flatpak test invocations granted access to a test executable for that invocation; they did not add persistent `flatpak override` permissions.

Temporary files were also created under `/tmp`: source archives, extracted RPM headers, build/staging outputs, temporary Qt and D-Bus test programs, screenshots, and the first rollback-script copy. These are not required by the final installed binary. Package-manager metadata/cache files may have been updated by repository queries and downloads. The rollback does not attempt to reset those caches or shell/app history.

## 15. Verification performed and its limits

### Initial investigation

- Read the repository configuration, CSS, and service launch setup.
- Queried session D-Bus registrations and icon properties.
- Checked Waybar's journal and installed package version.
- Checked relevant icon resources and Flatpak permissions.
- Captured only the relevant tray area for visual comparisons.

### Network icons

- Checked every packaged NetworkManager icon name against the generated set.
- Resolved and rendered all 105 packaged names at 16, 22, and 24 pixels.
- Checked rendered foreground pixels for non-orange colors.
- Parsed generated SVG files.
- Used temporary tray items to simulate weak/strong signal, disconnected, Ethernet, all connecting stages, VPN connecting, and secured Ethernet.
- Did not disconnect Wi-Fi, start a VPN, or change the real connection to perform those checks.

These tests validate name resolution, artwork, and tray update behavior. They do not constitute an end-to-end test of every physical network device or every future NetworkManager version.

### OBS

- Checked that its Flatpak runtime could find all three themed names.
- Used a Qt tray program in the same runtime to publish idle → active → paused → idle.
- Verified the actual D-Bus icon names and visually checked active/paused rendering.
- Did not start a recording as part of that test.

### Persistent overrides

The regression helper creates a temporary tray item using the configured `Zoom` key, then publishes a new red bitmap and an unrelated icon name. It exits automatically after roughly four seconds.

The stock build displayed 441 red pixels after the bitmap update. The patched build retained the orange camera through initial display, bitmap update, and icon-name update. Final screenshots were inspected, and a pixel check found no replacement red bitmap.

I also reopened the real Zoom application and checked its icon after startup updates. It remained orange with the rounded-square outline.

The helper can be rerun with:

```bash
python3 /home/soham/projects/HyprLife/waybar/tests/tray-override-regression.py check
```

It writes screenshots under `/tmp`. Its screenshot rectangle is tailored to this desktop's tray position. It is a visual regression helper, not a portable automated GUI test suite. The upstream Waybar test suite was not run; the build disabled it.

### Final executable and service

- The source compiled and staged successfully.
- `waybar --version` ran successfully.
- Runtime shared libraries resolved without temporary build paths.
- The service reported `ActiveState=active` and the intended executable.
- Final startup retained radio-status support.
- `git diff --check` was used to check patch whitespace.

The existing height warning and early empty-item icon messages were still present. This work addressed icon visibility and override persistence; it did not claim to eliminate every Waybar log warning.

## 16. Recommended full rollback

A durable copy of the rollback tool is now kept outside the directories that it removes:

```text
/home/soham/projects/HyprLife/maintenance/undo-tray-changes.py
```

The earlier `/tmp/hyprlife-undo-tray-changes.py` copy is temporary and can disappear on reboot or cleanup. Prefer the repository copy.

### Step 1: Preview

```bash
python3 /home/soham/projects/HyprLife/maintenance/undo-tray-changes.py
```

The default mode prints the exact files and directories it would change. It does not create a backup, edit files, remove anything, or restart the service.

### Step 2: Apply when you want the rollback

Save any work in OBS or Zoom first. The script itself does not close those applications.

```bash
python3 /home/soham/projects/HyprLife/maintenance/undo-tray-changes.py --apply
```

It will:

1. Check that the added CSS block still matches what it knows how to remove.
2. Check the marker files on the generated theme directories.
3. Check that the Waybar drop-in symlink still points to the expected repository file.
4. Create a timestamped backup beneath `~/.local/share/HyprLife-backups/`.
5. Back up both modified configuration files and all listed generated files/directories before deleting anything.
6. Remove the added app override entries and their explanatory comments from the tray block.
7. Remove the dedicated orange foreground CSS rule.
8. Remove the generated themes, patched executable, service override, and supporting source assets/scripts/test files listed in the preview.
9. Reload user systemd configuration.
10. Restart Waybar using its remaining service configuration, normally `/usr/bin/waybar`.

Backups preserve paths relative to `/home/soham`. For example, the configuration backup will be under:

```text
<backup-directory>/projects/HyprLife/waybar/config.jsonc
```

The tool copies files into the backup and then removes their originals; the preview's "Back up, then remove" wording reflects that sequence.

### Step 3: Restart icon-consuming applications

Close and reopen OBS and Zoom when convenient to clear any cached themed artwork. Other apps using the user Breeze Dark overlay may also need a restart, or you can log out and log back in.

The rollback removes the orange CSS rule, so the original black-on-black symbolic-icon problem can return. This is expected when fully restoring the old styling. To keep Telegram visible while undoing the rest, re-add a readable `#tray` foreground color afterward.

### What the rollback preserves

- Your already-commented Telegram file override.
- The current `show-passive-items: true` setting at the proper tray level.
- Your KDE Connect launcher customization.
- Unrelated repository changes, including `hypr/modules/windowrules.lua`.
- This report and the durable rollback script.
- The installed system packages and the original packaged Waybar.
- Recording files, application settings unrelated to the generated themes, and personal application data.

Empty helper directories can remain after their files are removed. They have no effect on the desktop.

### Rollback limitations

The tool is written for this account, repository location, and the current generated files. It is not a general-purpose uninstaller.

If you later add unrelated files inside one of the generated directories, applying the rollback will back up the entire directory and remove it from its original location. Review the preview and back up any later work you want to keep installed.

The tool deliberately stops if its known CSS block, theme markers, or service symlink no longer match. If configuration structure is substantially rearranged, its tray-block lookup can also fail. Inspect the changed files rather than bypassing the checks blindly.

It is not a transaction manager: a filesystem or service failure after the backup phase can leave a partially completed rollback. The backup remains available. If only the service restart fails, inspect `systemctl --user status waybar.service` and the remaining drop-ins, then restart it once the configuration is corrected.

## 17. Undo only the patched Waybar, keeping the orange theme

Use this narrower rollback if you want to return to the packaged executable while retaining the icons and theme assets:

```bash
mkdir -p /home/soham/.local/share/HyprLife-backups
mv /home/soham/.config/systemd/user/waybar.service.d/20-tray-icon-fix.conf \
   /home/soham/.local/share/HyprLife-backups/20-tray-icon-fix.conf.disabled
systemctl --user daemon-reload
systemctl --user restart waybar.service
systemctl --user show waybar.service -p ExecStart -p ActiveState
```

If that backup filename already exists, choose a new filename rather than overwriting an older backup.

Leave the binary and repository patch files in place if you may want to reactivate them later. They do not run without the drop-in selecting the binary.

**Expected consequence:** the stock 0.15.0 bug can return, so Zoom or another bitmap-supplying app may replace its orange override again. The NetworkManager and OBS native theme fixes remain installed.

To reactivate the local build, first confirm the executable still exists, then recreate the original symlink and reload/restart the service:

```bash
ln -s /home/soham/projects/HyprLife/systemd/user/waybar.service.d/20-tray-icon-fix.conf \
      /home/soham/.config/systemd/user/waybar.service.d/20-tray-icon-fix.conf
systemctl --user daemon-reload
systemctl --user restart waybar.service
```

This assumes that the destination symlink is absent. Do not overwrite a different override that you have subsequently created.

## 18. Manual full rollback, if you do not want to use the script

First copy the affected configuration files, generated directories, executable, and drop-in to a backup directory. The inventory in sections 13 and 14 is the deletion checklist.

Then perform these actions in order:

1. Remove only the `20-tray-icon-fix.conf` symlink from your user-service directory. Do not use `systemctl revert waybar.service`, because that can remove other custom drop-ins too.
2. In `waybar/config.jsonc`, remove the added mappings listed in section 5 and their added explanatory comments. Keep your original Spotify entry and commented Telegram entry. Keep or remove `show-passive-items` according to your preference.
3. In `waybar/style.css`, remove only the dedicated five-line orange `#tray` block shown in section 3.1.
4. Remove the marked user `breeze-dark` overlay and the marked OBS/Zoom app-local hicolor directories listed in section 14. Do not delete the system icon themes.
5. Remove the user-local patched binary once its service override has been removed.
6. Remove the repository additions from section 13 if you no longer want to retain the source work. Keep this report and rollback script if you want an audit trail.
7. Run `systemctl --user daemon-reload` followed by `systemctl --user restart waybar.service`.
8. Restart OBS and Zoom when convenient.

This is what the automated script performs with backups and checks. It is safer than restoring the entire repository to its Git baseline.

## 19. Optional undo of the KDE Connect launcher advice

This is separate because the launcher was not written by my tools and the normal rollback preserves it.

Your current user launcher is:

```text
/home/soham/.local/share/applications/org.kde.kdeconnect.app.desktop
```

Its current command is:

```ini
Exec=sh -c "kdeconnect-indicator & exec kdeconnect-app"
```

To stop launching the indicator automatically with the window, back up that file and change only the command back to:

```ini
Exec=kdeconnect-app
```

Alternatively, if this user launcher was created solely for that customization and contains nothing else you want to retain, move it out of `~/.local/share/applications`; the packaged desktop entry will then be available again. Prefer editing only `Exec` if you are uncertain about other customizations.

This does not stop an already-running indicator. To remove its current tray icon while leaving the connection daemon alone, quit the indicator separately. A previously used command was:

```bash
pkill -f '^(/usr/bin/)?kdeconnect-indicator$'
```

That command targets the matching indicator process, not the KDE Connect daemon. There is no persistent "undo" for the earlier one-time indicator restart.

## 20. Optional cleanup of temporary build/test files

The main temporary build directory was `/tmp/hyprlife-waybar-build`, with the source archive at `/tmp/hyprlife-waybar-0.15.0.tar.gz`. Test sources, executables, generated icon previews, and tray screenshots also used specific `/tmp/hyprlife-*` names.

They can be removed when no build or test is running and after retaining any evidence you want. Inspect the exact paths before deleting them; do not use a broad wildcard if you have since created other files with the same prefix.

No installed runtime component needs these temporary files. The normal rollback leaves them alone, and normal temporary-directory cleanup may remove them later. DNF metadata/cache cleanup is also optional and is separate from restoring the desktop behavior.

## 21. Reapplying after a full rollback

The backup contains the pre-rollback state, including the patched executable and theme assets. Restore only the paths you want from that backup, maintaining their original locations and symlink targets. Restore the repository files before restoring the service symlink that points to them.

A full restoration requires the modified Waybar configuration and CSS, source SVGs, generated host/app themes, patched executable, and service override. Then run `systemctl --user daemon-reload` and restart `waybar.service`.

Do not reinstall a stale patched binary blindly after major system-library upgrades. If it no longer loads, use the packaged Waybar by disabling the drop-in, then rebuild or migrate to a fixed packaged release.

## 22. What was done for this documentation request

I inspected the current service command, symlink, binary checksum, configuration, installer, patch, and helper documentation. I saved the rollback script at a durable repository path and prepared this report.

The rollback was previewed against the real setup. Its apply path was tested only in an isolated temporary fixture with a fake home directory and a stubbed `systemctl`; the actual desktop rollback was **not** applied.

The durable rollback script and this report intentionally remain after rollback so that the backup location, original decisions, and recovery instructions are still available.
