# Inventory Management

Manage kitchen stock — add after shopping, remove after cooking, check what's available.

## Modes

### After a shop (adding items)
Ask Ger what he bought. For each item, insert into inventory:
```sql
INSERT INTO inventory (name, quantity, unit, location, bought_date, expiry_date, notes)
VALUES (?, ?, ?, ?, date('now'), ?, ?);
```
- Location: fridge, freezer, pantry, spice_rack
- Estimate expiry dates based on item type if not specified (fresh meat ~3 days, veg ~5-7 days, dairy ~7 days, pantry items ~months)

### After cooking (removing items)
Based on the recipe that was cooked, subtract used ingredients:
```sql
UPDATE inventory SET quantity = quantity - ? WHERE name LIKE ? AND location = ?;
DELETE FROM inventory WHERE quantity <= 0;
```

### Check stock
Show current inventory by location:
```sql
SELECT name, quantity, unit, location, bought_date, expiry_date
FROM inventory
ORDER BY location, name;
```

### Running low
Flag items below a useful threshold:
```sql
SELECT name, quantity, unit, location FROM inventory
WHERE quantity <= 1 OR (expiry_date IS NOT NULL AND expiry_date <= date('now', '+3 days'))
ORDER BY expiry_date;
```

### Expiry warnings
Show items nearing or past expiry:
```sql
SELECT name, quantity, unit, location, expiry_date,
  CASE
    WHEN expiry_date < date('now') THEN 'EXPIRED'
    WHEN expiry_date <= date('now', '+1 day') THEN 'TODAY/TOMORROW'
    WHEN expiry_date <= date('now', '+3 days') THEN 'SOON'
  END as urgency
FROM inventory
WHERE expiry_date IS NOT NULL AND expiry_date <= date('now', '+3 days')
ORDER BY expiry_date;
```

## Notes

- Keep it quick — Ger will often just rattle off a list after shopping
- Group by location when displaying (Fridge, Freezer, Pantry, Spice Rack)
- Common staples that don't need tracking: salt, pepper, olive oil, water
- When in doubt about location, ask
