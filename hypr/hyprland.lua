require("modules.monitor")
require("modules.autostart")
require("modules.binds")
require("modules.decorations")
require("modules.animations")
require("modules.windowrules")
require("modules.layout")
require("modules.input")
-----------------------
----- PERMISSIONS -----
-----------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Permissions/
-- Please note permission changes here require a Hyprland restart and are not applied on-the-fly
-- for security reasons

-- hl.config({
--   ecosystem = {
--     enforce_permissions = true,
--   },
-- })

-- hl.permission("/usr/(bin|local/bin)/grim", "screencopy", "allow")
-- hl.permission("/usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland", "screencopy", "allow")
-- hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")

-- Default curves and animations, see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/

-- See https://wiki.hypr.land/Configuring/Layouts/Dwindle-Layout/ for more
--

hl.config({
	misc = {
		mouse_move_enables_dpms = true,
		key_press_enables_dpms = true,
	},
})
