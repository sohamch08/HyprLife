# Icon pickers

Open the combined picker from a terminal or a Hyprland keybinding:

```sh
~/.config/rofi/scripts/icon-picker
```

Press Ctrl+Tab to switch between Emoji and Material Symbols.
The separate launchers are also available:

```sh
~/.config/rofi/scripts/emoji-grid
~/.config/rofi/scripts/material-grid
```

Type a name to search, navigate with the arrow keys, and press Enter to copy.
Escape cancels without replacing the clipboard. Both pickers share
`rofi/icon-grid.rasi`, which imports applet type 4, style 3 (teal image card and
circular tiles), with a separate search bar beneath the image.
The header badge detects the distribution from `/etc/os-release`, using the
same Fedora and Arch symbols as the Zsh Starship config, with a Linux fallback.

The combined picker reads the installed `rofi-emoji` database, including names,
keywords and skin-tone variants. Ctrl+Tab reopens the other view with its actual
SVG header badge and clears the search. The standalone emoji launcher still
uses the `rofi-emoji` plugin.

The Material picker reads Google Material Symbols from the installed font. It
defaults to Rounded; use `--style outlined` or `--style sharp` for the other
styles. Names are searchable even though the tiles display only the glyphs.
Material selection copies a literal Unicode escape with eight hexadecimal
digits, using `~/.local/share/fonts/MaterialTerminal/mapping.json` to target the
matching Material Terminal style without colliding with Nerd Font glyphs.
For example, Rounded `person` copies `\U001044C7`. The corresponding Material
Terminal font must be installed and included in the terminal's font fallback.
Emoji selection still copies the emoji itself.

Dependencies: Rofi, rofi-emoji, wl-clipboard, Noto Color Emoji, Google Material
Symbols, fontconfig, Python 3, and fontTools (`python3-fonttools` on Fedora).
The UI uses JetBrainsMono Nerd Font Propo. No downloads happen at launch.

## Updating upstream themes

Run `~/.config/rofi/scripts/update-rofi`. It runs `git pull --ff-only` in
`~/projects/other-config/rofi` (falling back to `other-configs/rofi`, the current
checkout), then copies upstream `files/` into this Rofi directory.
An optional first argument selects another upstream checkout.
Locally customized files are reported and preserved; custom-only files and
removed upstream files are left in place. Fonts are not installed by this script.
