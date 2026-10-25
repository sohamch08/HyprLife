-------------------
---- AUTOSTART ----
-------------------

-- Waybar, SwayNC, Hyprsunset and MPD/MPRIS use enabled user services.
-- UWSM runs XDG autostart (nm-applet); PAM/D-Bus handles keyring.
local appList = {
	-- Polkit authentication agent
	"/usr/libexec/kf6/polkit-kde-authentication-agent-1",

	-- Clipboard history: text and images
	"wl-paste --type text --watch cliphist store",
	"wl-paste --type image --watch cliphist store",
}

-- Launch every command through UWSM when Hyprland starts.
hl.on("hyprland.start", function()
	for _, command in ipairs(appList) do
		hl.exec_cmd("uwsm app -- " .. command)
	end
end)
