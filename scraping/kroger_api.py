import sqlite3
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = "recipecostapp-bbcd2l09"
CLIENT_SECRET = "3y0-wBTAsMbL4ZglQnMj2p87RYH6VKL2HFGXNEg1"
STORE_ID = "01400943"

DB_PATH = "database/food_data.db"


def get_token():
    url = "https://api-ce.kroger.com/v1/connect/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "scope": "product.compact"
    }
    res = requests.post(url, data=data, auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET))
    return res.json()["access_token"]


def kroger_search(ingredient, token):
    url = "https://api-ce.kroger.com/v1/products"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "filter.term": ingredient,
        "filter.locationId": STORE_ID,
        "filter.limit": 1
    }

    res = requests.get(url, headers=headers, params=params)
    data = res.json()

    if not data.get("data"):
        return None, None, None

    item = data["data"][0]
    title = item.get("description")

    items = item.get("items", [])
    if not items:
        return title, None, None

    first = items[0]

    price_info = first.get("price", {})
    price = price_info.get("regular") or price_info.get("promo") or None

    size = first.get("size")

    return title, price, size


def update_all_ingredients():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM ingredients")
    rows = cursor.fetchall()

    token = get_token()

    for ing_id, name in rows:
        title, price, size = kroger_search(name, token)

        if price is not None:
            cursor.execute(
                """
                UPDATE ingredients
                SET price = ?, package_size = ?
                WHERE id = ?
                """,
                (price, size, ing_id)
            )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    update_all_ingredients()
