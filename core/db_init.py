import sqlite3
import os

def init_db():
    db_path = os.path.join("database", "food_data.db")

    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Resetting database...")

    cursor.execute("DROP TABLE IF EXISTS ingredients")
    cursor.execute("DROP TABLE IF EXISTS recipes")
    cursor.execute("DROP TABLE IF EXISTS walmart_products")

    cursor.execute("""
        CREATE TABLE recipes (
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

    cursor.execute("""
        CREATE TABLE ingredients (
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

    cursor.execute("""
        CREATE TABLE walmart_products (
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
    print("Database recreated successfully at database/food_data.db")


if __name__ == "__main__":
    init_db()
