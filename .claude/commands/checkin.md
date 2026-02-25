# Check-in - Post-Meal Debrief

Reconcile what was planned vs what actually happened. Log notes and modifications.

## Steps

1. **Check today's plan**: Run `sqlite3 data/homecook.db "SELECT mp.id, mp.recipe_id, mp.description, r.name FROM meal_plan mp LEFT JOIN recipes r ON r.id = mp.recipe_id WHERE mp.date = date('now') AND mp.meal_type = 'dinner';"` to see what was planned.

2. **Ask what happened**:
   - Did you cook what was planned?
   - If yes: any modifications? (ingredient swaps, technique changes, portion adjustments)
   - If no: what happened instead? (different recipe, takeaway, cancelled, ate out, at parents')

3. **Log the outcome** to `meal_log`:
   ```sql
   INSERT INTO meal_log (date, meal_type, planned_recipe_id, actual_recipe_id, outcome, modifications, notes)
   VALUES (date('now'), 'dinner', ?, ?, ?, ?, ?);
   ```
   - `outcome`: one of 'as_planned', 'modified', 'swapped', 'takeaway', 'cancelled', 'ate_out'
   - `modifications`: free text describing what changed
   - `notes`: general notes about the meal

4. **If the recipe was modified**, ask:
   - Should I **update the original recipe** with these changes?
   - Or **fork it as a new variation**? (creates a new recipe entry with a modified name)

5. **Collect notes** — prompt for:
   - How did the kids react? ("kids loved it", "too spicy for the little ones", "only the eldest ate it")
   - Taste notes? ("needs more garlic", "too salty", "perfect as-is")
   - Tips for next time? ("double the sauce", "marinate longer", "use fresh not dried herbs")

6. **Save notes** to `recipe_notes`:
   ```sql
   INSERT INTO recipe_notes (recipe_id, note) VALUES (?, ?);
   ```

7. **Inventory update**: Ask if Ger wants to update inventory based on what was used. If yes, help subtract used ingredients from the `inventory` table.

## Tone

Keep it quick and conversational. This is a 2-minute debrief, not an interrogation.
