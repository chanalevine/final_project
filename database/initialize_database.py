import sqlite3

def init_db():
    conn = sqlite3.connect("database/food_data.db")
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

    # Walmart products table (same as you already use)
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
    conn.close()
    print("Database schema initialized.")

if __name__ == "__main__":
    init_db()
