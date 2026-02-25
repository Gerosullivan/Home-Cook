# Cook Mode

Guide Ger through tonight's dinner, step by step.

## Steps

1. **Check today's plan**: Run `sqlite3 data/homecook.db "SELECT mp.recipe_id, mp.description, mp.servings, r.name FROM meal_plan mp LEFT JOIN recipes r ON r.id = mp.recipe_id WHERE mp.date = date('now') AND mp.meal_type = 'dinner';"` to find tonight's meal.

2. **If no plan exists**: Ask Ger what he's cooking. Help him pick a recipe by searching: `sqlite3 data/homecook.db "SELECT id, name, cuisine, protein, cook_time_mins FROM recipes WHERE name LIKE '%keyword%';"` or suggest something based on what's in the fridge.

3. **If it's takeaway or eating out**: Confirm and log it. No cooking guidance needed.

4. **Load the full recipe**: Once a recipe is identified (by ID), fetch everything:
   - Recipe details: `sqlite3 data/homecook.db "SELECT name, servings, cook_time_mins, prep_time_mins, notes, cuisine, protein FROM recipes WHERE id = ?;"`
   - Ingredients: `sqlite3 data/homecook.db "SELECT raw_ingredient FROM recipe_ingredients WHERE recipe_id = ? ORDER BY id;"`
   - Steps: `sqlite3 data/homecook.db "SELECT step_number, instruction FROM recipe_steps WHERE recipe_id = ? ORDER BY step_number;"`
   - Notes from previous cooks: `sqlite3 data/homecook.db "SELECT note, created_at FROM recipe_notes WHERE recipe_id = ? ORDER BY created_at DESC;"`

5. **Adjust portions**: Default is 5 servings (whole family). Ask if everyone's eating tonight. Scale ingredient quantities proportionally if different from the recipe's base servings.

6. **Present the cook plan**:
   - Show the full ingredient list (metric units, scaled to tonight's portions)
   - Identify the longest task (oven preheat, slow cook, marination) and start it first
   - Present steps in optimised order — parallelise where possible (e.g. "While the oven preheats, prep the veg")
   - Show estimated time for each step where applicable
   - All temperatures in Celsius, all weights in grams, all volumes in ml

7. **Kid-friendly adjustments**: If spice_level > 1 or the recipe has hot elements, suggest:
   - Reducing chilli/spice
   - Serving sauce on the side
   - Setting aside a milder portion before adding heat

8. **Guide through the cook**: Present each step clearly. Wait for Ger to confirm before moving on, or let him work through at his own pace. Be responsive to questions about technique, timing, or substitutions.

## Format

Use clear numbered steps. Keep text concise — Ger is cooking while reading the terminal. Bold key actions and timing.
