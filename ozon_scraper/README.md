# Ozon Seller API Scraper

Собирает все товары продавца через официальный **Ozon Seller API** и сохраняет в Excel:

- основные данные товара (ID, артикул, название, штрихкод, категория);
- полное описание;
- цены и скидочные цены;
- первое изображение + список всех изображений;
- все атрибуты/характеристики товара (включая сложные атрибуты).

## Стек

- Python 3
- `requests` — HTTP-клиент
- `openpyxl` — экспорт в `.xlsx`
- `python-dotenv` — переменные окружения

## Установка

```bash
cd /home/user/ozon_scraper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Настройка

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

```env
OZON_CLIENT_ID=ваш_client_id
OZON_API_KEY=ваш_api_key
OUTPUT_FILE=ozon_products_api.xlsx
OZON_VISIBILITY=ALL
MAX_PRODUCTS=0
BATCH_SIZE=500
DESCRIPTION_WORKERS=20
```

`OZON_CLIENT_ID` и `OZON_API_KEY` берутся в личном кабинете продавца Ozon.

## Запуск

```bash
source .venv/bin/activate
python main.py
```

Результат — файл `ozon_products_api.xlsx` (или тот, что указан в `OUTPUT_FILE`).

## Структура Excel

Один основной лист **Товары** — по одной строке на товар.

Колонки:

- `product_id`, `offer_id`, `sku`, `name`, `barcode`
- категории: `category_id`, `description_category_id`, `type_id`
- `description` — полное описание
- цены: `price`, `old_price`, `retail_price`, `marketing_price`, `min_price`, `currency_code`, `vat`
- статусы и габариты
- `Фото` — встроенное изображение товара (не ссылка)
- `attributes` — все атрибуты/характеристики товара в текстовом виде

Также создаётся лист **Ошибки**, если во время сбора были ошибки API.

## Используемые методы Ozon Seller API

- `POST /v3/product/list` — список всех товаров;
- `POST /v4/product/info/attributes` — характеристики, габариты, изображения;
- `POST /v5/product/info/prices` — цены;
- `POST /v2/product/pictures/info` — изображения (primary photo fallback);
- `POST /v1/product/info/description` — описание.

## Тесты

```bash
source .venv/bin/activate
python -m unittest discover -s tests -t . -v
```

## Лимиты

Скрипт соблюдает rate limit Ozon (~40 запросов/сек) и использует пагинацию. Описания запрашиваются параллельно с `DESCRIPTION_WORKERS` потоками.
