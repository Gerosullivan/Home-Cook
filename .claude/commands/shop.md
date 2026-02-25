# Shopping List Generator

Generate a categorised shopping list for the upcoming week's meals, minus what's already in stock.

## Steps

1. **Load next week's meal plan**: Query meals from the upcoming Monday to Sunday:
   ```sql
   SELECT mp.date, mp.meal_type, mp.description, r.id, r.name, mp.servings
   FROM meal_plan mp
   LEFT JOIN recipes r ON r.id = mp.recipe_id
   WHERE mp.date BETWEEN date('now', 'weekday 1') AND date('now', 'weekday 1', '+6 days')
   ORDER BY mp.date;
   ```
   If no upcoming plan, check the current week. Show Ger what's planned and confirm.

2. **Aggregate ingredients**: For each planned recipe, get scaled ingredients:
   ```sql
   SELECT ri.name, ri.quantity, ri.unit, ri.raw_ingredient, r.servings as recipe_servings, mp.servings as planned_servings
   FROM recipe_ingredients ri
   JOIN recipes r ON r.id = ri.recipe_id
   JOIN meal_plan mp ON mp.recipe_id = r.id
   WHERE mp.date BETWEEN ? AND ?;
   ```
   Scale quantities based on planned servings vs recipe's base servings.

3. **Check inventory**: Subtract what's already in stock:
   ```sql
   SELECT name, quantity, unit, location FROM inventory;
   ```
   Match ingredient names (fuzzy — "chicken breast" should match "chicken breasts").

4. **Categorise items**: Group the shopping list by Tesco section:
   - **Produce**: fruit, veg, herbs, salad
   - **Meat & Fish**: chicken, beef, lamb, pork, fish, seafood, mince
   - **Dairy**: milk, cheese, cream, yoghurt, butter, eggs
   - **Bakery**: bread, rolls, brioche, wraps, naan
   - **Pantry**: tinned goods, pasta, rice, oils, sauces, spices, condiments
   - **Frozen**: frozen veg, frozen chips, ice cream

5. **Present the list**: Format as a clear checklist grouped by category. Include quantities and units.

6. **Save to shopping_list table**:
   ```sql
   -- Clear previous list
   DELETE FROM shopping_list WHERE checked = 0;
   INSERT INTO shopping_list (item_name, quantity, unit, category, recipe_id) VALUES (?, ?, ?, ?, ?);
   ```

7. **During the shop**: Ger can come back and mark items as checked:
   ```sql
   UPDATE shopping_list SET checked = 1 WHERE id = ?;
   ```

## Notes

- Always include Maura's lunch ingredients (brioche, ham, cheese, rocket) unless told otherwise
- Ask if there are any extras needed (household items, snacks, etc.)
- Friday afternoon is the usual shop day
