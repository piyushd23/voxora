"""
Pydantic models for the Milestone 5 AI workflow.
Defines structured schemas for review analysis, content generation, and MCP actions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


# ─── Review Input ────────────────────────────────────────────────────────────

class Review(BaseModel):
    """A single customer review from the CSV."""
    date: str
    reviewer: str
    rating: int
    review_text: str
    source: str


# ─── Theme Clustering ────────────────────────────────────────────────────────

class Theme(BaseModel):
    """A clustered theme extracted from reviews."""
    name: str = Field(description="Short descriptive name for the theme")
    description: str = Field(description="1-2 sentence description of the theme")
    review_count: int = Field(description="Number of reviews in this cluster")
    avg_rating: float = Field(description="Average rating of reviews in this theme")
    sentiment: str = Field(description="Overall sentiment: positive, negative, or mixed")
    sample_keywords: List[str] = Field(description="Key phrases associated with this theme")


class UserQuote(BaseModel):
    """A real user quote extracted from reviews."""
    quote: str = Field(description="Exact quote from the review")
    reviewer: str = Field(description="Name of the reviewer")
    rating: int = Field(description="Rating given by the reviewer")
    theme: str = Field(description="Theme this quote is most relevant to")


class FeeConfusion(BaseModel):
    """Identified fee/charge confusion from reviews."""
    fee_name: str = Field(description="Name of the fee/charge causing confusion")
    confusion_summary: str = Field(description="Summary of what users are confused about")
    affected_review_count: int = Field(description="Number of reviews mentioning this confusion")
    common_misconceptions: List[str] = Field(description="List of common misconceptions")
    severity: str = Field(description="Severity level: low, medium, high, critical")


class AnalysisResult(BaseModel):
    """Complete analysis result from processing reviews."""
    total_reviews: int
    date_range: str
    themes: List[Theme] = Field(description="All identified themes (max 5)")
    top_themes: List[Theme] = Field(description="Top 3 themes by review count")
    user_quotes: List[UserQuote] = Field(description="3 representative user quotes")
    fee_confusion: FeeConfusion = Field(description="Identified fee/charge confusion")


# ─── Generated Content ──────────────────────────────────────────────────────

class WeeklyPulse(BaseModel):
    """Weekly internal product pulse note."""
    week_of: str = Field(description="Week date string")
    summary: str = Field(description="Summary of top themes (2-3 sentences)")
    top_themes_summary: List[str] = Field(description="Bullet points for each top theme")
    supporting_quotes: List[str] = Field(description="3 user quotes with attribution")
    key_observation: str = Field(description="What's going wrong or trending")
    action_ideas: List[str] = Field(description="3 action ideas for the product team")
    word_count: int = Field(description="Total word count of the pulse")


class FeeExplanation(BaseModel):
    """Structured explanation for the identified fee confusion."""
    fee_name: str
    explanation_bullets: List[str] = Field(description="Up to 6 bullet points explaining the fee")
    source_links: List[str] = Field(description="2 official source links")
    last_checked: str = Field(description="Date when sources were last verified")
    tone: str = Field(default="neutral, facts-only")


class GeneratedContent(BaseModel):
    """All generated content from the workflow."""
    weekly_pulse: WeeklyPulse
    fee_explanation: FeeExplanation


# ─── MCP Actions ─────────────────────────────────────────────────────────────

class MCPAction(BaseModel):
    """An MCP tool action pending approval."""
    action_id: str
    tool_name: str
    description: str
    parameters: dict
    status: str = Field(default="pending")  # pending, approved, rejected, executed


class MCPActionRequest(BaseModel):
    """Request to approve/reject an MCP action."""
    action_id: str
    approved: bool


class WorkflowPayload(BaseModel):
    """Complete payload for MCP logging — the JSON output structure."""
    date: str
    top_themes: List[str]
    weekly_pulse: str
    identified_fee_issue: str
    explanation_bullets: List[str]
    source_links: List[str]


class EmailDraft(BaseModel):
    """Email draft structure."""
    subject: str
    to: str = Field(default="product-team@company.com")
    cc: Optional[str] = Field(default="support-leads@company.com")
    body: str
