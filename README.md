# Home Cook

A personal food management system for a family of five, built entirely on Claude. There is no web UI, no app, and no code to maintain. The database holds the recipes and inventory, Claude generates the outputs, and the conversation is the interface.

## How it works

```
Google Calendar                Claude App                    Phone
(meal plan)            (scheduled task, daily)          (home screen shortcut)
     |                         |                              |
     +-----> Which recipe? --->+                              |
                               |                              |
             SQLite DB ------->+ recipe data                  |
             Cache ----------->+ or cached HTML               |
                               |                              |
                               +----> tonights-meal.html ---->+
                               |      (served on LAN)         |
                               |                              |
                        Mobile chat <-------------------------+
                        (Despatch)     "too dry, add more     |
                               |        garlic next time"     |
                               |                              |
                               +----> DB updated, cache       |
                                      invalidated             |
```

### Daily flow

1. **Scheduled task** runs on the Mac via the Claude app. It checks the Home-Cook Google Calendar for tonight's recipe, pulls it from the SQLite database, and generates a recipe card (`tonights-meal.html`).

2. **Recipe card** is served on the local network by a lightweight HTTP server. A home screen shortcut on the phone opens it directly.

3. **Before cooking**, a "Prep Ahead" section on the card tells you what to prep before the 5:00 PM school pickup, so active cooking after 5:30 PM is minimised. Checkboxes persist across page refreshes.

4. **After cooking**, feedback goes through the Claude app on mobile (via Despatch/Cowork). Say what you changed, what the kids thought, or that you swapped to takeaway. Claude updates the database and clears the cache so the card regenerates next time that recipe comes up.

### Caching

Recipes repeat on a 3-week rotation, so two layers of cache avoid redundant work:

- **HTML card cache** (`data/recipe-cards/{id}.html`) — the full generated card with a `{{DATE}}` placeholder. On repeat runs, the task just swaps in today's date. No LLM generation needed.
- **Prep-ahead analysis** (`recipe_prep_ahead` table) — classified prep steps stored in the DB. Avoids re-analysing the same recipe's steps every time.

Both caches are automatically invalidated when a recipe is modified.

## Prerequisites

- **Claude app** (macOS) with a scheduled task pointing to `scripts/generate-recipe-card.md`
- **Claude app** (iOS) for mobile chat via Despatch/Cowork
- **Claude Code** (CLI) for direct terminal interaction when needed
- **SQLite** (comes with macOS)
- **Chrome + Claude in Chrome extension** for importing recipes from external sites

## Tonight's Meal Server

A local HTTP server serves `tonights-meal.html` on the home network.

| | |
|---|---|
| **URL** | `http://192.168.4.200:9123/tonights-meal.html` |
| **Port** | 9123 |
| **Managed by** | macOS `launchd` — starts on boot, restarts on crash |
| **Plist** | `~/Library/LaunchAgents/com.homecook.server.plist` |
| **Logs** | `/tmp/homecook-server.log` |
| **Serves from** | repo root |

```bash
# Stop the server
launchctl unload ~/Library/LaunchAgents/com.homecook.server.plist

# Start the server
launchctl load ~/Library/LaunchAgents/com.homecook.server.plist

# Check logs
cat /tmp/homecook-server.log
```

## Database

SQLite at `data/homecook.db`. Schema in `data/schema.sql`.

Key tables:

| Table | Purpose |
|-------|---------|
| `recipes` | 480+ recipes with cuisine, protein, kid-friendly flags |
| `recipe_ingredients` | Parsed ingredients per recipe |
| `recipe_steps` | Method steps per recipe |
| `recipe_prep_ahead` | Cached prep-ahead analysis (step classifications) |
| `inventory` | Current kitchen stock (fridge, freezer, pantry, spice rack) |
| `meal_plan` | Planned meals by date |
| `meal_log` | What actually happened (outcome, modifications, notes) |
| `recipe_notes` | Feedback and tips collected after cooking |

## Repo structure

```
Home-Cook/
├── README.md                           # This file
├── CLAUDE.md                           # Instructions for Claude (family, rules, cache logic)
├── tonights-meal.html                  # Generated recipe card (served to phone)
├── data/
│   ├── schema.sql                      # Database schema
│   ├── homecook.db                     # SQLite database (gitignored)
│   ├── draft_meal_plan.json            # Fallback meal plan
│   └── recipe-cards/                   # Cached HTML cards per recipe (gitignored)
├── scripts/
│   ├── generate-recipe-card.md         # Scheduled task instructions
│   ├── import_anylist.py               # One-time AnyList import
│   ├── auto_tag.py                     # Cuisine/protein tagging
│   └── normalise_units.py              # Imperial-to-metric conversion
├── .claude/commands/                   # Slash command skills (legacy, still usable from CLI)
├── plan.md                             # Project roadmap
├── backlog.md                          # Future ideas
└── anylist.json                        # Original AnyList export (467 recipes)
```

## Interaction modes

| Mode | When | How |
|------|------|-----|
| **Scheduled task** | Daily, automatic | Claude app on Mac generates tonight's recipe card |
| **Mobile chat** | Before/after cooking | Despatch via Claude app on iOS — feedback, recipe changes, planning |
| **Terminal** | Setup, bulk operations | Claude Code CLI — imports, schema changes, debugging |
