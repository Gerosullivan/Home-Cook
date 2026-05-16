#!/usr/bin/env python3
"""Inject a small Cookbook nav link into a recipe card HTML file.

Idempotent: if the marker class is already present, the file is left alone.

Usage:
  python3 scripts/inject-cookbook-nav.py tonights-meal.html
  python3 scripts/inject-cookbook-nav.py --mode=archive archive/foo.html
  python3 scripts/inject-cookbook-nav.py --all-archive
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKER = "data-hc-nav"

NAV_TONIGHT = (
    '<div class="hc-nav" data-hc-nav="tonight" '
    'style="max-width:680px;margin:0 auto 1rem;display:flex;'
    'justify-content:flex-end;font-size:0.85rem;">'
    '<a href="/archive/" '
    'style="color:#a2262c;text-decoration:none;font-weight:600;">'
    '📖 Cookbook</a></div>'
)

NAV_ARCHIVE = (
    '<div class="hc-nav" data-hc-nav="archive" '
    'style="max-width:680px;margin:0 auto 1rem;display:flex;'
    'justify-content:space-between;font-size:0.85rem;">'
    '<a href="/archive/" '
    'style="color:#a2262c;text-decoration:none;font-weight:600;">'
    '← Cookbook</a>'
    '<a href="/" '
    'style="color:#a2262c;text-decoration:none;font-weight:600;">'
    'Tonight\'s Meal →</a></div>'
)

BODY_RE = re.compile(r"(<body[^>]*>)", re.IGNORECASE)
EXISTING_NAV_RE = re.compile(
    r'\n?<div class="hc-nav" data-hc-nav="[^"]*"[^>]*>.*?</div>',
    re.DOTALL,
)


def _flavour_of(text: str) -> str | None:
    m = re.search(r'data-hc-nav="([^"]*)"', text)
    return m.group(1) if m else None


def inject(path: Path, nav_html: str, preserve_mtime: bool = True) -> str:
    text = path.read_text(encoding="utf-8")
    desired_flavour = _flavour_of(nav_html)
    current_flavour = _flavour_of(text)

    if current_flavour == desired_flavour:
        return "skip"

    if current_flavour is not None:
        text = EXISTING_NAV_RE.sub("", text, count=1)

    new_text, n = BODY_RE.subn(r"\1\n" + nav_html, text, count=1)
    if n == 0:
        return "no-body"
    stat = path.stat()
    path.write_text(new_text, encoding="utf-8")
    if preserve_mtime:
        os.utime(path, (stat.st_atime, stat.st_mtime))
    return "replaced" if current_flavour else "wrote"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", nargs="?", help="File to inject")
    p.add_argument(
        "--mode",
        choices=("tonight", "archive"),
        default="tonight",
        help="Nav flavour to inject (default: tonight)",
    )
    p.add_argument(
        "--all-archive",
        action="store_true",
        help="Inject archive nav into every archive/*.html (excluding index.html)",
    )
    args = p.parse_args()

    if args.all_archive:
        archive_dir = REPO / "archive"
        for path in sorted(archive_dir.glob("*.html")):
            if path.name == "index.html":
                continue
            status = inject(path, NAV_ARCHIVE)
            print(f"{status}: {path.relative_to(REPO)}")
        return

    if not args.path:
        p.error("path required (or use --all-archive)")

    target = Path(args.path)
    if not target.is_absolute():
        target = REPO / target

    nav = NAV_TONIGHT if args.mode == "tonight" else NAV_ARCHIVE
    status = inject(target, nav)
    print(f"{status}: {target.relative_to(REPO)}")


if __name__ == "__main__":
    main()
