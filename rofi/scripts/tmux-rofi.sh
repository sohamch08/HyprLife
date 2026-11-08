#!/usr/bin/env bash

tmux_sessions() {
  tmux list-sessions -F '#S' 2>/dev/null
}

TMUX_SESSION=$( (
  echo new
  tmux_sessions
) | rofi -dmenu -p "Select tmux session")

if [[ "${TMUX_SESSION}" == "new" ]]; then
  kitty -e tmux new-session &
elif [[ -z "${TMUX_SESSION}" ]]; then
  echo "Cancel"
else
  kitty -e tmux attach-session -t "${TMUX_SESSION}" &
fi
