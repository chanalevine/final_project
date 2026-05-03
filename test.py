import sqlite3
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = "recipecostapp-bbcd2l09"
CLIENT_SECRET = "3y0-wBTAsMbL4ZglQnMj2p87RYH6VKL2HFGXNEg1"
STORE_ID = "01400943"   # working Kroger-family store


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
    title = item["description"]

    size = item["items"][0].get("size")
    price = item["items"][0]["price"].get("regular")

    return title, price, size


def test_first_five():
    conn = sqlite3.connect("database/food_data.db")
    cur = conn.cursor()

    cur.execute("SELECT name FROM ingredients LIMIT 5")
    ingredients = [row[0] for row in cur.fetchall()]

    token = get_token()

    print("\n===== TESTING FIRST 5 INGREDIENTS =====\n")

    for ing in ingredients:
        print(f"Ingredient: {ing}")

        title, price, size = kroger_search(ing, token)

        print("  Title:", title)
        print("  Price:", price)
        print("  Size:", size)
        print()

    conn.close()


if __name__ == "__main__":
    test_first_five()