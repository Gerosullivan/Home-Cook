# Generate Tonight's Recipe Card

Scheduled task prompt for the Claude app. Runs daily to produce `tonights-meal.html`.

---

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
