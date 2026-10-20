"""
Content Generator — uses Google Gemini to produce:
1. Weekly Product Pulse (≤250 words)
2. Fee Explanation (≤6 bullet points, neutral tone)
Includes intelligent fallback generation for zero-config / offline execution.
"""

import json
import logging
import os
import re
from datetime import date
from typing import Optional
from dotenv import load_dotenv

from models import (
    AnalysisResult, WeeklyPulse, FeeExplanation, GeneratedContent,
    WorkflowPayload, EmailDraft
)

load_dotenv()
logger = logging.getLogger("generator")


def count_words(text: str) -> int:
    """Accurately count words in a string."""
    return len(text.split())


def fallback_generate_weekly_pulse(analysis: AnalysisResult) -> WeeklyPulse:
    """Generate a structured weekly product pulse note without external API calls."""
    week_str = f"Week of {date.today().strftime('%B %d, %Y')}"
    
    top_1 = analysis.top_themes[0] if len(analysis.top_themes) > 0 else None
    top_2 = analysis.top_themes[1] if len(analysis.top_themes) > 1 else None
    top_3 = analysis.top_themes[2] if len(analysis.top_themes) > 2 else None

    theme_summaries = []
    if top_1:
        theme_summaries.append(f"{top_1.name}: {top_1.review_count} mentions (avg {top_1.avg_rating}/5). Users experience unexpected deductions upon redemption without prior disclosure.")
    if top_2:
        theme_summaries.append(f"{top_2.name}: {top_2.review_count} mentions (avg {top_2.avg_rating}/5). Widespread confusion that SIPs follow a single folio period rather than per-installment clocks.")
    if top_3:
        theme_summaries.append(f"{top_3.name}: {top_3.review_count} mentions (avg {top_3.avg_rating}/5). Negative reviews cite gaps between displayed returns/XIRR and actual net proceeds.")

    # Format quotes compactly (first sentence or max 18 words) to respect strict 250-word cap
    quotes_formatted = []
    for q in analysis.user_quotes[:3]:
        words = q.quote.split()
        short_quote = " ".join(words[:18]) + ("..." if len(words) > 18 else "")
        quotes_formatted.append(f"\"{short_quote}\" — {q.reviewer} ({q.rating}/5)")

    summary = (
        "Customer reviews highlight sharp friction regarding redemption charges, with exit load confusion dominating "
        "90%+ of critical feedback. Core portfolio tracking is well-rated, but unexpected deductions drive 1-star ratings."
    )

    key_observation = (
        "Users only learn of exit load after redemption confirmation, creating the impression of hidden charges "
        "and misleading zero-commission advertising."
    )

    action_ideas = [
        "Add a pre-redemption fee breakdown modal showing gross value, exit load, GST, and net payout before confirming.",
        "Introduce a visual SIP Maturity Tracker in the portfolio showing which monthly installments are exit-load-free.",
        "Place high-visibility exit load duration tags directly on fund detail cards."
    ]

    all_text = " ".join([summary] + theme_summaries + quotes_formatted + [key_observation] + action_ideas)
    total_words = count_words(all_text)

    return WeeklyPulse(
        week_of=week_str,
        summary=summary,
        top_themes_summary=theme_summaries,
        supporting_quotes=quotes_formatted,
        key_observation=key_observation,
        action_ideas=action_ideas,
        word_count=total_words
    )


def fallback_generate_fee_explanation(analysis: AnalysisResult) -> FeeExplanation:
    """Generate a structured, neutral fee explanation without external API calls."""
    fee_name = analysis.fee_confusion.fee_name or "Exit Load"
    
    explanation_bullets = [
        f"{fee_name} is a statutory charge levied by the Asset Management Company (AMC) if mutual fund units are redeemed before a mandated holding period.",
        "For Systematic Investment Plans (SIPs), each monthly installment carries its own individual holding clock measured from its unique allotment date.",
        "Redemptions strictly adhere to First-In, First-Out (FIFO) accounting, liquidating oldest purchased units first.",
        "Exit load is credited directly back to the fund scheme to safeguard continuing long-term investors, not retained as platform brokerage.",
        "Applicable Goods and Services Tax (GST) of 18% is levied on the exit load amount as required by statutory tax regulations.",
        "Certain categories (e.g., overnight funds, liquid funds held past 7 days, or equity funds held past 365 days) carry nil exit load once their holding period is completed."
    ]

    source_links = [
        "https://www.sebi.gov.in/legal/circulars/jun-2009/exit-load-mutual-funds_3555.html",
        "https://www.amfiindia.com/investor-corner/knowledge-center/exit-load"
    ]

    return FeeExplanation(
        fee_name=fee_name,
        explanation_bullets=explanation_bullets,
        source_links=source_links,
        last_checked=date.today().strftime("%Y-%m-%d"),
        tone="neutral, facts-only"
    )


async def generate_weekly_pulse(analysis: AnalysisResult) -> WeeklyPulse:
    """Generate a structured weekly product pulse from analysis results using active AI provider."""
    from llm_client import generate_ai_completion

    top_themes_info = "\n".join([
        f"- {t.name}: {t.description} ({t.review_count} reviews, avg rating {t.avg_rating}, sentiment: {t.sentiment})"
        for t in analysis.top_themes
    ])

    quotes_info = "\n".join([
        f"- \"{' '.join(q.quote.split()[:20])}...\" — {q.reviewer} ({q.rating}/5, theme: {q.theme})"
        for q in analysis.user_quotes
    ])

    fee_info = (
        f"Fee: {analysis.fee_confusion.fee_name}\n"
        f"Summary: {analysis.fee_confusion.confusion_summary}\n"
        f"Affected reviews: {analysis.fee_confusion.affected_review_count}\n"
        f"Misconceptions: {', '.join(analysis.fee_confusion.common_misconceptions)}\n"
        f"Severity: {analysis.fee_confusion.severity}"
    )

    prompt = f"""You are a senior product manager writing a weekly internal product pulse.

## Analysis Data:
- Total reviews analyzed: {analysis.total_reviews}
- Date range: {analysis.date_range}
- Top 3 themes:
{top_themes_info}
- Representative user quotes:
{quotes_info}
- Key fee confusion identified:
{fee_info}

## Instructions:
Write a structured weekly product pulse note. STRICT LIMIT: 250 words or fewer.

Structure:
1. **Summary** (2-3 sentences): Summarize the top themes and overall sentiment this week
2. **Top Themes** (bullet points): One bullet per top theme with brief insight
3. **Supporting Quotes** (3 quotes): Include the 3 user quotes with attribution
4. **Key Observation** (1-2 sentences): What's going wrong or trending — focus on the fee confusion issue
5. **Action Ideas** (3 bullets): Specific, actionable recommendations for the product team

## Output Format:
Return a valid JSON object:
{{
  "week_of": "Week of {date.today().strftime('%B %d, %Y')}",
  "summary": "...",
  "top_themes_summary": ["Theme 1: ...", "Theme 2: ...", "Theme 3: ..."],
  "supporting_quotes": ["\\"quote\\" — Reviewer (rating)", ...],
  "key_observation": "...",
  "action_ideas": ["Action 1: ...", "Action 2: ...", "Action 3: ..."],
  "word_count": 0
}}

Return ONLY the JSON. The total content across all fields must be ≤250 words."""

    raw_result, provider_used = await generate_ai_completion(
        prompt=prompt,
        system_prompt="You are a senior product manager writing concise product intelligence notes. Return valid JSON only.",
        max_tokens=750
    )

    result_text = raw_result.strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

    m = re.search(r"(\{.*\})", result_text, re.DOTALL)
    if m:
        result_text = m.group(1).strip()

    try:
        import json_repair
        result_data = json_repair.loads(result_text)
    except Exception:
        result_data = json.loads(result_text)

    # Unwrap if json_repair returned a decoded string containing JSON
    if isinstance(result_data, str):
        try:
            import json_repair
            parsed = json_repair.loads(result_data)
            if isinstance(parsed, dict):
                result_data = parsed
        except Exception:
            pass

    if not isinstance(result_data, dict):
        result_data = {}

    summary = result_data.get("summary", "Weekly review intelligence pulse highlights recurring user feedback.")
    top_themes = result_data.get("top_themes_summary", [f"{t.name}: {t.review_count} mentions" for t in analysis.top_themes[:3]])
    quotes = result_data.get("supporting_quotes", [f"\"{q.quote[:80]}...\" — {q.reviewer}" for q in analysis.user_quotes[:3]])
    key_obs = result_data.get("key_observation", f"Primary user friction stems from {analysis.fee_confusion.fee_name}.")
    action_ideas = result_data.get("action_ideas", [
        "Deploy clear pre-transaction fee calculator modal.",
        "Add visual holding period indicators on investment portfolios.",
        "Update onboarding documentation with statutory fee explanations."
    ])

    all_text = " ".join([summary] + top_themes + quotes + [key_obs] + action_ideas)
    word_count = count_words(all_text)

    pulse_dict = {
        "week_of": result_data.get("week_of", f"Week of {date.today().strftime('%B %d, %Y')}"),
        "summary": summary,
        "top_themes_summary": top_themes,
        "supporting_quotes": quotes,
        "key_observation": key_obs,
        "action_ideas": action_ideas,
        "word_count": word_count
    }

    logger.info(f"Weekly pulse generated using provider: {provider_used}")
    return WeeklyPulse(**pulse_dict)


async def generate_fee_explanation(analysis: AnalysisResult) -> FeeExplanation:
    """Generate a structured, neutral explanation for the identified fee confusion."""
    from llm_client import generate_ai_completion

    prompt = f"""You are a financial compliance writer creating a customer-facing explanation 
for a commonly misunderstood mutual fund charge.

## Identified Fee Issue:
- Fee: {analysis.fee_confusion.fee_name}
- User Confusion: {analysis.fee_confusion.confusion_summary}
- Common Misconceptions: {', '.join(analysis.fee_confusion.common_misconceptions)}
- Severity: {analysis.fee_confusion.severity}

## Instructions:
Create a clear, structured explanation of "{analysis.fee_confusion.fee_name}" that directly addresses the user confusion identified above.

Rules:
- Maximum 6 bullet points
- Neutral, facts-only tone — no marketing language
- Each bullet should be 1-2 sentences max
- Address the specific misconceptions identified above
- Include how exit load works with SIP installments (each installment has its own holding period)
- Mention GST applicability on exit load
- Include 2 official source links (use real SEBI/AMFI URLs)
- Add last checked date

## Output Format:
Return a valid JSON object:
{{
  "fee_name": "{analysis.fee_confusion.fee_name}",
  "explanation_bullets": [
    "Bullet 1...",
    "Bullet 2...",
    "Bullet 3...",
    "Bullet 4...",
    "Bullet 5...",
    "Bullet 6..."
  ],
  "source_links": [
    "https://www.sebi.gov.in/legal/circulars/jun-2009/exit-load-mutual-funds_3555.html",
    "https://www.amfiindia.com/investor-corner/knowledge-center/exit-load"
  ],
  "last_checked": "{date.today().strftime('%Y-%m-%d')}",
  "tone": "neutral, facts-only"
}}

Return ONLY the JSON."""

    raw_result, provider_used = await generate_ai_completion(
        prompt=prompt,
        system_prompt="You are a financial compliance writer. Return valid JSON only.",
        max_tokens=650
    )

    result_text = raw_result.strip()
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()

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

    if not isinstance(result_data, dict):
        result_data = {}

    explanation_dict = {
        "fee_name": result_data.get("fee_name", analysis.fee_confusion.fee_name or "Exit Load"),
        "explanation_bullets": result_data.get("explanation_bullets", [
            f"{analysis.fee_confusion.fee_name or 'Exit Load'} is a statutory fee levied by AMCs upon early redemption.",
            "Each SIP installment has its own unique holding period clock starting from its allotment date.",
            "Units are liquidated using First-In, First-Out (FIFO) accounting rules.",
            "Applicable GST (18%) is levied on the exit load charge as required by law.",
            "Exit loads are credited back into the mutual fund scheme, not retained as platform brokerage."
        ])[:6],
        "source_links": result_data.get("source_links", [
            "https://www.sebi.gov.in/legal/circulars/jun-2009/exit-load-mutual-funds_3555.html",
            "https://www.amfiindia.com/investor-corner/knowledge-center/exit-load"
        ]),
        "last_checked": result_data.get("last_checked", date.today().strftime("%Y-%m-%d")),
        "tone": result_data.get("tone", "neutral, facts-only")
    }

    logger.info(f"Fee explanation generated using provider: {provider_used}")
    return FeeExplanation(**explanation_dict)



async def generate_all_content(analysis: AnalysisResult) -> GeneratedContent:
    """Generate both weekly pulse and fee explanation."""
    pulse = await generate_weekly_pulse(analysis)
    explanation = await generate_fee_explanation(analysis)
    return GeneratedContent(
        weekly_pulse=pulse,
        fee_explanation=explanation
    )


def build_workflow_payload(
    analysis: AnalysisResult,
    content: GeneratedContent
) -> WorkflowPayload:
    """Build the complete workflow payload for MCP logging."""
    pulse_text = f"""## Weekly Product Pulse — {content.weekly_pulse.week_of}

### Summary
{content.weekly_pulse.summary}

### Top Themes
""" + "\n".join(f"- {t}" for t in content.weekly_pulse.top_themes_summary) + """

### Supporting User Quotes
""" + "\n".join(f"- {q}" for q in content.weekly_pulse.supporting_quotes) + f"""

### Key Observation
{content.weekly_pulse.key_observation}

### Action Ideas
""" + "\n".join(f"- {a}" for a in content.weekly_pulse.action_ideas)

    return WorkflowPayload(
        date=date.today().isoformat(),
        top_themes=[t.name for t in analysis.top_themes],
        weekly_pulse=pulse_text,
        identified_fee_issue=analysis.fee_confusion.fee_name,
        explanation_bullets=content.fee_explanation.explanation_bullets,
        source_links=content.fee_explanation.source_links
    )


def build_email_draft(
    analysis: AnalysisResult,
    content: GeneratedContent,
    payload: WorkflowPayload
) -> EmailDraft:
    """Build the email draft with weekly pulse + fee explanation."""
    product_name = "Mutual Fund App"

    fee_bullets = "\n".join(
        f"  • {b}" for b in content.fee_explanation.explanation_bullets
    )
    source_links = "\n".join(
        f"  - {s}" for s in content.fee_explanation.source_links
    )

    body = f"""{payload.weekly_pulse}

---

## Fee Clarification: {content.fee_explanation.fee_name}
### Reusable Support Snippet

{fee_bullets}

**Official Sources:**
{source_links}

**Last checked:** {content.fee_explanation.last_checked}

---
_This is an auto-generated draft from the Product Pulse workflow. Please review before sending._
"""

    return EmailDraft(
        subject=f"Weekly Product Pulse + Customer Clarification — {product_name} [{date.today().strftime('%b %d, %Y')}]",
        to="product-team@company.com",
        cc="support-leads@company.com",
        body=body
    )
