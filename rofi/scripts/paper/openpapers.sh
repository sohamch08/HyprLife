#!/usr/bin/env bash

# Search My Papers and Markdown note metadata in a single themed Rofi box.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/openpapers.py"
