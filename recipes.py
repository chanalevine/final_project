import requests
import math
import sqlite3
import json

# ---------- CONFIG ----------

TYPESENSE_URL = "https://pxuy5ezorfl4btw2p-1.a1.typesense.net/multi_search"

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
    "x-typesense-api-key": "qFh02BKRk3j2ID1k4t0xfdf3Lqw4XmO9"
}

PER_PAGE = 45


# ---------- DB SETUP ----------

def init_db():
    conn = sqlite3.connect("recipes.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY,
        title TEXT,
        author TEXT,
        image_url TEXT,
        instructions TEXT,
        date TEXT,
        url_slug TEXT,
        raw_json TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER,
        raw_text TEXT,
        quantity REAL,
        unit TEXT,
        ingredient_name TEXT,
        FOREIGN KEY(recipe_id) REFERENCES recipes(id)
    )
    """)

    conn.commit()
    return conn, cur


# ---------- SCRAPING ----------

def fetch_page(page: int):
    payload = {
        "searches": [
            {
                "collection": "live_recipes",
                "q": "",
                "query_by": "title",
                "per_page": str(PER_PAGE),
                "page": page,
                "sort_by": "date:desc",
                "filter_by": "community-recipe:=false"
            }
        ]
    }

    resp = requests.post(TYPESENSE_URL, headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()["results"][0]


def scrape_all_recipes():
    first = fetch_page(1)
    found = first["found"]
    total_pages = math.ceil(found / PER_PAGE)

    all_docs = []

    # Page 1
    for hit in first["hits"]:
        all_docs.append(hit["document"])

    # Remaining pages
    for page in range(2, total_pages + 1):
        result = fetch_page(page)
        for hit in result["hits"]:
            all_docs.append(hit["document"])

    return all_docs


# ---------- INSERT INTO DB ----------

def safe(v):
    """Convert dicts/lists to JSON strings; leave primitives unchanged."""
    return json.dumps(v) if isinstance(v, (dict, list)) else v


def insert_into_db(cur, conn, recipes):
    # Enable WAL mode for better concurrency
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")

    # Begin a single large transaction
    cur.execute("BEGIN TRANSACTION;")

    for doc in recipes:
        recipe_id = doc.get("id")

        cur.execute("""
            INSERT OR REPLACE INTO recipes
            (id, title, author, image_url, instructions, date, url_slug, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_id,
            safe(doc.get("title")),
            safe(doc.get("author")),
            safe(doc.get("image")),
            safe(doc.get("instructions")),
            safe(doc.get("date")),
            safe(doc.get("slug")),
            json.dumps(doc)
        ))

        # Delete old ingredients
        cur.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

        # Insert ingredients
        for ing in doc.get("ingredients", []):
            cur.execute("""
                INSERT INTO ingredients
                (recipe_id, raw_text, quantity, unit, ingredient_name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                recipe_id,
                ing,
                None,
                None,
                None
            ))

    # Commit once at the end
    conn.commit()


# ---------- MAIN ----------

def main():
    conn, cur = init_db()
    recipes = scrape_all_recipes()
    print("Collected:", len(recipes))
    insert_into_db(cur, conn, recipes)
    conn.close()


if __name__ == "__main__":
    main()
