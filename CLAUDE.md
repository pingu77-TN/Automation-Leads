# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Automation-Leads** — scrapes industry directories and trade fair exhibitor lists for companies in the automation and machine vision sector. Outputs CSV files with company name, address, phone, and website.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

For SPS/VISION scrapers (JavaScript-rendered sites), also install Playwright:
```
pip install playwright
playwright install chromium
```

## Scrapers

| Script | Source | Tech | Output |
|---|---|---|---|
| `scraper_emva.py` | EMVA member directory | requests + BS4 | `leads_emva.csv` |
| `scraper_vdma.py` | VDMA member directory | requests + BS4 | `leads_vdma.csv` |
| `scraper_sps.py` | SPS Nuremberg exhibitors | Playwright | `leads_sps.csv` |

Run any scraper directly:
```
python scraper_emva.py
python scraper_vdma.py
python scraper_sps.py
```

## Architecture

Each scraper is self-contained and writes its own output CSV. All CSVs share the same column schema: `company, street, zip, city, country, phone, website, source`.

**EMVA** — static HTML. Two-step: (1) parse member list page for profile URLs, (2) visit each profile to extract address + website. ~200 members, 1 req/sec.

**VDMA** — server-rendered HTML. Single-step: loop over A–Z letter pages, extract all contact fields directly from list view. ~3,500 members, 1.5 sec/page.

**SPS** — JavaScript-rendered. Uses Playwright (headless Chromium) to scroll and render the exhibitor search page. Selectors may need updating after each show year.

**VISION Stuttgart** — also JavaScript-rendered, same approach as SPS (not yet implemented).
