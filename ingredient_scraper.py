from bs4 import BeautifulSoup
import requests

url = "https://www.shoprite.com/sm/planning/rsid/3000/categories/produce-id-520676"
html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")

cards = soup.select('article[data-testid^="ProductCardWrapper"]')

for card in cards:
    # NAME
    name_el = card.select_one('h3[class^="ProductCardNameWrapper"]')
    name = name_el.get_text(strip=True) if name_el else None

    # PRICE
    price_el = card.select_one('div[class^="ProductPrice--"]')
    price = price_el.get_text(strip=True) if price_el else None

    # IMAGE
    img_el = card.select_one('img[class^="ProductImage--"]')
    image = img_el.get("src") if img_el else None

    # SIZE (optional)
    size_el = card.select_one('[class^="ProductCardSize"]')
    size = size_el.get_text(strip=True) if size_el else None

    print(name, price, size, image)
    print("hi")