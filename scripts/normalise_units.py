#!/usr/bin/env python3
"""Normalise imperial units to metric in recipe ingredients and Fahrenheit to Celsius in steps."""

import re
import sqlite3
from fractions import Fraction
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "homecook.db"

# Imperial to metric conversion map
# Volume: cups/fl oz -> ml
# Weight: oz/lb -> g
UNIT_CONVERSIONS = {
    # Volume
    "cup": ("ml", 240),
    "cups": ("ml", 240),
    "fl oz": ("ml", 30),
    # Weight
    "ounce": ("g", 28),
    "ounces": ("g", 28),
    "oz": ("g", 28),
    "pound": ("g", 454),
    "pounds": ("g", 454),
    "lb": ("g", 454),
    "lbs": ("g", 454),
    # Standardise spelling
    "tablespoon": ("tbsp", 1),
    "tablespoons": ("tbsp", 1),
    "teaspoon": ("tsp", 1),
    "teaspoons": ("tsp", 1),
    "grams": ("g", 1),
    "liter": ("l", 1),
}

# Units that are fine as-is (no conversion needed)
KEEP_UNITS = {
    "g", "kg", "ml", "l", "tsp", "tbsp",
    "cloves", "clove", "bunch", "bunches", "sprigs", "sprig",
    "large", "medium", "small", "slices", "slice",
    "pinch", "pinches", "can", "head", "heads",
    "sticks", "stick", "stalks", "pieces", "package", "packages", "bag",
}


def parse_fraction(s: str) -> float | None:
    """Parse a quantity string that may contain fractions like '1/2', '1 1/2', '2-3'."""
    if not s:
        return None
    s = s.strip()

    # Handle ranges like "2-3" or "2 to 3" — use the first number
    range_match = re.match(r"^([\d/.\s]+)\s*[-–to]+\s*[\d/.]+", s)
    if range_match:
        s = range_match.group(1).strip()

    # Handle mixed fractions like "1 1/2"
    mixed_match = re.match(r"^(\d+)\s+(\d+/\d+)$", s)
    if mixed_match:
        whole = int(mixed_match.group(1))
        frac = float(Fraction(mixed_match.group(2)))
        return whole + frac

    # Handle simple fractions like "1/2"
    if "/" in s:
        try:
            return float(Fraction(s))
        except (ValueError, ZeroDivisionError):
            return None

    # Handle decimals and integers
    try:
        return float(s)
    except ValueError:
        return None


def convert_quantity(qty_str: str, unit: str) -> tuple[str, str]:
    """Convert a quantity+unit to metric. Returns (new_quantity, new_unit)."""
    if unit not in UNIT_CONVERSIONS:
        return (qty_str, unit)

    new_unit, factor = UNIT_CONVERSIONS[unit]

    if factor == 1:
        # Just a unit rename (tablespoon -> tbsp), no math needed
        return (qty_str, new_unit)

    value = parse_fraction(qty_str)
    if value is None:
        # Can't parse quantity — just rename the unit
        return (qty_str, new_unit)

    converted = value * factor

    # Smart rounding
    if converted >= 100:
        converted = round(converted / 5) * 5  # Round to nearest 5
    elif converted >= 10:
        converted = round(converted)
    else:
        converted = round(converted, 1)

    # Format nicely
    if converted == int(converted):
        new_qty = str(int(converted))
    else:
        new_qty = str(converted)

    return (new_qty, new_unit)


def fahrenheit_to_celsius(f: float) -> int:
    """Convert Fahrenheit to Celsius, rounded to nearest 5."""
    c = (f - 32) * 5 / 9
    return round(c / 5) * 5


def convert_step_temperatures(instruction: str) -> str:
    """Replace Fahrenheit temperatures with Celsius in step text."""
    # Pattern: 350°F, 350 °F, 350 degrees F, 350°F
    def replace_f(match):
        f_temp = float(match.group(1))
        c_temp = fahrenheit_to_celsius(f_temp)
        return f"{c_temp}°C"

    # Match various Fahrenheit patterns
    # "350°F" or "350 °F"
    result = re.sub(r"(\d+)\s*°\s*F\b", replace_f, instruction)
    # "350 degrees F" or "350 degrees Fahrenheit"
    result = re.sub(r"(\d+)\s*degrees?\s+F(?:ahrenheit)?\b", replace_f, result)

    return result


def convert_step_inches(instruction: str) -> str:
    """Replace inch measurements with cm in step text."""
    def replace_inch(match):
        inches = float(match.group(1))
        cm = round(inches * 2.54, 1)
        if cm == int(cm):
            cm = int(cm)
        return f"{cm}cm"

    # "2 inch" or "2-inch" or '2"'
    result = re.sub(r"(\d+(?:\.\d+)?)\s*[-]?\s*inch(?:es)?\b", replace_inch, instruction)
    return result


def normalise_units():
    """Run unit normalisation on all ingredients and steps."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # --- Normalise ingredient units ---
    ingredients = cur.execute(
        "SELECT id, quantity, unit FROM recipe_ingredients WHERE unit IS NOT NULL"
    ).fetchall()

    converted_count = 0
    flagged = []

    for ing_id, qty, unit in ingredients:
        if unit in KEEP_UNITS:
            continue

        if unit in UNIT_CONVERSIONS:
            new_qty, new_unit = convert_quantity(qty, unit)
            cur.execute(
                "UPDATE recipe_ingredients SET quantity = ?, unit = ? WHERE id = ?",
                (new_qty, new_unit, ing_id),
            )
            converted_count += 1
        else:
            flagged.append((ing_id, qty, unit))

    # --- Convert Fahrenheit in steps ---
    steps = cur.execute(
        "SELECT id, instruction FROM recipe_steps"
    ).fetchall()

    steps_converted = 0
    for step_id, instruction in steps:
        new_instruction = convert_step_temperatures(instruction)
        new_instruction = convert_step_inches(new_instruction)
        if new_instruction != instruction:
            cur.execute(
                "UPDATE recipe_steps SET instruction = ? WHERE id = ?",
                (new_instruction, step_id),
            )
            steps_converted += 1

    conn.commit()
    conn.close()

    # Print summary
    print(f"Unit normalisation complete!")
    print(f"\nIngredients:")
    print(f"  Converted: {converted_count}")
    print(f"  Flagged (unknown unit): {len(flagged)}")
    if flagged:
        for ing_id, qty, unit in flagged[:10]:
            print(f"    id={ing_id}: {qty} {unit}")

    print(f"\nRecipe steps:")
    print(f"  Steps with temperature/inch conversions: {steps_converted}")

    # Show unit distribution after conversion
    print(f"\nUnit distribution after normalisation:")
    conn2 = sqlite3.connect(DB_PATH)
    for row in conn2.execute(
        "SELECT unit, COUNT(*) FROM recipe_ingredients WHERE unit IS NOT NULL GROUP BY unit ORDER BY COUNT(*) DESC"
    ).fetchall():
        print(f"  {row[0]}: {row[1]}")
    conn2.close()


if __name__ == "__main__":
    normalise_units()
