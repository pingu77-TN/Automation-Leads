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

## Scrapers

| Script | Source | Tech | Output |
|---|---|---|---|
| `scraper_emva.py` | EMVA member directory | requests + BS4 | `leads_emva.csv` |
| `scraper_vdma.py` | VDMA member directory | requests + JSON API | `leads_vdma.csv` |
| `scraper_sps.py` | SPS Nuremberg exhibitors | requests + JSON API | `leads_sps.csv` |
| `scraper_vision.py` | VISION Stuttgart exhibitors | requests + Solr API | `leads_vision.csv` |

Run any scraper directly:
```
python scraper_emva.py
python scraper_vdma.py
python scraper_sps.py
python scraper_vision.py
```

## Architecture

Each scraper is self-contained and writes its own output CSV. All CSVs share the same column schema: `company, street, zip, city, country, phone, website, source`.

**EMVA** — static HTML. Two-step: (1) parse member list page for profile URLs, (2) visit each profile to extract address + website from `div.column_content`. ~154 members, 1 req/sec.

**VDMA** — uses an internal Liferay portlet JSON API (`p_p_resource_id=getPage`, 10 members per page, 355 pages). Returns structured JSON with all contact fields pre-parsed — no HTML parsing needed. ~3,550 members, 1 sec/page.

**SPS** — uses the Messe Frankfurt exhibitor-service JSON API discovered in `app.min.js`. Endpoint: `api.messefrankfurt.com/service/esb_api/exhibitor-service/api/2.1/public/exhibitor/search`. Requires `Apikey` header and `findEventVariable=SPS` parameter. Returns up to 100 per page. ~619 exhibitors. No Playwright needed.

**VISION Stuttgart** — uses the Messe Stuttgart Solr API (`POST messe-stuttgart.de/solr/core_de/select?`). Filter: `fq=fair_ids:37230` (VISION fair ID) + `fq=appKey:mkdb3`. Returns `title, av_street, av_zip, av_city, av_country, av_url`. Country names are in German. No phone numbers available in the index. ~397 exhibitors.
