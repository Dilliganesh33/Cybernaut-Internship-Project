# To install the module, run this in your terminal or command prompt:
# pip install beautifulsoup4

from bs4 import BeautifulSoup
import requests
import pandas as pd
import time

# Amazon search URL
URL = "https://www.amazon.com/s?k=home+appliances"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.5"
}

def get_page(url):
    """Fetch page content safely"""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

def extract_product_info(item):
    """Extract product details from search result block"""
    title, price, rating, link = None, "Not Listed", None, None

    # ✅ Title (check multiple locations)
    title_tag = (
        item.find("span", class_="a-size-medium a-color-base a-text-normal")
        or item.find("span", class_="a-size-base-plus a-color-base a-text-normal")
        or item.find("h2")  # fallback to h2 tag
    )
    if title_tag:
        # If inside <a>, extract text
        if title_tag.find("a"):
            title = title_tag.find("a").get_text(strip=True)
        else:
            title = title_tag.get_text(strip=True)

    # ✅ Product link
    link_tag = item.find("a", class_="a-link-normal s-no-outline")
    if not link_tag:
        link_tag = item.find("a", class_="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal")
    if link_tag and "href" in link_tag.attrs:
        link = "https://www.amazon.com" + link_tag["href"]

    # ✅ Price
    price_tag = item.find("span", class_="a-offscreen")
    if price_tag:
        price = price_tag.get_text(strip=True)

    # ✅ Rating
    rating_tag = item.find("span", class_="a-icon-alt")
    if rating_tag:
        rating = rating_tag.get_text(strip=True)

    return {"title": title, "price": price, "rating": rating, "url": link}

def scrape_amazon(url):
    """Main scraping function"""
    page_content = get_page(url)
    if not page_content:
        return []

    soup = BeautifulSoup(page_content, "html.parser")
    items = soup.find_all("div", {"data-component-type": "s-search-result"})

    results = []
    for item in items:
        product_info = extract_product_info(item)
        if product_info["title"]:  # Only keep if title exists
            results.append(product_info)

    return results

if __name__ == "__main__":
    products = scrape_amazon(URL)
    df = pd.DataFrame(products)

    if not df.empty:
        df.to_csv("amazon_products.csv", index=False, encoding="utf-8")
        print(f"✅ {len(products)} products saved to amazon_products.csv")
    else:
        print("⚠️ No products found. Try changing URL or check if Amazon blocked the request.")
