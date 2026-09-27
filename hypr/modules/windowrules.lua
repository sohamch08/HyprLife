-- Ref https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- "Smart gaps" / "No gaps when only"
-- uncomment all if you wish to use that.
-- hl.workspace_rule({ workspace = "w[tv1]", gaps_out = 0, gaps_in = 0 })
-- hl.workspace_rule({ workspace = "f[1]",   gaps_out = 0, gaps_in = 0 })
-- hl.window_rule({
--     name  = "no-gaps-wtv1",
--     match = { float = false, workspace = "w[tv1]" },
--     border_size = 0,
--     rounding    = 0,
-- })
-- hl.window_rule({
--     name  = "no-gaps-f1",
--     match = { float = false, workspace = "f[1]" },
--     border_size = 0,
--     rounding    = 0,
-- })
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

-- Zoom uses transparent XWayland windows for notifications, annotation,
-- presenter controls and screen sharing. Tiling these creates oversized empty
-- surfaces; compositor blur fills their otherwise transparent margins.
hl.window_rule({
	name = "zoom-transparent-surfaces",
	match = { class = "^zoom$" },
	float = true,
	no_blur = true,
	no_shadow = true,
})

-- Keep the normal home and meeting windows in the tiling layout. This rule
-- follows the floating default so only auxiliary Zoom windows stay floating.
hl.window_rule({
	name = "zoom-main-windows",
	match = { class = "^zoom$", title = "^(Zoom Workplace( - .*)?|Meeting)$" },
	tile = true,
})

-- The pre-meeting audio/video preview can open at only 638x152 despite its
-- 638x510 size hints, leaving the device controls clipped.
hl.window_rule({
	name = "zoom-meeting-preview",
	match = { class = "^zoom$", title = "^.*'s Zoom Meeting$" },
	float = true,
	size = "638 510",
	min_size = { 638, 510 },
	center = true,
})

-- The feedback dialog reuses "Zoom Workplace", so the main-window rule
-- tiles it even though its visible content is only 540x340. Distinguish it
-- from the startup window by the separate, already-open account window.
local function configureZoomFeedback(w)
	if w.class ~= "zoom" or w.title ~= "Zoom Workplace" then
		return
	end
	for _, other in ipairs(hl.get_windows()) do
		if
			other.address ~= w.address
			and other.class == "zoom"
			and other.pid == w.pid
			and other.mapped
			and not other.hidden
			and other.title:match("^Zoom Workplace %- ")
		then
			hl.dispatch(hl.dsp.window.float({ action = "set", window = w }))
			hl.dispatch(hl.dsp.window.resize({ x = 540, y = 340, relative = false, window = w }))
			hl.dispatch(hl.dsp.window.center({ window = w }))
			return
		end
	end
end
hl.on("window.open", configureZoomFeedback)
hl.on("window.title", configureZoomFeedback)
for _, w in ipairs(hl.get_windows()) do
	configureZoomFeedback(w)
end

-- Zoom draws these frames itself; extra borders/rounding clip controls and
-- outline the transparent surface instead of the visible content.
hl.window_rule({
	name = "zoom-floating-decoration",
	match = { class = "^zoom$", float = true },
	border_size = 0,
	rounding = 0,
	no_anim = true,
})

-- The interactive sharing toolbar and preview incorrectly advertise the X11
-- TOOLTIP type. Override its input suppression for these two windows only.
hl.window_rule({
	name = "zoom-sharing-input",
	match = { class = "^zoom$", title = "^as_(toolbar|preview)$" },
	allows_input = true,
	no_focus = false,
	pin = true,
})

-- Hyprland's override-redirect hit test still checks the X11 TOOLTIP atom
-- even with allows_input. Remove that hint only from the interactive controls.
local function repairZoomSharingInput(w)
	if w.class == "zoom" and (w.title == "as_toolbar" or w.title == "as_preview") then
		hl.exec_cmd("python3 ~/.config/hypr/scripts/zoom-sharing-input.py")
	end
end
hl.on("window.open", repairZoomSharingInput)
for _, w in ipairs(hl.get_windows()) do
	repairZoomSharingInput(w)
end

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
	return tonumber(a.stable_id) < tonumber(b.stable_id)
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
