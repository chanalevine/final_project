import sqlite3
import os

def init_db():
    db_path = os.path.join("database", "food_data.db")

    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("Resetting database...")

    # Drop old tables
    cur.execute("DROP TABLE IF EXISTS recipe_ingredients")
    cur.execute("DROP TABLE IF EXISTS ingredients")
    cur.execute("DROP TABLE IF EXISTS recipes")
    cur.execute("DROP TABLE IF EXISTS nutrition")

    # Recipes table
    cur.execute("""
        CREATE TABLE recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            url_slug TEXT UNIQUE
        )
    """)

    # Ingredients table (ONLY price, no walmart_price)
    cur.execute("""
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price REAL,
            price_unit TEXT,
            package_size TEXT
        )
    """)

    # Recipe-Ingredient join table
    cur.execute("""
        CREATE TABLE recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity TEXT,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id),
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    """)

    # Nutrition table (description only)
    cur.execute("""
        CREATE TABLE nutrition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingredient_name TEXT UNIQUE,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database recreated successfully.")
    

if __name__ == "__main__":
    init_db()