import sqlite3

DB_PATH = "database/food_data.db"

def print_table(table, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get column names
    cur.execute(f"PRAGMA table_info({table})")
    cols = [col[1] for col in cur.fetchall()]

    print(f"\n===== {table.upper()} (showing {limit} rows) =====")
    print(" | ".join(cols))
    print("-" * 60)

    # Get rows
    cur.execute(f"SELECT * FROM {table} LIMIT {limit}")
    rows = cur.fetchall()

    for row in rows:
        print(" | ".join(str(x) if x is not None else "" for x in row))

    conn.close()

print_table("recipes", 5)
print_table("ingredients", 10)
print_table("recipe_ingredients", 10)