import sqlite3
import os

def init_db():
    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect("database/food_data.db")
    cursor = conn.cursor()

    # ---------------------------------------------------------
    # RECIPES TABLE
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            image_url TEXT,
            instructions TEXT,
            date TEXT,
            url_slug TEXT,
            raw_json TEXT
        )
    """)

    # ---------------------------------------------------------
    # INGREDIENTS TABLE
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            raw_text TEXT,
            quantity TEXT,
            unit TEXT,
            ingredient_name TEXT,
            normalized_name TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes(id)
        )
    """)

    # ---------------------------------------------------------
    # WALMART PRODUCTS TABLE
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS walmart_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            name TEXT,
            price REAL,
            url TEXT,
            image TEXT,
            package_amount REAL,
            package_unit TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database schema initialized correctly.")

if __name__ == "__main__":
    init_db()
