from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.agents.stats import brand_price_table
from app.schemas.research import AnalysisReport, ExtractedProduct, ImageAsset, PriceStats, ResearchRequest, ScrapedPage

_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=select_autoescape(enabled_extensions=()),  # markdown: no HTML escaping
    trim_blocks=False,
    lstrip_blocks=False,
)


def _thb(value, currency: str = "THB") -> str:
    if value is None:
        return "-"
    sym = "฿" if currency == "THB" else f"{currency} "
    return f"{sym}{value:,.0f}" if float(value).is_integer() else f"{sym}{value:,.2f}"


def _trunc(s: str, n: int) -> str:
    s = (s or "").replace("|", "/").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


_env.filters["thb"] = _thb
_env.filters["trunc"] = _trunc


def render_markdown(
    *,
    request: ResearchRequest,
    analysis: AnalysisReport,
    products: list[ExtractedProduct],
    stats: PriceStats | None,
    pages: list[ScrapedPage],
    max_rows: int = 40,
    charts: dict[str, str] | None = None,
    images: list[ImageAsset] | None = None,
) -> str:
    channel_counts = Counter(c.channel_name for p in products for c in p.sales_channels).most_common()
    ok_pages = [p for p in pages if p.ok]
    return _env.get_template("report.md.j2").render(
        a=analysis,
        req=request,
        products=sorted(products, key=lambda p: (p.price.amount is None, p.price.amount or 0)),
        brand_rows=brand_price_table(products),
        stats=stats,
        channel_counts=channel_counts,
        pages_ok=len(ok_pages),
        pages_total=len(pages),
        sources=ok_pages,
        max_rows=max_rows,
        charts=charts or {},
        images=images or [],
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )
