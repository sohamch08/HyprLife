#!/usr/bin/env python3
"""Generate tray-state SVGs in a chosen color over Breeze Dark.

Pass an alternate destination to generate/inspect the overlay without installing.
Use --color '#RRGGBB' to choose the foreground (default: #f5af67).
Requires Breeze, Papirus, and network-manager-applet icons.
Only generated paths are written.
"""
import argparse
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SOURCE = Path('/usr/share/icons/breeze-dark')
PAPIRUS = Path('/usr/share/icons/Papirus')
HICOLOR = Path('/usr/share/icons/hicolor')
ASSETS = Path(__file__).resolve().parents[1] / 'assets' / 'tray'
DEFAULT_COLOR = '#f5af67'
DEFAULT_DEST = (
    Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    / 'icons/breeze-dark'
)


def hex_color(value):
    value = value.removeprefix('#')
    if not re.fullmatch(r'(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})', value):
        raise argparse.ArgumentTypeError('use a hex color such as #f5af67 or #abc')
    if len(value) == 3:
        value = ''.join(char * 2 for char in value)
    return '#' + value.lower()


def recolor(svg, color):
    # Keep path geometry/opacity, including dim bars indicating signal strength.
    svg = re.sub(r'((?:color|fill|stroke)\s*:\s*)#[0-9a-fA-F]{3,8}\b',
                 lambda match: match[1] + color, svg)
    return re.sub(r'((?:color|fill|stroke)=["\'])#[0-9a-fA-F]{3,8}\b',
                  lambda match: match[1] + color, svg)


def asset_svg(name, color):
    # Recolor foreground only: keep dark badge backings and transparent fills.
    source = ASSETS.parent / 'chatgpt-tray.svg' if name == 'chatgpt-tray' else ASSETS / f'{name}.svg'
    return source.read_text().replace(DEFAULT_COLOR, color)


def papirus_app_icons(color):
    """Resolve the installed package's real aliases; exclude Steam game icons."""
    apps = PAPIRUS / '16x16/apps'
    groups = {}
    for app, asset in (('Zoom', 'zoom'), ('obs', 'obs-tray'),
                       ('steam', 'steam_tray_mono')):
        original = (apps / f'{app}.svg').resolve(strict=True)
        aliases = sorted(p.stem for p in apps.glob('*.svg') if p.resolve() == original)
        groups[app] = {name: asset_svg(asset, color) for name in aliases}
    return groups


def secured(svg, color):
    """Add a lock for dynamically requested <current-icon>-secure names."""
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    root = ET.fromstring(svg)
    bounds = root.get('viewBox')
    if bounds:
        x, y, width, height = map(float, bounds.split())
    else:
        x = y = 0
        width = float(root.get('width', '24').removesuffix('px'))
        height = float(root.get('height', '24').removesuffix('px'))
    badge = ET.fromstring('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 12">
      <rect x="0" y="0" width="10" height="12" rx="2" fill="#080303"/>
      <path d="M3 5V3a2 2 0 0 1 4 0v2M2 5h6v6H2z" fill="none"
            stroke="#f5af67" stroke-width="1.5" stroke-linejoin="round"/>
    </svg>'''.replace(DEFAULT_COLOR, color))
    badge.attrib.update(x=str(x + width * .55), y=str(y + height * .45),
                        width=str(width * .45), height=str(height * .55))
    root.append(badge)
    return ET.tostring(root, encoding='unicode')


def network_icons(files, color):
    # Retain Breeze where available; supplement all panel/animation variants.
    for size in (16, 22, 24):
        prefix = f'status/{size}/'
        for fallback_size in (size, 22):
            for category in ('panel', 'animations'):
                for source in (PAPIRUS / f'{fallback_size}x{fallback_size}' / category).glob('nm-*.svg'):
                    files.setdefault(prefix + source.name, recolor(source.read_text(), color))
        for source in (HICOLOR / 'scalable/apps').glob('nm-*.svg'):
            svg = recolor(source.read_text(), color)
            files.setdefault(prefix + source.name, svg)
            # The applet requests non-symbolic VPN animation names too.
            files.setdefault(prefix + source.name.replace('-symbolic.svg', '.svg'), svg)
        files.setdefault(prefix + 'nm-insecure-warn.svg',
                         recolor((SOURCE / 'status/22/dialog-warning.svg').read_text(), color))
        for name, svg in list(files.items()):
            if name.startswith(prefix + 'nm-') and not name.endswith(('-symbolic.svg', '-secure.svg')):
                files.setdefault(name[:-4] + '-secure.svg', secured(svg, color))

    # Fail before touching the installed theme if a package state is uncovered.
    required = {p.stem for p in (HICOLOR / '22x22/apps').glob('nm-*.png')}
    required |= {p.stem for p in (HICOLOR / 'scalable/apps').glob('nm-*.svg')}
    required |= {'nm-device-wireless', 'nm-device-wired', 'nm-device-wwan', 'nm-no-connection'}
    for size in (16, 22, 24):
        missing = sorted(name for name in required if f'status/{size}/{name}.svg' not in files)
        if missing:
            raise SystemExit(f'Missing nm-applet icons at {size}px: {missing}')
    print(f'Covered {len(required)} installed nm-applet icon names at 16, 22, and 24px')


def install_flatpak_icons(groups, color):
    # Each Flatpak has its own XDG_DATA_HOME. Supply both application aliases
    # and native tray-state names for apps which use QIcon::fromTheme.
    for app_id, group, states in (
        ('com.obsproject.Studio', 'obs', ('obs-tray', 'obs-tray-active', 'obs-tray-paused')),
        ('us.zoom.Zoom', 'Zoom', ('zoom', 'zoom-tray')),
        ('com.valvesoftware.Steam', 'steam', ('steam_tray_mono', 'steam_tray')),
    ):
        app = Path.home() / '.var/app' / app_id
        if not app.is_dir():
            continue
        dest = app / 'data/icons/hicolor'
        marker = dest / '.hyprlife-tray-icons'
        legacy_marker = dest / '.hyprlife-obs-tray'
        if dest.exists() and not (marker.exists() or legacy_marker.exists()):
            raise SystemExit(f'Refusing to overwrite an unmanaged app theme: {dest}')
        (dest / 'scalable/status').mkdir(parents=True, exist_ok=True)
        marker.write_text('Generated by HyprLife/waybar/scripts/install-tray-theme.py\n')
        (dest / 'index.theme').write_text((HICOLOR / 'index.theme').read_text())
        icons = dict(groups[group])
        for name in states:
            asset = {'zoom-tray': 'zoom', 'steam_tray': 'steam_tray_mono'}.get(name, name)
            icons[name] = asset_svg(asset, color)
        for name, svg in icons.items():
            (dest / f'scalable/status/{name}.svg').write_text(svg)
        print(f'Installed {len(icons)} app/tray names for {app_id}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', nargs='?', type=Path,
                        help='generate here only; omit to install host and Flatpak themes')
    parser.add_argument('--color', type=hex_color, default=DEFAULT_COLOR,
                        help='foreground hex color: #RGB or #RRGGBB (default: %(default)s)')
    args = parser.parse_args()
    dest = args.destination if args.destination is not None else DEFAULT_DEST
    color = args.color
    files = {'index.theme': (SOURCE / 'index.theme').read_text()}
    for size in (16, 22, 24):
        for pattern in ('nm-*.svg', 'network-wireless*.svg',
                        'network-wired*.svg', 'network-offline*.svg',
                        'network-vpn*.svg', 'network-cellular*.svg',
                        'network-mobile*.svg', 'network-bluetooth*.svg'):
            for source in (SOURCE / 'status' / str(size)).glob(pattern):
                files[str(source.relative_to(SOURCE))] = recolor(source.read_text(), color)
        for category in ('devices', 'places', 'status'):
            for name in ('bluetooth.svg', 'network-workgroup.svg'):
                source = SOURCE / category / str(size) / name
                if source.exists():
                    files[str(source.relative_to(SOURCE))] = recolor(source.read_text(), color)

    network_icons(files, color)
    groups = papirus_app_icons(color)
    for icons in groups.values():
        for name, svg in icons.items():
            files[f'status/24/{name}.svg'] = svg

    for name in ('obs-tray', 'obs-tray-active', 'obs-tray-paused', 'steam_tray_mono', 'claude', 'zoom', 'chatgpt-tray'):
        files[f'status/24/{name}.svg'] = asset_svg(name, color)
    for alias, target in {'steam': 'steam_tray_mono', 'steam_tray': 'steam_tray_mono',
                          'Zoom': 'zoom', 'zoom-tray': 'zoom',
                          'Claude': 'claude'}.items():
        files[f'status/24/{alias}.svg'] = files[f'status/24/{target}.svg']

    marker = dest / '.hyprlife-tray-overlay'
    if dest.exists() and not marker.exists():
        raise SystemExit(f'Refusing to overwrite an unmanaged theme: {dest}')
    dest.mkdir(parents=True, exist_ok=True)
    marker.write_text('Generated by HyprLife/waybar/scripts/install-tray-theme.py\n')
    for relative, contents in files.items():
        path = dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    print(f'Generated {len(files) - 1} tray icons in {dest} using {color}')
    if args.destination is None:
        install_flatpak_icons(groups, color)


if __name__ == '__main__':
    main()
