import sqlite3
import re

def normalize_ingredient(raw_text):
    text = raw_text.lower().strip()

    # Remove commas and parentheses
    text = re.sub(r"[(),]", " ", text)

    # Remove unicode fractions like ½, ¼, ¾
    text = re.sub(r"[¼½¾⅓⅔⅛⅜⅝⅞]", " ", text)

    # Remove numeric fractions like 1/2, 3/4
    text = re.sub(r"\b\d+\/\d+\b", " ", text)

    # Remove whole numbers
    text = re.sub(r"\b\d+\b", " ", text)

    # Remove measurement units
    units = [
        "tsp", "tbsp", "tablespoon", "teaspoon",
        "cup", "cups", "oz", "ounce", "ounces",
        "lb", "pound", "pounds", "gram", "g", "kg",
        "clove", "cloves", "slice", "slices",
        "medium", "large", "small"
    ]
    for u in units:
        text = re.sub(rf"\b{u}\b", " ", text)

    # Remove preparation words
    prep_words = [
        "diced", "chopped", "minced", "sliced",
        "fresh", "ground", "crushed", "peeled",
        "shredded", "grated"
    ]
    for p in prep_words:
        text = re.sub(rf"\b{p}\b", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Handle simple plurals
    if text.endswith("s") and len(text) > 3:
        text = text[:-1]

    return text

# ---------------------------------------------------------
# DATABASE SCHEMA (recipes + ingredients + walmart_products)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect("food_data.db")
    cursor = conn.cursor()

    # Recipes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            servings INTEGER
        )
    """)

    # Ingredients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            ingredient_name TEXT NOT NULL,
            quantity TEXT,
            normalized_name TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    """)

    # Walmart products table (already used in your scraper)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS walmart_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            name TEXT,
            price REAL,
            url TEXT,
            image TEXT
        )
    """)

    conn.commit()
    return conn


# ---------------------------------------------------------
# INSERT A RECIPE
# ---------------------------------------------------------
def add_recipe(conn, name, servings):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO recipes (name, servings)
        VALUES (?, ?)
    """, (name, servings))
    conn.commit()
    return cursor.lastrowid


# ---------------------------------------------------------
# INSERT AN INGREDIENT
# ---------------------------------------------------------
def add_ingredient(conn, recipe_id, ingredient_name, quantity, normalized_name):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO ingredients (recipe_id, ingredient_name, quantity, normalized_name)
        VALUES (?, ?, ?, ?)
    """, (recipe_id, ingredient_name, quantity, normalized_name))
    conn.commit()


# ---------------------------------------------------------
# EXAMPLE: INSERT ONE KOSHER.COM RECIPE
# ---------------------------------------------------------
if __name__ == "__main__":
    conn = init_db()

    # 1. Add recipe
    recipe_id = add_recipe(conn, "Onion Soup", 6)

    # 2. Add ingredients
    '''
    add_ingredient(conn, recipe_id, "2 medium onions, diced", "2 onions", "onion")
    add_ingredient(conn, recipe_id, "3 tbsp olive oil", "3 tbsp", "olive oil")
    add_ingredient(conn, recipe_id, "1 tsp paprika", "1 tsp", "paprika")
    add_ingredient(conn, recipe_id, "3 cloves garlic", "3 cloves", "garlic")
    '''
    print(normalize_ingredient("2 medium onions, diced"))      # onion
    print(normalize_ingredient("3 tbsp olive oil"))            # olive oil
    print(normalize_ingredient("1 tsp paprika"))               # paprika
    print(normalize_ingredient("3 cloves garlic"))             # garlic
    print(normalize_ingredient("½ cup brown sugar"))           # brown sugar
    print(normalize_ingredient("1 lb ground beef"))            # beef

    conn.close()
    print("Recipe + ingredients saved.")