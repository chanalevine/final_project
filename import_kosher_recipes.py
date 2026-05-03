import sqlite3
from normalizer import normalize_ingredient
from recipes import scrape_all_recipes   # adjust import

# ---------------------------------------------------------
# INSERT RECIPE INTO food_data.db
# ---------------------------------------------------------

def insert_recipe(conn, recipe):
    cursor = conn.cursor()

    # Insert recipe (default servings = 4)
    cursor.execute("""
        INSERT INTO recipes (name, servings)
        VALUES (?, ?)
    """, (recipe["title"], 4))

    recipe_id = cursor.lastrowid

    # Insert ingredients
    for raw in recipe.get("ingredients", []):
        normalized = normalize_ingredient(raw)

        cursor.execute("""
            INSERT INTO ingredients (recipe_id, ingredient_name, quantity, normalized_name)
            VALUES (?, ?, ?, ?)
        """, (recipe_id, raw, raw, normalized))

    conn.commit()
    return recipe_id


# ---------------------------------------------------------
# BULK IMPORT
# ---------------------------------------------------------

def import_all():
    conn = sqlite3.connect("food_data.db")
    recipes = scrape_all_recipes()

    print("Importing:", len(recipes))

    for r in recipes:
        rid = insert_recipe(conn, r)
        print("Imported:", r["title"], "→ ID", rid)

    conn.close()


if __name__ == "__main__":
    import_all()