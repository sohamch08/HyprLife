#!/usr/bin/env python3
"""Preview by default. --apply backs up and rolls back this session's tray changes."""
from datetime import datetime
from pathlib import Path
import argparse
import re
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply', action='store_true', help='perform the printed rollback with backups')
args = parser.parse_args()
home = Path('/home/soham')
repo = home / 'projects/HyprLife'
config = repo / 'waybar/config.jsonc'
style = repo / 'waybar/style.css'
config_text = config.read_text()
start = config_text.index('  "tray": {')
end = config_text.index('  "clock": {', start)
tray = config_text[start:end]
keys = ['chatgpt', 'claude', 'Claude', 'Claude_status_icon_1', 'zoom', 'Zoom', 'steam', 'Steam', 'KDE Connect Indicator']
for key in keys:
    tray = re.sub(r'^\s*"' + re.escape(key) + r'":.*\n', '', tray, flags=re.M)
comments = [
    '// nm-applet uses the tray theme\'s real signal-strength icons.',
    '// Resolve tray IDs through the installed Papirus alias mappings.',
    '// Steam advertises a private IconThemePath; use the installed alias directly.',
    '// OBS supplies themed idle/recording/paused icons from its Flatpak data directory.',
]
for comment in comments:
    tray = re.sub(r'^\s*' + re.escape(comment) + r'\n', '', tray, flags=re.M)
new_config = config_text[:start] + tray + config_text[end:]
css_block = '#tray {\n  /* Symbolic tray icons inherit this foreground color. */\n  color: #f5af67;\n}\n\n'
style_text = style.read_text()
if css_block not in style_text:
    raise SystemExit('The added #tray CSS has changed; review it before using this rollback.')
new_style = style_text.replace(css_block, '', 1)

managed = [
    (home / '.local/share/icons/breeze-dark', '.hyprlife-tray-overlay'),
    (home / '.var/app/com.obsproject.Studio/data/icons/hicolor', '.hyprlife-tray-icons'),
    (home / '.var/app/us.zoom.Zoom/data/icons/hicolor', '.hyprlife-tray-icons'),
]
for path, marker in managed:
    if path.exists() and not (path / marker).is_file():
        raise SystemExit(f'Refusing to move an unmarked theme: {path}')
link = home / '.config/systemd/user/waybar.service.d/20-tray-icon-fix.conf'
expected_link = repo / 'systemd/user/waybar.service.d/20-tray-icon-fix.conf'
if link.exists() or link.is_symlink():
    if not link.is_symlink() or link.resolve() != expected_link:
        raise SystemExit(f'The Waybar service override has changed: {link}')
paths = [link, home / '.local/libexec/waybar-tray-fix']
paths += [path for path, _ in managed]
paths += [repo / p for p in [
    'systemd/user/waybar.service.d/20-tray-icon-fix.conf',
    'waybar/assets/chatgpt-tray.svg', 'waybar/assets/tray',
    'waybar/patches', 'waybar/tests/tray-override-regression.py',
    'waybar/scripts/install-tray-theme.py', 'waybar/scripts/build-tray-fixed-waybar.sh',
]]
paths = [p for p in paths if p.exists() or p.is_symlink()]
backup = home / '.local/share/HyprLife-backups' / datetime.now().strftime('tray-rollback-%Y%m%d-%H%M%S-%f')
print('Backup directory:', backup)
print('Edit:', config, '(remove added overrides; keep your original entries)')
print('Edit:', style, '(remove orange tray foreground)')
for path in paths:
    print('Back up, then remove:', path)
print('Reload user services and restart packaged Waybar.')
print('Preserve: commented Telegram override, show-passive-items, KDE Connect launcher.')
print('Preserve: unrelated repository edits, this rollback script, and the change report.')
if not args.apply:
    print('\nPreview only. Run again with --apply to undo these changes.')
    raise SystemExit(0)

# Back up everything before changing configuration or moving any file.
backup.mkdir(parents=True)
for path in [config, style, *paths]:
    target = backup / path.relative_to(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        target.symlink_to(path.readlink())
    elif path.is_dir():
        shutil.copytree(path, target, symlinks=True)
    else:
        shutil.copy2(path, target)
config.write_text(new_config)
style.write_text(new_style)
for path in paths:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)
subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
subprocess.run(['systemctl', '--user', 'restart', 'waybar.service'], check=True)
print('\nRollback complete. Backup:', backup)
print('Restart OBS and Zoom when convenient to clear any cached themed icons.')
