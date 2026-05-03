"""
Walmart grocery ingredient price scraper
-----------------------------------------
Uses curl_cffi to spoof a real Chrome TLS fingerprint, which bypasses
Walmart's PerimeterX "Robot or human?" bot detection that blocks plain requests.
 
Install deps:
    pip install curl-cffi beautifulsoup4
 
Usage:
    python walmart_scraper.py
"""
 
import json
import random
import sqlite3
import time
from datetime import datetime
from pathlib import Path
 
from bs4 import BeautifulSoup
from curl_cffi.requests import Session  # drop-in replacement for requests.Session
 
BASE_URL = "https://www.walmart.com"
DB_FILE  = "ingredients.db"
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language":           "en-US,en;q=0.9",
    "Referer":                   "https://www.walmart.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest":            "document",
    "Sec-Fetch-Mode":            "navigate",
    "Sec-Fetch-Site":            "same-origin",
    "Sec-Fetch-User":            "?1",
}
 
 
# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
 
def init_db(db_file=DB_FILE):
    """Create the SQLite DB and tables if they don't already exist."""
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS searches (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            query      TEXT NOT NULL,
            scraped_at TEXT NOT NULL
        );
 
        CREATE TABLE IF NOT EXISTS products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            search_id    INTEGER NOT NULL REFERENCES searches(id),
            name         TEXT,
            brand        TEXT,
            price        REAL,
            unit_price   TEXT,
            size         TEXT,
            ingredients  TEXT,
            availability TEXT,
            image_url    TEXT,
            product_url  TEXT,
            scraped_at   TEXT NOT NULL
        );
 
        CREATE INDEX IF NOT EXISTS idx_products_search ON products(search_id);
        CREATE INDEX IF NOT EXISTS idx_products_name   ON products(name);
        CREATE INDEX IF NOT EXISTS idx_searches_query  ON searches(query);
    """)
    conn.commit()
    return conn
 
 
def save_search(conn, query, products):
    """Insert one search record + all its product rows into the DB."""
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        "INSERT INTO searches (query, scraped_at) VALUES (?, ?)",
        (query, now),
    )
    search_id = cur.lastrowid
    conn.executemany(
        """INSERT INTO products
           (search_id, name, brand, price, unit_price, size,
            ingredients, availability, image_url, product_url, scraped_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                search_id,
                p.get("name"),
                p.get("brand"),
                p.get("price"),
                p.get("unit_price"),
                p.get("size"),
                p.get("ingredients"),
                p.get("availability"),
                p.get("image"),
                p.get("url"),
                now,
            )
            for p in products
        ],
    )
    conn.commit()
    print(f"  Saved {len(products)} product(s) to DB (search_id={search_id})")
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def make_session():
    """
    Return a curl_cffi Session that impersonates Chrome 124.
    This is the key change from plain requests — it spoofs the TLS fingerprint
    that PerimeterX uses to detect bots, so Walmart serves real pages.
    """
    session = Session(impersonate="chrome110")
    session.headers.update(HEADERS)
    return session
 
 
def extract_next_data(soup):
    """Find and parse the __NEXT_DATA__ JSON blob Walmart embeds in every page."""
    tag = soup.find("script", {"id": "__NEXT_DATA__"})
    if not tag:
        return None
    try:
        return json.loads(tag.string)
    except (json.JSONDecodeError, TypeError):
        return None
 
 
def is_captcha_page(soup):
    """Return True if Walmart served a bot-check page instead of real content."""
    title = soup.find("title")
    return title and "robot or human" in title.get_text().lower()
 
 
def debug_dump(soup, label):
    """Save raw HTML to disk for manual inspection."""
    path = Path(f"debug_{label.replace(' ', '_')}.html")
    path.write_text(soup.prettify(), encoding="utf-8")
    print(f"  Debug HTML saved to '{path}'")
 
 
def parse_search_results(data):
    """Extract product stubs from a Walmart search-results __NEXT_DATA__ blob."""
    results = []
    try:
        search_result = (
            data.get("props", {})
                .get("pageProps", {})
                .get("initialData", {})
                .get("searchResult", {})
        )
 
        # Standard path: itemStacks is a list of "shelves"
        items = []
        for stack in search_result.get("itemStacks", []):
            items.extend(stack.get("items", []))
 
        # Fallback for alternate page layouts
        if not items:
            items = search_result.get("items", [])
 
        for item in items:
            canonical  = item.get("canonicalUrl", "")
            price_info = item.get("priceInfo") or {}
            current    = price_info.get("currentPrice") or {}
            unit       = price_info.get("unitPrice") or {}
 
            results.append({
                "name":         item.get("name"),
                "brand":        item.get("brand"),
                "price":        current.get("price"),
                "unit_price":   unit.get("displayValue"),
                "size":         item.get("weightUnitDisplayValue"),
                "ingredients":  None,   # only available on individual product pages
                "availability": item.get("availabilityStatus"),
                "image":        (item.get("imageInfo") or {}).get("thumbnailUrl"),
                "url": (
                    BASE_URL + canonical
                    if canonical.startswith("/")
                    else canonical
                ),
            })
    except (KeyError, TypeError, AttributeError):
        pass
    return results
 
 
# ---------------------------------------------------------------------------
# Core scraping
# ---------------------------------------------------------------------------
 
def fetch_page(session, url, referer=None):
    """GET a URL, set optional Referer, return BeautifulSoup or None."""
    if referer:
        session.headers.update({"Referer": referer})
    try:
        res = session.get(url, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None
    return BeautifulSoup(res.text, "html.parser")
 
 
def search_ingredient(session, query, max_results=5, debug=False):
    """
    Search Walmart grocery for one ingredient.
    Returns a list of product dicts, or [] on failure.
    """
    url = (
        f"{BASE_URL}/search"
        f"?q={query.replace(' ', '+')}"
        f"&sort=best_seller&page=1&affinityOverride=default"
    )
    print(f"\nSearching: '{query}'")
 
    soup = fetch_page(session, url, referer=BASE_URL + "/")
    if soup is None:
        return []
 
    if is_captcha_page(soup):
        print("  Blocked: Walmart served a CAPTCHA page.")
        print("  curl_cffi should prevent this — if it persists, add a longer delay before retrying.")
        if debug:
            debug_dump(soup, query)
        return []
 
    data = extract_next_data(soup)
    if not data:
        print("  Warning: __NEXT_DATA__ not found.")
        if debug:
            debug_dump(soup, query)
        return []
 
    results = parse_search_results(data)
    if not results:
        print("  Warning: page parsed OK but no products found — JSON path may have changed.")
        if debug:
            Path(f"debug_{query.replace(' ', '_')}.json").write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        return []
 
    return results[:max_results]
 
 
def scrape_product_page(session, url):
    """
    Deep-scrape a single product page to get full details including ingredients.
    Returns a product dict or None.
    """
    print(f"  Scraping product: {url}")
    soup = fetch_page(session, url)
    if soup is None:
        return None
 
    data = extract_next_data(soup)
    if not data:
        print("  Warning: __NEXT_DATA__ not found on product page.")
        return None
 
    try:
        product    = (
            data["props"]["pageProps"]
                .get("initialData", {})
                .get("data", {})
                .get("product", {})
        )
        if not product:
            return None
 
        price_info = product.get("priceInfo") or {}
        current    = price_info.get("currentPrice") or {}
        unit       = price_info.get("unitPrice") or {}
 
        # Ingredients are nested inside detailedDescription sections
        ingredients = None
        for section in (product.get("detailedDescription") or {}).get("sections", []):
            for item in section.get("items", []):
                if "ingredient" in (item.get("name") or "").lower():
                    ingredients = item.get("content")
 
        return {
            "name":         product.get("name"),
            "brand":        product.get("brand"),
            "price":        current.get("price"),
            "unit_price":   unit.get("displayValue"),
            "size":         product.get("weightIncrement"),
            "ingredients":  ingredients,
            "availability": product.get("availabilityStatus"),
            "image":        (product.get("imageInfo") or {}).get("thumbnailUrl"),
            "url":          url,
        }
    except (KeyError, TypeError):
        return None
 
 
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
 
def scrape_ingredients(ingredient_list, max_results=3, debug=False, db_file=DB_FILE):
    """
    Search Walmart for each ingredient, print prices, and save to SQLite.
 
    Args:
        ingredient_list: list of ingredient name strings
        max_results:     max products to store per ingredient
        debug:           save raw HTML/JSON on failure for inspection
        db_file:         SQLite database path
    """
    conn    = init_db(db_file)
    session = make_session()
 
    # Prime session cookies via homepage
    try:
        home = session.get(BASE_URL, timeout=10)
        home.raise_for_status()
        print(f"Homepage: {home.status_code} OK")
    except Exception as e:
        print(f"Warning: could not reach homepage — {e}")
 
    for i, ingredient in enumerate(ingredient_list):
        products = search_ingredient(session, ingredient, max_results=max_results, debug=debug)
 
        if products:
            save_search(conn, ingredient, products)
            for p in products:
                price_str = f"${p['price']:.2f}" if p["price"] else "N/A"
                unit_str  = f"  ({p['unit_price']})" if p["unit_price"] else ""
                print(f"    {(p['name'] or '')[:60]:<60} {price_str}{unit_str}")
        else:
            print("  No products saved for this ingredient.")
 
        # Polite delay — longer pause every 3rd request
        delay = random.uniform(2.5, 4.5) if i % 3 == 2 else random.uniform(1.2, 2.8)
        print(f"  Waiting {delay:.1f}s...")
        time.sleep(delay)
 
    conn.close()
    print(f"\nDone. All data stored in '{db_file}'.")
    print(f"Query example:")
    print(f'  sqlite3 {db_file} "SELECT name, price, unit_price FROM products;"')
 
 
if __name__ == "__main__":
    recipe_ingredients = [
        "spaghetti pasta",
        "canned crushed tomatoes",
        "ground beef",
        "garlic",
        "olive oil",
        "parmesan cheese",
    ]
 
    scrape_ingredients(recipe_ingredients, max_results=3, debug=True)