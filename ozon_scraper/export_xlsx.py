"""Export API-collected Ozon products to an .xlsx file."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


def _set_header_row(ws: Worksheet, headers: List[str]) -> None:
    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(color="FFFFFF", bold=True)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font


def _autofit_columns(ws: Worksheet, headers: List[str], rows: int) -> None:
    for col in range(1, len(headers) + 1):
        max_length = len(headers[col - 1])
        for row in range(2, rows + 2):
            value = ws.cell(row=row, column=col).value
            if value is not None:
                max_length = max(max_length, len(str(value)))
        ws.column_dimensions[get_column_letter(col)].width = min(max_length + 2, 80)


def _collect_attribute_rows(
    products: List[Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for product in products:
        pid = product.product_id
        offer_id = product.offer_id

        def add_attr(attr: Dict[str, Any], complex_idx: Optional[int] = None) -> None:
            attr_id = attr.get("attribute_id")
            complex_id = attr.get("complex_id")
            for value in attr.get("values", []) or []:
                rows.append(
                    {
                        "product_id": pid,
                        "offer_id": offer_id,
                        "attribute_id": attr_id,
                        "complex_id": complex_id,
                        "complex_index": complex_idx,
                        "dictionary_value_id": value.get("dictionary_value_id"),
                        "value": value.get("value"),
                    }
                )

        for attr in product.attributes:
            add_attr(attr)

        for cidx, complex_attr in enumerate(product.complex_attributes or []):
            for attr in complex_attr.get("attributes", []) or []:
                add_attr(attr, complex_idx=cidx)

    return rows


def _collect_image_rows(products: List[Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for product in products:
        for idx, url in enumerate(product.images or []):
            rows.append(
                {
                    "product_id": product.product_id,
                    "offer_id": product.offer_id,
                    "index": idx,
                    "url": url,
                    "is_primary": idx == 0,
                }
            )
    return rows


def export_api_products(
    products: List[Any],
    output_path: Optional[str] = None,
    errors: Optional[List[str]] = None,
) -> str:
    output_path = output_path or os.getenv("OUTPUT_FILE", "ozon_products_api.xlsx")

    wb = Workbook()

    # ------------------------------------------------------------------
    # Sheet: Товары
    # ------------------------------------------------------------------
    ws_products = wb.active
    if ws_products is None:
        raise RuntimeError("Failed to create workbook sheet")
    ws_products.title = "Товары"

    product_headers = [
        "product_id",
        "offer_id",
        "sku",
        "name",
        "barcode",
        "category_id",
        "description_category_id",
        "type_id",
        "description",
        "price",
        "old_price",
        "retail_price",
        "marketing_price",
        "min_price",
        "currency_code",
        "vat",
        "status",
        "visibility",
        "archived",
        "discounted",
        "height",
        "depth",
        "width",
        "dimension_unit",
        "weight",
        "weight_unit",
        "volume_weight",
        "primary_image",
        "images_count",
        "attributes_count",
    ]
    _set_header_row(ws_products, product_headers)

    for row, product in enumerate(products, 2):
        ws_products.cell(row=row, column=1, value=product.product_id)
        ws_products.cell(row=row, column=2, value=product.offer_id)
        ws_products.cell(row=row, column=3, value=product.sku)
        ws_products.cell(row=row, column=4, value=product.name)
        ws_products.cell(row=row, column=5, value=product.barcode)
        ws_products.cell(row=row, column=6, value=product.category_id)
        ws_products.cell(row=row, column=7, value=product.description_category_id)
        ws_products.cell(row=row, column=8, value=product.type_id)
        ws_products.cell(row=row, column=9, value=product.description)
        ws_products.cell(row=row, column=10, value=product.price)
        ws_products.cell(row=row, column=11, value=product.old_price)
        ws_products.cell(row=row, column=12, value=product.retail_price)
        ws_products.cell(row=row, column=13, value=product.marketing_price)
        ws_products.cell(row=row, column=14, value=product.min_price)
        ws_products.cell(row=row, column=15, value=product.currency_code)
        ws_products.cell(row=row, column=16, value=product.vat)
        ws_products.cell(row=row, column=17, value=product.status)
        ws_products.cell(row=row, column=18, value=product.visibility)
        ws_products.cell(row=row, column=19, value=product.archived)
        ws_products.cell(row=row, column=20, value=product.discounted)
        ws_products.cell(row=row, column=21, value=product.height)
        ws_products.cell(row=row, column=22, value=product.depth)
        ws_products.cell(row=row, column=23, value=product.width)
        ws_products.cell(row=row, column=24, value=product.dimension_unit)
        ws_products.cell(row=row, column=25, value=product.weight)
        ws_products.cell(row=row, column=26, value=product.weight_unit)
        ws_products.cell(row=row, column=27, value=product.volume_weight)
        ws_products.cell(row=row, column=28, value=product.primary_image)
        ws_products.cell(row=row, column=29, value=len(product.images or []))
        ws_products.cell(
            row=row,
            column=30,
            value=len(product.attributes or []) + len(product.complex_attributes or []),
        )

    _autofit_columns(ws_products, product_headers, len(products))

    # ------------------------------------------------------------------
    # Sheet: Атрибуты
    # ------------------------------------------------------------------
    ws_attrs = wb.create_sheet(title="Атрибуты")
    attr_rows = _collect_attribute_rows(products)
    attr_headers = [
        "product_id",
        "offer_id",
        "attribute_id",
        "complex_id",
        "complex_index",
        "dictionary_value_id",
        "value",
    ]
    _set_header_row(ws_attrs, attr_headers)

    for row, attr in enumerate(attr_rows, 2):
        ws_attrs.cell(row=row, column=1, value=attr["product_id"])
        ws_attrs.cell(row=row, column=2, value=attr["offer_id"])
        ws_attrs.cell(row=row, column=3, value=attr["attribute_id"])
        ws_attrs.cell(row=row, column=4, value=attr["complex_id"])
        ws_attrs.cell(row=row, column=5, value=attr["complex_index"])
        ws_attrs.cell(row=row, column=6, value=attr["dictionary_value_id"])
        ws_attrs.cell(row=row, column=7, value=attr["value"])

    _autofit_columns(ws_attrs, attr_headers, len(attr_rows))

    # ------------------------------------------------------------------
    # Sheet: Изображения
    # ------------------------------------------------------------------
    ws_images = wb.create_sheet(title="Изображения")
    image_rows = _collect_image_rows(products)
    image_headers = ["product_id", "offer_id", "index", "url", "is_primary"]
    _set_header_row(ws_images, image_headers)

    for row, img in enumerate(image_rows, 2):
        ws_images.cell(row=row, column=1, value=img["product_id"])
        ws_images.cell(row=row, column=2, value=img["offer_id"])
        ws_images.cell(row=row, column=3, value=img["index"])
        ws_images.cell(row=row, column=4, value=img["url"])
        ws_images.cell(row=row, column=5, value=img["is_primary"])

    _autofit_columns(ws_images, image_headers, len(image_rows))

    # ------------------------------------------------------------------
    # Sheet: Ошибки
    # ------------------------------------------------------------------
    if errors:
        ws_errors = wb.create_sheet(title="Ошибки")
        error_headers = ["#", "message"]
        _set_header_row(ws_errors, error_headers)
        for row, err in enumerate(errors, 2):
            ws_errors.cell(row=row, column=1, value=row - 1)
            ws_errors.cell(row=row, column=2, value=err)
        _autofit_columns(ws_errors, error_headers, len(errors))

    wb.save(output_path)
    return os.path.abspath(output_path)


def export_products(
    products: List[Any],
    output_path: Optional[str] = None,
) -> str:
    """Legacy compatibility for web-scraper products."""
    output_path = output_path or os.getenv("OUTPUT_FILE", "ozon_products.xlsx")

    wb = Workbook()
    ws = wb.active
    if ws is None:
        raise RuntimeError("Failed to create workbook sheet")
    ws.title = "Товары"

    headers = [
        "Название",
        "Цена",
        "Старая цена",
        "Скидка",
        "Рейтинг",
        "Отзывы",
        "Ссылка",
        "Изображение",
    ]

    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(color="FFFFFF", bold=True)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font

    for row, product in enumerate(products, 2):
        ws.cell(row=row, column=1, value=product.name)
        ws.cell(row=row, column=2, value=product.price)
        ws.cell(row=row, column=3, value=product.old_price)
        ws.cell(row=row, column=4, value=product.discount)
        ws.cell(row=row, column=5, value=product.rating)
        ws.cell(row=row, column=6, value=product.reviews)
        ws.cell(row=row, column=7, value=product.url)
        ws.cell(row=row, column=8, value=product.image)

    for col in range(1, len(headers) + 1):
        max_length = len(headers[col - 1])
        for row in range(2, len(products) + 2):
            value = ws.cell(row=row, column=col).value
            if value is not None:
                max_length = max(max_length, len(str(value)))
        ws.column_dimensions[get_column_letter(col)].width = min(max_length + 2, 80)

    wb.save(output_path)
    return os.path.abspath(output_path)
