from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

import pytest
from pydantic import BaseModel

from app.config import Settings
from app.schemas.research import (
    SWOT,
    AnalysisReport,
    CompetitorAssessment,
    CompetitorInfo,
    ExtractedProduct,
    PageExtraction,
    Price,
    ResearchPlan,
    SalesChannel,
    ScrapedPage,
    SearchResult,
)

T = TypeVar("T", bound=BaseModel)
FIXTURES = Path(__file__).parent / "fixtures"


class FakeLLM:
    """Returns canned structured outputs keyed by schema; records prompts for assertions."""

    def __init__(self, products_per_page: int = 2):
        self.calls: list[tuple[str, list[dict]]] = []
        self.products_per_page = products_per_page
        self.refine_calls = 0

    async def chat(self, messages, **kw) -> str:
        self.calls.append(("chat", messages))
        return "ok"

    async def chat_json(self, messages, schema: type[T], **kw) -> T:
        self.calls.append((schema.__name__, messages))
        user = json.loads(messages[-1]["content"])
        if schema is ResearchPlan:
            return ResearchPlan(
                input_type="keyword",
                product_category="sunscreen",
                search_queries=["q1", "q2"],
                target_channels=["Shopee"],
                rationale="r",
            )
        if schema.__name__ == "_RefinedQueries":
            self.refine_calls += 1
            return schema(search_queries=[f"q-refined-{self.refine_calls}"], rationale="thin data")
        if schema is PageExtraction:
            url = user["page_url"]
            return PageExtraction(
                is_relevant=True,
                page_type="product",
                competitors=[CompetitorInfo(brand_name="BrandA", market_segment="Mass")],
                products=[
                    ExtractedProduct(
                        product_name=f"Product {i} from {url}",
                        brand_name="BrandA" if i % 2 else "BRANDA",
                        price=Price(amount=100.0 * (i + 1)),
                        sales_channels=[SalesChannel(channel_name="Shopee", channel_url=url)],
                    )
                    for i in range(self.products_per_page)
                ],
            )
        if schema is AnalysisReport:
            assert "price_stats" in user and "brand_summary" in user
            return AnalysisReport(
                title="Report",
                executive_summary="sum",
                key_findings=["k"],
                market_overview="mo",
                competition_type="price",
                competitors=[CompetitorAssessment(brand_name="BrandA", price_position="mid-range")],
                pricing_insight="pi",
                recommended_price_range_thb="100-200",
                channel_insight="ci",
                recommended_channels=["Shopee"],
                sentiment_summary="ss",
                swot=SWOT(strengths=["s"]),
                recommendations=["r"],
                action_plan=["a"],
            )
        raise AssertionError(f"unexpected schema {schema}")


async def fake_search(queries, max_results=8):
    return [
        SearchResult(title=f"t-{q}-{i}", url=f"https://example.com/{q}/{i}", query=q) for q in queries for i in range(2)
    ]


async def fake_fetch(urls, task_id):
    return [ScrapedPage(url=u, final_url=u, title="T", text="x" * 500, status_code=200) for u in urls]


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path, max_iterations=2, max_pages=4, use_playwright=False, _env_file=None)
