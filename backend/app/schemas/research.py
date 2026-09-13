"""Pydantic models shared by the agents, LLM structured outputs, API and reports.

Field names follow the PRD §5 JSON schemas (Competitor Info / Product Price / Image Asset).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class OutputFormat(StrEnum):
    markdown = "md"
    pdf = "pdf"


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Keyword, URL, SKU or competitor name")
    target_competitors: list[str] = Field(default_factory=list)
    product_category: str | None = None
    our_brand: str | None = Field(None, description="The user's own brand, for benchmarking")
    language: Literal["th", "en"] = "th"
    output_formats: list[OutputFormat] = Field(default_factory=lambda: [OutputFormat.markdown])


# ---------- Stage 1: Planning ----------


class ResearchPlan(BaseModel):
    input_type: Literal["keyword", "url", "sku", "competitor_name", "mixed"]
    product_category: str
    search_queries: list[str] = Field(..., description="Expanded search queries, mixed Thai/English")
    direct_urls: list[str] = Field(default_factory=list, description="URLs to scrape directly")
    target_channels: list[str] = Field(
        default_factory=list, description="e.g. Shopee, Lazada, TikTok Shop, Official Website, Blog Review"
    )
    rationale: str


# ---------- Stage 2: Research ----------


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    query: str = ""


class ScrapedPage(BaseModel):
    url: str
    final_url: str
    title: str = ""
    text: str = ""
    json_ld: list[dict] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    status_code: int = 0
    fetched_with: Literal["httpx", "playwright"] = "httpx"
    raw_path: str | None = None
    error: str | None = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def ok(self) -> bool:
        return self.error is None and len(self.text) > 200


# ---------- Stage 3: Extraction (PRD §5.2 Product Price schema) ----------


class Price(BaseModel):
    amount: float | None = None
    currency: str = "THB"
    original_price: float | None = None
    discount_percentage: float | None = Field(None, ge=0, le=100)
    unit_price: float | None = Field(None, description="Price per ml/g/unit if derivable")


class SalesChannel(BaseModel):
    channel_name: str
    channel_url: str | None = None
    availability: Literal["In Stock", "Out of Stock", "Pre-order", "Unknown"] = "Unknown"
    seller_rating: float | None = None


class Promotion(BaseModel):
    promo_type: str
    promo_description: str = ""
    valid_until: str | None = None


class ExtractedProduct(BaseModel):
    product_name: str
    brand_name: str | None = None
    variant: str | None = None
    category: str | None = None
    price: Price = Field(default_factory=Price)
    sales_channels: list[SalesChannel] = Field(default_factory=list)
    promotions: list[Promotion] = Field(default_factory=list)
    specs: dict[str, str] = Field(default_factory=dict)
    rating: float | None = None
    review_count: int | None = None
    image_urls: list[str] = Field(default_factory=list)
    review_highlights: list[str] = Field(default_factory=list, description="Short quotes / sentiment cues")
    data_source_url: str = ""


class CompetitorInfo(BaseModel):
    brand_name: str
    website_url: str | None = None
    market_segment: str | None = Field(None, description="e.g. Premium, Mass Market")
    target_audience: list[str] = Field(default_factory=list)
    description: str | None = None


class PageExtraction(BaseModel):
    """What the LLM returns for one scraped page."""

    is_relevant: bool = Field(..., description="Page contains data about the researched product/market")
    page_type: Literal["product", "listing", "review", "brand", "news", "other"] = "other"
    competitors: list[CompetitorInfo] = Field(default_factory=list)
    products: list[ExtractedProduct] = Field(default_factory=list)
    notes: str = ""


# ---------- Stage 4: Analysis ----------


class PriceStats(BaseModel):
    currency: str = "THB"
    min: float | None = None
    max: float | None = None
    median: float | None = None
    mean: float | None = None
    sample_size: int = 0


class CompetitorAssessment(BaseModel):
    brand_name: str
    price_position: Literal["budget", "mid-range", "premium", "unknown"] = "unknown"
    price_range_thb: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    sentiment: Literal["positive", "neutral", "negative", "mixed", "unknown"] = "unknown"
    sentiment_note: str = ""


class SWOT(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[str]
    market_overview: str
    competition_type: Literal["price", "quality", "brand", "channel", "mixed"]
    competitors: list[CompetitorAssessment]
    pricing_insight: str
    recommended_price_range_thb: str
    channel_insight: str
    recommended_channels: list[str]
    sentiment_summary: str
    swot: SWOT = Field(..., description="SWOT for the user's brand entering / competing in this market")
    recommendations: list[str]
    action_plan: list[str]
    data_gaps: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


# ---------- Stage 5: Output ----------


class ReportArtifact(BaseModel):
    format: OutputFormat
    path: str
    size_bytes: int


class ResearchResult(BaseModel):
    task_id: str
    request: ResearchRequest
    plan: ResearchPlan | None = None
    pages_fetched: int = 0
    products: list[ExtractedProduct] = Field(default_factory=list)
    competitors: list[CompetitorInfo] = Field(default_factory=list)
    price_stats: PriceStats | None = None
    analysis: AnalysisReport | None = None
    report_markdown: str | None = None
    artifacts: list[ReportArtifact] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    pages: list[ScrapedPage] = Field(default_factory=list, exclude=True)  # persisted, not serialised


__all__ = [n for n in dir() if n[0].isupper()] + ["HttpUrl"]
