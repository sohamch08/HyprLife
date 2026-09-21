#!/usr/bin/env python3
"""Open the cached paper picker, counting live PDFs without reading metadata.

Choose Update paper cache in the menu after adding papers or editing notes.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

THEME = Path(__file__).resolve().parents[2] / "themes/papers.rasi"
REFRESH = Path(__file__).resolve().with_name("update-papers-cache.sh")


def cache_path() -> Path:
    base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return Path(os.environ.get("PAPERS_CACHE", str(base / "hyprlife/papers.json"))).expanduser()


def source_paths() -> tuple[Path, Path]:
    # Keep source paths consistent with the cache without resolving symlinks.
    return tuple(Path(os.path.abspath(Path(os.environ.get(variable, str(default))).expanduser()))
                 for variable, default in (
                     ("PAPERS_DIR", Path.home() / "My Papers"),
                     ("PAPERS_NOTES_DIR", Path.home() / "projects/my-research")))


def count_pdfs(root: Path) -> int:
    total = 0
    with os.scandir(root) as entries:
        for entry in entries:
            if entry.is_dir(follow_symlinks=False):
                total += count_pdfs(Path(entry.path))
            elif entry.name.lower().endswith(".pdf") and entry.is_file():
                total += 1
    return total


def read_cache() -> dict:
    data = json.loads(cache_path().read_text(encoding="utf-8"))
    root, notes = source_paths()
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Unsupported cache format")
    if data.get("papers_dir") != str(root) or data.get("notes_dir") != str(notes):
        raise ValueError("Cache belongs to different paper or note folders")
    papers = data.get("papers")
    if not isinstance(papers, list) or not isinstance(data.get("rows"), str):
        raise ValueError("Invalid cached paper list")
    if not isinstance(data.get("enriched"), int):
        raise ValueError("Invalid cached metadata count")
    for paper in papers:
        if not isinstance(paper, dict) or not isinstance(paper.get("path"), str):
            raise ValueError("Invalid cached paper path")
        path = Path(paper["path"])
        if not path.is_absolute() or ".." in path.parts or not path.is_relative_to(root):
            raise ValueError("Cached paper is outside My Papers")
    if len(data["rows"].splitlines()) != len(papers):
        raise ValueError("Cached rows and paper paths do not match")
    return data


def error(message: str) -> int:
    print(message, file=sys.stderr)
    subprocess.run(["rofi", "-theme", str(THEME), "-e", message], check=False)
    return 1


def main() -> int:
    if not shutil.which("rofi"):
        print("Rofi is not installed.", file=sys.stderr)
        return 1
    while True:
        try:
            data = read_cache()
            papers = data["papers"]
            placeholder = "Search: sudan 2008, or type update"
        except (OSError, UnicodeError, ValueError):
            data = {"rows": ""}
            papers = []
            placeholder = "Choose Update paper cache to rebuild the cache"
        if not papers:
            placeholder = "Choose Update paper cache to load papers"
        try:
            total = str(count_pdfs(source_paths()[0]))
        except OSError as exc:
            print(f"Could not count PDFs: {exc}", file=sys.stderr)
            total = "?"
        count = f"{len(papers)}/{total}"
        rows = ('<span font_desc="Iosevka Nerd Font Propo 12">↻</span>'
                '<span rise="1024">  Update paper cache</span>\n' + data["rows"])
        result = subprocess.run([
            "rofi", "-dmenu", "-i", "-no-custom", "-markup-rows", "-no-multi-select",
            "-hover-select",
            "-pid", str(Path(os.environ.get("XDG_RUNTIME_DIR", str(cache_path().parent))) / "hyprlife-papers.pid"),
            "-matching", "normal", "-tokenize", "-normalize-match", "-format", "i",
            "-selected-row", "1" if papers else "0",
            "-p", "📚 My Papers:", "-theme", str(THEME),
            "-theme-str", (f'entry {{ placeholder: {json.dumps(placeholder)}; }}\n'
                           f'textbox-paper-count {{ str: {json.dumps(count)}; }}'),
        ], input=rows, text=True, stdout=subprocess.PIPE, check=False)
        selected = result.stdout.strip()
        if result.returncode != 0 or not selected.isdecimal():
            return 0
        choice = int(selected)
        if choice == 0:
            try:
                update = subprocess.run([str(REFRESH)], text=True,
                                        capture_output=True, check=False)
                if update.returncode != 0:
                    error("Cache update failed:\n" + (update.stderr or update.stdout))
            except OSError as exc:
                error(f"Could not run the cache updater: {exc}")
            # Read the new snapshot and reopen Rofi after the updater finishes.
            continue
        if choice > len(papers):
            return 1
        path = Path(papers[choice - 1]["path"])
        if not path.is_file():
            error(f"Paper moved or deleted: {path}\nChoose Update paper cache in the menu.")
            continue
        break
    # Viewer discovery happens only after selection, never before showing Rofi.
    if shutil.which("okular"):
        viewer = ["okular"]
    elif shutil.which("flatpak") and subprocess.run(
        ["flatpak", "info", "org.kde.okular"], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0:
        viewer = ["flatpak", "run", "org.kde.okular"]
    else:
        return error("Okular is not installed (native or Flatpak).")
    os.execvp(viewer[0], viewer + [str(path)])


if __name__ == "__main__":
    raise SystemExit(main())
