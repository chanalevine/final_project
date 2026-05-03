import sqlite3
import requests
import time

DB_PATH = "database/food_data.db"

# ---------------------------------------------------------
# 1. Get price + size from Target
# ---------------------------------------------------------

def get_target_price_and_size(ingredient):
    search_url = "https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v1"
    params = {
        "keyword": ingredient,
        "offset": 0,
        "limit": 1,
        "store_id": "3991",
        "pricing_store_id": "3991"
    }

    try:
        res = requests.get(search_url, params=params, timeout=10)
        products = res.json()["data"]["search"]["products"]
    except:
        return None, None

    if not products:
        return None, None

    tcin = products[0]["tcin"]

    detail_url = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
    params = {
        "tcin": tcin,
        "store_id": "3991",
        "pricing_store_id": "3991"
    }

    try:
        res = requests.get(detail_url, params=params, timeout=10)
        data = res.json()["data"]["product"]

        price = data["price"]["current_retail"]
        size = data["item"]["product_description"].get("downstream_description")

        return price, size
    except:
        return None, None


# ---------------------------------------------------------
# 2. Store price + size in DB
# ---------------------------------------------------------

def store_price(ingredient, price, size):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE ingredients
        SET price = ?, price_unit = 'each', package_size = ?
        WHERE name = ?
    """, (price, size, ingredient))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 3. Loop through all ingredients
# ---------------------------------------------------------

def update_all_prices():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT name FROM ingredients")
    ingredients = [row[0] for row in cur.fetchall()]
    conn.close()

    for ing in ingredients:
        print(f"Searching Target for: {ing}")

        price, size = get_target_price_and_size(ing)

        if price is not None:
            store_price(ing, price, size)
            print(f"Stored price for {ing}: ${price} ({size})")
        else:
            print(f"No price found for {ing}")

        time.sleep(0.5)  # avoid rate limits


if __name__ == "__main__":
    update_all_prices()