"""Collect all Ozon seller products and details via official Seller API."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from api_client import OzonAPIClient, OzonAPIError


@dataclass
class ProductData:
    product_id: Optional[int] = None
    offer_id: str = ""
    sku: Optional[int] = None
    name: str = ""
    barcode: str = ""
    category_id: Optional[int] = None
    description_category_id: Optional[int] = None
    type_id: Optional[int] = None
    description: str = ""
    price: Optional[float] = None
    old_price: Optional[float] = None
    retail_price: Optional[float] = None
    marketing_price: Optional[float] = None
    min_price: Optional[float] = None
    currency_code: str = ""
    vat: Optional[float] = None
    status: str = ""
    visibility: str = ""
    archived: bool = False
    discounted: bool = False
    height: Optional[int] = None
    depth: Optional[int] = None
    width: Optional[int] = None
    dimension_unit: str = ""
    weight: Optional[float] = None
    weight_unit: str = ""
    volume_weight: Optional[float] = None
    primary_image: str = ""
    images: List[str] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    complex_attributes: List[Dict[str, Any]] = field(default_factory=list)
    raw_attributes: Dict[str, Any] = field(default_factory=dict)
    raw_prices: Dict[str, Any] = field(default_factory=dict)
    raw_pictures: Dict[str, Any] = field(default_factory=dict)


class OzonAPIScraper:
    def __init__(
        self,
        client: OzonAPIClient,
        visibility: str = "ALL",
        max_products: int = 0,
        batch_size: int = 500,
        desc_workers: int = 20,
    ):
        self.client = client
        self.visibility = visibility
        self.max_products = max_products
        self.batch_size = min(batch_size, 1000)
        self.desc_workers = desc_workers
        self.products: Dict[int, ProductData] = {}
        self.errors: List[str] = []

    # ------------------------------------------------------------------
    # Public orchestration
    # ------------------------------------------------------------------
    def run(self) -> List[ProductData]:
        self._fetch_product_list()
        if not self.products:
            return []

        product_ids = list(self.products.keys())
        offer_ids = [p.offer_id for p in self.products.values() if p.offer_id]

        self._fetch_attributes_for_offer_ids(offer_ids)
        self._fetch_prices_for_product_ids(product_ids)
        self._fetch_pictures_for_product_ids(product_ids)
        self._fetch_descriptions(product_ids)

        return list(self.products.values())

    # ------------------------------------------------------------------
    # 1. Product list
    # ------------------------------------------------------------------
    def _fetch_product_list(self) -> None:
        last_id = ""
        collected = 0
        while True:
            try:
                resp = self.client.get_product_list(
                    visibility=self.visibility, last_id=last_id
                )
            except OzonAPIError as exc:
                self.errors.append(f"product_list failed: {exc}")
                break

            result = resp.get("result", {}) or {}
            items = result.get("items", []) or []
            if not items:
                break

            for item in items:
                product_id = item.get("product_id")
                offer_id = item.get("offer_id", "")
                if not product_id:
                    continue

                product = ProductData(
                    product_id=product_id,
                    offer_id=str(offer_id) if offer_id is not None else "",
                    sku=item.get("sku"),
                )
                self.products[product_id] = product
                collected += 1

                if self.max_products and collected >= self.max_products:
                    return

            last_id = result.get("last_id", "")
            if not last_id:
                break

    # ------------------------------------------------------------------
    # 2. Attributes (contains dimensions, images, name, barcode, attributes)
    # ------------------------------------------------------------------
    def _fetch_attributes_for_offer_ids(self, offer_ids: List[str]) -> None:
        chunks = self._chunks(offer_ids, self.batch_size)
        for chunk in chunks:
            self._fetch_attributes_chunk(chunk)

    def _fetch_attributes_chunk(self, offer_ids: List[str]) -> None:
        last_id = ""
        while True:
            try:
                resp = self.client.get_product_info_attributes(
                    offer_ids=offer_ids, limit=self.batch_size, last_id=last_id
                )
            except OzonAPIError as exc:
                self.errors.append(f"attributes chunk failed: {exc}")
                return

            result = resp.get("result", []) or []
            for item in result:
                self._apply_attributes(item)

            last_id = resp.get("last_id", "")
            if not last_id or not result:
                break

    def _apply_attributes(self, item: Dict[str, Any]) -> None:
        product_id = item.get("id") or item.get("product_id")
        if not product_id or product_id not in self.products:
            return

        product = self.products[product_id]
        product.raw_attributes = item
        product.name = item.get("name", "") or product.name
        product.offer_id = str(item.get("offer_id", product.offer_id))
        product.barcode = item.get("barcode", "") or product.barcode
        product.category_id = item.get("category_id") or product.category_id
        product.description_category_id = (
            item.get("description_category_id") or product.description_category_id
        )
        product.type_id = item.get("type_id") or product.type_id
        product.height = item.get("height") or product.height
        product.depth = item.get("depth") or product.depth
        product.width = item.get("width") or product.width
        product.dimension_unit = item.get("dimension_unit", "") or product.dimension_unit
        product.weight = item.get("weight") or product.weight
        product.weight_unit = item.get("weight_unit", "") or product.weight_unit
        product.volume_weight = item.get("volume_weight") or product.volume_weight

        images = item.get("images", []) or []
        normalized_images: List[str] = []
        for img in images:
            if isinstance(img, str):
                normalized_images.append(img)
            elif isinstance(img, dict):
                file_name = img.get("file_name")
                if file_name:
                    normalized_images.append(file_name)
        product.images = normalized_images
        if not product.primary_image and product.images:
            product.primary_image = product.images[0]

        product.attributes = item.get("attributes", []) or []
        product.complex_attributes = item.get("complex_attributes", []) or []

    # ------------------------------------------------------------------
    # 3. Prices
    # ------------------------------------------------------------------
    def _fetch_prices_for_product_ids(self, product_ids: List[int]) -> None:
        chunks = self._chunks(product_ids, self.batch_size)
        for chunk in chunks:
            self._fetch_prices_chunk(chunk)

    def _fetch_prices_chunk(self, product_ids: List[int]) -> None:
        cursor = ""
        while True:
            try:
                resp = self.client.get_product_prices(
                    product_ids=product_ids, limit=self.batch_size, cursor=cursor
                )
            except OzonAPIError as exc:
                self.errors.append(f"prices chunk failed: {exc}")
                return

            result = resp.get("result", {}) or {}
            items = result.get("items", []) or []
            for item in items:
                self._apply_prices(item)

            cursor = result.get("cursor", "")
            if not cursor or not items:
                break

    def _apply_prices(self, item: Dict[str, Any]) -> None:
        product_id = item.get("product_id")
        offer_id = item.get("offer_id")

        product = None
        if product_id and product_id in self.products:
            product = self.products[product_id]
        elif offer_id:
            product = next(
                (p for p in self.products.values() if p.offer_id == str(offer_id)), None
            )

        if not product:
            self.errors.append(
                f"price item not matched: product_id={product_id}, offer_id={offer_id}"
            )
            return

        product.raw_prices = item
        price_info = item.get("price", {}) or {}
        product.price = self._to_float(price_info.get("price"))
        product.old_price = self._to_float(price_info.get("old_price"))
        product.retail_price = self._to_float(price_info.get("retail_price"))
        product.marketing_price = self._to_float(price_info.get("marketing_price"))
        product.min_price = self._to_float(price_info.get("min_price"))
        product.currency_code = price_info.get("currency_code", "") or product.currency_code
        product.vat = self._to_float(price_info.get("vat"))

    # ------------------------------------------------------------------
    # 4. Pictures (primary photo fallback)
    # ------------------------------------------------------------------
    def _fetch_pictures_for_product_ids(self, product_ids: List[int]) -> None:
        chunks = self._chunks(product_ids, self.batch_size)
        for chunk in chunks:
            self._fetch_pictures_chunk(chunk)

    def _fetch_pictures_chunk(self, product_ids: List[int]) -> None:
        last_id = ""
        while True:
            try:
                resp = self.client.get_product_pictures(
                    product_ids=product_ids, limit=self.batch_size, last_id=last_id
                )
            except OzonAPIError as exc:
                self.errors.append(f"pictures chunk failed: {exc}")
                return

            items = resp.get("items", []) or resp.get("result", {}).get("items", []) or []
            for item in items:
                self._apply_pictures(item)

            last_id = resp.get("last_id", "")
            if not last_id or not items:
                break

    def _apply_pictures(self, item: Dict[str, Any]) -> None:
        product_id = item.get("product_id")
        if not product_id or product_id not in self.products:
            return

        product = self.products[product_id]
        product.raw_pictures = item
        primary = item.get("primary_photo", []) or []
        photos = item.get("photo", []) or []
        if primary:
            product.primary_image = primary[0]
        elif photos and not product.primary_image:
            product.primary_image = photos[0]

    # ------------------------------------------------------------------
    # 5. Descriptions (one per product)
    # ------------------------------------------------------------------
    def _fetch_descriptions(self, product_ids: List[int]) -> None:
        def fetch_one(pid: int) -> tuple[int, Optional[str]]:
            product = self.products.get(pid)
            if not product:
                return pid, None
            try:
                resp = self.client.get_product_description(
                    product_id=pid,
                    offer_id=product.offer_id,
                )
                result = resp.get("result", {}) or {}
                return pid, result.get("description", "")
            except OzonAPIError as exc:
                self.errors.append(f"description {pid} failed: {exc}")
                return pid, None

        with ThreadPoolExecutor(max_workers=self.desc_workers) as executor:
            futures = {executor.submit(fetch_one, pid): pid for pid in product_ids}
            for future in as_completed(futures):
                pid, description = future.result()
                if description is not None and pid in self.products:
                    self.products[pid].description = description

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _chunks(lst: List[Any], size: int) -> List[List[Any]]:
        return [lst[i : i + size] for i in range(0, len(lst), size)]

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
