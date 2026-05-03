import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def extract_price(text):
    m = re.search(r"\$([0-9]+(?:\.[0-9]{1,2})?)", text)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------
# SEARCH GOURMET GLATT
# ---------------------------------------------------------

def search_gourmet(query):
    search_url = f"https://www.gourmetglatt.com/search?q={query.replace(' ', '+')}"
    print(f"Search URL: {search_url}")

    res = requests.get(search_url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")

    # Product cards
    link = soup.select_one("a.product-item__title")
    if not link:
        print("No product found in search.")
        return None

    href = link.get("href")
    if href.startswith("/"):
        href = "https://www.gourmetglatt.com" + href

    print(f"Found product URL: {href}")
    return href


# ---------------------------------------------------------
# SCRAPE PRODUCT PAGE
# ---------------------------------------------------------

def scrape_gourmet_product(url):
    print(f"\nScraping product page:\n{url}\n")

    res = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(res.text, "html.parser")

    # Title
    title_tag = soup.select_one("h1.product__title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Price
    price_tag = soup.select_one("span.price-item--regular")
    price = extract_price(price_tag.get_text(strip=True)) if price_tag else None

    # Size
    size_tag = soup.select_one("span.product__subtitle")
    size = size_tag.get_text(strip=True) if size_tag else None

    print("Title:", title)
    print("Price:", price)
    print("Size:", size)


# ---------------------------------------------------------
# MAIN TEST
# ---------------------------------------------------------

if __name__ == "__main__":
    ingredient = "milk"
    product_url = search_gourmet(ingredient)

    if product_url:
        scrape_gourmet_product(product_url)