# Meal Planning

Set up or adjust upcoming meals for the week.

## Steps

1. **Show current state**: Query the upcoming week's plan:
   ```sql
   SELECT mp.date, strftime('%w', mp.date) as day_num, mp.meal_type, mp.description, r.name, mp.rotation_week, mp.servings
   FROM meal_plan mp
   LEFT JOIN recipes r ON r.id = mp.recipe_id
   WHERE mp.date >= date('now')
   ORDER BY mp.date LIMIT 14;
   ```
   Format as a readable week view (Mon-Sun).

2. **Identify gaps**: Check which days need meals assigned. The default pattern is:
   - Mon-Thu: Cook dinner
   - Fri: Takeaway (flexible swap with Thu)
   - Sat: Takeaway
   - Sun: Flexible

3. **Suggest or assign recipes**: For days that need a recipe:
   - If a 3-week rotation is configured, suggest from the current rotation week
   - Otherwise, let Ger pick. Help with search:
     ```sql
     SELECT id, name, cuisine, protein, kid_friendly, cook_time_mins
     FROM recipes
     WHERE name LIKE '%keyword%'
        OR cuisine = ?
        OR protein = ?
     ORDER BY name;
     ```
   - Suggest variety: avoid repeating the same protein or cuisine in the same week
   - Prefer kid-friendly meals (kid_friendly = 1) for weeknights

4. **Handle adjustments**:
   - **Swap days**: Move a cook day to a different day (e.g. swap Thu/Fri)
   - **Cancel a cook**: Mark a day as takeaway, eating out, or at parents'
   - **Change a recipe**: Replace one recipe with another

5. **Save the plan**:
   ```sql
   INSERT OR REPLACE INTO meal_plan (date, meal_type, recipe_id, description, rotation_week, servings)
   VALUES (?, 'dinner', ?, ?, ?, 5);
   ```
   For non-cooking days:
   ```sql
   INSERT OR REPLACE INTO meal_plan (date, meal_type, description, servings)
   VALUES (?, 'dinner', 'takeaway', 5);
   ```

6. **Flag missing ingredients**: For each planned recipe, check if key ingredients are in inventory and warn about anything that might need to go on the shopping list.

## Tips

- Show recipe cook times to help balance the week (don't stack all long cooks together)
- Consider what's in the freezer that could be defrosted
- Sunday is flexible — sometimes Ger does a roast, sometimes they eat at parents'
