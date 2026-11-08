#!/usr/bin/env zsh

# Zsh loads .zshenv, including the exported SOHAM_PAPERS_* paths, for desktop launches.
set -euo pipefail
script_dir="${0:A:h}"
exec python3 "$script_dir/openpapers.py"
