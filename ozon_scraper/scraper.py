"""Ozon seller catalog scraper.

Uses Playwright to load a seller page, scroll through the product grid,
extract product cards and save results via openpyxl.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, sync_playwright, TimeoutError as PWTimeout


@dataclass
class Product:
    name: str = ""
    price: int = 0
    old_price: Optional[int] = None
    discount: str = ""
    rating: float = 0.0
    reviews: int = 0
    url: str = ""
    image: str = ""
    raw: dict = field(default_factory=dict)


class OzonScraper:
    def __init__(
        self,
        seller_url: Optional[str] = None,
        headless: bool = True,
        max_products: int = 100,
        timeout: int = 60_000,
    ):
        self.seller_url = seller_url or os.getenv(
            "OZON_SELLER_URL",
            "https://www.ozon.ru/seller/swikki-1313863/products/",
        )
        self.headless = headless
        self.max_products = max_products
        self.timeout = timeout
        self.products: List[Product] = []

    # ------------------------------------------------------------------
    # Browser helpers
    # ------------------------------------------------------------------
    def _launch_context(self, p):
        browser = p.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
                ),
            },
        )
        # Hide webdriver / automation flags
        context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            window.chrome = { runtime: {} };
        """
        )
        return browser, context

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------
    def _extract_price(self, text: str) -> int:
        digits = re.sub(r"[^\d]", "", text or "")
        return int(digits) if digits else 0

    def _clean_name(self, text: str) -> str:
        return " ".join((text or "").split())

    def _parse_product_card(self, card) -> Optional[Product]:
        """Try several common Ozon selectors."""
        # Title
        name = ""
        for sel in [
            'span[data-testid="tile-name"]',
            'a[data-testid="tile-name"]',
            '.tsBody500Medium',
            '[class*="tsBody500"]',
            'span[class*="name"]',
        ]:
            el = card.query_selector(sel)
            if el:
                name = self._clean_name(el.inner_text())
                if name:
                    break

        # Link
        url = ""
        link_el = card.query_selector("a")
        if link_el:
            href = link_el.get_attribute("href") or ""
            url = urljoin("https://www.ozon.ru", href)

        # Image
        image = ""
        for sel in ["img", 'div[class*="image"] img']:
            img = card.query_selector(sel)
            if img:
                image = (
                    img.get_attribute("src")
                    or img.get_attribute("data-src")
                    or ""
                )
                if image:
                    break

        # Price
        price = 0
        for sel in [
            'span[data-testid="price"]',
            'span[class*="price"]',
            '.tsHeadline500Medium',
            '.tsBodyControl500Medium',
        ]:
            el = card.query_selector(sel)
            if el:
                price = self._extract_price(el.inner_text())
                if price:
                    break

        # Old price / discount
        old_price = None
        discount = ""
        for sel in [
            'span[data-testid="old-price"]',
            'span[class*="old-price"]',
            'span[class*="strike"]',
        ]:
            el = card.query_selector(sel)
            if el:
                old_price = self._extract_price(el.inner_text())
                break

        # Rating
        rating = 0.0
        reviews = 0
        for sel in [
            'span[data-testid="rating"]',
            'span[class*="rating"]',
            'div[class*="rating"]',
        ]:
            el = card.query_selector(sel)
            if el:
                text = el.inner_text().replace(",", ".")
                m = re.search(r"(\d+(?:\.\d+)?)", text)
                if m:
                    rating = float(m.group(1))
                break

        if not name and not url:
            return None

        return Product(
            name=name,
            price=price,
            old_price=old_price,
            discount=discount,
            rating=rating,
            reviews=reviews,
            url=url,
            image=image,
        )

    def _scroll_and_collect(self, page: Page):
        """Scroll page and collect unique product cards."""
        seen_urls = set()
        last_count = 0
        stalled = 0
        max_stalls = 6

        while len(self.products) < self.max_products and stalled < max_stalls:
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)

            # Query product cards via multiple selectors
            cards = page.query_selector_all(
                '[data-widget="searchResultsV2"] .tile-root, '
                '.widget-search-result-container [data-testid="tile-root"], '
                '[data-testid="tile-root"], '
                '.tile-root'
            )

            for card in cards:
                try:
                    product = self._parse_product_card(card)
                except Exception:
                    continue
                if not product:
                    continue
                key = product.url or product.name
                if key and key not in seen_urls:
                    seen_urls.add(key)
                    self.products.append(product)
                    if len(self.products) >= self.max_products:
                        break

            if len(self.products) == last_count:
                stalled += 1
            else:
                stalled = 0
            last_count = len(self.products)

            # Try clicking "Next" if available
            try:
                next_btn = page.query_selector(
                    'a[aria-label="Следующая страница"], '
                    'a[data-testid="next-page"], '
                    'div[class*="pagination"] a:last-child'
                )
                if next_btn and stalled >= 2:
                    next_btn.click()
                    page.wait_for_load_state("networkidle", timeout=10_000)
                    stalled = 0
            except Exception:
                pass

    def _try_api(self, page: Page) -> List[Product]:
        """Attempt to read ozon state / api from page scripts (best-effort)."""
        try:
            data = page.evaluate(
                """() => {
                    const scripts = Array.from(document.querySelectorAll('script'));
                    for (const s of scripts) {
                        if (s.textContent && s.textContent.includes('__NUXT__')) {
                            return s.textContent.slice(0, 50000);
                        }
                    }
                    return '';
                }"""
            )
            # Ozon sometimes embeds __NUXT__ data; quick heuristic parse
            if data:
                # Look for product-like JSON blocks
                matches = re.findall(
                    r'"name"[:\s]*"([^"]+)".*?"price"[:\s]*(\d+)', data
                )
                # Not reliable, return empty
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> List[Product]:
        with sync_playwright() as p:
            browser, context = self._launch_context(p)
            page = context.new_page()
            try:
                page.goto(self.seller_url, timeout=self.timeout)
                page.wait_for_load_state("networkidle", timeout=self.timeout)
                # Additional wait for dynamic content
                time.sleep(3)

                title = page.title()
                print(f"Loaded: {page.url}")
                print(f"Title: {title}")

                if "Похоже, нет соединения" in title or "робот" in title.lower():
                    print("WARNING: Ozon returned antibot/challenge page.")
                    # Save HTML for diagnostics
                    html = page.content()
                    with open("/tmp/ozon_blocked.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print("Saved blocked page to /tmp/ozon_blocked.html")
                    return self.products

                self._scroll_and_collect(page)
            except PWTimeout as e:
                print(f"Timeout error: {e}")
            except Exception as e:
                print(f"Error during scraping: {e}")
            finally:
                context.close()
                browser.close()

        return self.products
