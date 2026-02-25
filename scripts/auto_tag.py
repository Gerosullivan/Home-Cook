#!/usr/bin/env python3
"""Auto-tag recipes with cuisine, protein, spice level, kid-friendly, and meal type."""

import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "homecook.db"

# --- Cuisine detection ---

CUISINE_KEYWORDS = {
    "italian": [
        "pasta", "pesto", "risotto", "carbonara", "parmigiana", "gnocchi",
        "bolognese", "lasagne", "lasagna", "tagliatelle", "tagliolini",
        "spaghetti", "penne", "fusilli", "rigatoni", "linguine", "bucatini",
        "fettuccine", "pappardelle", "orzo", "orecchiette", "ravioli",
        "tortellini", "prosciutto", "bruschetta", "ciabatta", "focaccia",
        "arrabbiata", "puttanesca", "amatriciana", "cacio e pepe",
        "aglio e olio", "al pomodoro", "marinara", "pomodoro",
        "pancetta", "nduja", "mascarpone", "tiramisu", "panna cotta",
        "osso buco", "saltimbocca", "piccata", "milanese",
        "antipasti", "ai carciofi",
    ],
    "asian": [
        "stir-fry", "stir fry", "stirfry", "noodles", "wok",
        "soy sauce", "sesame", "hoisin", "oyster sauce",
        "bok choy", "pak choi", "edamame", "spring roll",
    ],
    "indian": [
        "curry", "tikka", "biryani", "masala", "korma", "rogan josh",
        "tandoori", "dal", "dhal", "daal", "naan", "chapati",
        "samosa", "chutney", "paneer", "vindaloo", "madras",
        "jalfrezi", "bhaji", "pakora", "raita", "garam masala",
        "turmeric rice", "basmati",
    ],
    "mexican": [
        "tacos", "taco", "burrito", "enchilada", "quesadilla",
        "salsa", "chipotle", "carnitas", "guacamole", "tortilla",
        "fajita", "nachos", "refried beans", "jalapeño",
        "churro", "mole",
    ],
    "irish": [
        "colcannon", "guinness", "stout", "irish stew",
        "shepherd's pie", "shepherds pie", "soda bread", "boxty",
        "coddle", "champ",
    ],
    "british": [
        "roast dinner", "fish and chips", "fish & chips",
        "bangers", "toad in the hole", "bubble and squeak",
        "cottage pie", "ploughman", "yorkshire pudding",
        "full english", "sunday roast", "british",
    ],
    "mediterranean": [
        "feta", "halloumi", "couscous", "tabbouleh", "hummus",
        "mediterranean", "pita", "pitta", "tzatziki", "za'atar",
        "zaatar", "sumac", "pomegranate molasses", "tahini",
        "greek", "shakshuka",
    ],
    "french": [
        "en croûte", "en croute", "papillote", "niçoise", "nicoise",
        "ratatouille", "cassoulet", "bouillabaisse", "bourguignon",
        "beurre blanc", "béarnaise", "hollandaise", "gratin",
        "dauphinoise", "quiche", "crêpe", "croque",
        "provençal", "provencal", "boursin",
    ],
    "spanish": [
        "paella", "chorizo", "tapas", "patatas bravas",
        "gazpacho", "calasparra", "pimiento",
        "spanish", "espanol",
    ],
    "korean": [
        "bulgogi", "kimchi", "gochujang", "bibimbap",
        "korean", "tteokbokki", "japchae",
    ],
    "thai": [
        "pad thai", "laksa", "thai curry", "thai basil",
        "thai-style", "thai style", "green curry", "red curry",
        "panang", "massaman", "tom yum", "tom kha",
        "kaffir lime", "lemongrass", "fish sauce",
        "coconut curry",
    ],
    "japanese": [
        "ramen", "tsukemen", "miso", "teriyaki", "katsu",
        "tempura", "sushi", "udon", "soba", "yakitori",
        "japanese", "tonkotsu", "gyoza", "edamame",
    ],
    "chinese": [
        "kung pao", "sweet and sour", "chow mein", "fried rice",
        "dim sum", "wonton", "dumpling", "szechuan", "sichuan",
        "char siu", "mapo tofu", "chinese",
    ],
    "middle_eastern": [
        "shawarma", "falafel", "kebab", "kofta", "keftedes",
        "baba ghanoush", "labneh", "fattoush",
    ],
    "portuguese": [
        "bacalhau", "piri piri", "peri peri", "portuguese",
        "pastéis", "natas",
    ],
    "caribbean": [
        "jerk", "plantain", "scotch bonnet", "caribbean",
        "jamaican", "reggae reggae",
    ],
}

# --- Protein detection ---

# Ingredient name patterns that are NOT actual protein (stocks, sauces, etc.)
PROTEIN_EXCLUDES = re.compile(
    r"stock|broth|consommé|consomme|bouillon|sauce|gravy|"
    r"flavour|flavor|season|powder|cube|paste|extract|"
    r"fat|dripping|lard|suet|gelatin",
    re.IGNORECASE,
)

PROTEIN_MAP = {
    "chicken": [r"\bchicken\b"],
    "beef": [r"\bbeef\b", r"\bsteak\b", r"\bsirloin\b", r"\bribeye\b",
             r"\bfillet steak\b", r"\bbraising\b", r"\bstewing\b",
             r"\bbrisket\b", r"\bmince\b(?!.*lamb)", r"\bground beef\b",
             r"\bbeef patties\b", r"\bburger\b"],
    "lamb": [r"\blamb\b", r"\bmutton\b"],
    "pork": [r"\bpork\b", r"\bbacon\b", r"\bpancetta\b", r"\bham\b",
             r"\bprosciutto\b", r"\bchorizo\b", r"\bsausage\b",
             r"\bserrano\b", r"\bguanciale\b", r"\blardons?\b"],
    "turkey": [r"\bturkey\b"],
    "duck": [r"\bduck\b"],
    "salmon": [r"\bsalmon\b"],
    "tuna": [r"\btuna\b"],
    "cod": [r"\bcod\b", r"\bhaddock\b", r"\bpollack\b", r"\bpollock\b"],
    "sea_bass": [r"\bsea bass\b", r"\bbass\b"],
    "trout": [r"\btrout\b"],
    "halibut": [r"\bhalibut\b"],
    "monkfish": [r"\bmonkfish\b"],
    "mackerel": [r"\bmackerel\b"],
    "fish": [r"\bfish\b", r"\bwhite fish\b"],
    "prawns": [r"\bprawns?\b", r"\bshrimp\b", r"\bscampi\b", r"\blangoustine\b"],
    "shellfish": [r"\bclams?\b", r"\bmussels?\b", r"\bscallops?\b", r"\bcrab\b",
                  r"\blobster\b", r"\bsquid\b", r"\bcalamari\b", r"\bshellfish\b",
                  r"\boctopus\b"],
    "tofu": [r"\btofu\b"],
}

# --- Spice detection ---

SPICE_3_HOT = [
    "scotch bonnet", "habanero", "extra hot", "birds eye chilli",
    "bird's eye chilli", "ghost pepper", "carolina reaper",
]

SPICE_2_MEDIUM = [
    "chilli", "chili", "jalapeño", "jalapeno", "cayenne",
    "nduja", "sriracha", "harissa", "jerk", "chipotle",
    "hot sauce", "red pepper flakes", "chili flakes",
    "gochujang", "sambal", "tabasco",
]

SPICE_1_MILD = [
    "paprika", "mild curry", "cumin", "ginger", "coriander seed",
    "curry powder", "turmeric", "five spice", "allspice",
    "nutmeg", "cinnamon",
]


def detect_cuisine(name: str, ingredients: list[str], steps: list[str]) -> str | None:
    """Detect cuisine from recipe name and ingredients."""
    text = f"{name} {' '.join(ingredients)} {' '.join(steps)}".lower()
    name_lower = name.lower()

    scores = {}
    for cuisine, keywords in CUISINE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in name_lower:
                score += 3  # Name match is strong signal
            elif kw in text:
                score += 1
        if score > 0:
            scores[cuisine] = score

    if not scores:
        return None

    # Return the highest scoring cuisine
    best = max(scores, key=scores.get)
    return best


def detect_protein(name: str, ingredients: list[str]) -> str | None:
    """Detect primary protein from recipe name and ingredient names."""
    name_lower = name.lower()

    # Filter out stock/broth/sauce ingredients
    real_ingredients = [
        ing for ing in ingredients
        if not PROTEIN_EXCLUDES.search(ing)
    ]
    ing_text = " ".join(real_ingredients).lower()

    found = []
    for protein, patterns in PROTEIN_MAP.items():
        for pat in patterns:
            # Check recipe name first (strong signal)
            if re.search(pat, name_lower):
                found.append((protein, 3))
                break
            # Check ingredients
            elif re.search(pat, ing_text):
                found.append((protein, 1))
                break

    if not found:
        return "vegetarian"

    # Return highest scored protein
    found.sort(key=lambda x: x[1], reverse=True)
    return found[0][0]


def detect_spice_level(name: str, ingredients: list[str], steps: list[str]) -> int:
    """Detect spice level 0-3."""
    text = f"{name} {' '.join(ingredients)} {' '.join(steps)}".lower()

    for kw in SPICE_3_HOT:
        if kw in text:
            return 3

    for kw in SPICE_2_MEDIUM:
        if kw in text:
            return 2

    for kw in SPICE_1_MILD:
        if kw in text:
            return 1

    return 0


def detect_meal_type(name: str, ingredients: list[str]) -> str:
    """Classify meal type."""
    name_lower = name.lower()
    text = f"{name} {' '.join(ingredients)}".lower()

    # Smoothie/drink
    if any(kw in name_lower for kw in ["smoothie", "martini", "cocktail", "drink", "lemonade"]):
        return "drink"

    # Dessert
    if any(kw in name_lower for kw in ["crumble", "ice cream", "cake", "brownie",
                                         "cookie", "pudding", "tart", "pie" , "tiramisu",
                                         "panna cotta", "mousse", "cheesecake"]):
        # "pie" can be savoury — check for meat
        if "pie" in name_lower and any(kw in text for kw in ["chicken", "beef", "lamb",
                                                               "shepherd", "cottage", "steak"]):
            return "dinner"
        return "dessert"

    # Breakfast
    if any(kw in name_lower for kw in ["breakfast", "omelette", "omelet", "pancake",
                                         "granola", "porridge", "eggs benedict",
                                         "french toast", "waffle"]):
        return "breakfast"

    # Side
    if any(kw in name_lower for kw in ["coleslaw", "fries", "roasted veg",
                                         "mash", "side salad", "green beans",
                                         "roasted potatoes", "rice simple"]):
        return "side"

    # Snack
    if any(kw in name_lower for kw in ["guacamole", "hummus", "dip", "snack",
                                         "bruschetta", "crostini"]):
        return "snack"

    # Lunch/sandwich
    if any(kw in name_lower for kw in ["sandwich", "wrap", "panini", "salad"]):
        return "lunch"

    # Soup
    if "soup" in name_lower:
        return "dinner"

    return "dinner"


def is_kid_friendly(spice_level: int, name: str, ingredients: list[str]) -> bool:
    """Determine if a recipe is kid-friendly."""
    if spice_level > 1:
        return False

    # Check for complex/unusual ingredients kids might not like
    name_lower = name.lower()
    unfriendly = [
        "anchov", "olive tapenade", "blue cheese", "gorgonzola",
        "stilton", "liver", "offal", "tartare", "raw fish",
        "octopus", "squid", "calamari", "oyster",
        "wasabi", "horseradish",
    ]
    text = f"{name} {' '.join(ingredients)}".lower()
    for kw in unfriendly:
        if kw in text:
            return False

    return True


def auto_tag():
    """Run auto-tagging on all recipes."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    recipes = cur.execute("SELECT id, name FROM recipes").fetchall()

    stats = {
        "cuisine": {},
        "protein": {},
        "spice_level": {0: 0, 1: 0, 2: 0, 3: 0},
        "kid_friendly": {True: 0, False: 0},
        "meal_type": {},
    }

    for recipe_id, name in recipes:
        # Get ingredients
        ingredients = [
            row[0] for row in
            cur.execute(
                "SELECT COALESCE(name, raw_ingredient, '') FROM recipe_ingredients WHERE recipe_id = ?",
                (recipe_id,),
            ).fetchall()
        ]

        # Get steps
        steps = [
            row[0] for row in
            cur.execute(
                "SELECT instruction FROM recipe_steps WHERE recipe_id = ? ORDER BY step_number",
                (recipe_id,),
            ).fetchall()
        ]

        cuisine = detect_cuisine(name, ingredients, steps)
        protein = detect_protein(name, ingredients)
        spice_level = detect_spice_level(name, ingredients, steps)
        kid_friendly = is_kid_friendly(spice_level, name, ingredients)
        meal_type = detect_meal_type(name, ingredients)

        cur.execute(
            """UPDATE recipes
               SET cuisine = ?, protein = ?, spice_level = ?, kid_friendly = ?, meal_type = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (cuisine, protein, spice_level, kid_friendly, meal_type, recipe_id),
        )

        # Track stats
        stats["cuisine"][cuisine] = stats["cuisine"].get(cuisine, 0) + 1
        stats["protein"][protein] = stats["protein"].get(protein, 0) + 1
        stats["spice_level"][spice_level] += 1
        stats["kid_friendly"][kid_friendly] += 1
        stats["meal_type"][meal_type] = stats["meal_type"].get(meal_type, 0) + 1

    conn.commit()
    conn.close()

    # Print summary
    print(f"Auto-tagged {len(recipes)} recipes\n")

    print("Cuisine breakdown:")
    for cuisine, count in sorted(stats["cuisine"].items(), key=lambda x: -x[1]):
        label = cuisine if cuisine else "(undetected)"
        print(f"  {label}: {count}")

    print(f"\nProtein breakdown:")
    for protein, count in sorted(stats["protein"].items(), key=lambda x: -x[1]):
        print(f"  {protein}: {count}")

    print(f"\nSpice level:")
    for level, count in sorted(stats["spice_level"].items()):
        labels = {0: "none", 1: "mild", 2: "medium", 3: "hot"}
        print(f"  {level} ({labels[level]}): {count}")

    print(f"\nKid-friendly: {stats['kid_friendly'][True]} yes, {stats['kid_friendly'][False]} no")

    print(f"\nMeal type:")
    for mtype, count in sorted(stats["meal_type"].items(), key=lambda x: -x[1]):
        print(f"  {mtype}: {count}")


if __name__ == "__main__":
    auto_tag()
