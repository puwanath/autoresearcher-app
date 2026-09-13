from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from app.schemas.research import (
    AnalysisReport,
    CompetitorInfo,
    ExtractedProduct,
    PriceStats,
    ReportArtifact,
    ResearchPlan,
    ResearchRequest,
    ScrapedPage,
    SearchResult,
)


class ResearchState(TypedDict, total=False):
    task_id: str
    request: ResearchRequest
    plan: ResearchPlan
    iteration: int
    search_results: list[SearchResult]
    visited_urls: list[str]
    pages: list[ScrapedPage]
    products: list[ExtractedProduct]
    competitors: list[CompetitorInfo]
    price_stats: PriceStats
    analysis: AnalysisReport
    report_markdown: str
    artifacts: list[ReportArtifact]
    events: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
    # loop bookkeeping (underscore = not part of the public result)
    _new_queries: list[str]
    _extracted_urls: list[str]
