import sqlite3

conn = sqlite3.connect("food_data.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE walmart_products ADD COLUMN package_amount REAL;")
cursor.execute("ALTER TABLE walmart_products ADD COLUMN package_unit TEXT;")

conn.commit()
conn.close()

print("Columns added.")