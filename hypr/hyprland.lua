-- Locate Hyprland modules directory
local modules = os.getenv("HOME") .. "/.config/hypr/modules"

-- Quote text safely for the shell
local function shellQuote(value)
	return "'" .. value:gsub("'", "'\\''") .. "'"
end

-- Display errors through SwayNC
local function warn(message)
	hl.exec_cmd(
		"notify-send -a hypr-autoload -u normal -t 8000 -- "
			.. shellQuote("Hyprland configuration error")
			.. " "
			.. shellQuote(message)
	)
end

-- Get all Lua files, one path per line, in alphabetical order
local pipe, err = io.popen("find -L " .. shellQuote(modules) .. " -type f -name '*.lua' -print | sort")

if not pipe then
	warn("Could not start file search:\n" .. tostring(err))
else
	for path in pipe:lines() do
		local ok, loadErr = pcall(dofile, path)
		if not ok then
			warn(path .. "\n" .. tostring(loadErr))
		end
	end
	pipe:close()
end

hl.config({
	misc = {
		mouse_move_enables_dpms = true,
		key_press_enables_dpms = true,
	},
})
