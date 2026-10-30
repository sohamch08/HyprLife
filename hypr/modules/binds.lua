-- Window movement helper
-- With two dwindle tiles, movement can also change the split direction.
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

	hl.dispatch(hl.dsp.window.move({
		direction = direction,
		window = w,
	}))

	if tilePair then
		-- Do not carry this direction over to the next new window.
		hl.dispatch(hl.dsp.layout("preselect none"))
	end
end

-- Modifier and workspace keys
local mainMod = "SUPER + "
local keyboardString = "1234567890"

-- Application commands
local terminal = "uwsm app -- alacritty"
local fileManager = "uwsm app -- dolphin"
local menu = "uwsm app -- ~/.config/rofi/launchers/type-2/launcher.sh"
local clipboard =
	"uwsm app -- rofi -modi 'Clipboard:/home/soham/.config/cliphist/cliphist-rofi' -show Clipboard -theme ~/.config/rofi/launchers/type-1/style-11.rasi"

---@type { mod?: string, key: string[], dispatch: string|HL.Dispatcher|function, opts?: HL.BindOptions }[]
local globalAppBinds = {
	---- Window functions
	{ key = { "Q" }, dispatch = hl.dsp.window.close() },
	{ key = { "SHIFT + Q" }, dispatch = hl.dsp.window.kill() },
	{ key = { "F" }, dispatch = hl.dsp.window.float({ action = "toggle" }) },
	{ key = { "SHIFT + M" }, dispatch = hl.dsp.window.fullscreen({ action = "toggle" }) },

	---- Apps
	-- Terminal
	{ key = { "RETURN" }, dispatch = terminal },

	-- File manager
	{ key = { "E" }, dispatch = fileManager },

	-- Browser
	{ key = { "SHIFT + b" }, dispatch = "uwsm app -- brave-browser --password-store=gnome-libsecret" },

	-- Application launcher
	{ key = { "D" }, dispatch = menu },

	---- Clipboard and pickers
	-- Clipboard history
	{ key = { "C" }, dispatch = clipboard },

	-- Icon picker
	{ key = { "period" }, dispatch = "uwsm app -- ~/.config/rofi/scripts/icon-picker" },

	-- Papers
	{ key = { "P" }, dispatch = "uwsm app -- ~/.config/rofi/scripts/paper/openpapers.sh" },

	-- Wallpaper picker
	{ key = { "W" }, dispatch = "uwsm app -- skwd-wall-v2" },

	---- Screenshots
	{ key = { "PRINT" }, dispatch = "uwsm app -- hyprshot -m output -m eDP-1" },
	{ key = { "SHIFT + PRINT" }, dispatch = "uwsm app -- hyprshot -m region" },

	---- Session
	{
		key = { "SHIFT + N" },
		dispatch = [[uwsm app -- alacritty --class neo-screensaver -o 'window.startup_mode="Fullscreen"' -o 'window.padding={x=0,y=0}' -e zsh -c 'source "$HOME/.config/zsh/aliases.zsh"; eval "neowake -s"']],
	},
	{ key = { "SHIFT + E" }, dispatch = "uwsm app -- ~/.config/rofi/powermenu/type-4/powermenu.sh" },
	{ key = { "SHIFT + X" }, dispatch = "uwsm app -- hyprlock" },
	{ key = { "SHIFT + R" }, dispatch = "~/.config/waybar/scripts/launch.sh" },

	---- Focus windows
	{ key = { "H" }, dispatch = hl.dsp.focus({ direction = "left" }) },
	{ key = { "J" }, dispatch = hl.dsp.focus({ direction = "down" }) },
	{ key = { "K" }, dispatch = hl.dsp.focus({ direction = "up" }) },
	{ key = { "L" }, dispatch = hl.dsp.focus({ direction = "right" }) },

	---- Move windows
	{
		key = { "SHIFT + H" },
		dispatch = function()
			moveWindowInDirection("left")
		end,
	},
	{
		key = { "SHIFT + J" },
		dispatch = function()
			moveWindowInDirection("down")
		end,
	},
	{
		key = { "SHIFT + K" },
		dispatch = function()
			moveWindowInDirection("up")
		end,
	},
	{
		key = { "SHIFT + L" },
		dispatch = function()
			moveWindowInDirection("right")
		end,
	},

	---- Cycle workspaces
	{ key = { "SHIFT + TAB" }, dispatch = hl.dsp.focus({ workspace = "e-1" }) },
	{ key = { "TAB" }, dispatch = hl.dsp.focus({ workspace = "e+1" }) },

	---- Special workspace
	{ key = { "S" }, dispatch = hl.dsp.workspace.toggle_special("magic") },
	{ key = { "SHIFT + S" }, dispatch = hl.dsp.window.move({ workspace = "special:magic" }) },

	---- Mouse / touchpad buttons
	{ key = { "mouse:272" }, dispatch = hl.dsp.window.drag(), opts = { mouse = true } },
	{ key = { "mouse:273" }, dispatch = hl.dsp.window.resize(), opts = { mouse = true } },

	---- Resize mode
	{ key = { "R" }, dispatch = hl.dsp.submap("resize") },

	---- Laptop volume keys
	-- Empty modifier means these keys do not require SUPER.
	{
		mod = "",
		key = { "XF86AudioRaiseVolume" },
		dispatch = "wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+",
		opts = { locked = true, repeating = true },
	},
	{
		mod = "",
		key = { "XF86AudioLowerVolume" },
		dispatch = "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-",
		opts = { locked = true, repeating = true },
	},
	{
		mod = "",
		key = { "XF86AudioMute" },
		dispatch = "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle",
		opts = { locked = true, repeating = true },
	},
	{
		mod = "",
		key = { "XF86AudioMicMute" },
		dispatch = "wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle",
		opts = { locked = true, repeating = true },
	},

	---- Laptop brightness keys
	{
		mod = "",
		key = { "XF86MonBrightnessUp" },
		dispatch = "brightnessctl -n2 set 5%+",
		opts = { locked = true, repeating = true },
	},
	{
		mod = "",
		key = { "XF86MonBrightnessDown" },
		dispatch = "brightnessctl -n2 set 5%-",
		opts = { locked = true, repeating = true },
	},

	---- Media playback
	{ mod = "", key = { "XF86AudioNext" }, dispatch = "playerctl next", opts = { locked = true } },
	{ mod = "", key = { "XF86AudioPause" }, dispatch = "playerctl play-pause", opts = { locked = true } },
	{ mod = "", key = { "XF86AudioPlay" }, dispatch = "playerctl play-pause", opts = { locked = true } },
	{ mod = "", key = { "XF86AudioPrev" }, dispatch = "playerctl previous", opts = { locked = true } },
}

-- Register bindings
for _, bind in ipairs(globalAppBinds) do
	-- Use the specified modifier, otherwise use SUPER.
	local modBind = bind.mod or mainMod
	local dispatch = bind.dispatch
	local command

	-- Wrap shell commands in exec_cmd.
	-- Hyprland actions and Lua functions pass through directly.
	if type(dispatch) == "string" then
		command = hl.dsp.exec_cmd(dispatch)
	else
		command = dispatch
	end

	local opts = bind.opts or {}

	-- One keyboard setup, so always use the first key.
	hl.bind(modBind .. bind.key[1], command, opts)
end

-- Numbered workspace keys
local keyboardSplit = {}

for char in keyboardString:gmatch(".") do
	table.insert(keyboardSplit, char)
end

for index, key in ipairs(keyboardSplit) do
	-- SUPER + number: switch workspace.
	hl.bind(mainMod .. key, hl.dsp.focus({ workspace = index }))

	-- SUPER + SHIFT + number: send window without following.
	hl.bind(mainMod .. "SHIFT + " .. key, hl.dsp.window.move({ workspace = index, follow = false }))
end

-- Resize submap
-- SUPER + R enters; Escape leaves.
hl.define_submap("resize", function()
	hl.bind("H", hl.dsp.window.resize({ x = -10, y = 0, relative = true }), { repeating = true })
	hl.bind("J", hl.dsp.window.resize({ x = 0, y = -10, relative = true }), { repeating = true })
	hl.bind("K", hl.dsp.window.resize({ x = 0, y = 10, relative = true }), { repeating = true })
	hl.bind("L", hl.dsp.window.resize({ x = 10, y = 0, relative = true }), { repeating = true })
	hl.bind("escape", hl.dsp.submap("reset"))
end)
