import sqlite3, pandas as pd

conn = sqlite3.connect("database/food_data.db")

print(pd.read_sql_query("SELECT id, title, author, url_slug FROM recipes LIMIT 5", conn))
print(pd.read_sql_query("SELECT recipe_id, raw_text, quantity, unit, ingredient_name, normalized_name FROM ingredients LIMIT 5", conn))

conn.close()