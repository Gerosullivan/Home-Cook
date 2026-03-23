# Home Cook

A personal food management system for Ger's family, operated entirely through Claude Code. No web UI — the conversation is the interface.

## Family

| Who | Role | Notes |
|-----|------|-------|
| Ger | Dad, main cook | Engineer. Does all cooking and shopping |
| Maura | Mum | Lunch prepped by Ger (currently ham & cheese brioche with rocket) |
| Child 1 | 8 years old | Makes own school lunch |
| Child 2 | 3 years old | |
| Child 3 | 2 years old | |

- **Location**: Ireland
- **Units**: Always metric. Convert any imperial units on sight.
- **Dietary**: No allergies. Kids don't like spicy or hot food.

## Meal Patterns

| Day | Plan |
|-----|------|
| Monday–Thursday | Cook dinner |
| Friday | Takeaway (flexible swap with Thursday) |
| Saturday | Takeaway |
| Sunday | Flexible — sometimes roast, sometimes at parents' |

- **Default servings**: 5 (whole family)
- **3-week rotation**: Recipes are assigned to a 3-week cycle (weeks 1, 2, 3). Rotation to be populated after initial setup.
- **Lunches**: Maura gets a prepped sandwich. Eldest makes his own. Younger two eat at home.

## Shopping

- **Where**: Tesco
- **When**: Friday afternoons
- **Categories**: produce, meat, dairy, bakery, pantry, frozen

## Database

SQLite database at `data/homecook.db`. Schema defined in `data/schema.sql`.

### Quick queries

```bash
# All recipes
sqlite3 data/homecook.db "SELECT id, name FROM recipes ORDER BY name;"

# Recipe with ingredients and steps
sqlite3 data/homecook.db "
  SELECT r.name, r.servings, r.cuisine, r.protein
  FROM recipes r WHERE r.id = ?;
"
sqlite3 data/homecook.db "SELECT raw_ingredient FROM recipe_ingredients WHERE recipe_id = ?;"
sqlite3 data/homecook.db "SELECT step_number, instruction FROM recipe_steps WHERE recipe_id = ? ORDER BY step_number;"

# Today's meal plan
sqlite3 data/homecook.db "SELECT * FROM meal_plan WHERE date = date('now');"

# Search recipes by name
sqlite3 data/homecook.db "SELECT id, name, cuisine, protein FROM recipes WHERE name LIKE '%keyword%';"

# What can I cook with chicken?
sqlite3 data/homecook.db "SELECT id, name FROM recipes WHERE protein = 'chicken';"
```

## Skills

All skills are in `.claude/commands/` and invoked as slash commands.

| Skill | When to use |
|-------|------------|
| `/cook` | Ger says "let's start" or it's time to cook. Guides through tonight's recipe step-by-step with timing optimisation. |
| `/checkin` | After a meal. Reconciles what was planned vs what actually happened. Logs notes and modifications. |
| `/shop` | Friday (or before shopping). Generates a categorised shopping list from the upcoming week's meal plan minus current inventory. |
| `/plan` | Setting up or adjusting upcoming meals. Shows the rotation, allows assigning recipes to days. |
| `/inventory` | After shopping or cooking. Adds/removes/checks kitchen stock. |

## Recipe Cache

Recipes have two layers of cache to avoid redundant work by the scheduled card generator:

1. **HTML card cache**: `data/recipe-cards/{recipe_id}.html` — full recipe card with `{{DATE}}` placeholder
2. **Prep-ahead analysis**: `recipe_prep_ahead` table + `prep_ahead_status` column on `recipes`

**When modifying a recipe** (steps, ingredients, or anything that affects the card), always invalidate both:
```sql
DELETE FROM recipe_prep_ahead WHERE recipe_id = ?;
UPDATE recipes SET prep_ahead_status = NULL, prep_ahead_total_mins = NULL WHERE id = ?;
```
```bash
rm -f data/recipe-cards/{recipe_id}.html
```

This ensures the next scheduled run regenerates the card fresh.

## Inventory & Ingredient Mapping

### How ingredients map between systems

Recipe ingredient names, inventory names, and Tesco product names are all different. The `ingredient_map` table resolves recipe names → inventory names. The `tesco_name` column on `inventory` resolves Tesco names → inventory names.

```sql
-- Look up mapping
SELECT inventory_name FROM ingredient_map WHERE recipe_name = 'Smoked paprika';
-- → 'Paprika'
```

The map populates lazily — on first encounter, find the best inventory match and save it. If no match exists (staple, or not in stock), set `inventory_name = NULL`.

### Deduction rules

Each inventory item has a `deduction_type`:

| Type | When | How |
|------|------|-----|
| `measured` | g, ml, kg, l, pieces | Deduct actual quantity (convert units if needed) |
| `container` | bag, bottle, jar, tub, can | Full use → deduct 1 container. Partial use (tsp, splash) → log as `check_stock`, don't deduct |
| `none` | Spice rack, staples | Never deduct |

### When deductions happen

- **Only planned meals** trigger auto-deduction (from `meal_plan` table or Google Calendar)
- AI-generated suggestions do NOT auto-deduct — Ger must confirm via chat
- The daily scheduled task reconciles yesterday's meal each morning
- If Ger already checked in via chat, the task skips deduction

### Shopping list auto-population

When a recipe ingredient has no inventory match at all, it's auto-added to `shopping_list`. The shopping list is always a draft for Ger's review — the system never auto-orders. Items logged as `check_stock` surface at review time as "you've been using X — do you need more?"

## Kitchen Equipment

- **Wireless thermometers**: 2 available. Use for meat doneness — no guessing.
  - Chicken: 68°C internal temp
  - Remind Ger to probe when oven-cooking meat

## Cooking Mode Guidelines

When guiding a cook via `/cook`:

1. **Timing first**: Identify the longest-running step (e.g. oven preheat, slow roast) and start it immediately
2. **Parallel prep**: While things heat/cook, guide ingredient prep
3. **Portion adjustment**: Scale ingredients to the number of people eating (default 5)
4. **Metric always**: Show all temperatures in Celsius, all weights in grams, all volumes in ml
5. **Step format**: Number each step clearly. Include estimated time per step where relevant.
6. **Kid-friendly notes**: If a recipe has a spice/heat element, suggest reducing or serving sauce on the side for kids

## Fetching External Recipes

When Ger shares a URL to import a recipe (e.g. from ReciMe, BBC Good Food, etc.), use the **Claude in Chrome** browser tools (`mcp__claude-in-chrome__*`) to navigate to the page and read the recipe content. `WebFetch` often fails on these sites due to auth or blocking. The Chrome extension can access pages Ger is logged into.

## File Structure

```
Home-Cook/
├── CLAUDE.md              # This file
├── plan.md                # Project plan and roadmap
├── backlog.md             # Future ideas
├── .claude/commands/      # Claude skills (slash commands)
├── data/
│   ├── schema.sql         # Database schema
│   └── homecook.db        # SQLite database (gitignored)
├── scripts/               # One-time and utility scripts
└── anylist.json           # Original AnyList export (467 recipes)
```
