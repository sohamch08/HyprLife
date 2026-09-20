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
    name           = "suppress-maximize-events",
    match          = { class = ".*" },

    suppress_event = "maximize",
})
-- suppressMaximizeRule:set_enabled(false)

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
    name     = "fix-xwayland-drags",
    match    = {
        class      = "^$",
        title      = "^$",
        xwayland   = true,
        float      = true,
        fullscreen = false,
        pin        = false,
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
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },

    move  = "20 monitor_h-120",
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
