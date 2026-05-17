"""
SPS Nuremberg exhibitor scraper.
Source: https://sps.mesago.com/nuernberg/en/exhibitor-search.html

NOTE: The SPS exhibitor search is JavaScript-rendered and loads data via
an internal API. This scraper uses the Playwright library to render the
page and extract exhibitor data.

Install Playwright before running:
    pip install playwright
    playwright install chromium
"""
import csv
import sys
import time
from pathlib import Path

OUTPUT = Path("leads_sps.csv")
FIELDNAMES = ["company", "street", "zip", "city", "country", "phone", "website", "source"]
BASE_URL = "https://sps.mesago.com/nuernberg/en/exhibitor-search.html"


def run() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Loading {BASE_URL} ...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)

        # Scroll to trigger lazy loading
        prev_count = 0
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            cards = page.query_selector_all("[class*='exhibitor'], [class*='company'], [class*='entry']")
            if len(cards) == prev_count:
                break
            prev_count = len(cards)

        from bs4 import BeautifulSoup
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "lxml")

    # Try to extract exhibitor cards — selector may need adjusting per show year
    for card in soup.select("[class*='exhibitor-card'], [class*='company-card'], .entry"):
        name = card.get_text(" ", strip=True)[:100]
        rows.append({
            "company": name,
            "street": "", "zip": "", "city": "", "country": "",
            "phone": "", "website": "",
            "source": "SPS",
        })

    if not rows:
        print("No entries extracted. The page structure may have changed; inspect the HTML and update the selectors.")
        sys.exit(1)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done. {len(rows)} rows -> {OUTPUT}")


if __name__ == "__main__":
    run()
