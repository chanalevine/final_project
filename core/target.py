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

    bulk_words = ["bulk", "family size", "value size", "restaurant"]
    if any(b in name for b in bulk_words):
        return True

    if amount and unit:
        if "oz" in unit and amount > 32:
            return True
        if "lb" in unit and amount > 2:
            return True

    return False


# ---------------------------------------------------------
# TARGET SCRAPER
# ---------------------------------------------------------

def get_target_price(query):
    url = f"https://www.target.com/s?searchTerm={query.replace(' ', '+')}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    time.sleep(random.uniform(1.0, 2.0))

    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("Target request failed:", res.status_code)
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    # Target product tiles
    products = soup.select("div[data-test='product-card']")

    if not products:
        print("No Target products found")
        return None

    for product in products:

        # NAME
        name_tag = product.select_one("a[data-test='product-title']")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)

        # PRICE
        price_tag = product.select_one("span[data-test='current-price']")
        if not price_tag:
            continue

        price_text = price_tag.get_text(strip=True).replace("$", "")
        try:
            price = float(price_text)
        except:
            continue

        # URL
        link_tag = product.select_one("a[data-test='product-title']")
        url = "https://www.target.com" + link_tag["href"] if link_tag else ""

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
# SAVE TO DATABASE
# ---------------------------------------------------------

def save_target_product(conn, data):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO target_products (query, name, price, url, image, package_amount, package_unit)
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


# ---------------------------------------------------------
# PRICE LOOKUP ENGINE (same interface as Walmart)
# ---------------------------------------------------------

def get_price_for_ingredient(conn, normalized_name):
    cursor = conn.cursor()

    # 1. Check DB cache
    cursor.execute("""
        SELECT price, package_amount, package_unit
        FROM target_products
        WHERE query = ?
        LIMIT 1
    """, (normalized_name,))

    row = cursor.fetchone()
    if row:
        return row[0], row[1], row[2]

    # 2. Scrape Target
    data = get_target_price(normalized_name)

    # 3. Save + return
    if data and data["price"]:
        save_target_product(conn, data)
        return data["price"], data["package_amount"], data["package_unit"]

    return None, None, None