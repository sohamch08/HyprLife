#!/usr/bin/env bash
set -euo pipefail

fail() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Usage: deploy.sh [--dry-run] [MANIFEST]

Create config symlinks under HOME using MANIFEST (default: this repo's MANIFEST).
Relative manifest paths are resolved from the repository, regardless of cwd.
Existing matching symlinks are kept; conflicting destinations are never replaced.
All entries are checked before creating any links. Run as your normal user.

  --dry-run  Preview links without changing files or directories.
  -h, --help Show this help.
EOF
}

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
dry_run=false
manifest=''
while (( $# )); do
    case $1 in
        --dry-run) dry_run=true ;;
        -h|--help) usage; exit 0 ;;
        -*) fail "Unknown option: $1" ;;
        *)
            [[ -z $manifest ]] || fail 'Expected at most one manifest path.'
            manifest=$1
            ;;
    esac
    shift
done
manifest=${manifest:-MANIFEST}
[[ $manifest == /* ]] || manifest="$ROOT/$manifest"
[[ -f $manifest && -r $manifest ]] || fail "Cannot read manifest: $manifest"
[[ -n ${HOME:-} && $HOME == /* && -d $HOME ]] ||
    fail 'HOME must be an existing absolute directory.'
home_dir="$(cd -- "$HOME" && pwd -P)"

# Empty destination prefixes are allowed. Empty sources are rejected by parsing.
relative_path() {
    [[ $1 != /* && $1 != */ && $1 != *//* && /$1/ != */../* && /$1/ != */./* ]]
}

sources=()
targets=()
declare -A seen_targets=()
number=0
errors=0
while IFS= read -r row || [[ -n $row ]]; do
    ((number += 1))
    row=${row%$'\r'}
    [[ $row =~ ^[[:space:]]*$ || $row =~ ^[[:space:]]*# ]] && continue

    [[ $row =~ ^[^\|]+\|[^\|]+\|[^\|]*$ ]] ||
        fail "Line $number: expected source|symlink|destination-directory"
    IFS='|' read -r item operation folder <<< "$row"
    [[ $operation == symlink ]] || fail "Line $number: unsupported operation: $operation"
    if ! relative_path "$item" || ! relative_path "$folder"; then
        fail "Line $number: use relative paths without '.', '..', repeated or trailing slashes."
    fi

    source="$ROOT/$item"
    target="$home_dir/${folder:+$folder/}$item"
    [[ -e $source ]] || fail "Line $number: source does not exist: $source"
    [[ ! ${seen_targets[$target]+exists} ]] || fail "Line $number: duplicate destination: $target"
    for previous in "${!seen_targets[@]}"; do
        [[ $target != "$previous/"* && $previous != "$target/"* ]] ||
            fail "Line $number: overlapping destinations: $previous and $target"
    done
    seen_targets[$target]=1

    # Accept equivalent relative or absolute symlinks to the same source.
    if [[ -L $target && $target -ef $source ]]; then
        printf 'Already linked: %s\n' "$target"
        continue
    fi

    # -L also detects dangling symlinks, which -e alone would miss.
    if [[ -e $target || -L $target ]]; then
        printf 'Conflict: %s (back it up or move it before deploying)\n' "$target" >&2
        ((errors += 1))
        continue
    fi

    parent=$(dirname -- "$target")
    while [[ ! -e $parent && ! -L $parent ]]; do
        parent=$(dirname -- "$parent")
    done
    if [[ ! -d $parent ]]; then
        printf 'Conflict: parent is not a directory: %s\n' "$parent" >&2
        ((errors += 1))
        continue
    fi
    sources+=("$source")
    targets+=("$target")
done < "$manifest"

if $dry_run || (( errors > 0 )); then
    for i in "${!targets[@]}"; do
        printf 'Would link: %s -> %s\n' "${targets[$i]}" "${sources[$i]}"
    done
fi
(( errors == 0 )) || fail "$errors conflict(s) found; no links created."
if $dry_run; then
    printf 'Dry run complete: %s link(s) to create.\n' "${#targets[@]}"
    exit 0
fi

for i in "${!targets[@]}"; do
    mkdir -p -- "$(dirname -- "${targets[$i]}")"
    ln -sT -- "${sources[$i]}" "${targets[$i]}"
    printf 'Linked: %s -> %s\n' "${targets[$i]}" "${sources[$i]}"
done
printf 'Done: %s link(s) created.\n' "${#targets[@]}"
