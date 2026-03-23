# Generate Tonight's Recipe Card

Scheduled task prompt for the Claude app. Runs daily to produce `tonights-meal.html`.

---

## Step 0: Yesterday's Meal Reconciliation

Before generating today's card, reconcile yesterday's meal to keep inventory accurate.

1. Check if yesterday had a **planned** meal:
   ```sql
   SELECT recipe_id FROM meal_plan WHERE date = date('now', '-1 day') AND meal_type = 'dinner';
   ```

2. **No meal plan** → skip entirely. AI-generated suggestions don't trigger inventory changes. Only planned meals auto-deduct.

3. **Meal plan exists** → check if Ger already handled it via chat:
   ```sql
   SELECT id FROM meal_log WHERE date = date('now', '-1 day') AND meal_type = 'dinner';
   ```

4. **Log exists** → already reconciled via Despatch chat → skip.

5. **No log** → assume cooked as planned. Process each recipe ingredient:
   ```sql
   SELECT name, quantity, unit FROM recipe_ingredients WHERE recipe_id = ?;
   ```

   For each ingredient:

   a. **Look up mapping**: `SELECT inventory_name FROM ingredient_map WHERE recipe_name = ?`
      - Match found with `inventory_name` → proceed to deduction
      - Match found with `NULL` → skip (staple or not tracked)
      - No match → resolve it: find the best match in inventory (fuzzy name match), save to `ingredient_map`. If no plausible match, set `inventory_name = NULL`

   b. **Check deduction type**: `SELECT deduction_type, quantity, unit FROM inventory WHERE name = ?`
      - `none` → skip
      - `measured` → convert recipe quantity to inventory unit if needed, subtract from inventory. Floor at 0.
      - `container` + recipe uses full/most of container (whole bag, whole can) → deduct 1 container
      - `container` + recipe uses small amount (tsp, tbsp, splash) → don't deduct, log as `check_stock`

   c. **No inventory match at all** → log as `not_in_inventory`, auto-add to `shopping_list`:
      ```sql
      INSERT INTO shopping_list (item_name, quantity, unit, recipe_id, created_date)
      VALUES (?, ?, ?, ?, date('now', '-1 day'));
      ```

   d. **Log every action** to `inventory_log`:
      ```sql
      INSERT INTO inventory_log (inventory_name, change_type, quantity_change, unit, source, date)
      VALUES (?, ?, ?, ?, ?, date('now', '-1 day'));
      ```
      - `change_type`: `meal_deduction`, `check_stock`, or `not_in_inventory`

   e. **Record the meal**:
      ```sql
      INSERT INTO meal_log (date, meal_type, planned_recipe_id, actual_recipe_id, outcome)
      VALUES (date('now', '-1 day'), 'dinner', ?, ?, 'as_planned');
      ```

## Data Source

Check the **Home-Cook** Google Calendar (ID: `23a1ee918bf80873ea6fd3f845c846083e12d1d9d1b2fe6471f892f2f53d0c55@group.calendar.google.com`) for today's meal plan event.

Pull the matching recipe from the SQLite database at `data/homecook.db` (use python3 with sqlite3 module — copy the DB locally first to avoid disk I/O errors on the mounted file).

If there's no meal plan event on the Home-Cook calendar for tonight, fall back to `draft_meal_plan.json` to determine which recipe is planned. If neither has a plan, generate a suggestion based on current inventory.

## Recipe Card Output

### HTML Cache (check first)

Before generating anything, check if a cached HTML card exists for this recipe:

1. Look for `data/recipe-cards/{recipe_id}.html`
2. **If it exists** → read it, replace the date placeholder `{{DATE}}` with today's formatted date (e.g. "Thursday 19 March 2026"), write to `tonights-meal.html`. **Done — no further work needed.**
3. **If it doesn't exist** → generate the full card (see below), then save a cache copy:
   - Replace today's date in the generated HTML with the literal string `{{DATE}}`
   - Write that version to `data/recipe-cards/{recipe_id}.html`
   - Write the version with the real date to `tonights-meal.html`

### Full Generation (only when no cached HTML)

Create a recipe card using `tonights-meal.html` as a template, matching the existing design: colour scheme appropriate to the cuisine, ingredient tooltips, timing plan table, kid-friendly callouts where relevant, and all measurements in metric.

## Prep Ahead Analysis

Ger leaves at 5:00 PM for a 30-minute school pickup. The goal is to minimise active cooking after 5:30 PM. Build a "Prep Ahead" section between the Ingredients and Method sections.

### Cache Lookup (check before analysing)

Before running LLM analysis, check if this recipe already has cached prep data:

```sql
SELECT prep_ahead_status, prep_ahead_total_mins FROM recipes WHERE id = ?;
```

- **`NULL`** → Not yet analysed. Run the full classification below, then save results:
  ```sql
  -- Save each classified step
  INSERT INTO recipe_prep_ahead (recipe_id, sort_order, description, classification, tag, is_passive, safety_note)
  VALUES (?, ?, ?, ?, ?, ?, ?);

  -- Mark recipe as analysed
  UPDATE recipes SET prep_ahead_status = 'ready', prep_ahead_total_mins = ? WHERE id = ?;
  -- Or if skipping: prep_ahead_status = 'skip_quick' or 'skip_no_steps'
  ```

- **`'ready'`** → Use cached data. Read steps and generate HTML directly:
  ```sql
  SELECT sort_order, description, classification, tag, is_passive, safety_note
  FROM recipe_prep_ahead WHERE recipe_id = ? ORDER BY sort_order;
  ```

- **`'skip_quick'`** → Quick recipe. Show callout: "Quick one tonight — start to finish after pickup"
- **`'skip_no_steps'`** → No method steps. Show callout: "No method steps found — check the recipe"

### Step Classification (only when cache is empty)

Assign every sub-task from the recipe to one of these categories:

| Tag | Class | Rule | Example |
|-----|-------|------|---------|
| `before` | `PURE_PREP` | Cold prep, no heat needed | Chop veg, grate cheese, measure spices |
| `before` | `SAFE_TO_START` | Output can safely sit for 30 min | Brown mince, par-boil potatoes, room-temp sauces |
| `during` | `PASSIVE_DURING` | Benefits from sitting or runs unattended | Marinate meat, dough resting, oven braise already started |
| *(none)* | `COOK_AFTER` | Must produce hot food for the table | Final fry, assemble, plate, reheat |

### Extraction Rule

Split bundled recipe steps into their component tasks. For example, "Dice onion and fry" becomes:
- Dicing → `PURE_PREP`
- Frying → `COOK_AFTER`

### Timing

- Estimate total prep time, then work backwards from 5:00 PM for the Prep Phase start time
- Cook Phase starts at 5:30 PM and runs forward
- Use clock times in the timing table (e.g. "4:40 PM", "5:35 PM"), not relative offsets (e.g. "0:00")
- Add `.timing-phase-row.prep` separator before prep rows and `.timing-phase-row.cook` separator before cook rows

### Edge Cases

- **Quick recipe (<20 min total)**: Skip the Prep Ahead section entirely. Add a callout instead: "Quick one tonight — start to finish after pickup"
- **No steps in DB**: Skip section, add callout: "No method steps found — check the recipe"
- **Long braise/roast (>45 min cook)**: Flag "Start oven before you leave" as a `before` step; the oven time becomes `during`
- **Dough recipes**: Making dough = `SAFE_TO_START`, resting = `PASSIVE_DURING`

### Food Safety Notes

Add as callouts where relevant:
- Wash boards/knives after prepping raw meat
- If marinating meat and kitchen is warm, put it in the fridge while away
- Squeeze lemon on prepped avocado to prevent browning

### HTML Generation

- Use `.prep-ahead` container with `.prep-ahead-header` (clock icon, "Prep Ahead" title, `.prep-time-pill` with estimated time)
- Add `.prep-context` line: "Before you leave for pickup at 5:00 PM"
- Use `.prep-step` rows with `.prep-step-check` checkboxes (not numbered circles — prep is a checklist)
- Add `data-prep="0"`, `data-prep="1"`, etc. attributes on checkboxes for localStorage persistence
- Use `.prep-step-tag.before` (green) or `.prep-step-tag.during` (amber) badges on each step
- Include `.prep-passive` block with `.prep-passive-header` only if there are `PASSIVE_DURING` tasks
- If no prep tasks apply, omit the entire `.prep-ahead` div
