#!/usr/bin/env python3
"""Build archive/index.html — a cookbook view of every recipe card ever deployed.

Scans archive/*.html (excluding index.html), extracts the recipe name from each
file's <h1>, and lays them out as a grid sorted by mtime (most recently served
first). The page reuses the colour palette from tonights-meal.html.
"""
from __future__ import annotations

import datetime as dt
import html
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = REPO / "archive"
INDEX_PATH = ARCHIVE_DIR / "index.html"

H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def extract_title(card_path: Path) -> str:
    text = card_path.read_text(encoding="utf-8", errors="ignore")
    m = H1_RE.search(text)
    if not m:
        return card_path.stem.replace("-", " ").title()
    return html.unescape(TAG_RE.sub("", m.group(1))).strip()


def format_date(ts: float) -> str:
    return dt.date.fromtimestamp(ts).strftime("%a %-d %b %Y")


def build():
    entries = []
    for path in ARCHIVE_DIR.glob("*.html"):
        if path.name == "index.html":
            continue
        entries.append((path.stat().st_mtime, path))
    entries.sort(key=lambda x: x[0], reverse=True)

    cards_html = []
    for mtime, path in entries:
        title = extract_title(path)
        date_str = format_date(mtime)
        href = html.escape(path.name)
        title_escaped = html.escape(title)
        cards_html.append(
            f'      <a class="cookbook-card" href="{href}">\n'
            f'        <div class="cookbook-card-title">{title_escaped}</div>\n'
            f'        <div class="cookbook-card-date">Last served {date_str}</div>\n'
            f"      </a>"
        )

    count = len(entries)
    generated_at = dt.datetime.now().strftime("%-d %b %Y")

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Cookbook">
<title>Cookbook — Home Cook</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📖</text></svg>">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: #faf8f5;
    color: #2d2a26;
    line-height: 1.6;
    padding: 2rem 1rem 4rem;
  }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  .topnav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    font-size: 0.9rem;
  }}
  .topnav a {{
    color: #a2262c;
    text-decoration: none;
    font-weight: 600;
  }}
  .topnav a:hover {{ text-decoration: underline; }}
  .hero {{
    background: linear-gradient(135deg, #e07b3b 0%, #a2262c 100%);
    color: white;
    border-radius: 16px;
    padding: 2rem 2rem 1.75rem;
    box-shadow: 0 2px 20px rgba(0,0,0,0.06);
    margin-bottom: 1.5rem;
  }}
  .hero .label {{
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.9;
    margin-bottom: 0.35rem;
  }}
  .hero h1 {{
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1.25;
  }}
  .hero p {{
    margin-top: 0.4rem;
    opacity: 0.92;
    font-size: 0.95rem;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.9rem;
  }}
  .cookbook-card {{
    background: #fff;
    border-radius: 14px;
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 8px rgba(0,0,0,0.05);
    text-decoration: none;
    color: inherit;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    border: 1px solid transparent;
    transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
  }}
  .cookbook-card:hover {{
    border-color: #e07b3b;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
  }}
  .cookbook-card-title {{
    font-weight: 700;
    font-size: 1rem;
    color: #2d2a26;
  }}
  .cookbook-card-date {{
    font-size: 0.78rem;
    color: #7a716a;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .footer {{
    margin-top: 2rem;
    text-align: center;
    font-size: 0.8rem;
    color: #9c948c;
  }}
</style>
</head>
<body>
  <div class="wrap">
    <div class="topnav">
      <a href="/">← Tonight's Meal</a>
      <span style="color:#9c948c;">{count} recipes</span>
    </div>

    <div class="hero">
      <div class="label">Cookbook</div>
      <h1>Every recipe we've cooked</h1>
      <p>Sorted by most recently served. Click any card to view the full recipe.</p>
    </div>

    <div class="grid">
{chr(10).join(cards_html)}
    </div>

    <div class="footer">Updated {generated_at}</div>
  </div>
</body>
</html>
"""

    INDEX_PATH.write_text(html_out, encoding="utf-8")
    print(f"Wrote {INDEX_PATH} ({count} recipes)")


if __name__ == "__main__":
    build()
