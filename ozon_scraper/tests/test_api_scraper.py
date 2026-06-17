"""Unit tests for Ozon API scraper with mocked HTTP responses."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client import OzonAPIClient
from export_xlsx import export_api_products
from ozon_api_scraper import OzonAPIScraper


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data
        self.text = json.dumps(json_data, ensure_ascii=False)

    def json(self):
        return self._json


class TestOzonAPIScraper(unittest.TestCase):
    def setUp(self):
        self.client = OzonAPIClient(client_id="123", api_key="secret")

    def _mock_request(self, url: str, payload: dict) -> dict:
        path = url.replace("https://api-seller.ozon.ru", "")

        if path == "/v3/product/list":
            return {
                "result": {
                    "items": [
                        {"product_id": 1001, "offer_id": "SKU-001"},
                        {"product_id": 1002, "offer_id": "SKU-002"},
                    ],
                    "last_id": "",
                    "total": 2,
                }
            }

        if path == "/v4/product/info/attributes":
            offer_ids = payload.get("filter", {}).get("offer_id", [])
            items = []
            for offer_id in offer_ids:
                pid = 1001 if offer_id == "SKU-001" else 1002
                items.append(
                    {
                        "id": pid,
                        "offer_id": offer_id,
                        "name": f"Product {offer_id}",
                        "barcode": f"BAR-{offer_id}",
                        "category_id": 10,
                        "description_category_id": 11,
                        "type_id": 20,
                        "height": 10,
                        "depth": 20,
                        "width": 30,
                        "dimension_unit": "mm",
                        "weight": 100,
                        "weight_unit": "g",
                        "volume_weight": 120,
                        "images": [
                            f"https://cdn.ozone.ru/{offer_id}-1.jpg",
                            {"file_name": f"https://cdn.ozone.ru/{offer_id}-2.jpg", "index": 1},
                        ],
                        "attributes": [
                            {
                                "attribute_id": 1,
                                "complex_id": 0,
                                "values": [{"dictionary_value_id": 0, "value": "Red"}],
                            }
                        ],
                        "complex_attributes": [],
                    }
                )
            return {"result": items}

        if path == "/v5/product/info/prices":
            product_ids = payload.get("filter", {}).get("product_id", [])
            items = []
            for pid in product_ids:
                offer_id = "SKU-001" if pid == 1001 else "SKU-002"
                items.append(
                    {
                        "product_id": pid,
                        "offer_id": offer_id,
                        "price": {
                            "price": 1000 + pid,
                            "old_price": 1200 + pid,
                            "retail_price": 900 + pid,
                            "marketing_price": 950 + pid,
                            "min_price": 800 + pid,
                            "currency_code": "RUB",
                            "vat": 20,
                        },
                    }
                )
            return {"result": {"items": items, "cursor": "", "total": len(items)}}

        if path == "/v2/product/pictures/info":
            product_ids = payload.get("filter", {}).get("product_id", [])
            items = []
            for pid in product_ids:
                items.append(
                    {
                        "product_id": pid,
                        "primary_photo": [f"https://cdn.ozone.ru/{pid}-primary.jpg"],
                        "photo": [f"https://cdn.ozone.ru/{pid}-1.jpg"],
                    }
                )
            return {"items": items}

        if path == "/v1/product/info/description":
            pid = payload.get("product_id")
            return {
                "result": {
                    "id": pid,
                    "offer_id": payload.get("offer_id"),
                    "name": "Product",
                    "description": f"Description for {pid}",
                }
            }

        return {}

    def test_full_scrape(self):
        with patch.object(
            self.client._session, "request", side_effect=lambda method, url, **kwargs: FakeResponse(
                200, self._mock_request(url, json.loads(kwargs.get("data", "{}")))
            )
        ):
            scraper = OzonAPIScraper(client=self.client, batch_size=1000)
            products = scraper.run()

        self.assertEqual(len(products), 2)

        product = next(p for p in products if p.product_id == 1001)
        self.assertEqual(product.offer_id, "SKU-001")
        self.assertEqual(product.name, "Product SKU-001")
        self.assertEqual(product.barcode, "BAR-SKU-001")
        self.assertEqual(product.price, 2001.0)
        self.assertEqual(product.old_price, 2201.0)
        self.assertEqual(product.currency_code, "RUB")
        self.assertTrue(product.primary_image.endswith("1001-primary.jpg"))
        self.assertEqual(len(product.images), 2)
        self.assertIn("Description for 1001", product.description)
        self.assertEqual(len(product.attributes), 1)

    def test_export_api_products(self):
        with patch.object(
            self.client._session, "request", side_effect=lambda method, url, **kwargs: FakeResponse(
                200, self._mock_request(url, json.loads(kwargs.get("data", "{}")))
            )
        ):
            scraper = OzonAPIScraper(client=self.client, batch_size=1000)
            products = scraper.run()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.xlsx")
            result = export_api_products(products, path)
            self.assertTrue(os.path.exists(result))


if __name__ == "__main__":
    unittest.main()
