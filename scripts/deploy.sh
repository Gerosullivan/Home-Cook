#!/bin/bash
# Auto-deploy tonights-meal.html to Vercel via git push.
# Runs as a cron job after the scheduled recipe card generation.
# Handles stale lock files from sandboxed processes.
#
# Also snapshots tonights-meal.html into archive/<slug>.html and regenerates
# archive/index.html so the deployed cookbook stays current.

set -uo pipefail
cd /Users/ger/Agents/Home-Cook || exit 1

# Clean up any stale git lock files
rm -f .git/index.lock .git/HEAD.lock

# Bail early if nothing to do
if git diff --quiet tonights-meal.html 2>/dev/null \
   && git diff --quiet archive/ 2>/dev/null; then
  exit 0
fi

# Ensure tonights-meal.html has the Cookbook nav link (idempotent safety net)
if [ -f tonights-meal.html ]; then
  python3 scripts/inject-cookbook-nav.py tonights-meal.html >/dev/null 2>&1 || true
fi

# Snapshot tonight's card into archive/<slug>.html if it exists
if [ -f tonights-meal.html ]; then
  slug=$(python3 -c "
import re, sys, html
text = open('tonights-meal.html', encoding='utf-8', errors='ignore').read()
m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.DOTALL | re.IGNORECASE)
if not m:
    sys.exit(1)
s = html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
s = re.sub(r'[\U0001F300-\U0001FAFF\U00002600-\U000027BF️]', '', s)
s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
print(s)
")
  if [ -n "$slug" ]; then
    mkdir -p archive
    cp tonights-meal.html "archive/${slug}.html"
    # Make sure the archive copy has the archive-flavour nav (back/forward links)
    python3 scripts/inject-cookbook-nav.py --mode=archive "archive/${slug}.html" >/dev/null 2>&1 || true
  fi
fi

# Regenerate cookbook index
python3 scripts/build-archive-index.py >/dev/null

# Stage everything we care about and commit if there's a diff to commit
git add tonights-meal.html archive/
if git diff --cached --quiet; then
  exit 0
fi

git commit -m "Update tonight's meal card ($(date +%Y-%m-%d))"
git push
