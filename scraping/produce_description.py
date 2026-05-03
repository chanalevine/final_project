import sqlite3
import requests
from bs4 import BeautifulSoup
import time

DB_PATH = "database/food_data.db"

# ---------------------------------------------------------
# 1. Scrape Wikipedia description
# ---------------------------------------------------------

def get_wikipedia_description(ingredient):
    search_url = f"https://en.wikipedia.org/wiki/{ingredient.replace(' ', '_')}"

    try:
        res = requests.get(search_url, timeout=10)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # First paragraph of the article
        p = soup.find("p")
        if p:
            text = p.get_text().strip()
            return text
    except:
        return None

    return None


# ---------------------------------------------------------
# 2. Store description in DB
# ---------------------------------------------------------

def store_description(ingredient, description):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO nutrition (ingredient_name, description)
        VALUES (?, ?)
    """, (ingredient, description))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 3. Loop through all ingredients
# ---------------------------------------------------------

def update_all_descriptions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Only fetch ingredients missing descriptions
    cur.execute("""
        SELECT name FROM ingredients
        WHERE name NOT IN (SELECT ingredient_name FROM nutrition)
    """)

    ingredients = [row[0] for row in cur.fetchall()]
    conn.close()

    for ing in ingredients:
        print(f"Scraping description for: {ing}")

        desc = get_wikipedia_description(ing)

        if desc:
            store_description(ing, desc)
            print(f"Stored description for {ing}")
        else:
            print(f"No description found for {ing}")

        time.sleep(0.5)


if __name__ == "__main__":
    update_all_descriptions()