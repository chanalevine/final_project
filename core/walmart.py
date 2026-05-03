import requests
from bs4 import BeautifulSoup
import sqlite3
import time

# -----------------------------
# DATABASE SETUP
# -----------------------------
DB_PATH = "database/food_data.db"
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Add walmart_price column if it doesn't exist
try:
    cur.execute("ALTER TABLE ingredients ADD COLUMN walmart_price REAL;")
except:
    pass  # column already exists

conn.commit()

# -----------------------------
# WALMART HTML SCRAPER
# -----------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def get_walmart_price(ingredient_name):
    """Scrape Walmart search results and return the first product price."""
    query = ingredient_name.replace(" ", "+")
    url = f"https://www.walmart.com/search?q={query}"

    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
    except Exception:
        return None

    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # Walmart price selector (HTML only)
    price_tag = soup.select_one("span[data-automation-id='product-price']")
    if not price_tag:
        return None

    price_text = price_tag.get_text(strip=True).replace("$", "")
    try:
        return float(price_text)
    except:
        return None

# -----------------------------
# UPDATE ALL INGREDIENT PRICES
# -----------------------------
def update_all_prices():
    cur.execute("SELECT id, ingredient FROM ingredients")
    rows = cur.fetchall()

    for ing_id, ing_text in rows:
        print(f"Looking up price for: {ing_text}")

        price = get_walmart_price(ing_text)
        if price is None:
            print("  No price found.")
            continue

        cur.execute("""
            UPDATE ingredients
            SET walmart_price = ?
            WHERE id = ?
        """, (price, ing_id))

        conn.commit()
        print(f"  Saved price: ${price}")

        time.sleep(1)  # avoid rate limiting

# -----------------------------
# RUN
# -----------------------------
update_all_prices()
conn.close()