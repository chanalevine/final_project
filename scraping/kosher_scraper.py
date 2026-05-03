import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import requests
import math
import sqlite3
import json
import re

from core.normalizer import normalize_ingredient


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

TYPESENSE_URL = "https://pxuy5ezorfl4btw2p-1.a1.typesense.net/multi_search"

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0",
    "x-typesense-api-key": "qFh02BKRk3j2ID1k4t0xfdf3Lqw4XmO9"
}

PER_PAGE = 45


# ---------------------------------------------------------
# DB SETUP (NORMALIZED SCHEMA)
# ---------------------------------------------------------

def init_db():
    os.makedirs("database", exist_ok=True)

    conn = sqlite3.connect("database/food_data.db")
    cur = conn.cursor()

    # Recipes table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url_slug TEXT
        )
    """)

    # Ingredients table (unique ingredients)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            price REAL,
            price_unit TEXT,
            package_size TEXT
        )
    """)

    # Recipe-Ingredient join table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS recipe_ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_id INTEGER,
            quantity TEXT,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id),
            FOREIGN KEY(ingredient_id) REFERENCES ingredients(id)
        )
    """)

    conn.commit()
    return conn, cur


# ---------------------------------------------------------
# SCRAPING
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# ADVANCED INGREDIENT PARSER (OPTION B)
# ---------------------------------------------------------

def normalize_unicode_fractions(text):
    unicode_fractions = {
        "¼": "1/4",
        "½": "1/2",
        "¾": "3/4",
        "⅐": "1/7",
        "⅑": "1/9",
        "⅒": "1/10",
        "⅓": "1/3",
        "⅔": "2/3",
        "⅕": "1/5",
        "⅖": "2/5",
        "⅗": "3/5",
        "⅘": "4/5",
        "⅙": "1/6",
        "⅚": "5/6",
        "⅛": "1/8",
        "⅜": "3/8",
        "⅝": "5/8",
        "⅞": "7/8"
    }
    for uf, ascii_f in unicode_fractions.items():
        text = text.replace(uf, ascii_f)
    return text


def parse_ingredient(raw):
    if not raw:
        return None, None, None

    raw = raw.strip()
    raw = normalize_unicode_fractions(raw)

    VALID_UNITS = [
        "tsp", "tbsp", "cup", "cups", "oz", "ounce", "ounces",
        "lb", "lbs", "gram", "g", "kg", "ml", "liter", "liters",
        "clove", "cloves", "bag", "can", "package", "container",
        "stick", "sticks", "slice", "slices", "pound", "pounds"
    ]

    # Remove parenthetical info
    cleaned = re.sub(r"\(.*?\)", "", raw).strip()

    pattern = r"""
        ^\s*
        (?P<qty>\d+\s\d+/\d+|\d+/\d+|\d+)?   
        \s*
        (?P<unit>[a-zA-Z\.]+)?              
        \s*
        (?P<name>.+?)\s*$
    """

    match = re.match(pattern, cleaned, re.VERBOSE)

    # If no match → treat full cleaned string as name
    if not match:
        return None, None, cleaned

    qty = match.group("qty")
    unit = match.group("unit")
    name = match.group("name").strip()

    if unit:
        unit = unit.rstrip(".").lower()
        if unit not in VALID_UNITS:
            # Invalid unit → treat full cleaned as name
            return None, None, cleaned

    # If qty missing but starts with a number
    if qty is None:
        num_match = re.match(r"^(\d+)\s+(.*)$", cleaned)
        if num_match:
            qty = num_match.group(1)
            name = num_match.group(2).strip()

    return qty, unit, name


# ---------------------------------------------------------
# INSERT INTO DB (NORMALIZED STRUCTURE)
# ---------------------------------------------------------

def insert_into_db(cur, conn, recipes):
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("BEGIN TRANSACTION;")

    for doc in recipes:
        recipe_id = doc.get("id")
        title = doc.get("title")
        slug = doc.get("slug") or doc.get("url_slug")

        # Insert recipe
        cur.execute("""
            INSERT OR IGNORE INTO recipes (id, title, url_slug)
            VALUES (?, ?, ?)
        """, (recipe_id, title, slug))

        # Process ingredients
        for raw_ing in doc.get("ingredients", []):
            qty, unit, name = parse_ingredient(raw_ing)

            # If parser fails → skip
            if not name:
                continue

            # Normalize ingredient name
            normalized = normalize_ingredient(name)

            # Insert ingredient if missing
            cur.execute("SELECT id FROM ingredients WHERE name = ?", (normalized,))
            ing_row = cur.fetchone()

            if ing_row:
                ingredient_id = ing_row[0]
            else:
                cur.execute("INSERT INTO ingredients (name) VALUES (?)", (normalized,))
                ingredient_id = cur.lastrowid

            # Insert into recipe_ingredients
            cur.execute("""
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity)
                VALUES (?, ?, ?)
            """, (recipe_id, ingredient_id, qty))

    conn.commit()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    conn, cur = init_db()
    recipes = scrape_all_recipes()
    print("Collected:", len(recipes))
    insert_into_db(cur, conn, recipes)
    conn.close()


if __name__ == "__main__":
    main()