# Competitor Analysis Workflow

**Objective:** Automatically discover, scrape, and analyze up to 10 competitors for Hacker's Unity, outputting a branded PDF report with market opportunities.

## Inputs
1. **Business Profile:** `data/business_profile.json` (Describes your offering, industry, and known competitors)
2. **Brand Guidelines:** `assets/brand.json` (Colors, fonts, logo path)
3. **Logo Image:** Must be present at `assets/logo.png`
4. **Environment Variables:** `FIRECRAWL_API_KEY`, `SERPER_API_KEY`, and `GEMINI_API_KEY` defined in `.env`.

## Steps
1. **Discover:** The agent runs `tools/find_competitors.py`, resolving known rival URLs and discovering new ones via Google (Serper). Results go to `tmp/competitors_found.json`.
2. **Scrape:** The agent runs `tools/scrape_competitor.py`, converting webpages (home, pricing, about) and review hubs into markdown. Results go to `tmp/all_scraped.json`.
3. **Analyze:** The agent runs `tools/analyze_competitors.py`, prompting Gemini 1.5 Pro to compare the competitor data with Hacker's Unity's profile. Results map to `tmp/analysis_results.json`.
4. **Generate Report:** The agent runs `tools/generate_report.py`, converting the JSON into a branded HTML document and rendering it as `Hackers_Unity_Competitor_Analysis.pdf` using WeasyPrint.

## Orchestrator
You can run this manually on demand via:
```bash
python run_analysis.py
```

## Edge Cases & Failures
*   **WeasyPrint Installation Issues:** PDF generation implies dependencies like Cairo and Pango. If `weasyprint` isn't installed properly, the script safely falls back to generating a `.html` version in `tmp/`, which the user can open in Chrome and "Print to PDF".
*   **Scraping Blocks:** If a site blocks Firecrawl, the script simply logs it and continues parsing the remaining competitors.
*   **Gemini Quotas:** Heavy JSON processing. If rate-limited, increase delays in the execution logic or switch model endpoints.
