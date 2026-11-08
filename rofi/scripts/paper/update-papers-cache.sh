#!/usr/bin/env zsh
# Load the exported SOHAM_PAPERS_* paths from .zshenv on startup.
set -euo pipefail
script_dir="${0:A:h}"
exec python3 -B "$script_dir/update-papers-cache.py"
