-- Sections: Applications | Utilities | Screenshots | Session | Windows
--           Focus | Move windows | Mouse | Resize mode | Workspaces
--           Audio | Brightness | Media playback

-----------------------
-- MODIFIER AND APPS --
-----------------------

local terminal = "uwsm app -- alacritty"
local fileManager = "uwsm app -- dolphin"
local menu = "uwsm app -- ~/.config/rofi/launchers/type-2/launcher.sh"
local clipboard =
	"uwsm app -- rofi -modi 'Clipboard:/home/soham/.config/cliphist/cliphist-rofi' -show Clipboard -theme ~/.config/rofi/launchers/type-1/style-11.rasi"
local mainMod = "SUPER" -- Sets "Windows" key as main modifier

------------------
-- APPLICATIONS --
------------------

-- Terminal, file manager, browser and application launcher
hl.bind(mainMod .. " + RETURN", hl.dsp.exec_cmd(terminal))
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + SHIFT + b", hl.dsp.exec_cmd("uwsm app -- brave-browser --password-store=gnome-libsecret"))
hl.bind(mainMod .. " + D", hl.dsp.exec_cmd(menu))

---------------
-- UTILITIES --
---------------

-- Clipboard history, icon picker, papers and wallpaper picker
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd(clipboard))
hl.bind(mainMod .. " + period", hl.dsp.exec_cmd("uwsm app -- ~/.config/rofi/scripts/icon-picker"))
hl.bind(mainMod .. " + P", hl.dsp.exec_cmd("uwsm app -- ~/.config/rofi/scripts/paper/openpapers.sh"))
hl.bind(mainMod .. " + W", hl.dsp.exec_cmd("uwsm app -- skwd-wall-v2"))

-----------------
-- SCREENSHOTS --
-----------------

-- Full display (eDP-1) or a selected region
hl.bind(mainMod .. " + PRINT", hl.dsp.exec_cmd("uwsm app -- hyprshot -m output -m eDP-1"))
hl.bind(mainMod .. " + SHIFT + PRINT", hl.dsp.exec_cmd("uwsm app -- hyprshot -m region"))

-------------
-- SESSION --
-------------

-- Power menu, lock screen and restart bar
hl.bind(mainMod .. " + SHIFT + E", hl.dsp.exec_cmd("uwsm app -- ~/.config/rofi/powermenu/type-4/powermenu.sh"))
hl.bind(mainMod .. " + SHIFT + X", hl.dsp.exec_cmd("uwsm app -- hyprlock"))
hl.bind(mainMod .. " + SHIFT + R", hl.dsp.exec_cmd("~/.config/waybar/scripts/launch.sh"))

-------------
-- WINDOWS --
-------------

-- Close normally or force-kill
hl.bind(mainMod .. " + Q", hl.dsp.window.close())
hl.bind(mainMod .. " + SHIFT + Q", hl.dsp.window.kill())

-- Toggle floating or fullscreen
hl.bind(mainMod .. " + F", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + SHIFT + M", hl.dsp.window.fullscreen({ action = "toggle" }))

-- Optional dwindle bindings (currently disabled)
-- hl.bind(mainMod .. " + P", hl.dsp.window.pseudo())
-- hl.bind(mainMod .. " + S", hl.dsp.layout("togglesplit"))    -- dwindle only

-----------
-- FOCUS --
-----------

-- SUPER + H/J/K/L: focus left/down/up/right
hl.bind(mainMod .. " + H", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + J", hl.dsp.focus({ direction = "down" }))
hl.bind(mainMod .. " + K", hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + L", hl.dsp.focus({ direction = "right" }))

------------------
-- MOVE WINDOWS --
------------------

-- With two dwindle tiles, preselect lets movement change the split direction.
local function moveWindowInDirection(direction)
	local w = hl.get_active_window()
	if not w then
		return
	end
	local tilePair = not w.floating and w.workspace and w.workspace.tiled_layout == "dwindle"
	if tilePair then
		local tiledCount = 0
		for _, candidate in ipairs(hl.get_workspace_windows(w.workspace)) do
			if candidate.mapped and not candidate.hidden and not candidate.floating then
				tiledCount = tiledCount + 1
			end
		end
		tilePair = tiledCount == 2
	end
	if tilePair then
		hl.dispatch(hl.dsp.layout("preselect " .. direction))
	end
	hl.dispatch(hl.dsp.window.move({ direction = direction, window = w }))
	if tilePair then
		-- Keep the next new window from inheriting this direction.
		hl.dispatch(hl.dsp.layout("preselect none"))
	end
end

-- SUPER + SHIFT + H/J/K/L: move left/down/up/right
for key, direction in pairs({ H = "left", L = "right", K = "up", J = "down" }) do
	hl.bind(mainMod .. " + SHIFT + " .. key, function()
		moveWindowInDirection(direction)
	end)
end

-----------
-- MOUSE --
-----------

-- SUPER + left/right mouse drag: move/resize the window
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-----------------
-- RESIZE MODE --
-----------------

-- SUPER + R: enter resize mode
hl.bind(mainMod .. "+ R", hl.dsp.submap("resize"))

-- Hold H/J/K/L to resize; Escape returns to normal bindings.
hl.define_submap("resize", function()
	-- Set repeating binds for resizing the active window.
	hl.bind("L", hl.dsp.window.resize({ x = 10, y = 0, relative = true }), { repeating = true })
	hl.bind("H", hl.dsp.window.resize({ x = -10, y = 0, relative = true }), { repeating = true })
	hl.bind("K", hl.dsp.window.resize({ x = 0, y = 10, relative = true }), { repeating = true })
	hl.bind("J", hl.dsp.window.resize({ x = 0, y = -10, relative = true }), { repeating = true })

	-- Use `reset` to go back to the global submap
	hl.bind("escape", hl.dsp.submap("reset"))
end)

----------------
-- WORKSPACES --
----------------

-- Previous/next existing workspace
hl.bind(mainMod .. " + SHIFT + TAB", hl.dsp.focus({ workspace = "e-1" }))
hl.bind(mainMod .. " + TAB", hl.dsp.focus({ workspace = "e+1" }))

-- Switch workspaces with mainMod + [0-9]
-- Move active window to a workspace with mainMod + SHIFT + [0-9]
for i = 1, 10 do
	local key = i % 10 -- 10 maps to key 0
	hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i }))
	hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i, follow = false }))
end

-- Scratchpad: toggle visibility or send the active window there
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

-- Scroll through existing workspaces with mainMod + scroll
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))

-----------
-- AUDIO --
-----------

-- Volume and mute keys also work while locked; holding a key repeats it
hl.bind(
	"XF86AudioRaiseVolume",
	hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"),
	{ locked = true, repeating = true }
)
hl.bind(
	"XF86AudioLowerVolume",
	hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),
	{ locked = true, repeating = true }
)
hl.bind(
	"XF86AudioMute",
	hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),
	{ locked = true, repeating = true }
)
hl.bind(
	"XF86AudioMicMute",
	hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),
	{ locked = true, repeating = true }
)

----------------
-- BRIGHTNESS --
----------------

hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("brightnessctl -n2 set 5%-"), { locked = true, repeating = true })

--------------------
-- MEDIA PLAYBACK --
--------------------

-- Requires playerctl; these keys also work while locked
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })
