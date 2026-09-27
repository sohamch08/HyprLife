-------------------
---- AUTOSTART ----
-------------------
hl.on("hyprland.start", function()
	-- Waybar, SwayNC, Hyprsunset and MPD/MPRIS use enabled user services.
	-- UWSM runs XDG autostart (nm-applet); PAM/D-Bus handles keyring.
	hl.exec_cmd("uwsm app -- /usr/libexec/kf6/polkit-kde-authentication-agent-1")
	hl.exec_cmd("uwsm app -- wl-paste --type text --watch cliphist store")
	hl.exec_cmd("uwsm app -- wl-paste --type image --watch cliphist store")
end)
