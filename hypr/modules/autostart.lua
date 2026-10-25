-------------------
---- AUTOSTART ----
-------------------

-- Waybar, SwayNC, Hyprsunset and MPD/MPRIS use enabled user services.
-- UWSM runs XDG autostart (nm-applet); PAM/D-Bus handles keyring.
local appList = {
	-- Polkit authentication agent
	"uwsm app -- /usr/libexec/kf6/polkit-kde-authentication-agent-1",

	-- Clipboard history: text and images
	"uwsm app -- wl-paste --type text --watch cliphist store",
	"uwsm app -- wl-paste --type image --watch cliphist store",
}

-- Run every command in the list when Hyprland starts.
hl.on("hyprland.start", function()
	for _, command in ipairs(appList) do
		hl.exec_cmd(command)
	end
end)
