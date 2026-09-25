"""Distro badge shared by the icon pickers, matching our Starship symbols."""
import json
import platform


def distro_theme(release=None):
    if release is None:
        try:
            release = platform.freedesktop_os_release()
        except OSError:
            release = {}
    symbols = {
        "fedora": "",
        "arch": "󰣇",
        "artix": "󰣇",
        "cachyos": "󰣇",
        "ubuntu": "󰕈",
    }
    candidates = [release.get("ID", ""), *release.get("ID_LIKE", "").split()]
    symbol = next((symbols[name] for name in candidates if name in symbols), "")
    return 'textbox-prompt-colon { str: ' + json.dumps(symbol, ensure_ascii=False) + '; }'


if __name__ == "__main__":
    print(distro_theme())
