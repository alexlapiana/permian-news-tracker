#!/usr/bin/env python3
"""
Permian Basin News Tracker â Web Application
Deployable to Render, Railway, Heroku, or any cloud platform.
Entry point: python app.py (dev) or gunicorn app:app (production)
"""

import json
import hashlib
import os
import sys
import time
import threading
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus
from html.parser import HTMLParser

from flask import Flask, jsonify, send_from_directory, request as flask_request
from apscheduler.schedulers.background import BackgroundScheduler

import requests
from bs4 import BeautifulSoup

from config import (
    COMPANIES, BASINS, REGIONS, CATEGORIES,
    BASE_SEARCH_QUERIES, RSS_FEEDS, SCORE_WEIGHTS,
    MAX_RESULTS_PER_SOURCE, MAX_ARTICLE_AGE_DAYS, DATA_DIR,
)

# âââ Config âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
PORT = int(os.environ.get("PORT", 5000))
SCRAPE_INTERVAL_HOURS = int(os.environ.get("SCRAPE_INTERVAL_HOURS", 12))
SECRET_KEY = os.environ.get("SECRET_KEY", "permian-tracker-2026")

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / DATA_DIR
DATA_PATH.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# âââ Logging ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("app")

# âââ Global scraper state âââââââââââââââââââââââââââââââââââââââââââââââââââ
scraper_status = {
    "running": False,
    "last_run": None,
    "last_error": None,
    "progress": "",
}


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# SCRAPER ENGINE
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def strip_html(html_text: str) -> str:
    try:
        return BeautifulSoup(html_text, "html.parser").get_text(separator=" ", strip=True)
    except Exception:
        return html_text


def fetch_url(url: str, timeout: int = 15) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log.warning(f"Fetch failed {url}: {e}")
        return None


def make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def score_article(title: str, summary: str) -> dict:
    title_lower = title.lower()
    body_lower = summary.lower()
    matched_companies, matched_basins, matched_regions = [], [], []
    matched_categories = {}
    score = 0.0

    for company in COMPANIES:
        cl = company.lower()
        if cl in title_lower:
            score += SCORE_WEIGHTS["company_match"] * SCORE_WEIGHTS["title_multiplier"]
            matched_companies.append(company)
        elif cl in body_lower:
            score += SCORE_WEIGHTS["company_match"]
            matched_companies.append(company)

    for basin in BASINS:
        bl = basin.lower()
        if bl in title_lower:
            score += SCORE_WEIGHTS["basin_match"] * SCORE_WEIGHTS["title_multiplier"]
            matched_basins.append(basin)
        elif bl in body_lower:
            score += SCORE_WEIGHTS["basin_match"]
            matched_basins.append(basin)

    for region in REGIONS:
        rl = region.lower()
        if rl in title_lower:
            score += SCORE_WEIGHTS["region_match"] * SCORE_WEIGHTS["title_multiplier"]
            matched_regions.append(region)
        elif rl in body_lower:
            score += SCORE_WEIGHTS["region_match"]
            matched_regions.append(region)

    for cat_name, keywords in CATEGORIES.items():
        cat_hits = []
        for kw in keywords:
            kwl = kw.lower()
            if kwl in title_lower:
                w = SCORE_WEIGHTS["compression_keyword"] if cat_name == "Compression Specific" else SCORE_WEIGHTS["category_keyword"]
                score += w * SCORE_WEIGHTS["title_multiplier"]
                cat_hits.append(kw)
            elif kwl in body_lower:
                w = SCORE_WEIGHTS["compression_keyword"] if cat_name == "Compression Specific" else SCORE_WEIGHTS["category_keyword"]
                score += w
                cat_hits.append(kw)
        if cat_hits:
            matched_categories[cat_name] = cat_hits

    return {
        "score": round(score, 1),
        "companies": list(set(matched_companies)),
        "basins": list(set(matched_basins)),
        "regions": list(set(matched_regions)),
        "categories": matched_categories,
    }


def parse_rss_xml(xml_text: str) -> list[dict]:
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for item in items[:MAX_RESULTS_PER_SOURCE]:
        title, link, desc, pub_date = "", "", "", ""
        for child in item:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "title":
                title = (child.text or "").strip()
            elif tag == "link":
                if child.text:
                    link = child.text.strip()
                elif child.attrib.get("href"):
                    link = child.attrib["href"].strip()
            elif tag in ("description", "summary", "content"):
                desc = (child.text or "").strip()
            elif tag in ("pubDate", "published", "updated", "date"):
                pub_date = (child.text or "").strip()
        if title and link:
            articles.append({
                "id": make_id(link),
                "title": title,
                "summary": strip_html(desc)[:1000],
                "url": link,
                "published": pub_date or datetime.now(timezone.utc).isoformat(),
                "source_type": "rss",
            })
    return articles


def fetch_rss_feeds() -> list[dict]:
    articles = []
    for i, feed_url in enumerate(RSS_FEEDS):
        scraper_status["progress"] = f"RSS feeds ({i+1}/{len(RSS_FEEDS)})"
        log.info(f"RSS: {feed_url}")
        xml_text = fetch_url(feed_url)
        if xml_text:
            feed_articles = parse_rss_xml(xml_text)
            for art in feed_articles:
                art["source"] = feed_url.split("/")[2]
            articles.extend(feed_articles)
        time.sleep(0.5)
    return articles


def fetch_google_news(query: str, max_results: int = 20) -> list[dict]:
    encoded = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    xml_text = fetch_url(url)
    if not xml_text:
        return []
    articles = parse_rss_xml(xml_text)[:max_results]
    for art in articles:
        art["source"] = "Google News"
        art["source_type"] = "google_news"
    return articles


def fetch_all_google_news() -> list[dict]:
    articles = []
    total = len(BASE_SEARCH_QUERIES)
    for i, query in enumerate(BASE_SEARCH_QUERIES):
        scraper_status["progress"] = f"News search ({i+1}/{total})"
        articles.extend(fetch_google_news(query, max_results=15))
        time.sleep(1)

    priority_companies = COMPANIES[:12]
    for i, company in enumerate(priority_companies):
        scraper_status["progress"] = f"Companies ({i+1}/{len(priority_companies)})"
        articles.extend(fetch_google_news(f'"{company}" Permian Basin', max_results=10))
        time.sleep(1)
    return articles


def deduplicate(articles: list[dict]) -> list[dict]:
    seen = set()
    return [a for a in articles if not (a["id"] in seen or seen.add(a["id"]))]


def enrich_articles(articles: list[dict]) -> list[dict]:
    enriched = []
    for art in articles:
        scoring = score_article(art["title"], art["summary"])
        if scoring["score"] >= 2:
            art["relevance"] = scoring
            enriched.append(art)
    enriched.sort(key=lambda x: x["relevance"]["score"], reverse=True)
    return enriched


def load_data() -> dict:
    data_file = DATA_PATH / "articles.json"
    if data_file.exists():
        try:
            with open(data_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {"articles": [], "last_updated": None, "run_count": 0}


def save_data(data: dict):
    data_file = DATA_PATH / "articles.json"
    with open(data_file, "w") as f:
        json.dump(data, f, indent=2, default=str)


def run_scraper():
    """Full scraper pipeline."""
    global scraper_status
    if scraper_status["running"]:
        return
    scraper_status.update({"running": True, "progress": "Starting...", "last_error": None})

    try:
        log.info("=" * 50)
        log.info("SCRAPER STARTED")
        log.info("=" * 50)

        existing = load_data()
        all_articles = []

        all_articles.extend(fetch_rss_feeds())
        all_articles.extend(fetch_all_google_news())

        log.info(f"Raw articles: {len(all_articles)}")
        all_articles = deduplicate(all_articles)

        scraper_status["progress"] = "Scoring..."
        relevant = enrich_articles(all_articles)
        log.info(f"Relevant: {len(relevant)}")

        cutoff = (datetime.now(timezone.utc) - timedelta(days=MAX_ARTICLE_AGE_DAYS)).isoformat()
        merged_map = {}
        for art in existing.get("articles", []):
            if art.get("published", "") >= cutoff:
                merged_map[art["id"]] = art

        new_count = 0
        for art in relevant:
            if art["id"] not in merged_map:
                new_count += 1
                art["first_seen"] = datetime.now(timezone.utc).isoformat()
            art["last_seen"] = datetime.now(timezone.utc).isoformat()
            merged_map[art["id"]] = art

        merged = sorted(merged_map.values(), key=lambda x: x.get("relevance", {}).get("score", 0), reverse=True)

        save_data({
            "articles": merged,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "run_count": existing.get("run_count", 0) + 1,
            "stats": {
                "total_articles": len(merged),
                "new_this_run": new_count,
                "sources": {
                    "rss": sum(1 for a in merged if a.get("source_type") == "rss"),
                    "google_news": sum(1 for a in merged if a.get("source_type") == "google_news"),
                },
            },
        })

        log.info(f"DONE â {new_count} new, {len(merged)} total")
        scraper_status["last_run"] = datetime.now(timezone.utc).isoformat()
        scraper_status["progress"] = f"Done â {new_count} new articles"

    except Exception as e:
        log.error(f"Scraper error: {e}", exc_info=True)
        scraper_status["last_error"] = str(e)
        scraper_status["progress"] = f"Error: {e}"
    finally:
        scraper_status["running"] = False


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# FLASK APP
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

app = Flask(__name__, static_folder="static")
app.secret_key = SECRET_KEY


@app.route("/")
def index():
    return send_from_directory(SCRIPT_DIR, "dashboard.html")


@app.route("/api/articles")
def api_articles():
    return jsonify(load_data())


@app.route("/api/stats")
def api_stats():
    data = load_data()
    articles = data.get("articles", [])
    cat_counts, company_counts = {}, {}
    for art in articles:
        for cat in art.get("relevance", {}).get("categories", {}):
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        for co in art.get("relevance", {}).get("companies", []):
            company_counts[co] = company_counts.get(co, 0) + 1
    return jsonify({
        "total_articles": len(articles),
        "last_updated": data.get("last_updated"),
        "run_count": data.get("run_count", 0),
        "category_distribution": cat_counts,
        "top_companies": dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:15]),
        "source_breakdown": data.get("stats", {}).get("sources", {}),
    })


@app.route("/api/config")
def api_config():
    return jsonify({
        "companies": COMPANIES,
        "basins": BASINS,
        "categories": list(CATEGORIES.keys()),
    })


@app.route("/api/status")
def api_status():
    return jsonify(scraper_status)


@app.route("/api/scrape", methods=["GET", "POST"])
def api_scrape():
    if scraper_status["running"]:
        return jsonify({"started": False, "message": "Already running", "status": scraper_status})
    t = threading.Thread(target=run_scraper, daemon=True)
    t.start()
    return jsonify({"started": True, "status": scraper_status})


# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# SCHEDULER & STARTUP
# âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

scheduler = BackgroundScheduler()
scheduler.add_job(run_scraper, "interval", hours=SCRAPE_INTERVAL_HOURS, id="scraper",
                  next_run_time=datetime.now(timezone.utc) + timedelta(seconds=5))
scheduler.start()

log.info(f"Scheduled scraper every {SCRAPE_INTERVAL_HOURS} hours")


if __name__ == "__main__":
    print()
    print("  ââââââââââââââââââââââââââââââââââââââââââââââââ")
    print("  â   Permian Basin News Tracker                 â")
    print("  â   Gas Compression Business Intelligence      â")
    print("  ââââââââââââââââââââââââââââââââââââââââââââââââ")
    print()
    print(f"  http://localhost:{PORT}")
    print()

    import webbrowser
    threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(f"http://localhost:{PORT}")), daemon=True).start()

    app.run(host="0.0.0.0", port=PORT, debug=False)
