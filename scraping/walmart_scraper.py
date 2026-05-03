import requests
import sqlite3
from bs4 import BeautifulSoup
import re

# ---------------------------------------------------------
# PACKAGE SIZE EXTRACTION (IMPROVED)
# ---------------------------------------------------------

def extract_package_size(product_name):
    """
    Extracts package size from Walmart product name.
    Returns (amount, unit) or (None, None)
    """

    text = product_name.lower()

    patterns = [
        r"(\d+(\.\d+)?)\s*fl\s*oz",
        r"(\d+(\.\d+)?)\s*fl-oz",
        r"(\d+(\.\d+)?)\s*oz",
        r"(\d+(\.\d+)?)\s*-?oz",
        r"(\d+(\.\d+)?)\s*ounce",
        r"(\d+(\.\d+)?)\s*-?ounce",
        r"(\d+(\.\d+)?)\s*lb",
        r"(\d+(\.\d+)?)\s*lbs",
        r"(\d+(\.\d+)?)\s*pound",
        r"(\d+(\.\d+)?)\s*pack",
        r"(\d+(\.\d+)?)\s*ct",
        r"(\d+(\.\d+)?)\s*count",
    ]

    for p in patterns:
        match = re.search(p, text)
        if match:
            amount = float(match.group(1))

            # Extract unit from the regex pattern
            unit = re.findall(r"[a-z]+", p)[-1]
            return amount, unit

    return None, None


# ---------------------------------------------------------
# BULK FILTER
# ---------------------------------------------------------

def is_bulk_item(name, amount, unit):
    name = name.lower()

    bulk_keywords = [
        "bulk", "restaurant", "family size", "value size",
        "pack of 6", "pack of 12", "pack of 24",
        "5 lb", "4 lb", "3 lb", "2 lb"
    ]

    if any(b in name for b in bulk_keywords):
        return True

    # Reject huge containers
    if amount and unit:
        if ("oz" in unit and amount > 32):
            return True
        if ("lb" in unit and amount > 2):
            return True

    return False


# ---------------------------------------------------------
# WALMART SCRAPER
# ---------------------------------------------------------

def get_walmart_price(query):
    search_url = f"https://www.walmart.com/search?q={query.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }

    res = requests.get(search_url, headers=headers)
    if res.status_code != 200:
        print("Walmart request failed:", res.status_code)
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    products = soup.select("div[data-item-id]") or soup.select("div.search-result-gridview-item-wrapper")

    if not products:
        print("No Walmart products found")
        return None

    # Try each product until we find a non-bulk one
    for product in products:

        # NAME
        name_tag = (
            product.select_one("span.lh-title") or
            product.select_one("a[data-type='itemTitles'] span") or
            product.select_one("a span")
        )
        name = name_tag.get_text(strip=True) if name_tag else "Unknown"

        # PRICE
        price = None
        price_patterns = [
            "span[data-automation-id='product-price']",
            "span[data-testid='price']",
            "div[data-testid='price'] span",
            "span.price-characteristic",
            "span.visuallyhidden",
        ]

        for selector in price_patterns:
            tag = product.select_one(selector)
            if tag:
                text = tag.get_text(strip=True).replace("$", "").replace(",", "")
                try:
                    price = float(text)
                    break
                except:
                    continue

        # Fallback: extract price from name
        if price is None:
            match = re.search(r"\$([0-9]+\.[0-9]{2})", name)
            if match:
                price = float(match.group(1))

        if price is None:
            continue

        # IMAGE
        img_tag = product.select_one("img")
        image = img_tag["src"] if img_tag and "src" in img_tag.attrs else ""

        # URL
        link_tag = product.select_one("a")
        url = "https://www.walmart.com" + link_tag["href"] if link_tag else ""

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

def save_walmart_product(conn, data):
    cursor = conn.cursor()
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


# ---------------------------------------------------------
# PRICE LOOKUP ENGINE
# ---------------------------------------------------------

def get_price_for_ingredient(conn, normalized_name):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT price, package_amount, package_unit
        FROM walmart_products
        WHERE query = ?
        LIMIT 1
    """, (normalized_name,))
    
    row = cursor.fetchone()
    if row:
        price, amount, unit = row
        return price, amount, unit

    data = get_walmart_price(normalized_name)

    if data and data["price"]:
        save_walmart_product(conn, data)
        return data["price"], data["package_amount"], data["package_unit"]

    return None, None, None


# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------

if __name__ == "__main__":
    conn = sqlite3.connect("food_data.db")
    price, amount, unit = get_price_for_ingredient(conn, "garlic")
    print("Price:", price)
    print("Package:", amount, unit)
    conn.close()