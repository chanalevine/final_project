import sqlite3
import pandas as pd

conn = sqlite3.connect("/workspaces/final_project/recipes.db")

print(pd.read_sql_query("SELECT COUNT(*) FROM recipes", conn))
print(pd.read_sql_query("SELECT COUNT(*) FROM ingredients", conn))

conn.close()