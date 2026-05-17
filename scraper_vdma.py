"""
VDMA member directory scraper.
Source: https://www.vdma.eu/mitglieder
Uses the internal JSON API (p_p_resource_id=getPage) to paginate through
all ~3,500 members and extract contact data directly from the JSON response.
"""
import csv
import json
import sys
import time
from pathlib import Path

import requests

API_URL = (
    "https://www.vdma.eu/de/mitglieder"
    "?p_p_id=org_vdma_publicusers_portlet_PublicUsersPortlet_INSTANCE_H0VO3QljCiRM"
    "&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view"
    "&p_p_resource_id=getPage&p_p_cacheability=cacheLevelPage"
)
PREFIX = "_org_vdma_publicusers_portlet_PublicUsersPortlet_INSTANCE_H0VO3QljCiRM_"

OUTPUT = Path("leads_vdma.csv")
DELAY = 1.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)",
    "Accept-Language": "de-DE,de;q=0.9",
}

FIELDNAMES = ["company", "street", "zip", "city", "country", "phone", "website", "source"]


def fetch_page(page: int) -> dict:
    params = {
        PREFIX + "query": "",
        PREFIX + "s": "",
        PREFIX + "page": page,
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    outer = json.loads(r.text)
    return json.loads(outer["publicUserList"])


def to_row(member: dict) -> dict:
    return {
        "company": (member.get("companyName") or "").strip(),
        "street": (member.get("address") or "").strip(),
        "zip": (member.get("plz") or "").strip(),
        "city": (member.get("city") or "").strip(),
        "country": (member.get("country") or "").strip(),
        "phone": (member.get("phoneNum") or "").strip(),
        "website": (member.get("webAddr") or "").strip(),
        "source": "VDMA",
    }


def run() -> None:
    print("Fetching page 1 to determine total pages...")
    first = fetch_page(1)
    total_pages = first["totalPages"]
    print(f"Total pages: {total_pages} (~{total_pages * 10} members)")

    rows = []
    seen = set()

    pages = [first] + [None] * (total_pages - 1)
    for i, page_data in enumerate(pages, 1):
        if page_data is None:
            try:
                page_data = fetch_page(i)
            except Exception as e:
                print(f"  ERROR page {i}: {e}", file=sys.stderr)
                time.sleep(DELAY)
                continue

        for member in page_data.get("content", []):
            row = to_row(member)
            key = (row["company"].lower(), row["street"].lower())
            if key not in seen and row["company"]:
                seen.add(key)
                rows.append(row)

        print(f"  Page {i}/{total_pages}: {len(rows)} rows total")
        if i < total_pages:
            time.sleep(DELAY)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. {len(rows)} rows -> {OUTPUT}")


if __name__ == "__main__":
    run()
