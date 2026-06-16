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

1. **Товары** — основная таблица с одним товаром на строку.
2. **Атрибуты** — длинный формат: каждое значение каждого атрибута на отдельной строке.
3. **Изображения** — все URL изображений по товарам.
4. **Ошибки** — ошибки/предупреждения API во время сбора (если были).

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
