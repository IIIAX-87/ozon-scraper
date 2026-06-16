"""Entry point: collect Ozon seller catalog via API and save to xlsx."""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from api_client import OzonAPIClient, OzonAPIError
from export_xlsx import export_api_products
from ozon_api_scraper import OzonAPIScraper


def main():
    load_dotenv()

    client_id = os.getenv("OZON_CLIENT_ID")
    api_key = os.getenv("OZON_API_KEY")
    output_file = os.getenv("OUTPUT_FILE", "ozon_products_api.xlsx")
    visibility = os.getenv("OZON_VISIBILITY", "ALL")
    max_products = int(os.getenv("MAX_PRODUCTS", "0"))
    batch_size = int(os.getenv("BATCH_SIZE", "500"))
    desc_workers = int(os.getenv("DESCRIPTION_WORKERS", "20"))

    if not client_id or not api_key:
        print(
            "ERROR: OZON_CLIENT_ID and OZON_API_KEY must be set in .env file.\n"
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    try:
        client = OzonAPIClient(client_id=client_id, api_key=api_key)
    except OzonAPIError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    scraper = OzonAPIScraper(
        client=client,
        visibility=visibility,
        max_products=max_products,
        batch_size=batch_size,
        desc_workers=desc_workers,
    )

    products = scraper.run()
    print(f"Collected {len(products)} products")

    if scraper.errors:
        print(f"API errors/warnings: {len(scraper.errors)}")

    path = export_api_products(products, output_file, errors=scraper.errors)
    print(f"Saved to: {path}")


if __name__ == "__main__":
    main()
