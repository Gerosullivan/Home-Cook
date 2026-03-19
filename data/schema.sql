-- Home Cook database schema

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    icon TEXT,
    servings INTEGER,
    cook_time_mins INTEGER,
    prep_time_mins INTEGER,
    source_name TEXT,
    source_url TEXT,
    rating REAL,
    notes TEXT,
    nutritional_info TEXT,
    cuisine TEXT,
    protein TEXT,
    meal_type TEXT,
    difficulty TEXT,
    kid_friendly BOOLEAN,
    spice_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    prep_ahead_total_mins INTEGER,
    prep_ahead_status TEXT
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name TEXT,
    quantity TEXT,
    unit TEXT,
    raw_ingredient TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS recipe_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    instruction TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recipe_tags (
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (recipe_id, tag)
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    quantity REAL,
    unit TEXT,
    location TEXT,
    bought_date DATE,
    expiry_date DATE,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS meal_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    meal_type TEXT DEFAULT 'dinner',
    recipe_id INTEGER REFERENCES recipes(id),
    description TEXT,
    rotation_week INTEGER,
    servings INTEGER DEFAULT 5
);

CREATE TABLE IF NOT EXISTS shopping_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    quantity REAL,
    unit TEXT,
    category TEXT,
    recipe_id INTEGER REFERENCES recipes(id),
    checked BOOLEAN DEFAULT 0,
    created_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS meal_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    meal_type TEXT DEFAULT 'dinner',
    planned_recipe_id INTEGER REFERENCES recipes(id),
    actual_recipe_id INTEGER REFERENCES recipes(id),
    outcome TEXT,
    modifications TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recipe_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    author TEXT DEFAULT 'ger',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recipe_prep_ahead (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL,
    description TEXT NOT NULL,
    classification TEXT NOT NULL,
    tag TEXT,
    is_passive BOOLEAN DEFAULT 0,
    safety_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name);
CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine);
CREATE INDEX IF NOT EXISTS idx_recipes_protein ON recipes(protein);
CREATE INDEX IF NOT EXISTS idx_recipes_meal_type ON recipes(meal_type);
CREATE INDEX IF NOT EXISTS idx_recipes_kid_friendly ON recipes(kid_friendly);
CREATE INDEX IF NOT EXISTS idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_steps_recipe_id ON recipe_steps(recipe_id);
CREATE INDEX IF NOT EXISTS idx_recipe_tags_recipe_id ON recipe_tags(recipe_id);
CREATE INDEX IF NOT EXISTS idx_meal_plan_date ON meal_plan(date);
CREATE INDEX IF NOT EXISTS idx_meal_log_date ON meal_log(date);
CREATE INDEX IF NOT EXISTS idx_shopping_list_checked ON shopping_list(checked);
CREATE INDEX IF NOT EXISTS idx_inventory_location ON inventory(location);
CREATE INDEX IF NOT EXISTS idx_inventory_expiry ON inventory(expiry_date);
CREATE INDEX IF NOT EXISTS idx_recipe_prep_ahead_recipe_id ON recipe_prep_ahead(recipe_id);
