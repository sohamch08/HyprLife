#!/usr/bin/env python3
"""Rebuild the paper search cache from PDFs and matching Markdown frontmatter.

PAPERS_DIR: ~/My Papers
PAPERS_NOTES_DIR: ~/projects/my-research
PAPERS_CACHE: ~/.cache/hyprlife/papers.json (honors XDG_CACHE_HOME)
Requires PyYAML. This is the only script that scans PDFs and reads notes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from html import escape
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

from openpapers import cache_path, source_paths

def key(text: str) -> str:
    return "".join(c for c in text.casefold() if c.isalnum())


def note_text(value: object) -> str:
    """Flatten YAML lists and turn Obsidian author links into readable names."""
    if isinstance(value, list):
        return "; ".join(filter(None, (note_text(item) for item in value)))
    if value is None or isinstance(value, dict):
        return ""
    text = str(value)
    def link(match: re.Match) -> str:
        target, _, alias = match[1].partition("|")
        name = target.split("#", 1)[0].rsplit("/", 1)[-1]
        if name.endswith(".md"):
            name = name[:-3]
        return name + (" " + alias if alias and alias != name else "")
    return clean(re.sub(r"\[\[([^\]]+)\]\]", link, text))


def notes_index(root: Path, wanted: set[str]) -> dict[str, list[dict[str, str]]]:
    import yaml

    # Use LibYAML's safe parser when available; retain a safe portable fallback.
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    index: dict[str, list[dict[str, str]]] = {}
    if not root.is_dir():
        print(f"Notes folder not found; using filenames only: {root}", file=sys.stderr)
        return index
    for path in root.rglob("*.md"):
        identifier = key(path.stem)
        if identifier not in wanted:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
            frontmatter = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)",
                                   text, re.DOTALL)
            if not frontmatter:
                continue
            data = yaml.load(frontmatter[1], Loader=loader)
            if not isinstance(data, dict):
                continue
            fields = {
                "author": note_text(data.get("authors") or data.get("author")),
                "year": note_text(data.get("year")),
                "conference": note_text(data.get("conference")),
                "journal": note_text(data.get("journal")),
                "title": note_text(data.get("title")),
            }
            if any(fields.values()):
                index.setdefault(identifier, []).append(fields)
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            print(f"Skipping unreadable note {path}: {exc}", file=sys.stderr)
    return index


def clean(text: str) -> str:
    # Preserve literal text; never allow filenames/metadata to inject Rofi rows.
    return " ".join(re.sub(r"[\x00-\x1f\x7f{}]", " ", text).split())


def author_last_names(authors: str) -> str:
    """Shorten display names; keep full author metadata for searching."""
    names = []
    particles = {"van", "von", "de", "del", "der", "den", "di", "da", "dos", "du", "la", "le"}
    for author in authors.split(";"):
        parts = author.strip().split()
        if not parts:
            continue
        start = len(parts) - 1
        while start > 0 and parts[start - 1].casefold() in particles:
            start -= 1
        names.append(" ".join(parts[start:]))
    return ", ".join(names)


@dataclass(frozen=True)
class Paper:
    path: Path
    label: str
    search: str
    enriched: bool
    author: str
    year: str
    conference: str
    journal: str
    title: str


def column(text: str, width: int) -> str:
    """Pad or shorten a display cell without truncating searchable metadata."""
    text = unicodedata.normalize("NFC", text)
    def cells(char: str) -> int:
        if unicodedata.combining(char):
            return 0
        return 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
    size = sum(cells(char) for char in text)
    if size > width:
        result = ""
        size = 0
        for char in text:
            if size + cells(char) > width - 1:
                break
            result += char
            size += cells(char)
        text = result + "…"
        size += 1
    return text + " " * (width - size)


def paper_entry(path: Path, root: Path, index: dict) -> Paper:
    relative = str(path.relative_to(root))
    # Only use an unambiguous corresponding note, never another paper's metadata.
    candidates = index.get(key(path.stem), [])
    fields = candidates[0] if len(candidates) == 1 else {}
    authors = clean(fields.get("author", ""))
    year = fields.get("year", "")
    venue = fields.get("conference", "") or fields.get("journal", "")
    details = ", ".join(value for value in (venue, year) if value)
    label = ("  " + column(author_last_names(authors) or "—", 95)
             + "    " + column(details, 44).rstrip())
    search = clean(" ".join([relative] + [fields.get(f, "") for f in
                         ("author", "year", "conference", "journal", "title")]))
    words = re.findall(r"[^\W_]+", unicodedata.normalize("NFKD", search), re.UNICODE)
    # Comma-suffixed aliases allow both 'Sudan 2008' and 'Sudan, 2008'.
    search += " " + " ".join(words) + " " + " ".join(word + ',' for word in words)
    return Paper(path, label, search, bool(fields), authors, fields.get("year", ""),
                 fields.get("conference", ""), fields.get("journal", ""),
                 fields.get("title", ""))



def display_markup(label: str) -> str:
    # Raise the smaller text to the center of the enlarged icons.
    return "".join(
        f'<span font_desc="Iosevka Nerd Font Propo {17 if part == "" else 18}">{part}</span>'
        if part in ("", "", "") else
        f'<span rise="3072">{escape(part)}</span>'
        for part in re.split(r"([])", label) if part
    )


def rebuild() -> dict:
    root, notes = source_paths()
    if not root.is_dir():
        raise ValueError(f"Paper folder not found: {root}")
    if not notes.is_dir():
        raise ValueError(f"Notes folder not found: {notes}")
    paths = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"]
    index = notes_index(notes, {key(p.stem) for p in paths})
    papers = sorted((paper_entry(p, root, index) for p in paths),
                    key=lambda p: str(p.path.relative_to(root)).casefold())
    records = [dict(asdict(p), path=str(p.path)) for p in papers]
    data = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "papers_dir": str(root),
        "notes_dir": str(notes),
        "papers": records,
        "enriched": sum(p.enriched for p in papers),
        "rows": "\n".join(escape(p.search) + "\0display\x1f" + display_markup(p.label) for p in papers) + ("\n" if papers else ""),
    }
    destination = cache_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        # Replace atomically so an open picker never reads a half-written cache.
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                         dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return data


def main() -> int:
    try:
        data = rebuild()
    except ImportError:
        print("Install PyYAML: sudo dnf install python3-pyyaml", file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Cache update failed; previous cache kept: {exc}", file=sys.stderr)
        return 1
    print(f"Cached {len(data['papers'])} PDFs ({data['enriched']} with note metadata): {cache_path()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
