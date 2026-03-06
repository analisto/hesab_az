import requests
import csv
import os
import time

BASE_URL = "https://hesab.az/api/pg/unregistered"
BEARER_TOKEN = "59560cf4-f984-46ff-93ae-a786b368beaa"
OAUTH_CLIENT = "Sff345cvGkefG957H7v35Fsfd3s94"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "data.csv")

HEADERS_BASE = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "az",
    "content-type": "application/json",
    "dnt": "1",
    "referer": "https://hesab.az/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/145.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

HEADERS_AUTH = {
    **HEADERS_BASE,
    "authorization": f"bearer {BEARER_TOKEN}",
    "oauth-client": OAUTH_CLIENT,
    "referer": "https://hesab.az/unregistered/",
}


def get_categories(session: requests.Session) -> list[dict]:
    url = f"{BASE_URL}/categories"
    resp = session.get(url, headers=HEADERS_BASE)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    # Some APIs wrap in a key
    return data.get("data") or data.get("categories") or data.get("items") or data


def get_category_items(session: requests.Session, slug: str) -> list[dict]:
    url = f"{BASE_URL}/categories/{slug}/items/"
    all_items = []
    page = 1

    while True:
        params = {"page": page, "size": 50}
        resp = session.get(url, headers=HEADERS_AUTH, params=params)
        if resp.status_code == 401:
            print(f"  [!] 401 Unauthorized for '{slug}' — bearer token may have expired.")
            break
        resp.raise_for_status()
        data = resp.json()

        # Normalise response shape
        if isinstance(data, list):
            items = data
            has_next = False
        else:
            items = (
                data.get("data")
                or data.get("items")
                or data.get("content")
                or []
            )
            total_pages = (
                data.get("totalPages")
                or data.get("total_pages")
                or data.get("pages")
            )
            has_next = total_pages is not None and page < int(total_pages)

        if not items:
            break

        all_items.extend(items)
        print(f"  page {page}: {len(items)} items (total so far: {len(all_items)})")

        if not has_next:
            break

        page += 1
        time.sleep(0.3)

    return all_items


def flatten(obj: dict, prefix: str = "") -> dict:
    """Recursively flatten a nested dict into a single-level dict."""
    result = {}
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, full_key))
        elif isinstance(value, list):
            result[full_key] = "; ".join(str(v) for v in value)
        else:
            result[full_key] = value
    return result


def main():
    os.makedirs(os.path.dirname(os.path.abspath(OUTPUT_FILE)), exist_ok=True)

    session = requests.Session()

    print("Fetching categories...")
    categories = get_categories(session)
    print(f"Found {len(categories)} categories.\n")

    all_rows: list[dict] = []

    for cat in categories:
        slug = cat.get("slug") or cat.get("code") or cat.get("id")
        name = cat.get("name") or cat.get("title") or slug
        print(f"[{name}] fetching items (slug={slug})...")

        items = get_category_items(session, slug)
        print(f"  -> {len(items)} total items\n")

        for item in items:
            row = flatten(item)
            row.setdefault("_category_slug", slug)
            row.setdefault("_category_name", name)
            all_rows.append(row)

        time.sleep(0.5)

    if not all_rows:
        print("No data collected.")
        return

    # Build unified fieldnames (preserves insertion order; union across all rows)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in all_rows:
        for k in row:
            if k not in seen:
                fieldnames.append(k)
                seen.add(k)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Saved {len(all_rows)} rows to {os.path.abspath(OUTPUT_FILE)}")


if __name__ == "__main__":
    main()
