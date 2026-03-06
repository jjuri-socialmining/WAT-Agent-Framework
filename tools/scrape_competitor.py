"""
scrape_competitor.py
--------------------
Uses Firecrawl to scrape each competitor's website.
Also uses Serper to find review pages and pricing pages.

Reads:  tmp/competitors_found.json
Writes: tmp/scraped_<name>.json  (one per competitor)
        tmp/all_scraped.json     (combined)
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.environ["FIRECRAWL_API_KEY"]
SERPER_API_KEY = os.environ["SERPER_API_KEY"]

# Pages to try scraping on each site
TARGET_PATHS = ["/", "/pricing", "/about", "/courses", "/events",
                "/hackathons", "/blog", "/features", "/plans"]

SERPER_URL = "https://google.serper.dev/search"


def firecrawl_scrape(url: str, timeout: int = 30) -> str | None:
    """Scrape a single URL via Firecrawl REST API and return markdown."""
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "waitFor": 1000,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("markdown") or data.get("markdown")
    except Exception as e:
        print(f"      Firecrawl error for {url}: {e}")
        return None


def firecrawl_map(base_url: str) -> list[str]:
    """Get a sitemap of URLs from Firecrawl."""
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/map",
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"url": base_url, "limit": 20},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("links", [])
    except Exception as e:
        print(f"      Map error for {base_url}: {e}")
        return []


def search_for_reviews(competitor_name: str) -> list[str]:
    """Use Serper to find review pages for a competitor."""
    try:
        resp = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": f"{competitor_name} reviews students experience", "num": 5},
            timeout=20,
        )
        resp.raise_for_status()
        hits = resp.json().get("organic", [])
        review_domains = ["g2.com", "trustpilot.com", "reddit.com",
                          "producthunt.com", "glassdoor.com"]
        return [h["link"] for h in hits if any(d in h["link"] for d in review_domains)]
    except Exception:
        return []


def scrape_competitor(name: str, base_url: str) -> dict:
    print(f"\n  📡 Scraping: {name} ({base_url})")

    data = {"name": name, "url": base_url, "pages": {}, "reviews": []}

    # Always scrape homepage first
    homepage = firecrawl_scrape(base_url)
    if homepage:
        data["pages"]["homepage"] = {"url": base_url, "content": homepage[:6000]}
        print(f"      ✓ homepage")

    # Map the site to find real page URLs
    site_links = firecrawl_map(base_url)
    time.sleep(1)  # be polite

    # Score links by relevance to our target paths
    priority_links = []
    for link in site_links:
        path = link.replace(base_url.rstrip("/"), "").lower()
        if any(t in path for t in TARGET_PATHS[1:]):  # skip "/" already done
            priority_links.append(link)

    # Scrape up to 5 priority pages
    scraped_count = 0
    for url in priority_links[:5]:
        path_key = url.replace(base_url.rstrip("/"), "") or url
        content = firecrawl_scrape(url)
        if content:
            data["pages"][path_key] = {"url": url, "content": content[:4000]}
            print(f"      ✓ {path_key}")
            scraped_count += 1
        time.sleep(0.5)

    # If no priority pages found, try common paths by guessing
    if scraped_count == 0:
        for path in TARGET_PATHS[1:4]:
            guessed = base_url.rstrip("/") + path
            content = firecrawl_scrape(guessed)
            if content and len(content) > 200:
                data["pages"][path] = {"url": guessed, "content": content[:4000]}
                print(f"      ✓ {path} (guessed)")
                scraped_count += 1
            time.sleep(0.5)

    # Fetch review URLs via Serper
    review_urls = search_for_reviews(name)
    for rurl in review_urls[:2]:
        content = firecrawl_scrape(rurl)
        if content:
            data["reviews"].append({"url": rurl, "content": content[:3000]})
            print(f"      ✓ review: {rurl}")
        time.sleep(0.5)

    total_pages = len(data["pages"]) + len(data["reviews"])
    print(f"      → {total_pages} pages collected")
    return data


if __name__ == "__main__":
    with open("tmp/competitors_found.json") as f:
        found = json.load(f)

    competitors = found["competitors"]
    print(f"🕷️  Scraping {len(competitors)} competitors...\n")

    all_scraped = []
    for comp in competitors:
        scraped = scrape_competitor(comp["name"], comp["url"])
        all_scraped.append(scraped)

        # Save individual file immediately (safe against partial failures)
        safe = comp["name"].lower().replace(" ", "_").replace("'", "").replace("(", "").replace(")", "")
        with open(f"tmp/scraped_{safe}.json", "w") as f:
            json.dump(scraped, f, indent=2)

        time.sleep(1)  # rate limit courtesy

    with open("tmp/all_scraped.json", "w") as f:
        json.dump(all_scraped, f, indent=2)

    print(f"\n✅ Done — scraped {len(all_scraped)} competitors → tmp/all_scraped.json")
