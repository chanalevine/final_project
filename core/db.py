import os
import sqlite3

def get_connection():
    """
    Returns a SQLite connection to database/food_data.db
    """
    db_path = os.path.join("database", "food_data.db")
    return sqlite3.connect(db_path)
