--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

-- Example window rules that are useful

local suppressMaximizeRule = hl.window_rule({
	-- Ignore maximize requests from all apps. You'll probably like this.
	name = "suppress-maximize-events",
	match = { class = ".*" },

	suppress_event = "maximize",
})
-- suppressMaximizeRule:set_enabled(false)

-- Xwayland Video Bridge exposes a capture helper window at login.
-- Keep it available for screen sharing without displaying or focusing it.
-- https://wiki.hypr.land/useful-utilities/screen-sharing/
hl.window_rule({
	name = "hide-xwayland-video-bridge",
	match = { class = "^xwaylandvideobridge$" },
	float = true,
	no_initial_focus = true,
	no_focus = true,
	no_anim = true,
	no_blur = true,
	no_shadow = true,
	border_size = 0,
	max_size = { 1, 1 },
	opacity = 0.0,
})

-- GTK portal dialogs draw their own frame and shadow under XWayland.
-- Avoid blurring or decorating the transparent margin around that frame.
hl.window_rule({
	name = "gtk-portal-client-decorations",
	match = {
		class = "^[Xx]dg-desktop-portal-gtk$",
		xwayland = true,
	},
	no_blur = true,
	no_shadow = true,
	border_size = 0,
	rounding = 0,
})

-- Unnamed XWayland menus (including ChatGPT's) have no app class/title and
-- include transparent margins for their own shadow. Do not blur or decorate
-- the outer rectangle; matching the parent app's class misses these popups.
hl.window_rule({
	name = "xwayland-popup-client-decorations",
	match = { class = "^$", title = "^$", xwayland = true, float = true },
	no_blur = true,
	no_shadow = true,
	border_size = 0,
	rounding = 0,
})

-- Keep the first window of each Obsidian process as its main window.
-- Float subsequent windows without depending on vault or dialog titles.
local obsidianMainWindows = {}

local function configureObsidianWindow(w)
	if w.class ~= "md.obsidian.Obsidian" and w.class ~= "obsidian" then
		return
	end

	local main = obsidianMainWindows[w.pid]
	if not main then
		obsidianMainWindows[w.pid] = w.address
		return
	end
	if main == w.address then
		return
	end

	local isSettings = w.initial_title:match("^Settings %- ") ~= nil
	local width, height = 900, 675
	if isSettings then
		width, height = 1000, 750
	end

	hl.dispatch(hl.dsp.window.float({ action = "set", window = w }))
	hl.dispatch(hl.dsp.window.resize({ x = width, y = height, relative = false, window = w }))
	hl.dispatch(hl.dsp.window.center({ window = w }))
end

-- Recover opening order when reloading the config with Obsidian running.
local existingWindows = hl.get_windows()
table.sort(existingWindows, function(a, b)
	-- Hyprland exposes stable IDs as hexadecimal strings without a 0x prefix.
	return tonumber(a.stable_id, 16) < tonumber(b.stable_id, 16)
end)
for _, w in ipairs(existingWindows) do
	configureObsidianWindow(w)
end

hl.on("window.open", configureObsidianWindow)
hl.on("window.close", function(w)
	if obsidianMainWindows[w.pid] == w.address then
		obsidianMainWindows[w.pid] = nil
	end
end)

hl.window_rule({
	-- Fix some dragging issues with XWayland
	name = "fix-xwayland-drags",
	match = {
		class = "^$",
		title = "^$",
		xwayland = true,
		float = true,
		fullscreen = false,
		pin = false,
	},

	no_focus = true,
})

-- Layer rules also return a handle.
-- local overlayLayerRule = hl.layer_rule({
--     name  = "no-anim-overlay",
--     match = { namespace = "^my-overlay$" },
--     no_anim = true,
-- })
-- overlayLayerRule:set_enabled(false)

-- Hyprland-run windowrule
hl.window_rule({
	name = "move-hyprland-run",
	match = { class = "hyprland-run" },

	move = "20 monitor_h-120",
	float = true,
})
hl.layer_rule({
	name = "blurs-blur",
	match = { namespace = "^blurs$" },
	blur = true,
	ignore_alpha = 0.3,
})
hl.window_rule({
	match = { fullscreen = true },
	rounding = 0,
	border_size = 0, -- optional: removes border too if desired
})

hl.layer_rule({
	name = "wifi-manager",
	match = { namespace = "wifi-manager" },
	blur = true,
	ignore_alpha = 0.3,
})

hl.layer_rule({
	name = "swaync-control",
	match = { namespace = "swaync-control-center" },
	blur = true,
	ignore_alpha = 0.5,
})

hl.layer_rule({
	name = "swaync-notification",
	match = { namespace = "swaync-notification-window" },
	blur = true,
	ignore_alpha = 0.5,
})

hl.window_rule({
	name = "float-pavucontrol",
	match = { class = "org.pulseaudio.pavucontrol" },
	float = true,
	min_size = { 900, 600 },
})
hl.window_rule({
	name = "alacritty-blur",
	match = { class = "Alacritty" },
	-- blur = true,
	-- opacity = { "0.8", "0.8" },
	opacity = "0.85 override 0.7 override 0.7 override",
})

hl.window_rule({
	name = "kitty-blur",
	match = { class = "kitty" },
	-- blur = true,
	-- opacity = { "0.8", "0.8" },
	opacity = "0.85 override 0.7 override 0.8 override",
})

hl.window_rule({
	name = "popup-file-manager-float",
	match = { class = "^xdg-desktop-portal-gtk$" },
	float = true,
})

hl.window_rule({
	name = "Matplotlib-window-float",
	match = { class = "^Matplotlib$" },
	float = true,
})
