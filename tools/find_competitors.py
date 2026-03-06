"""
find_competitors.py
-------------------
Uses the Serper API to:
1. Find website URLs for known competitors
2. Discover additional competitors in the same space
3. Save results to tmp/competitors_found.json
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.environ["SERPER_API_KEY"]
SERPER_URL = "https://google.serper.dev/search"
MAX_COMPETITORS = 10


def search_serper(query: str, num: int = 10, gl: str = "in") -> dict:
    response = requests.post(
        SERPER_URL,
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num, "gl": gl},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_competitor_url(name: str) -> str | None:
    """Search for the official website of a known competitor."""
    results = search_serper(f"{name} official site hackathon platform", num=5)
    for hit in results.get("organic", []):
        link = hit.get("link", "")
        # Skip aggregators, review sites, and social platforms
        skip = ["linkedin.com", "youtube.com", "twitter.com", "facebook.com",
                "instagram.com", "crunchbase.com", "wikipedia.org", "glassdoor"]
        if not any(s in link for s in skip):
            return link
    return None


def discover_competitors(profile: dict) -> list[dict]:
    """Discover up to MAX_COMPETITORS from known list + web search."""
    known = profile.get("known_competitors", [])
    company_name = profile["name"]

    competitors = {}  # name -> url

    # Step 1: resolve known competitor URLs
    print(f"  Resolving {len(known)} known competitors...")
    for name in known:
        url = get_competitor_url(name)
        if url:
            competitors[name] = url
            print(f"    ✓ {name}: {url}")
        else:
            print(f"    ✗ {name}: URL not found, skipping")

    # Step 2: discover additional competitors via search
    discovery_queries = [
        "top hackathon organizing platforms India 2024",
        "online hackathon platform blockchain AI cybersecurity courses",
        f"alternatives to {known[0] if known else 'MLH'} hackathon platform",
        "best platforms to host hackathons for students India",
    ]

    print(f"\n  Discovering additional competitors via search...")
    seen_domains = {_extract_domain(u) for u in competitors.values()}

    for query in discovery_queries:
        if len(competitors) >= MAX_COMPETITORS:
            break
        results = search_serper(query, num=10)
        for hit in results.get("organic", []):
            if len(competitors) >= MAX_COMPETITORS:
                break
            link = hit.get("link", "")
            title = hit.get("title", "").split("|")[0].split("-")[0].strip()
            domain = _extract_domain(link)

            skip = ["linkedin.com", "youtube.com", "twitter.com", "facebook.com",
                    "instagram.com", "crunchbase.com", "wikipedia.org", "glassdoor",
                    "medium.com", "dev.to", "reddit.com",
                    company_name.lower().replace(" ", "").replace("'", "")]
            if any(s in link.lower() for s in skip):
                continue
            if domain in seen_domains or not title:
                continue

            competitors[title] = link
            seen_domains.add(domain)
            print(f"    ✓ {title}: {link}")

    return [{"name": k, "url": v} for k, v in competitors.items()]


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url


if __name__ == "__main__":
    with open("data/business_profile.json") as f:
        profile = json.load(f)

    print(f"🔍 Finding competitors for {profile['name']}...\n")
    result = discover_competitors(profile)

    os.makedirs("tmp", exist_ok=True)
    output = {"competitors": result}
    with open("tmp/competitors_found.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Found {len(result)} competitors → saved to tmp/competitors_found.json")
