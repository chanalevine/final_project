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
# DB SETUP
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
            author TEXT,
            image_url TEXT,
            instructions TEXT,
            date TEXT,
            url_slug TEXT,
            raw_json TEXT
        )
    """)

    # Ingredients table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            raw_text TEXT,
            quantity TEXT,
            unit TEXT,
            ingredient_name TEXT,
            normalized_name TEXT,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
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
# ADVANCED INGREDIENT PARSER
# ---------------------------------------------------------

# Convert unicode fractions like ½ → 1/2
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

    # Known cooking units
    VALID_UNITS = [
        "tsp", "tbsp", "cup", "cups", "oz", "ounce", "ounces",
        "lb", "lbs", "gram", "g", "kg", "ml", "liter", "liters",
        "clove", "cloves", "bag", "can", "package", "container",
        "stick", "sticks", "slice", "slices", "pound", "pounds"
    ]

    # Extract parenthetical package sizes
    paren_match = re.search(r"\((.*?)\)", raw)
    package_info = paren_match.group(1) if paren_match else None

    cleaned = re.sub(r"\(.*?\)", "", raw).strip()

    # Try to match: quantity + unit + name
    pattern = r"""
        ^\s*
        (?P<qty>\d+\s\d+/\d+|\d+/\d+|\d+)?   # 1 1/2, 1/2, 2
        \s*
        (?P<unit>[a-zA-Z\.]+)?              # tsp, tbsp., cups, cloves, bag
        \s*
        (?P<name>.+?)\s*$
    """

    match = re.match(pattern, cleaned, re.VERBOSE)

    if not match:
        return None, None, cleaned

    qty = match.group("qty")
    unit = match.group("unit")
    name = match.group("name")

    # Normalize unit
    if unit:
        unit = unit.rstrip(".").lower()
        if unit not in VALID_UNITS:
            # Not a real unit → treat entire string as ingredient name
            return None, None, cleaned

    # If qty missing but starts with a number (e.g., "3 onions")
    if qty is None:
        num_match = re.match(r"^(\d+)\s+(.*)$", cleaned)
        if num_match:
            qty = num_match.group(1)
            name = num_match.group(2)

    if name:
        name = name.strip()

    return qty, unit, name


# ---------------------------------------------------------
# INSERT INTO DB
# ---------------------------------------------------------

def insert_into_db(cur, conn, recipes):
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA synchronous=NORMAL;")
    cur.execute("BEGIN TRANSACTION;")

    for doc in recipes:
        recipe_id = doc.get("id")

        # Clean fields
        title = doc.get("title")

        # Author may be dict or string
        author = doc.get("author")
        if isinstance(author, dict):
            author = author.get("name")
        if not isinstance(author, str):
            author = None

        # Instructions may be list or string
        instructions = doc.get("instructions") or doc.get("instruction") or None
        if isinstance(instructions, list):
            instructions = "\n".join(instructions)
        if not isinstance(instructions, str):
            instructions = None

        image_url = doc.get("image")
        date = doc.get("date")
        slug = doc.get("slug") or doc.get("url_slug") or None
        raw_json = json.dumps(doc)

        # Insert recipe
        cur.execute("""
            INSERT OR REPLACE INTO recipes
            (id, title, author, image_url, instructions, date, url_slug, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_id,
            title,
            author,
            image_url,
            instructions,
            date,
            slug,
            raw_json
        ))

        # Clear old ingredients
        cur.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))

        # Insert ingredients
        for raw_ing in doc.get("ingredients", []):
            qty, unit, name = parse_ingredient(raw_ing)
            normalized = normalize_ingredient(name)

            cur.execute("""
                INSERT INTO ingredients
                (recipe_id, raw_text, quantity, unit, ingredient_name, normalized_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                raw_ing,
                qty,
                unit,
                name,
                normalized
            ))

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