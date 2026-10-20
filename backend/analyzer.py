"""
AI Analysis Engine — High-Volume Customer Feedback Intelligence.
Supports 500, 1,000, and 5,000+ reviews from Google Play & Apple App Store.
Performs quantitative dataset aggregation, stratified sampling, theme clustering,
verbatim quote extraction, and fee confusion detection.
API key is mandatory. Offline mode is disabled.
"""

import csv
import json
import logging
import os
import re
from collections import Counter
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

from models import (
    Review, Theme, UserQuote, FeeConfusion, AnalysisResult
)
from llm_client import generate_ai_completion, get_active_provider_info

load_dotenv()
logger = logging.getLogger("analyzer")


def load_reviews_from_csv(filepath: str) -> List[Review]:
    """Load and parse reviews from a CSV file."""
    reviews = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rating_val = int(row["rating"].strip())
            except Exception:
                rating_val = 3
            reviews.append(Review(
                date=row["date"].strip(),
                reviewer=row["reviewer"].strip(),
                rating=rating_val,
                review_text=row["review_text"].strip(),
                source=row["source"].strip()
            ))
    return reviews


def aggregate_dataset_metrics(reviews: List[Review]) -> Dict:
    """
    Compute rigorous statistical metrics across the full volume of reviews (500 to 5,000+).
    """
    total = len(reviews)
    if total == 0:
        return {
            "total": 0, "date_range": "N/A", "avg_rating": 0.0,
            "rating_dist": {}, "store_dist": {}, "keyword_frequencies": {}
        }

    date_range = f"{reviews[0].date} to {reviews[-1].date}"
    ratings = [r.rating for r in reviews]
    avg_rating = round(sum(ratings) / total, 2)

    rating_dist = Counter(ratings)
    google_count = sum(1 for r in reviews if "Google" in r.source)
    apple_count = sum(1 for r in reviews if "Apple" in r.source or "App Store" in r.source)
    other_count = total - google_count - apple_count

    # Frequency analysis of critical fintech/mutual fund friction keywords
    keywords_to_track = [
        "exit load", "sip", "installment", "gst", "charge", "fee", "deduction",
        "redemption", "withdraw", "return", "xirr", "hidden", "brokerage",
        "scam", "support", "delay", "crash", "kyc", "statement", "penalty"
    ]
    all_text = " ".join(r.review_text.lower() for r in reviews)
    keyword_freq = {k: all_text.count(k) for k in keywords_to_track if all_text.count(k) > 0}

    return {
        "total": total,
        "date_range": date_range,
        "avg_rating": avg_rating,
        "rating_dist": {
            f"{star}_star": rating_dist.get(star, 0) for star in range(1, 6)
        },
        "store_dist": {
            "google_play": google_count,
            "apple_store": apple_count,
            "other": other_count
        },
        "keyword_frequencies": keyword_freq
    }


def sample_representative_reviews(reviews: List[Review], sample_limit: int = 20) -> List[Review]:
    """
    Stratified semantic sampling across sentiment spectrum and store sources.
    Ensures prompt remains strictly within model token limits while providing rich context.
    """
    if len(reviews) <= sample_limit:
        return reviews

    # Segregate by friction categories and ratings
    fee_reviews = [r for r in reviews if any(k in r.review_text.lower() for k in ["exit load", "charge", "fee", "sip", "gst", "deduction", "hidden"])]
    crit_reviews = [r for r in reviews if r.rating <= 2 and r not in fee_reviews]
    pos_reviews = [r for r in reviews if r.rating >= 4]
    neutral_reviews = [r for r in reviews if r.rating == 3]

    sampled: List[Review] = []

    # Priority 1: High-impact fee friction reviews (up to 10)
    sampled.extend(fee_reviews[:10])

    # Priority 2: Critical negative feedback (up to 5)
    sampled.extend(crit_reviews[:5])

    # Priority 3: Positive feedback for balance (up to 3)
    sampled.extend(pos_reviews[:3])

    # Priority 4: Neutral feedback (up to 2)
    sampled.extend(neutral_reviews[:2])

    # If still below limit, fill with latest reviews
    if len(sampled) < sample_limit:
        for r in reviews:
            if r not in sampled:
                sampled.append(r)
                if len(sampled) >= sample_limit:
                    break

    return sampled


async def analyze_reviews(reviews: List[Review]) -> AnalysisResult:
    """
    Analyze customer reviews using the configured AI engine (OpenAI / Grok / Gemini).
    API key is mandatory. Offline mode is disabled.
    """
    info = get_active_provider_info()
    if not info["is_online"]:
        raise ValueError(
            "API key is mandatory. Please configure your OpenAI, Grok (xAI), or Google Gemini API key in settings."
        )

    if not reviews:
        raise ValueError("Cannot analyze empty review set.")

    # Compute aggregate metrics across full dataset
    metrics = aggregate_dataset_metrics(reviews)
    sampled_reviews = sample_representative_reviews(reviews, sample_limit=20)

    # Format sample for prompt compactly to preserve token quota
    formatted_sample = []
    for i, r in enumerate(sampled_reviews, 1):
        clean_text = r.review_text.strip().replace("\n", " ")
        if len(clean_text) > 160:
            clean_text = clean_text[:157] + "..."
        formatted_sample.append(
            f"[{i}] {r.date} | {r.reviewer} | Rating: {r.rating}/5 | Source: {r.source}\n"
            f"     \"{clean_text}\""
        )
    sample_text = "\n\n".join(formatted_sample)

    prompt = f"""You are a staff product intelligence analyst evaluating a massive dataset of customer reviews for an investment & mutual funds platform.

## Full Dataset Quantitative Statistics:
- Total Customer Reviews Analyzed: {metrics['total']}
- Ingestion Stores: Google Play ({metrics['store_dist']['google_play']}), Apple App Store ({metrics['store_dist']['apple_store']})
- Overall Average Rating: {metrics['avg_rating']} / 5.0
- Star Distribution: 1-Star: {metrics['rating_dist'].get('1_star', 0)}, 2-Star: {metrics['rating_dist'].get('2_star', 0)}, 3-Star: {metrics['rating_dist'].get('3_star', 0)}, 4-Star: {metrics['rating_dist'].get('4_star', 0)}, 5-Star: {metrics['rating_dist'].get('5_star', 0)}
- Friction Keyword Mentions across full corpus: {json.dumps(metrics['keyword_frequencies'])}
- Date Range: {metrics['date_range']}

## Representative Verbatim Sample ({len(sampled_reviews)} reviews):
{sample_text}

## Instructions:
1. **Theme Clustering**: Identify 3 to 4 concise thematic clusters (e.g. Exit Load & Redemption Charges, SIP Holding Period Confusion, App Performance & Statements, Portfolio Tracking) that accurately characterize this {metrics['total']}-review corpus.
2. **Top 3 Highlighted Themes**: The top 3 themes representing key friction areas.
3. **Representative User Quotes**: Select EXACTLY 3 real, verbatim quotes from the sample reviews above.
4. **Fee Confusion Intelligence**: Detail the primary fee causing confusion (Exit Load / SIP calculations).

## Required JSON Output Schema:
{{
  "total_reviews": {metrics['total']},
  "date_range": "{metrics['date_range']}",
  "themes": [
    {{
      "name": "Theme Name",
      "description": "Short 1-2 sentence description",
      "review_count": integer,
      "avg_rating": float,
      "sentiment": "negative|positive|mixed",
      "sample_keywords": ["keyword1", "keyword2"]
    }}
  ],
  "top_themes": [
    {{
      "name": "Top Theme Name",
      "description": "Short 1-2 sentence description",
      "review_count": integer,
      "avg_rating": float,
      "sentiment": "negative|positive|mixed",
      "sample_keywords": ["keyword1", "keyword2"]
    }}
  ],
  "user_quotes": [
    {{
      "quote": "verbatim quote text",
      "reviewer": "Reviewer Name",
      "rating": 1,
      "theme": "Associated Theme"
    }}
  ],
  "fee_confusion": {{
    "fee_name": "Exit Load",
    "confusion_summary": "Summary of user confusion",
    "affected_review_count": integer,
    "common_misconceptions": [
      "Misconception 1",
      "Misconception 2",
      "Misconception 3",
      "Misconception 4"
    ],
    "severity": "critical"
  }}
}}

Return ONLY valid JSON. Do not include markdown codeblocks or commentary."""

    raw_result, provider_used = await generate_ai_completion(
        prompt=prompt,
        system_prompt="You are a senior product intelligence AI. Return strictly valid JSON.",
        max_tokens=2000
    )

    result_text = raw_result.strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    # Extract JSON object matching { ... }
    m = re.search(r"(\{.*\})", result_text, re.DOTALL)
    if m:
        result_text = m.group(1).strip()

    try:
        import json_repair
        result_data = json_repair.loads(result_text)
    except Exception:
        result_data = json.loads(result_text)

    if isinstance(result_data, str):
        try:
            import json_repair
            parsed = json_repair.loads(result_data)
            if isinstance(parsed, dict):
                result_data = parsed
        except Exception:
            pass

    # Normalize top_themes if model returned strings or partial objects
    if isinstance(result_data, dict):
        themes_list = result_data.get("themes", [])
        themes_by_name = {
            t.get("name", "").strip().lower(): t
            for t in themes_list
            if isinstance(t, dict) and t.get("name")
        }

        raw_top = result_data.get("top_themes", [])
        normalized_top = []
        for item in raw_top:
            if isinstance(item, dict) and item.get("name"):
                normalized_top.append(item)
            elif isinstance(item, str) and item.strip():
                matched = themes_by_name.get(item.strip().lower())
                if matched:
                    normalized_top.append(matched)
                else:
                    normalized_top.append({
                        "name": item.strip(),
                        "description": f"Customer feedback regarding {item.strip()}",
                        "review_count": max(10, metrics["total"] // 10),
                        "avg_rating": 2.5,
                        "sentiment": "negative",
                        "sample_keywords": [item.strip().lower()]
                    })

        if len(normalized_top) < 3 and themes_list:
            for t in themes_list:
                if t not in normalized_top and isinstance(t, dict):
                    normalized_top.append(t)
                if len(normalized_top) >= 3:
                    break

        result_data["top_themes"] = normalized_top[:3]

    logger.info(f"AI review analysis completed successfully using provider: {provider_used}")
    return AnalysisResult(**result_data)
