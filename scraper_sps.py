"""
SPS Nuremberg exhibitor scraper.
Source: https://sps.mesago.com/nuernberg/en/exhibitor-search.html
Uses the Messe Frankfurt exhibitor-service JSON API (no Playwright needed).
API endpoint discovered from app.min.js embedded in the page.
"""
import csv
import json
import math
import sys
import time
from pathlib import Path

import requests

API_URL = (
    "https://api.messefrankfurt.com/service/esb_api/exhibitor-service"
    "/api/2.1/public/exhibitor/search"
)
API_KEY = "LXnMWcYQhipLAS7rImEzmZ3CkrU033FMha9cwVSngG4vbufTsAOCQQ=="
EVENT_ID = "SPS"
PAGE_SIZE = 100

OUTPUT = Path("leads_sps.csv")
DELAY = 0.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://sps.mesago.com/",
    "Apikey": API_KEY,
}

FIELDNAMES = ["company", "street", "zip", "city", "country", "phone", "website", "source"]


def fetch_page(page: int) -> dict:
    params = {
        "language": "en-GB",
        "orderBy": "name",
        "orSearchFallback": "false",
        "findEventVariable": EVENT_ID,
        "pageNumber": page,
        "pageSize": PAGE_SIZE,
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()["result"]


def to_row(exhibitor: dict) -> dict:
    addr = exhibitor.get("address") or {}
    country_field = addr.get("country") or {}
    homepage = (exhibitor.get("homepage") or "").strip()
    if homepage and not homepage.startswith("http"):
        homepage = "https://" + homepage
    return {
        "company": (exhibitor.get("name") or "").strip(),
        "street": (addr.get("street") or "").strip(),
        "zip": (addr.get("zip") or "").strip(),
        "city": (addr.get("city") or "").strip(),
        "country": (country_field.get("label") or "").strip(),
        "phone": (addr.get("tel") or "").strip(),
        "website": homepage,
        "source": "SPS",
    }


def run() -> None:
    print("Fetching SPS exhibitor list (page 1)...")
    first = fetch_page(1)
    meta = first["metaData"]
    total = meta["hitsTotal"]
    total_pages = math.ceil(total / PAGE_SIZE)
    print(f"Total exhibitors: {total} across {total_pages} pages")

    rows = []
    seen: set[str] = set()

    def process_page(result: dict) -> None:
        for hit in result.get("hits", []):
            ex = hit.get("exhibitor", {})
            row = to_row(ex)
            if row["company"] and row["company"] not in seen:
                seen.add(row["company"])
                rows.append(row)

    process_page(first)
    print(f"  Page 1/{total_pages}: {len(rows)} rows")

    for page in range(2, total_pages + 1):
        try:
            result = fetch_page(page)
            process_page(result)
            print(f"  Page {page}/{total_pages}: {len(rows)} rows")
        except Exception as e:
            print(f"  ERROR page {page}: {e}", file=sys.stderr)
        time.sleep(DELAY)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. {len(rows)} rows -> {OUTPUT}")


if __name__ == "__main__":
    run()
