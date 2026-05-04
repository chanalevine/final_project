import sqlite3
import requests
from bs4 import BeautifulSoup
import time

DB_PATH = "database/food_data.db"

# ---------------------------------------------------------
# 1. Scrape Wikipedia description
# ---------------------------------------------------------


def get_wikipedia_description(ingredient):
    # Convert ingredient to Wikipedia-style title
    title = ingredient.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{title}"

    try:
        res = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })

        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        # Skip disambiguation pages
        if soup.find("table", {"id": "disambigbox"}):
            return None

        # Find the first REAL paragraph (skip empty or citation-only)
        for p in soup.find_all("p"):
            text = p.get_text().strip()

            # Skip empty paragraphs
            if not text:
                continue

            # Skip paragraphs that are just pronunciation or metadata
            if text.startswith("(") and ")" in text[:20]:
                continue

            return text

    except Exception:
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
# 3. Loop through all ingredients missing descriptions
# ---------------------------------------------------------

def update_all_descriptions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT name FROM ingredients
        WHERE name NOT IN (SELECT ingredient_name FROM nutrition)
    """)

    ingredients = [row[0] for row in cur.fetchall()]
    conn.close()

    print(f"Found {len(ingredients)} ingredients missing descriptions.\n")

    for ing in ingredients:
        print(f"Scraping description for: {ing}")

        desc = get_wikipedia_description(ing)

        if desc:
            store_description(ing, desc)
            print("  ✔ Stored description")
        else:
            print("  ✘ No description found")

        time.sleep(0.5)  # Be polite to Wikipedia

    print("\nAll descriptions updated.")


if __name__ == "__main__":
    update_all_descriptions()
