#!/bin/bash

killall -9 waybar
killall -9 swaync
awww img ~/Pictures/Wallpapers/wallhaven-4dqvkg_2560x1440.png --transition-type center
waybar &
swaync &

