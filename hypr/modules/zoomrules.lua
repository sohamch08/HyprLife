-- Zoom window rules and handlers.

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
-- Bare "Zoom Workplace" is also used by incoming-chat notifications.
hl.window_rule({
	name = "zoom-main-windows",
	match = { class = "^zoom$", title = "^(Zoom Workplace - .*|Meeting)$" },
	tile = true,
})

-- The home window gains its account title after the opening rules have run.
local function tileZoomHome(w)
	if w.class == "zoom" and w.mapped and w.floating
		and w.initial_title == "Zoom Workplace" and w.title:match("^Zoom Workplace %- ") then
		hl.dispatch(hl.dsp.window.float({ action = "unset", window = w }))
	end
end

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

-- Size the generic "Zoom Workplace" feedback dialog to its 540x340 content.
-- Distinguish it from startup by the separate, already-open account window.
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

-- Zoom's chat toast shares its title with ordinary dialogs. Confirm its X11
-- utility type and Meeting parent before changing it or sending a notification.
local pending, popups = {}, {}
local timer

local function tag(w, value)
	hl.dispatch(hl.dsp.window.tag({ tag = value, window = w }))
end

-- Hide an unclassified toast before its first frame on the current workspace.
hl.window_rule({
	name = "zoom-popup-pending",
	match = { class = "^zoom$", tag = "zoom-popup-pending" },
	opacity = 0.0,
	no_focus = true,
})
hl.window_rule({
	name = "zoom-chat-no-focus",
	match = { class = "^zoom$", tag = "zoom-chat" },
	no_focus = true,
})

local function place(w, meeting, anchor)
	if not w.floating then
		hl.dispatch(hl.dsp.window.float({ action = "set", window = w }))
	end
	if w.pinned then
		hl.dispatch(hl.dsp.window.pin({ action = "unset", window = w }))
	end
	if w.workspace.id ~= meeting.workspace.id then
		local workspace = meeting.workspace.id < 0 and meeting.workspace.name or meeting.workspace.id
		hl.dispatch(hl.dsp.window.move({ workspace = workspace, follow = false, window = w }))
	end
	-- Zoom draws a 300px bubble even when its transparent surface retains an
	-- old tiled width. Keep its native height as the message wraps.
	local width = math.min(300, math.max(1, meeting.size.x - 24))
	local height = math.min(w.size.y, math.max(1, meeting.size.y - 24))
	if w.size.x ~= width or w.size.y ~= height then
		hl.dispatch(hl.dsp.window.resize({ x = width, y = height, relative = false, window = w }))
	end
	-- Zoom keeps its meeting controls at the bottom and its Chat button in
	-- the central group. Accessibility gives the actual button offsets.
	local buttonX = meeting.at.x + meeting.size.x / 2 + anchor.centerOffset
	local buttonY = meeting.at.y + meeting.size.y - anchor.bottomInset
	local x = math.max(meeting.at.x + 12, math.min(buttonX - width / 2, meeting.at.x + meeting.size.x - width - 12))
	local y = math.max(meeting.at.y + 12, buttonY - height - 4)
	if w.at.x ~= x or w.at.y ~= y then
		hl.dispatch(hl.dsp.window.move({ x = x, y = y, relative = false, window = w }))
	end
end

-- Called by the short-lived X11 inspector; the stable ID guards against a
-- window closing and its address being reused while inspection was running.
function hyprlifeZoomPopupClassified(address, stableId, meetingAddress, centerOffset, bottomInset)
	local item = pending[address]
	local w = hl.get_window("address:" .. address)
	if not item or item.id ~= stableId or not w or w.stable_id ~= stableId or not w.mapped then
		return
	end
	pending[address] = nil
	local meeting = meetingAddress and hl.get_window("address:" .. meetingAddress)
	if meeting and meeting.mapped and meeting.class == "zoom" and meeting.title == "Meeting" and meeting.pid == w.pid then
		tag(w, "+zoom-chat")
		popups[address] = {
			id = stableId, meeting = meetingAddress, meetingId = meeting.stable_id,
			centerOffset = centerOffset or -10, bottomInset = bottomInset or 56,
		}
		place(w, meeting, popups[address])
		hl.dispatch(hl.dsp.window.alter_zorder({ mode = "top", window = w }))
	else
		configureZoomFeedback(w)
	end
	tag(w, "-zoom-popup-pending")
end

local function inspect(w, notify)
	if w.class ~= "zoom" or w.title ~= "Zoom Workplace" or not w.mapped or pending[w.address] or popups[w.address] then
		return
	end
	local hasMeeting = false
	for _, other in ipairs(hl.get_windows()) do
		if other.class == "zoom" and other.title == "Meeting" and other.pid == w.pid and other.mapped then
			hasMeeting = true
			break
		end
	end
	if not hasMeeting then
		configureZoomFeedback(w)
		return
	end
	pending[w.address] = { id = w.stable_id, notify = notify, ticks = 0 }
	tag(w, "+zoom-popup-pending")
	timer:set_enabled(true)
	hl.exec_cmd(string.format("python3 ~/.config/hypr/scripts/zoom-chat-popup.py %s %d %s", w.address, w.stable_id, notify and "notify" or "quiet"))
end

-- Hyprland has no Lua move/resize event. Track geometry only while a toast
-- exists, so it follows the meeting when resized or moved to another workspace.
timer = hl.timer(function()
	for address, item in pairs(pending) do
		item.ticks = item.ticks + 1
		if item.ticks >= 25 then
			-- Fail open if the inspector cannot run; never leave a dialog invisible.
			hyprlifeZoomPopupClassified(address, item.id, nil)
			pending[address] = nil
		end
	end
	for address, item in pairs(popups) do
		local w = hl.get_window("address:" .. address)
		local meeting = hl.get_window("address:" .. item.meeting)
		if not w or not w.mapped or w.stable_id ~= item.id then
			popups[address] = nil
		elseif not meeting or not meeting.mapped or meeting.stable_id ~= item.meetingId then
			hl.dispatch(hl.dsp.window.close({ window = w }))
			popups[address] = nil
		else
			place(w, meeting, item)
		end
	end
	if not next(pending) and not next(popups) then
		timer:set_enabled(false)
	end
end, { timeout = 100, type = "repeat" })
timer:set_enabled(false)

hl.on("window.open", function(w) inspect(w, true) end)
hl.on("window.title", function(w)
	tileZoomHome(w)
	inspect(w, false)
end)
hl.on("window.close", function(w)
	pending[w.address], popups[w.address] = nil, nil
end)
for _, w in ipairs(hl.get_windows()) do
	tileZoomHome(w)
	inspect(w, false)
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
