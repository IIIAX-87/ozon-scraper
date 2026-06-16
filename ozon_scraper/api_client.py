"""Synchronous HTTP client for Ozon Seller API with connection pooling."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests


class OzonAPIError(Exception):
    def __init__(self, message: str, status: int = 0, response: Any = None):
        super().__init__(message)
        self.status = status
        self.response = response


class OzonAPIClient:
    """Low-level client with retries and rate limiting."""

    BASE_URL = "https://api-seller.ozon.ru"

    def __init__(
        self,
        client_id: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        min_interval: float = 0.025,
    ):
        self.client_id = client_id or os.getenv("OZON_CLIENT_ID", "")
        self.api_key = api_key or os.getenv("OZON_API_KEY", "")
        if not self.client_id or not self.api_key:
            raise OzonAPIError(
                "OZON_CLIENT_ID and OZON_API_KEY must be set in environment or .env"
            )

        self.max_retries = max_retries
        self.min_interval = min_interval
        self._last_request_time: Optional[float] = None
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Client-Id": self.client_id,
                "Api-Key": self.api_key,
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.BASE_URL}{path}"

        # Rate limiting
        now = time.time()
        if self._last_request_time is not None:
            elapsed = now - self._last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)

        for attempt in range(self.max_retries):
            try:
                resp = self._session.request(
                    method, url, data=json.dumps(payload, ensure_ascii=False).encode("utf-8")
                )
                self._last_request_time = time.time()

                if resp.status_code == 429:
                    wait = 2 ** attempt + 0.5
                    time.sleep(wait)
                    continue

                try:
                    data = resp.json() if resp.text else {}
                except json.JSONDecodeError as exc:
                    raise OzonAPIError(
                        f"Invalid JSON from {path}: {resp.text[:200]}",
                        status=resp.status_code,
                    ) from exc

                if resp.status_code >= 400:
                    raise OzonAPIError(
                        f"Ozon API error {resp.status_code} on {path}: {data}",
                        status=resp.status_code,
                        response=data,
                    )

                return data
            except requests.RequestException as exc:
                if attempt == self.max_retries - 1:
                    raise OzonAPIError(f"Network error on {path}: {exc}") from exc
                time.sleep(2 ** attempt)

        raise OzonAPIError(f"Max retries exceeded for {path}")

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", path, payload)

    def get_product_list(
        self, visibility: str = "ALL", limit: int = 1000, last_id: str = ""
    ) -> Dict[str, Any]:
        payload = {"filter": {"visibility": visibility}, "limit": limit}
        if last_id:
            payload["last_id"] = last_id
        return self.post("/v3/product/list", payload)

    def get_product_info_attributes(
        self,
        offer_ids: Optional[List[str]] = None,
        product_ids: Optional[List[int]] = None,
        limit: int = 1000,
        last_id: str = "",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"limit": limit}
        filt: Dict[str, Any] = {}
        if offer_ids:
            filt["offer_id"] = offer_ids
        if product_ids:
            filt["product_id"] = product_ids
        if filt:
            payload["filter"] = filt
        if last_id:
            payload["last_id"] = last_id
        return self.post("/v4/product/info/attributes", payload)

    def get_product_description(
        self,
        product_id: int,
        offer_id: str,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"product_id": product_id}
        if offer_id:
            payload["offer_id"] = offer_id
        return self.post("/v1/product/info/description", payload)

    def get_product_prices(
        self,
        offer_ids: Optional[List[str]] = None,
        product_ids: Optional[List[int]] = None,
        cursor: str = "",
        limit: int = 1000,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"limit": limit}
        filt: Dict[str, Any] = {}
        if offer_ids:
            filt["offer_id"] = offer_ids
        if product_ids:
            filt["product_id"] = product_ids
        if filt:
            payload["filter"] = filt
        if cursor:
            payload["cursor"] = cursor
        return self.post("/v5/product/info/prices", payload)

    def get_product_pictures(
        self,
        offer_ids: Optional[List[str]] = None,
        product_ids: Optional[List[int]] = None,
        sku: Optional[List[int]] = None,
        limit: int = 1000,
        last_id: str = "",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"limit": limit}
        filt: Dict[str, Any] = {}
        if offer_ids:
            filt["offer_id"] = offer_ids
        if product_ids:
            filt["product_id"] = product_ids
        if sku:
            filt["sku"] = sku
        if filt:
            payload["filter"] = filt
        if last_id:
            payload["last_id"] = last_id
        return self.post("/v2/product/pictures/info", payload)
