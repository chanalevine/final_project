import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.shopevergreenkosher.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.shopevergreenkosher.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}

def scrape_category(category_url):
    res = requests.get(category_url, headers=HEADERS)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    products = soup.select("div.product-grid-item")
    results = []

    for p in products:
        name_tag = p.select_one(".product-item-name, .product-title, a.product-item-link")
        price_tag = p.select_one(".price, .product-price")
        unit_tag = p.select_one(".product-unit, .size, .weight")
        img_tag = p.select_one("img")

        name = name_tag.get_text(strip=True) if name_tag else None
        price = price_tag.get_text(strip=True) if price_tag else None
        unit = unit_tag.get_text(strip=True) if unit_tag else None

        img = None
        if img_tag and img_tag.has_attr("src"):
            img = img_tag["src"]
            if img.startswith("/"):
                img = BASE_URL + img

        results.append({
            "name": name,
            "price": price,
            "unit": unit,
            "image": img
        })

    return results


category_url = "https://www.shopevergreenkosher.com/categories/78151/products"
data = scrape_category(category_url)

for item in data:
    print(item)