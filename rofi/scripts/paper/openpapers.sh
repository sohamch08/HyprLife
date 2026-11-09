#!/bin/sh

# SOHAM_PAPERS_* paths are inherited from the launching environment.
set -eu
script_path=$(realpath -- "$0")
script_dir=$(dirname -- "$script_path")
exec python3 "$script_dir/openpapers.py"
