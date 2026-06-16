"""Export scraped products to an .xlsx file."""
from __future__ import annotations

import os
from typing import List, Optional

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from scraper import Product


def export_products(
    products: List[Product],
    output_path: Optional[str] = None,
) -> str:
    output_path = output_path or os.getenv("OUTPUT_FILE", "ozon_products.xlsx")

    wb = Workbook()
    ws: Worksheet = wb.active  # type: ignore[assignment]
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

    # Header row
    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(color="FFFFFF", bold=True)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font

    # Data rows
    for row, product in enumerate(products, 2):
        ws.cell(row=row, column=1, value=product.name)
        ws.cell(row=row, column=2, value=product.price)
        ws.cell(row=row, column=3, value=product.old_price)
        ws.cell(row=row, column=4, value=product.discount)
        ws.cell(row=row, column=5, value=product.rating)
        ws.cell(row=row, column=6, value=product.reviews)
        ws.cell(row=row, column=7, value=product.url)
        ws.cell(row=row, column=8, value=product.image)

    # Auto-width columns
    for col in range(1, len(headers) + 1):
        max_length = len(headers[col - 1])
        for row in range(2, len(products) + 2):
            value = ws.cell(row=row, column=col).value
            if value:
                max_length = max(max_length, len(str(value)))
        ws.column_dimensions[get_column_letter(col)].width = min(max_length + 2, 80)

    wb.save(output_path)
    return os.path.abspath(output_path)
