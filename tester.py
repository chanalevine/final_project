import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.shopevergreenkosher.com"

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
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.shopevergreenkosher.com/",
}

def scrape_evergreen(url):
    session = requests.Session()
    session.headers.update(HEADERS)

    # Warm-up request for cookies
    session.get(BASE_URL)

    res = session.get(url)
    print("Status:", res.status_code)

    soup = BeautifulSoup(res.text, "html.parser")

    # Evergreen uses <sp-product> custom elements
    products = soup.select("sp-product")
    results = []

    for p in products:
        results.append({
            "name": p.get("product-name"),
            "price": p.get("price"),
            "unit": p.get("unit"),
            "image": p.get("image")
        })

    return results


category_url = "https://www.shopevergreenkosher.com/categories/78151/products"
print(scrape_evergreen(category_url))