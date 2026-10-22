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
from llm_client import generate_ai_completion, get_active_provider_info, LLMError

load_dotenv()
logger = logging.getLogger("analyzer")


def load_reviews_from_csv(filepath: str) -> List[Review]:
    """Load and parse reviews from a CSV file, skipping rows without review text."""
    reviews = []
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {(k or "").strip().lower(): (v or "") for k, v in row.items()}
            text = row.get("review_text", "").strip()
            if not text:
                continue
            try:
                rating_val = min(5, max(1, int(float(row.get("rating", "3").strip()))))
            except Exception:
                rating_val = 3
            reviews.append(Review(
                date=row.get("date", "").strip() or "Unknown",
                reviewer=row.get("reviewer", "").strip() or "Anonymous",
                rating=rating_val,
                review_text=text,
                source=row.get("source", "").strip() or "Unknown"
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

    known_dates = sorted(r.date for r in reviews if r.date and r.date != "Unknown")
    date_range = f"{known_dates[0]} to {known_dates[-1]}" if known_dates else "N/A"
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

    last_error = ""
    for attempt in range(2):
        attempt_prompt = prompt if attempt == 0 else (
            prompt + f"\n\nYour previous answer was invalid ({last_error}). "
            "Return the COMPLETE JSON object with every key from the schema, keeping descriptions short."
        )
        raw_result, provider_used = await generate_ai_completion(
            prompt=attempt_prompt,
            system_prompt="You are a senior product intelligence AI. Return strictly valid JSON.",
            max_tokens=4000
        )
        result_data = _parse_json_object(raw_result)
        problem = _missing_required(result_data)
        if not problem:
            break
        last_error = problem
        logger.warning(f"Analysis attempt {attempt + 1} from {provider_used} unusable: {problem}")
    else:
        # Keep whatever usable themes we got; fail only if there is nothing to show
        if not isinstance(result_data, dict) or not _valid_themes(result_data.get("themes")):
            raise LLMError(
                "invalid_output",
                "The AI returned an incomplete analysis twice. Please retry — this is usually temporary.",
                provider_used, True, last_error
            )

    result = _normalize_analysis(result_data, metrics, sampled_reviews)
    logger.info(f"AI review analysis completed successfully using provider: {provider_used}")
    return result


def _parse_json_object(raw: str):
    """Extract a JSON object from a model response, tolerating code fences and minor syntax errors."""
    text = (raw or "").strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        import json_repair
        data = json_repair.loads(text)
        if isinstance(data, str):
            data = json_repair.loads(data)
        return data
    except Exception:
        return None


def _valid_themes(themes) -> bool:
    return isinstance(themes, list) and any(isinstance(t, dict) and t.get("name") for t in themes)


def _missing_required(data) -> str:
    """Describe what is missing from a parsed analysis, or '' if it is complete."""
    if not isinstance(data, dict):
        return "response was not a JSON object"
    missing = []
    if not _valid_themes(data.get("themes")):
        missing.append("themes")
    if not isinstance(data.get("fee_confusion"), dict) or not data["fee_confusion"].get("fee_name"):
        missing.append("fee_confusion")
    if not isinstance(data.get("user_quotes"), list) or not data["user_quotes"]:
        missing.append("user_quotes")
    return f"missing or empty: {', '.join(missing)}" if missing else ""


def _to_int(value, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip("~+ ")))
    except Exception:
        return default


def _to_float(value, default: float = 0.0) -> float:
    try:
        return round(float(str(value).strip("~+ ")), 2)
    except Exception:
        return default


def _normalize_theme(t, total: int) -> Optional[Dict]:
    if isinstance(t, str) and t.strip():
        t = {"name": t.strip()}
    if not isinstance(t, dict) or not str(t.get("name", "")).strip():
        return None
    name = str(t["name"]).strip()
    keywords = t.get("sample_keywords") or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    sentiment = str(t.get("sentiment", "mixed")).lower()
    return {
        "name": name,
        "description": str(t.get("description") or f"Customer feedback regarding {name}"),
        "review_count": _to_int(t.get("review_count"), max(1, total // 10)),
        "avg_rating": _to_float(t.get("avg_rating"), 2.5),
        "sentiment": sentiment if sentiment in ("negative", "positive", "mixed") else "mixed",
        "sample_keywords": [str(k) for k in keywords][:8] or [name.lower()],
    }


def _normalize_analysis(data: Dict, metrics: Dict, sampled: List[Review]) -> AnalysisResult:
    """Coerce a model response into a valid AnalysisResult, filling gaps from the real dataset."""
    total = metrics["total"]

    themes = [nt for nt in (_normalize_theme(t, total) for t in data.get("themes") or []) if nt]
    themes_by_name = {t["name"].lower(): t for t in themes}

    top = []
    for item in data.get("top_themes") or []:
        raw_name = item if isinstance(item, str) else item.get("name", "") if isinstance(item, dict) else ""
        nt = themes_by_name.get(str(raw_name).strip().lower()) or _normalize_theme(item, total)
        if nt and nt["name"].lower() not in {x["name"].lower() for x in top}:
            top.append(nt)
    for t in sorted(themes, key=lambda x: x["review_count"], reverse=True):
        if len(top) >= 3:
            break
        if t["name"].lower() not in {x["name"].lower() for x in top}:
            top.append(t)

    quotes = []
    for q in data.get("user_quotes") or []:
        if isinstance(q, dict) and str(q.get("quote", "")).strip():
            quotes.append({
                "quote": str(q["quote"]).strip(),
                "reviewer": str(q.get("reviewer") or "Anonymous"),
                "rating": min(5, max(1, _to_int(q.get("rating"), 3))),
                "theme": str(q.get("theme") or (top[0]["name"] if top else "General")),
            })
    # Back-fill with real verbatim reviews from the sample (never invented text)
    for r in sorted(sampled, key=lambda x: x.rating):
        if len(quotes) >= 3:
            break
        if r.review_text not in {q["quote"] for q in quotes}:
            text = r.review_text.replace("\n", " ").strip()
            quotes.append({
                "quote": text if len(text) <= 200 else text[:197] + "...",
                "reviewer": r.reviewer, "rating": r.rating,
                "theme": top[0]["name"] if top else "General",
            })

    fc = data.get("fee_confusion") if isinstance(data.get("fee_confusion"), dict) else {}
    kw = metrics.get("keyword_frequencies", {})
    fee_mentions = sum(kw.get(k, 0) for k in ("exit load", "charge", "fee", "hidden", "gst", "deduction", "brokerage"))
    misconceptions = fc.get("common_misconceptions") or []
    if isinstance(misconceptions, str):
        misconceptions = [misconceptions]
    severity = str(fc.get("severity", "")).lower()
    if severity not in ("low", "medium", "high", "critical"):
        severity = "high" if fee_mentions >= total * 0.1 else "medium"
    fee_confusion = {
        "fee_name": str(fc.get("fee_name") or "Charges & Exit Load"),
        "confusion_summary": str(fc.get("confusion_summary") or
            f"Fee-related terms are mentioned {fee_mentions} times across {total} reviews, indicating unclear charge communication."),
        "affected_review_count": _to_int(fc.get("affected_review_count"), fee_mentions),
        "common_misconceptions": [str(m) for m in misconceptions if str(m).strip()][:6] or
            ["Users are unsure which charges apply to their transactions."],
        "severity": severity,
    }

    return AnalysisResult(
        total_reviews=total,
        date_range=metrics["date_range"],
        themes=themes,
        top_themes=top[:3],
        user_quotes=quotes[:3],
        fee_confusion=fee_confusion,
    )
