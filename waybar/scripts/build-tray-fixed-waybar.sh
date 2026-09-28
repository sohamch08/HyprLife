#!/bin/sh
# Requires Waybar 0.15's build dependencies (on Fedora: dnf builddep waybar).
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
version=0.15.0
archive_sha=21c2bbef88c40473c355003582f9331d2f9b8a01efdcce0935edfc5f6b023a3e
build_root=$(mktemp -d "${TMPDIR:-/tmp}/hyprlife-waybar.XXXXXX")
trap 'rm -rf "$build_root"' EXIT HUP INT TERM

curl --fail --location --retry 2 \
  "https://github.com/Alexays/Waybar/archive/refs/tags/$version.tar.gz" \
  -o "$build_root/source.tar.gz"
printf '%s  %s\n' "$archive_sha" "$build_root/source.tar.gz" | sha256sum --check -
tar -xf "$build_root/source.tar.gz" -C "$build_root"
patch -d "$build_root/Waybar-$version" -p1 \
  < "$script_dir/../patches/0001-preserve-custom-tray-icons.patch"
meson setup "$build_root/build" "$build_root/Waybar-$version" \
  --prefix=/usr --wrap-mode=nofallback -Doptimization=2 -Dtests=disabled \
  -Dman-pages=disabled -Dsystemd=disabled -Dcava=disabled -Dsndio=disabled \
  -Ddbusmenu-gtk=enabled -Dpulseaudio=enabled -Dlibnl=enabled -Dlibudev=enabled \
  -Drfkill=enabled
meson compile -C "$build_root/build" -j "${BUILD_JOBS:-2}"
# Stage the install to strip temporary build-library search paths.
DESTDIR="$build_root/stage" meson install -C "$build_root/build" --no-rebuild
install -Dm755 "$build_root/stage/usr/bin/waybar" "$HOME/.local/libexec/waybar-tray-fix"
printf '%s\n' 'Installed ~/.local/libexec/waybar-tray-fix; restart waybar.service to activate.'
