import requests
from bs4 import BeautifulSoup
import re
import time
import random


# ---------------------------------------------------------
# PACKAGE SIZE EXTRACTION
# ---------------------------------------------------------

def extract_package_size(name):
    text = name.lower()

    patterns = [
        r"(\d+(\.\d+)?)\s*oz",
        r"(\d+(\.\d+)?)\s*fl\s*oz",
        r"(\d+(\.\d+)?)\s*lb",
        r"(\d+(\.\d+)?)\s*pound",
        r"(\d+(\.\d+)?)\s*ct",
        r"(\d+(\.\d+)?)\s*count",
        r"(\d+(\.\d+)?)\s*pack",
    ]

    for p in patterns:
        m = re.search(p, text)
        if m:
            amount = float(m.group(1))
            unit = re.findall(r"[a-z]+", p)[-1]
            return amount, unit

    return None, None


# ---------------------------------------------------------
# BULK FILTER
# ---------------------------------------------------------

def is_bulk_item(name, amount, unit):
    name = name.lower()

    bulk_words = ["bulk", "family size", "restaurant", "value size"]
    if any(b in name for b in bulk_words):
        return True

    if amount and unit:
        if "oz" in unit and amount > 32:
            return True
        if "lb" in unit and amount > 2:
            return True

    return False


# ---------------------------------------------------------
# STRONGEST POSSIBLE HTML SCRAPER (REQUESTS-ONLY)
# ---------------------------------------------------------

def get_walmart_price(query):
    url = f"https://www.walmart.com/search?q={query.replace(' ', '+')}"

    # Random delay to avoid bot detection
    time.sleep(random.uniform(1.5, 4.0))

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    cookies = {
        "aka_debug": "true",
        "x-walmart-edge-id": "1",
        "x-walmart-persist": "1",
    }

    # First request
    res = requests.get(url, headers=headers, cookies=cookies)
    html = res.text

    # If robot page, try again
    if "Robot or human?" in html:
        time.sleep(random.uniform(2.0, 5.0))
        res = requests.get(url, headers=headers, cookies=cookies)
        html = res.text

    # If still robot page, give up
    if "Robot or human?" in html:
        print("Blocked by Walmart bot protection")
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Try all known Walmart selectors
    selectors = [
        "div[data-testid='product-tile']",
        "div[data-type='items'] div",
        "div.search-result-gridview-item",
        "div[data-automation-id='search-result-gridview-item']",
    ]

    products = []
    for sel in selectors:
        products = soup.select(sel)
        if products:
            break

    if not products:
        print("No Walmart products found")
        return None

    # Extract product info
    for product in products:

        # NAME
        name_selectors = [
            "span[data-testid='product-title']",
            "a[data-type='itemTitles'] span",
            "span.lh-title",
            "a span",
        ]

        name = None
        for sel in name_selectors:
            tag = product.select_one(sel)
            if tag:
                name = tag.get_text(strip=True)
                break

        if not name:
            continue

        # PRICE
        price_selectors = [
            "span[data-testid='price-characteristic']",
            "span[data-automation-id='product-price']",
            "div[data-testid='price'] span",
            "span.price-characteristic",
            "span.visuallyhidden",
        ]

        price = None
        for sel in price_selectors:
            tag = product.select_one(sel)
            if tag:
                try:
                    price = float(tag.get_text(strip=True).replace("$", ""))
                    break
                except:
                    continue

        if price is None:
            continue

        # URL
        link_tag = product.select_one("a")
        url = "https://www.walmart.com" + link_tag["href"] if link_tag else ""

        # IMAGE
        img_tag = product.select_one("img")
        image = img_tag["src"] if img_tag else ""

        # PACKAGE SIZE
        amount, unit = extract_package_size(name)

        # BULK FILTER
        if is_bulk_item(name, amount, unit):
            continue

        return {
            "query": query,
            "name": name,
            "price": price,
            "url": url,
            "image": image,
            "package_amount": amount,
            "package_unit": unit
        }

    return None

# ---------------------------------------------------------
# PRICE LOOKUP ENGINE (REQUIRED BY cost_engine.py)
# ---------------------------------------------------------

def get_price_for_ingredient(conn, normalized_name):
    cursor = conn.cursor()

    # 1. Check DB cache
    cursor.execute("""
        SELECT price, package_amount, package_unit
        FROM walmart_products
        WHERE query = ?
        LIMIT 1
    """, (normalized_name,))

    row = cursor.fetchone()
    if row:
        return row[0], row[1], row[2]

    # 2. Scrape Walmart
    data = get_walmart_price(normalized_name)

    # 3. Save + return
    if data and data["price"]:
        cursor.execute("""
            INSERT INTO walmart_products (query, name, price, url, image, package_amount, package_unit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["query"],
            data["name"],
            data["price"],
            data["url"],
            data["image"],
            data["package_amount"],
            data["package_unit"]
        ))
        conn.commit()

        return data["price"], data["package_amount"], data["package_unit"]

    return None, None, None