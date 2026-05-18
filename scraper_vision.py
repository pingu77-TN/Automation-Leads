"""
VISION Stuttgart exhibitor scraper.
Source: https://www.messe-stuttgart.de/vision/ausstellung/unternehmen-produkte/ausstellerverzeichnis/
Uses the Messe Stuttgart Solr search API (core_de/select) to fetch all exhibitors.
fair_ids:37230 is the VISION fair identifier (Weltleitmesse fuer Bildverarbeitung).
No Playwright needed — pure requests.
"""
import csv
import json
import sys
import time
from pathlib import Path

import requests

SOLR_URL = "https://www.messe-stuttgart.de/solr/core_de/select?"
FAIR_ID = "37230"
APP_KEY = "mkdb3"
PAGE_SIZE = 200

OUTPUT = Path("leads_vision.csv")
DELAY = 0.5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.messe-stuttgart.de/vision/ausstellung/unternehmen-produkte/ausstellerverzeichnis/",
    "Origin": "https://www.messe-stuttgart.de",
}

FIELDNAMES = ["company", "street", "zip", "city", "country", "phone", "website", "source"]

FL = "title,av_street,av_zip,av_city,av_country,av_url"


def fetch_page(start: int) -> dict:
    body = (
        f"q=*:*"
        f"&fq=fair_ids:{FAIR_ID}"
        f"&fq=appKey:{APP_KEY}"
        f"&rows={PAGE_SIZE}"
        f"&start={start}"
        f"&wt=json"
        f"&fl={FL}"
        f"&sort=title+asc"
    )
    r = requests.post(SOLR_URL, data=body, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()["response"]


def to_row(doc: dict) -> dict:
    homepage = (doc.get("av_url") or "").strip()
    if homepage and not homepage.startswith("http"):
        homepage = "https://" + homepage
    return {
        "company": (doc.get("title") or "").strip(),
        "street": (doc.get("av_street") or "").strip(),
        "zip": (doc.get("av_zip") or "").strip(),
        "city": (doc.get("av_city") or "").strip(),
        "country": (doc.get("av_country") or "").strip(),
        "phone": "",
        "website": homepage,
        "source": "VISION",
    }


def run() -> None:
    print("Fetching VISION Stuttgart exhibitor list...")
    first = fetch_page(0)
    total = first["numFound"]
    print(f"Total exhibitors: {total}")

    rows = []
    seen: set[str] = set()

    def process(response: dict) -> None:
        for doc in response.get("docs", []):
            row = to_row(doc)
            if row["company"] and row["company"] not in seen:
                seen.add(row["company"])
                rows.append(row)

    process(first)
    print(f"  Batch 1: {len(rows)} rows")

    start = PAGE_SIZE
    batch = 2
    while start < total:
        try:
            resp = fetch_page(start)
            process(resp)
            print(f"  Batch {batch}: {len(rows)} rows")
        except Exception as e:
            print(f"  ERROR at start={start}: {e}", file=sys.stderr)
        start += PAGE_SIZE
        batch += 1
        time.sleep(DELAY)

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. {len(rows)} rows -> {OUTPUT}")


if __name__ == "__main__":
    run()
