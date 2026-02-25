# Home Cook - Project Plan

## Overview

A personal food management system operated entirely through Claude Code. No web UI - the conversation is the interface. Built for Ger's family of 5 in Ireland.

---

## Family Profile

| Member | Role | Notes |
|--------|------|-------|
| Ger | Dad / main cook | Engineer, does the cooking and shopping |
| Maura | Mum | Needs lunch prepped (currently: ham & cheese brioche with rocket) |
| Child 1 | 8 years old | Makes own school lunch |
| Child 2 | 3 years old | |
| Child 3 | 2 years old | |

- **Location**: Ireland
- **Units**: Metric (convert any imperial in recipes)
- **Dietary**: No allergies. Kids don't like spicy/hot food.
- **Shopping**: Tesco, Friday afternoons

---

## Meal Patterns

| Day | Dinner | Notes |
|-----|--------|-------|
| Monday | Cook | |
| Tuesday | Cook | |
| Wednesday | Cook | |
| Thursday | Cook | Flexible swap with Friday |
| Friday | Takeaway | Flexible swap with Thursday |
| Saturday | Takeaway | |
| Sunday | Flexible | Sometimes roast, sometimes at parents' |

- **3-week rotation**: Ger has a rough plan for which recipes go in which week. To be populated after setup.
- **Lunches**: Maura's lunch is prepped by Ger (sandwich rotation). Eldest makes his own. Younger two at home.

---

## Claude Skills (`.claude/commands/`)

Skills are slash commands that trigger guided conversational workflows. These are the primary way Ger interacts with the system day-to-day.

### `/cook` - Cooking Mode
Triggered when Ger says "let's start" (typically around 5pm):
1. Look up today's meal plan
2. Present the recipe step-by-step
3. Optimise timing (e.g. "preheat oven now, prep veg while it heats")
4. Adjust portions for number of people eating
5. Guide through the cook in a CLI-friendly format

### `/checkin` - Post-Meal Debrief
Triggered after a meal to reconcile plan vs reality:
1. Ask what was actually cooked vs what was planned
2. Note any ingredient swaps or modifications
3. Offer to **update the existing recipe** or **fork it as a new variation**
4. Update inventory based on what was used
5. Log notes ("kids loved this", "too salty", "double the garlic next time")
6. Handle cancellations (meal didn't happen, had something else instead)

### `/shop` - Shopping List
Generate and manage the Tesco shopping list:
1. Pull next week's meal plan
2. Calculate required ingredients
3. Subtract what's already in inventory
4. Group by category (produce, meat, dairy, bakery, pantry, frozen)
5. Present as a checklist for the Friday shop

### `/plan` - Meal Planning
Set up or adjust upcoming meals:
1. Show the current rotation week (1, 2, or 3)
2. Suggest meals based on rotation, or let Ger override
3. Handle swaps (e.g. move Thursday's cook to Friday)
4. Flag if a planned meal needs ingredients not in inventory

### `/inventory` - Kitchen Update
Quick inventory management:
1. Add items after a shop
2. Remove/adjust after cooking
3. Check what's running low
4. Flag items nearing expiry

---

## Architecture

### Tech Stack
- **Database**: SQLite (single file at `data/homecook.db`)
- **Interface**: Claude Code (no web UI, no API server)
- **Platform**: macOS

### Project Structure

```
Home-Cook/
├── CLAUDE.md              # Project context for Claude across sessions
├── plan.md                # This file - project plan and roadmap
├── backlog.md             # Future ideas and feature requests
├── .claude/
│   └── commands/          # Claude skills (slash commands)
│       ├── cook.md        # /cook - guided cooking mode
│       ├── checkin.md     # /checkin - post-meal debrief
│       ├── shop.md        # /shop - shopping list generation
│       ├── plan.md        # /plan - meal planning
│       └── inventory.md   # /inventory - kitchen stock update
├── data/
│   ├── schema.sql         # Database schema definition
│   └── homecook.db        # SQLite database (generated)
├── scripts/
│   └── import_anylist.py  # One-time import from AnyList JSON
└── anylist.json           # Original AnyList export (reference)
```

---

## Database Schema

### recipes

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| name | TEXT NOT NULL | Recipe name |
| icon | TEXT | AnyList icon field |
| servings | INTEGER | Default portions |
| cook_time_mins | INTEGER | |
| prep_time_mins | INTEGER | |
| source_name | TEXT | Where the recipe came from |
| source_url | TEXT | Link to original |
| rating | REAL | 0-5 scale |
| notes | TEXT | |
| cuisine | TEXT | italian, asian, mexican, irish, indian, mediterranean, etc. |
| protein | TEXT | chicken, beef, lamb, pork, fish, seafood, vegetarian, vegan |
| meal_type | TEXT | dinner, lunch, side, snack, breakfast, dessert |
| difficulty | TEXT | easy, medium, hard |
| kid_friendly | BOOLEAN | Based on spice level and ingredients |
| spice_level | INTEGER | 0=none, 1=mild, 2=medium, 3=hot |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### recipe_ingredients

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| recipe_id | INTEGER FK | References recipes |
| name | TEXT | Parsed ingredient name |
| quantity | TEXT | Kept as text ("1/2", "2-3") |
| unit | TEXT | Normalised to metric |
| raw_ingredient | TEXT | Original AnyList string |
| note | TEXT | Prep instructions (e.g. "diced") |

### recipe_steps

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| recipe_id | INTEGER FK | |
| step_number | INTEGER | |
| instruction | TEXT | |

### recipe_tags

| Column | Type | Notes |
|--------|------|-------|
| recipe_id | INTEGER FK | |
| tag | TEXT | Flexible tagging system |
| | PRIMARY KEY | (recipe_id, tag) |

### inventory

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT | Item name |
| quantity | REAL | |
| unit | TEXT | |
| location | TEXT | fridge, freezer, pantry, spice_rack |
| bought_date | DATE | |
| expiry_date | DATE | |
| notes | TEXT | |

### meal_plan

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| date | DATE | |
| meal_type | TEXT | dinner, lunch |
| recipe_id | INTEGER FK | Nullable (for takeaway, eating out) |
| description | TEXT | "takeaway", "at parents'", "ham & cheese brioche" |
| rotation_week | INTEGER | 1, 2, or 3 |
| servings | INTEGER | Usually 5, adjustable per meal |

### shopping_list

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| item_name | TEXT | |
| quantity | REAL | |
| unit | TEXT | |
| category | TEXT | produce, meat, dairy, bakery, pantry, frozen |
| recipe_id | INTEGER FK | Which recipe needs this (nullable) |
| checked | BOOLEAN | Tick off during Tesco shop |
| created_date | DATE | |

---

## Detailed Todo List

### Phase 1: Foundation

#### 1.1 Repository Setup
- [x] Initialise git repo (`git init`)
- [x] Create `.gitignore` (ignore `data/homecook.db`, `.DS_Store`, `__pycache__/`, `*.pyc`)
- [x] Create directory structure (`data/`, `scripts/`, `.claude/commands/`)
- [x] Initial commit with `plan.md` and `anylist.json`

#### 1.2 Project Context
- [x] Create `CLAUDE.md` with:
  - [x] Family profile (names, ages, roles)
  - [x] Meal patterns (Mon-Thu cook, Fri/Sat takeaway, Sunday flexible)
  - [x] 3-week rotation framework
  - [x] Lunch details (Maura's sandwich, eldest's school lunch)
  - [x] Dietary notes (no allergies, kids don't like spicy)
  - [x] Shopping habits (Tesco, Friday afternoons)
  - [x] Database location and how to query it
  - [x] Skill descriptions and when to use them
  - [x] Metric units policy
  - [x] Cooking mode instructions (timing optimisation, portion adjustment)

#### 1.3 Database
- [x] Write `data/schema.sql` with all table definitions:
  - [x] `recipes` table
  - [x] `recipe_ingredients` table
  - [x] `recipe_steps` table
  - [x] `recipe_tags` table
  - [x] `inventory` table
  - [x] `meal_plan` table
  - [x] `shopping_list` table
  - [x] `meal_log` table (actual vs planned - supports `/checkin`)
  - [x] `recipe_notes` table (per-recipe notes from check-ins, e.g. "kids loved this")
- [x] Create indexes on frequently queried columns (recipe name, date, cuisine, protein)
- [x] Initialise `data/homecook.db` by running the schema

#### 1.4 Recipe Import
- [x] Write `scripts/import_anylist.py`:
  - [x] Parse `anylist.json`
  - [x] Insert into `recipes` (map name, icon, servings, cookTime, prepTime, sourceName, sourceUrl, rating, note)
  - [x] Parse `servings` string to integer
  - [x] Parse `cookTime` and `prepTime` strings to minutes (seconds ÷ 60)
  - [x] Insert into `recipe_ingredients` (map name, quantity, rawIngredient, note)
  - [x] Parse and separate quantity from unit in ingredient quantities
  - [x] Insert into `recipe_steps` (map preparationSteps with step numbers)
  - [x] Handle duplicates (8 skipped: Pad Thai, Chicken in a pot, etc.)
  - [x] Log import summary (459 imported, 8 skipped)
- [x] Run the import script
- [x] Verify: 459 unique recipes (467 - 8 dupes), spot-checked

#### 1.5 Claude Skills
- [x] Write `.claude/commands/cook.md`:
  - [x] Query today's meal plan from database
  - [x] Fetch full recipe (ingredients, steps)
  - [x] Instructions for timing optimisation
  - [x] Portion adjustment guidance (default 5 servings)
  - [x] CLI-friendly step-by-step presentation format
- [x] Write `.claude/commands/checkin.md`:
  - [x] Query today's planned meal
  - [x] Prompt: did you cook what was planned?
  - [x] If yes: any modifications? Log to `meal_log`
  - [x] If no: what happened instead? (cancelled, swapped, takeaway)
  - [x] Offer to update recipe or fork as new variation
  - [x] Prompt for notes (kid reactions, taste adjustments, tips)
  - [x] Save notes to `recipe_notes`
  - [x] Update inventory based on what was used
- [x] Write `.claude/commands/shop.md`:
  - [x] Query upcoming week's meal plan
  - [x] Aggregate all required ingredients
  - [x] Query inventory and subtract what's in stock
  - [x] Group items by category (produce, meat, dairy, bakery, pantry, frozen)
  - [x] Present as a formatted checklist
  - [x] Instructions for marking items as checked during shop
- [x] Write `.claude/commands/plan.md`:
  - [x] Query current rotation week
  - [x] Show current week's plan (or upcoming week)
  - [x] Allow assigning recipes to days
  - [x] Handle day swaps (e.g. swap Thu cooking with Fri takeaway)
  - [x] Flag missing ingredients for planned recipes
  - [x] Support marking days as takeaway, eating out, at parents', etc.
- [x] Write `.claude/commands/inventory.md`:
  - [x] Query current inventory by location
  - [x] Instructions for adding items (after a shop)
  - [x] Instructions for removing/adjusting items
  - [x] Show what's running low
  - [x] Flag items nearing expiry

#### 1.6 Backlog
- [x] Create `backlog.md` with all future ideas, categorised

#### 1.7 Foundation Commit
- [x] Commit all Phase 1 work

---

### Phase 2: Recipe Enhancement

#### 2.1 Auto-Tagging
- [x] Write `scripts/auto_tag.py`:
  - [x] **Cuisine detection**: keyword matching on recipe name + ingredients
    - [x] Italian, Asian, Indian, Mexican, Irish, British, Mediterranean, French, Spanish, Korean, Thai, Japanese + Chinese, Middle Eastern, Portuguese, Caribbean
  - [x] **Protein detection**: scan ingredient names (excludes stock/broth/sauce false positives)
    - [x] Chicken, beef, lamb, pork, turkey, duck
    - [x] Salmon, tuna, cod, sea bass, trout, halibut, monkfish, mackerel
    - [x] Prawns/shrimp, shellfish (clams, mussels, scallops, crab, squid)
    - [x] Tofu (vegetarian)
    - [x] No protein → vegetarian
  - [x] **Spice level**: scan recipe name + ingredients + steps
    - [x] Level 3 (hot): 4 recipes
    - [x] Level 2 (medium): 169 recipes
    - [x] Level 1 (mild): 56 recipes
    - [x] Level 0 (none): 230 recipes
  - [x] **Kid-friendly**: spice_level <= 1 AND no unusual ingredients (263 yes, 196 no)
  - [x] **Meal type**: dinner (381), lunch (46), side (10), snack (6), breakfast (6), dessert (5), drink (5)
- [x] Run auto-tagger against all 459 recipes
- [x] Review summary: counts per cuisine, protein, spice level
- [x] Commit tagging results

#### 2.2 Unit Normalisation
- [x] Write `scripts/normalise_units.py`:
  - [x] Build imperial→metric conversion map:
    - [x] Cups → ml (1 cup = 240ml)
    - [x] Oz → g (1 oz = 28g)
    - [x] Lb → g (1 lb = 454g)
    - [x] Fl oz → ml
    - [x] Fahrenheit → Celsius (in prep steps)
    - [x] Inches → cm (in prep notes)
  - [x] Parse quantity+unit from `recipe_ingredients.quantity` field
  - [x] Convert and update the `unit` column
  - [x] Keep `raw_ingredient` untouched as original reference
  - [x] Flag any quantities that can't be parsed (0 flagged)
  - [x] Scan `recipe_steps` for Fahrenheit temperatures and convert to Celsius
- [x] Run normaliser (674 ingredient conversions, 54 step conversions)
- [x] Review flagged items (none)
- [x] Commit normalisation results

#### 2.3 Phase 2 Verification
- [x] Run all verification queries (459 recipes, 5370 ingredients, 0 imperial units remaining, 0 °F remaining)
- [x] Spot-check recipes for correct tags (Bolognese, Pad Thai, jerk chicken, Guinness pies, halloumi, carbonara, smoothies)
- [x] Spot-check unit conversions (1/4 cup → 60ml, 1 lb → 455g, °F → °C)
- [x] Final commit for Phase 2

---

### Phase 3: Inventory System

#### 3.1 Initial Population
- [x] Walk through kitchen with Ger to populate inventory:
  - [x] Fridge contents (26 items)
  - [x] Freezer contents (22 items)
  - [x] Pantry / dry goods (38 items incl. fruit basket & veg)
  - [x] Spice rack (25 items)
- [x] Insert all items into `inventory` table (111 total)

#### 3.2 Inventory Workflows
- [ ] Test `/inventory` skill: add items after a shop
- [ ] Test `/inventory` skill: remove items after cooking
- [ ] Test `/inventory` skill: check low stock
- [ ] Test `/inventory` skill: expiry warnings

---

### Phase 4: Meal Planning (future)

#### 4.1 Rotation Setup
- [ ] Work with Ger to define Week 1 recipes
- [ ] Work with Ger to define Week 2 recipes
- [ ] Work with Ger to define Week 3 recipes
- [ ] Populate `meal_plan` with initial 3-week rotation

#### 4.2 Shopping List
- [ ] Test `/shop` skill: generate list from meal plan
- [ ] Test `/shop` skill: subtract inventory from required ingredients
- [ ] Test `/shop` skill: group by Tesco aisle/category

#### 4.3 Calendar Integration
- [ ] Research best approach for macOS (osascript, .ics export, CalDAV)
- [ ] Implement chosen approach
- [ ] Test adding/removing meal plan entries to Apple Calendar

#### 4.4 Lunch Rotation
- [ ] Build a small set of lunch ideas for Maura
- [ ] Integrate into `/plan` skill and shopping list generation

---

### Phase 5: Recommendations (future)

#### 5.1 Inventory-Aware Suggestions
- [ ] "What can I cook with what I have?" query logic
- [ ] Rank recipes by ingredient match percentage
- [ ] Factor in expiring items (prioritise recipes using them)

#### 5.2 Weekly Suggestions
- [ ] Suggest balanced weeks (variety of cuisine, protein, difficulty)
- [ ] Ensure kid-friendly meals are well distributed
- [ ] Avoid repeating the same protein too many days in a row

#### 5.3 Expiry Alerts
- [ ] Query inventory for items expiring within 3 days
- [ ] Suggest recipes that use those items
- [ ] Surface during `/plan` and `/cook` workflows

---

## Backlog / Future Ideas

- Seasonal veg recommendations for Ireland
- Tesco integration (log in, see special offers and seasonal items)
- Receipt parsing for automatic inventory updates
- Recipe scaling (auto-adjust portions)
- Nutritional tracking
- Favourite / most-cooked recipe tracking
- Lunch rotation ideas for Maura (beyond ham & cheese brioche)
- Cooking history log

---

## Verification (after Phase 1+2)

```bash
# Should return 467
sqlite3 data/homecook.db "SELECT COUNT(*) FROM recipes;"

# Spot-check a recipe
sqlite3 data/homecook.db "SELECT name, cuisine, protein, kid_friendly FROM recipes WHERE name LIKE '%Bolognese%';"

# Check ingredients imported
sqlite3 data/homecook.db "SELECT COUNT(*) FROM recipe_ingredients;"

# Check tagging coverage
sqlite3 data/homecook.db "SELECT cuisine, COUNT(*) FROM recipes WHERE cuisine IS NOT NULL GROUP BY cuisine;"
sqlite3 data/homecook.db "SELECT protein, COUNT(*) FROM recipes WHERE protein IS NOT NULL GROUP BY protein;"
```
