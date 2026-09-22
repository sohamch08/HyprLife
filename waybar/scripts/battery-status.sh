#!/bin/sh

# Waybar's battery events require a capacity/state suffix. Track status
# separately to notify once when charging starts or the battery discharges.
status=$(cat /sys/class/power_supply/BAT0/status) || exit 1
state_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/waybar-battery-status"
previous=$(cat "$state_file" 2>/dev/null) || previous=

[ "$status" = "$previous" ] && exit 0

case "$status" in
    Charging|Discharging)
        notify-send -u normal 'Power Switch' "$status" || exit 1
        ;;
esac

printf '%s\n' "$status" > "$state_file"
