"""
Dual Store Review Scraper — fetches live customer reviews from Google Play Store and Apple App Store.
Supports single-store scraping (Google Play or Apple App Store) and combined scraping across both stores.
Includes dynamic search resolution, rich preset mappings for fintech/mutual fund apps,
and automatic fallback caching.
"""

import csv
import json
import logging
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from google_play_scraper import Sort, reviews as fetch_play_reviews

from models import Review

logger = logging.getLogger("scraper")

# Popular Indian Fintech / Mutual Fund App Presets with both Play Store & Apple Store IDs
APP_PRESETS = {
    "groww": {
        "display_name": "Groww — Stocks & Mutual Funds",
        "play_id": "com.nextbillion.groww",
        "apple_id": "1404871703"
    },
    "zerodha kite": {
        "display_name": "Zerodha Kite — Trade & Invest",
        "play_id": "com.zerodha.kite3",
        "apple_id": "1449453802"
    },
    "zerodha": {
        "display_name": "Zerodha Kite — Trade & Invest",
        "play_id": "com.zerodha.kite3",
        "apple_id": "1449453802"
    },
    "kite": {
        "display_name": "Zerodha Kite — Trade & Invest",
        "play_id": "com.zerodha.kite3",
        "apple_id": "1449453802"
    },
    "coin": {
        "display_name": "Coin by Zerodha — Mutual Funds",
        "play_id": "com.zerodha.coin",
        "apple_id": "1392892554"
    },
    "zerodha coin": {
        "display_name": "Coin by Zerodha — Mutual Funds",
        "play_id": "com.zerodha.coin",
        "apple_id": "1392892554"
    },
    "paytm money": {
        "display_name": "Paytm Money — Stocks & MF",
        "play_id": "com.paytmmoney",
        "apple_id": "1344431352"
    },
    "angel one": {
        "display_name": "Angel One — Stocks & Mutual Fund",
        "play_id": "com.msf.angelmobile",
        "apple_id": "1060530981"
    },
    "upstox": {
        "display_name": "Upstox — Demat, Stock & MF",
        "play_id": "in.upstox.app",
        "apple_id": "1584953620"
    },
    "et money": {
        "display_name": "ET Money — Mutual Funds & SIP",
        "play_id": "com.etmoney.android",
        "apple_id": "1212752482"
    },
    "kuvera": {
        "display_name": "Kuvera — Free Direct Mutual Funds",
        "play_id": "com.kuvera.app",
        "apple_id": "1327893814"
    },
    "indmoney": {
        "display_name": "INDmoney — US Stocks, MF & Tracking",
        "play_id": "com.indwealth",
        "apple_id": "1450178837"
    }
}

DEFAULT_PLAY_ID = "com.nextbillion.groww"
DEFAULT_APPLE_ID = "1404871703"
DEFAULT_DISPLAY_NAME = "Groww — Stocks & Mutual Funds"


def search_apple_app_id(query: str, country: str = "in") -> Tuple[Optional[str], Optional[str]]:
    """
    Search iTunes Search API for an iOS application ID and track name.
    Returns (apple_track_id, track_name) or (None, None).
    """
    try:
        encoded_query = urllib.parse.quote(query.strip())
        url = f"https://itunes.apple.com/search?term={encoded_query}&country={country}&entity=software&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("results"):
                res = data["results"][0]
                track_id = str(res.get("trackId", ""))
                track_name = str(res.get("trackName", query))
                return track_id, track_name
    except Exception as e:
        logger.warning(f"iTunes Search API lookup failed for '{query}': {e}")
    return None, None


def resolve_app_identifiers(query: Optional[str]) -> Tuple[str, str, str]:
    """
    Resolve an app name or identifier to (play_package_id, apple_track_id, display_name).
    """
    if not query or not query.strip():
        return DEFAULT_PLAY_ID, DEFAULT_APPLE_ID, DEFAULT_DISPLAY_NAME

    q = query.strip().lower()

    # Exact or partial match in presets
    if q in APP_PRESETS:
        p = APP_PRESETS[q]
        return p["play_id"], p["apple_id"], p["display_name"]

    for key, p in APP_PRESETS.items():
        if key in q or q in key:
            return p["play_id"], p["apple_id"], p["display_name"]

    # Check if query is directly a Play Store package ID (contains '.')
    play_id = DEFAULT_PLAY_ID
    apple_id = DEFAULT_APPLE_ID
    display_name = query.strip().title()

    if "." in query and not query.isdigit():
        play_id = query.strip()

    # Check if query is directly an Apple App ID (all digits)
    if query.strip().isdigit():
        apple_id = query.strip()

    # Try dynamic search for Apple App ID if not recognized as digits
    if not query.strip().isdigit():
        searched_apple_id, searched_name = search_apple_app_id(query)
        if searched_apple_id:
            apple_id = searched_apple_id
            if searched_name:
                display_name = searched_name

    return play_id, apple_id, display_name


def scrape_google_play_reviews(
    package_id: str,
    display_name: str,
    count: int = 25,
    country: str = "in"
) -> List[Review]:
    """Scrape customer reviews from Google Play Store."""
    reviews: List[Review] = []
    try:
        logger.info(f"Scraping Google Play Store for {package_id} (count={count})...")
        results, _ = fetch_play_reviews(
            package_id,
            lang="en",
            country=country,
            sort=Sort.NEWEST,
            count=max(count, 10)
        )

        for r in results:
            content = (r.get("content") or "").strip()
            if not content:
                continue

            at_dt = r.get("at")
            date_str = at_dt.strftime("%Y-%m-%d") if at_dt else datetime.now().strftime("%Y-%m-%d")
            user_name = (r.get("userName") or "Play Store User").strip()
            score = int(r.get("score") or 3)

            reviews.append(Review(
                date=date_str,
                reviewer=user_name,
                rating=score,
                review_text=content,
                source=f"Google Play ({display_name})"
            ))

            if len(reviews) >= count:
                break

    except Exception as e:
        logger.warning(f"Google Play Store scraping error: {e}")

    return reviews


def scrape_apple_store_reviews(
    apple_id: str,
    display_name: str,
    count: int = 25,
    country: str = "in"
) -> List[Review]:
    """Scrape customer reviews from Apple App Store via official RSS customer reviews endpoint."""
    reviews: List[Review] = []
    page = 1
    # Apple iTunes RSS customer reviews is officially capped at 10 pages (50 reviews per page = ~500 reviews max)
    max_pages = min(10, max(1, (count + 49) // 50))

    try:
        logger.info(f"Scraping Apple App Store for track ID {apple_id} (count={count})...")
        while len(reviews) < count and page <= max_pages:
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={apple_id}/sortBy=mostRecent/json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                entries = data.get("feed", {}).get("entry", [])
                if not entries or len(entries) <= 1:
                    break

                # The first entry in iTunes RSS is app metadata; subsequent entries are customer reviews
                for e in entries[1:]:
                    content_block = e.get("content", {})
                    content_text = content_block.get("label", "").strip() if isinstance(content_block, dict) else ""
                    title_text = e.get("title", {}).get("label", "").strip()

                    full_review = f"{title_text}: {content_text}" if title_text and content_text else (content_text or title_text)
                    if not full_review:
                        continue

                    # Extract author
                    author_name = e.get("author", {}).get("name", {}).get("label", "App Store User").strip()

                    # Extract rating (1-5)
                    try:
                        rating = int(e.get("im:rating", {}).get("label", "3"))
                    except (ValueError, TypeError):
                        rating = 3

                    # Extract date
                    updated_str = e.get("updated", {}).get("label", "")
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    if updated_str:
                        try:
                            # e.g. "2026-10-16T03:45:09-07:00"
                            date_str = updated_str[:10]
                        except Exception:
                            pass

                    reviews.append(Review(
                        date=date_str,
                        reviewer=author_name,
                        rating=rating,
                        review_text=full_review,
                        source=f"Apple App Store ({display_name})"
                    ))

                    if len(reviews) >= count:
                        break

            page += 1

    except Exception as e:
        logger.warning(f"Apple App Store scraping error: {e}")

    return reviews


def scrape_reviews(
    app_query: Optional[str] = None,
    store: str = "both",
    count: int = 50,
    country: str = "in",
    save_csv_path: Optional[str] = None
) -> Tuple[List[Review], Dict]:
    """
    Scrape customer reviews from Google Play Store, Apple App Store, or Both.
    
    Parameters:
      app_query: App name, package ID, or Apple App ID.
      store: "both", "google", or "apple".
      count: Total number of reviews to collect.
      country: Store country code (default 'in' for India mutual fund / fintech apps).
      save_csv_path: Optional path to write output CSV.
      
    Returns:
      (reviews_list, metadata_dict)
    """
    play_id, apple_id, display_name = resolve_app_identifiers(app_query)
    store = (store or "both").strip().lower()

    gp_reviews: List[Review] = []
    ap_reviews: List[Review] = []

    if store in ("both", "apple", "ios", "appstore"):
        ap_target = min(500, count // 2) if store == "both" else count
        ap_reviews = scrape_apple_store_reviews(apple_id, display_name, count=ap_target, country=country)

    if store in ("both", "google", "play", "playstore"):
        gp_target = count - len(ap_reviews) if store == "both" else count
        gp_reviews = scrape_google_play_reviews(play_id, display_name, count=gp_target, country=country)

    # If 'both' was requested and we still have a deficit, try topping up
    if store == "both":
        total_so_far = len(gp_reviews) + len(ap_reviews)
        if total_so_far < count:
            deficit = count - total_so_far
            more_gp = scrape_google_play_reviews(play_id, display_name, count=len(gp_reviews) + deficit, country=country)
            gp_reviews = more_gp

    # Interleave reviews chronologically or alternating
    all_reviews: List[Review] = []
    if store == "both":
        # Alternate items to give a balanced dataset from both stores
        i, j = 0, 0
        while i < len(gp_reviews) or j < len(ap_reviews):
            if i < len(gp_reviews):
                all_reviews.append(gp_reviews[i])
                i += 1
            if j < len(ap_reviews):
                all_reviews.append(ap_reviews[j])
                j += 1
    elif store in ("apple", "ios", "appstore"):
        all_reviews = ap_reviews
    else:
        all_reviews = gp_reviews

    # Fallback to curated dataset if both stores returned too few reviews (e.g., offline network)
    if len(all_reviews) < 10:
        logger.info("Live scraping returned fewer than 10 reviews; loading fallback mutual fund dataset.")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_csv = os.path.join(base_dir, "reviews.csv")
        if os.path.exists(default_csv):
            from analyzer import load_reviews_from_csv
            all_reviews = load_reviews_from_csv(default_csv)
            display_name = f"{display_name} (Curated Mutual Fund Dataset)"

    # Trim to requested count if exceeded
    if len(all_reviews) > count:
        all_reviews = all_reviews[:count]

    # Save to CSV
    if save_csv_path and all_reviews:
        os.makedirs(os.path.dirname(save_csv_path), exist_ok=True)
        with open(save_csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "reviewer", "rating", "review_text", "source"])
            for r in all_reviews:
                writer.writerow([r.date, r.reviewer, r.rating, r.review_text, r.source])

    google_count = sum(1 for r in all_reviews if "Google Play" in r.source)
    apple_count = sum(1 for r in all_reviews if "Apple App Store" in r.source)
    other_count = len(all_reviews) - google_count - apple_count

    date_range = f"{all_reviews[0].date} to {all_reviews[-1].date}" if all_reviews else "N/A"

    meta = {
        "app_name": display_name,
        "play_id": play_id,
        "apple_id": apple_id,
        "store": store,
        "total_count": len(all_reviews),
        "google_count": google_count,
        "apple_count": apple_count,
        "other_count": other_count,
        "date_range": date_range
    }

    return all_reviews, meta
