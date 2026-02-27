import asyncio
import csv
import logging
from pathlib import Path

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://mp-catalog.umico.az/api/v1/products"
CATEGORY_ID = 257
PER_PAGE = 30
SORT = "global_popular_score"
CONCURRENCY = 50

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "az",
    "content-language": "az",
    "http_accept_language": "az",
    "http_content_language": "az",
    "origin": "https://birmarket.az",
    "referer": "https://birmarket.az/",
    "dnt": "1",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
}

CSV_FIELDS = [
    "id",
    "name",
    "slugged_name",
    "status",
    "avail_check",
    "image_url",
    "offer_uuid",
    "installment_enabled",
    "max_installment_months",
    "old_price",
    "retail_price",
    "offer_avail_check",
    "offer_qty",
    "seller_name",
    "seller_rating",
    "seller_role",
    "min_qty",
    "preorder_available",
    "rating_value",
    "review_count",
    "brand",
    "category_id",
    "category_name",
]


def extract_product(p: dict) -> dict:
    offer = p.get("default_offer") or {}
    seller = offer.get("seller") or {}
    seller_name_obj = seller.get("marketing_name") or {}
    ratings = p.get("ratings") or {}
    img = p.get("main_img") or {}
    category = p.get("category") or {}

    return {
        "id": p.get("id"),
        "name": p.get("name"),
        "slugged_name": p.get("slugged_name"),
        "status": p.get("status"),
        "avail_check": p.get("avail_check"),
        "image_url": img.get("big"),
        "offer_uuid": offer.get("uuid"),
        "installment_enabled": offer.get("installment_enabled"),
        "max_installment_months": offer.get("max_installment_months"),
        "old_price": offer.get("old_price"),
        "retail_price": offer.get("retail_price"),
        "offer_avail_check": offer.get("avail_check"),
        "offer_qty": offer.get("qty"),
        "seller_name": seller_name_obj.get("name"),
        "seller_rating": seller.get("rating"),
        "seller_role": seller.get("role_name"),
        "min_qty": p.get("min_qty"),
        "preorder_available": p.get("preorder_available"),
        "rating_value": ratings.get("rating_value"),
        "review_count": ratings.get("session_count"),
        "brand": p.get("brand"),
        "category_id": category.get("id"),
        "category_name": category.get("name"),
    }


async def fetch_page(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    page: int,
) -> list[dict]:
    params = {
        "page": page,
        "category_id": CATEGORY_ID,
        "per_page": PER_PAGE,
        "sort": SORT,
    }
    timeout = aiohttp.ClientTimeout(total=30)
    async with semaphore:
        for attempt in range(3):
            try:
                async with session.get(
                    BASE_URL, params=params, headers=HEADERS, timeout=timeout
                ) as resp:
                    if resp.status != 200:
                        logger.warning("Page %d: HTTP %d", page, resp.status)
                        return []
                    data = await resp.json(content_type=None)
                    products = data.get("products") or []
                    return [extract_product(p) for p in products]
            except Exception as exc:
                logger.warning("Page %d attempt %d failed: %s", page, attempt + 1, exc)
                await asyncio.sleep(1)
        logger.error("Page %d: all retries exhausted", page)
        return []


async def main() -> None:
    output_path = Path("data/cosmetics.csv")
    output_path.parent.mkdir(exist_ok=True)

    # Page 1 — discover total
    async with aiohttp.ClientSession() as session:
        logger.info("Fetching page 1 to discover total...")
        params = {
            "page": 1,
            "category_id": CATEGORY_ID,
            "per_page": PER_PAGE,
            "sort": SORT,
        }
        async with session.get(
            BASE_URL,
            params=params,
            headers=HEADERS,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            data = await resp.json(content_type=None)

    total = (data.get("meta") or {}).get("total", 0)
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    logger.info("Total products: %d  |  Total pages: %d", total, total_pages)

    all_products: list[dict] = [extract_product(p) for p in (data.get("products") or [])]

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(fetch_page(session, semaphore, page))
            for page in range(2, total_pages + 1)
        ]

        completed = 0
        for coro in asyncio.as_completed(tasks):
            batch = await coro
            all_products.extend(batch)
            completed += 1
            if completed % 200 == 0 or completed == len(tasks):
                logger.info(
                    "Progress: %d/%d pages  |  %d products collected",
                    completed + 1,  # +1 for page 1 already done
                    total_pages,
                    len(all_products),
                )

    logger.info("Writing %d products to %s", len(all_products), output_path)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(all_products)

    logger.info("Done. Saved to %s", output_path)


if __name__ == "__main__":
    asyncio.run(main())
