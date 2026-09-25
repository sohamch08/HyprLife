-------------------
---- AUTOSTART ----
-------------------
hl.on("hyprland.start", function()
	hl.exec_cmd("nm-applet")
	-- hl.exec_cmd("blueman-applet")
	hl.exec_cmd("waybar")
	hl.exec_cmd("/usr/libexec/kf6/polkit-kde-authentication-agent-1")
	hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")
	hl.exec_cmd("swaync")
	-- Publish MPD/rmpc playback to SwayNC and other MPRIS clients.
	hl.exec_cmd("systemctl --user start mpd-mpris.service")
	hl.exec_cmd("hyprsunset")
	hl.exec_cmd("wl-paste --type text --watch cliphist store")
	hl.exec_cmd("wl-paste --type image --watch cliphist store")
	-- hl.exec_cmd("wifi-manager")
	hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
end)
