"""
EMVA member directory scraper.
Source: https://www.emva.org/about-emva/members/
Fetches list page -> visits each member profile -> extracts contact details.
"""
import csv
import sys
import time
from pathlib import Path

import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.emva.org"
LIST_URL = "https://www.emva.org/about-emva/members/"
OUTPUT = Path("leads_emva.csv")
DELAY = 1.0  # seconds between requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-scraper/1.0)"
}

FIELDNAMES = ["company", "type", "street", "zip", "city", "country", "website", "source"]


def get_member_urls() -> list[str]:
    r = requests.get(LIST_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/members/" in href and href.rstrip("/") != LIST_URL.rstrip("/"):
            full = href if href.startswith("http") else BASE_URL + href
            # filter out pagination/anchor links
            if full.count("/members/") >= 1 and not full.endswith("/members/"):
                urls.add(full.rstrip("/") + "/")
    return sorted(urls)


def parse_profile(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    main = soup.find("main") or soup

    # Company name from the entry-title div
    name = ""
    title_div = main.find(class_="entry-title")
    if title_div:
        name = title_div.get_text(strip=True)

    # Member type from entry-content ("Company type\n<type>")
    member_type = ""
    entry_content = main.find(class_="entry-content")
    if entry_content:
        lines = [l.strip() for l in entry_content.get_text("\n").splitlines() if l.strip()]
        for i, line in enumerate(lines):
            if line == "Company type" and i + 1 < len(lines):
                member_type = lines[i + 1]
                break

    # Contact block: column_content has [name, street, zip, city, (country?), phone?, ...]
    street = zip_code = city = country = website = ""
    col = main.find(class_="column_content")
    if col:
        lines = [l.strip() for l in col.get_text("\n").splitlines() if l.strip()]
        # lines[0] is the company name — skip it; address starts at index 1
        _SKIP = {"Write email", "Visit corporate website", "Subsidiaries"}
        if len(lines) > 1:
            street = lines[1] if len(lines) > 1 else ""
            zip_code = lines[2] if len(lines) > 2 else ""
            city = lines[3] if len(lines) > 3 else ""
            candidate = lines[4] if len(lines) > 4 else ""
            # country line is text, not a phone (+...) or known label
            if candidate and not re.match(r"^[+\d]", candidate) and candidate not in _SKIP:
                country = candidate

        for a in col.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "emva.org" not in href:
                website = href
                break

    return {
        "company": name,
        "type": member_type,
        "street": street,
        "zip": zip_code,
        "city": city,
        "country": country,
        "website": website,
        "source": "EMVA",
    }


def run() -> None:
    print("Fetching EMVA member list...")
    urls = get_member_urls()
    print(f"Found {len(urls)} member profiles")

    rows = []
    for i, url in enumerate(urls, 1):
        try:
            row = parse_profile(url)
            rows.append(row)
            print(f"  [{i:>3}/{len(urls)}] {row['company'] or url}")
        except Exception as e:
            print(f"  [{i:>3}/{len(urls)}] ERROR {url}: {e}", file=sys.stderr)
        time.sleep(DELAY)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone. {len(rows)} rows -> {OUTPUT}")


if __name__ == "__main__":
    run()
