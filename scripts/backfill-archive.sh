#!/bin/bash
# Backfill archive/ from git history of tonights-meal.html.
# Walks every commit that touched the file, oldest -> newest, and writes
# archive/<slug>.html for each unique recipe. Repeats overwrite, so the final
# mtime of each file is the most recent serving date.
#
# Idempotent: safe to re-run. Will not touch archive/index.html.

set -euo pipefail
cd "$(dirname "$0")/.."

ARCHIVE_DIR="archive"
mkdir -p "$ARCHIVE_DIR"

slugify() {
  python3 -c "
import re, sys, html
s = sys.stdin.read()
s = html.unescape(s)
s = re.sub(r'<[^>]+>', '', s)
s = re.sub(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF️]', '', s)
s = s.lower().strip()
s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
print(s)
"
}

extract_h1() {
  python3 -c "
import re, sys
m = re.search(r'<h1[^>]*>(.*?)</h1>', sys.stdin.read(), re.DOTALL | re.IGNORECASE)
print(m.group(1).strip() if m else '')
"
}

count=0
written=0

# Oldest -> newest so newer commits naturally overwrite older slug collisions
while IFS=$'\t' read -r commit date; do
  count=$((count + 1))
  content=$(git show "$commit:tonights-meal.html" 2>/dev/null || true)
  if [ -z "$content" ]; then
    echo "skip $commit ($date): empty"
    continue
  fi

  h1=$(printf '%s' "$content" | extract_h1)
  slug=$(printf '%s' "$h1" | slugify)

  if [ -z "$slug" ]; then
    echo "skip $commit ($date): no h1"
    continue
  fi

  out="$ARCHIVE_DIR/$slug.html"
  printf '%s' "$content" > "$out"
  # Set mtime to commit date so the index can sort by recency
  touch -t "$(date -j -f %Y-%m-%d "$date" +%Y%m%d0000)" "$out"
  written=$((written + 1))
  echo "$date  $slug"
done < <(git log --reverse --format=$'%H\t%ad' --date=short tonights-meal.html)

echo
echo "Scanned $count commits, wrote $written archive entries to $ARCHIVE_DIR/"
