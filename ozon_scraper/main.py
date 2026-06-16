"""Entry point: scrape Ozon seller catalog and save to xlsx."""
from __future__ import annotations

import os

from dotenv import load_dotenv

from export_xlsx import export_products
from scraper import OzonScraper


def main():
    load_dotenv()

    seller_url = os.getenv("OZON_SELLER_URL")
    output_file = os.getenv("OUTPUT_FILE", "ozon_products.xlsx")
    max_products = int(os.getenv("MAX_PRODUCTS", "100"))
    headless = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")

    scraper = OzonScraper(
        seller_url=seller_url,
        headless=headless,
        max_products=max_products,
    )

    products = scraper.run()
    print(f"Collected {len(products)} products")

    if products:
        path = export_products(products, output_file)
        print(f"Saved to: {path}")
    else:
        print("No products found. Nothing to save.")
        # Still create an empty xlsx with headers
        path = export_products([], output_file)
        print(f"Empty result file saved to: {path}")


if __name__ == "__main__":
    main()
