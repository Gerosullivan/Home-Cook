#!/usr/bin/env python3
"""Import recipes from AnyList JSON export into the Home Cook SQLite database."""

import json
import re
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "homecook.db"
JSON_PATH = Path(__file__).parent.parent / "anylist.json"


def parse_servings(raw: str) -> int | None:
    """Extract the first integer from a servings string."""
    if not raw:
        return None
    # Find the first number in the string
    match = re.search(r"(\d+)", raw.strip())
    if match:
        return int(match.group(1))
    return None


def seconds_to_minutes(seconds) -> int | None:
    """Convert time in seconds to minutes."""
    if seconds is None:
        return None
    try:
        return int(seconds) // 60
    except (ValueError, TypeError):
        return None


def parse_quantity_unit(raw_qty: str) -> tuple[str, str | None]:
    """Split a quantity string like '1 cup' into (quantity, unit).

    Returns the original string and None if no unit is detected.
    """
    if not raw_qty:
        return (raw_qty, None)

    raw_qty = raw_qty.strip()

    # Common unit patterns (order matters - longer matches first)
    unit_patterns = [
        r"tablespoons?", r"teaspoons?", r"Tablespoons?", r"Teaspoons?",
        r"Tbsp\.?", r"tbsp\.?", r"Tsp\.?", r"tsp\.?",
        r"cups?", r"Cups?",
        r"ounces?", r"oz\.?",
        r"pounds?", r"lbs?\.?", r"lb\.?",
        r"grams?", r"g\b",
        r"kilograms?", r"kg\.?",
        r"liters?", r"litres?", r"l\b", r"L\b",
        r"milliliters?", r"millilitres?", r"ml\.?", r"mL\.?",
        r"cloves?", r"bunch(?:es)?", r"sprigs?", r"heads?",
        r"cans?", r"bags?", r"packages?", r"jars?",
        r"slices?", r"pieces?", r"stalks?", r"sticks?",
        r"pinch(?:es)?", r"dashes?", r"handfuls?",
        r"large", r"medium", r"small",
    ]

    combined = "|".join(unit_patterns)
    # Match: number part (fractions, decimals, ranges) then unit
    match = re.match(
        rf"^([\d\s/.\-–]+)\s+({combined})\b(.*)$", raw_qty, re.IGNORECASE
    )
    if match:
        qty = match.group(1).strip()
        unit = match.group(2).strip().lower().rstrip(".")
        return (qty, unit)

    # No unit found - return as-is
    return (raw_qty, None)


def import_recipes():
    """Main import function."""
    with open(JSON_PATH) as f:
        recipes = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    imported = 0
    skipped_dupes = []
    seen_names = {}

    for recipe in recipes:
        name = recipe["name"].strip()

        # Handle duplicates: skip if we've already imported this name
        if name in seen_names:
            skipped_dupes.append(name)
            continue
        seen_names[name] = True

        servings = parse_servings(recipe.get("servings"))
        cook_time = seconds_to_minutes(recipe.get("cookTime"))
        prep_time = seconds_to_minutes(recipe.get("prepTime"))
        rating = recipe.get("rating")
        if rating is not None:
            rating = float(rating)

        cur.execute(
            """INSERT INTO recipes (name, icon, servings, cook_time_mins, prep_time_mins,
               source_name, source_url, rating, notes, nutritional_info)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                name,
                recipe.get("icon"),
                servings,
                cook_time,
                prep_time,
                recipe.get("sourceName"),
                recipe.get("sourceUrl"),
                rating,
                recipe.get("note"),
                recipe.get("nutritionalInfo"),
            ),
        )
        recipe_id = cur.lastrowid

        # Import ingredients
        for ing in recipe.get("ingredients", []):
            raw_qty = ing.get("quantity", "")
            qty, unit = parse_quantity_unit(raw_qty)

            cur.execute(
                """INSERT INTO recipe_ingredients (recipe_id, name, quantity, unit, raw_ingredient, note)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    recipe_id,
                    ing.get("name"),
                    qty,
                    unit,
                    ing.get("rawIngredient"),
                    ing.get("note"),
                ),
            )

        # Import preparation steps
        for i, step in enumerate(recipe.get("preparationSteps", []), 1):
            cur.execute(
                """INSERT INTO recipe_steps (recipe_id, step_number, instruction)
                   VALUES (?, ?, ?)""",
                (recipe_id, i, step),
            )

        imported += 1

    conn.commit()

    # Print summary
    total_ingredients = cur.execute("SELECT COUNT(*) FROM recipe_ingredients").fetchone()[0]
    total_steps = cur.execute("SELECT COUNT(*) FROM recipe_steps").fetchone()[0]
    recipes_with_steps = cur.execute(
        "SELECT COUNT(DISTINCT recipe_id) FROM recipe_steps"
    ).fetchone()[0]
    recipes_with_ingredients = cur.execute(
        "SELECT COUNT(DISTINCT recipe_id) FROM recipe_ingredients"
    ).fetchone()[0]

    print(f"Import complete!")
    print(f"  Recipes imported: {imported}")
    print(f"  Duplicates skipped: {len(skipped_dupes)}")
    if skipped_dupes:
        print(f"    Skipped: {skipped_dupes}")
    print(f"  Total ingredients: {total_ingredients}")
    print(f"  Recipes with ingredients: {recipes_with_ingredients}")
    print(f"  Total steps: {total_steps}")
    print(f"  Recipes with steps: {recipes_with_steps}")

    conn.close()


if __name__ == "__main__":
    import_recipes()
