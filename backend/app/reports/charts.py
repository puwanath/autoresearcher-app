"""Dependency-free SVG charts for the report. Written as files next to the report so the Markdown stays
readable (`![..](chart-prices.svg)`) and WeasyPrint embeds them as vector graphics."""

from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from app.agents.stats import brand_price_table
from app.schemas.research import ExtractedProduct

FONT = "Sarabun, 'Noto Sans Thai', Loma, Garuda, -apple-system, Helvetica, Arial, sans-serif"
INK, INK2, LINE, ACCENT, RANGE = "#1d1d1f", "#86868b", "#e8e8ed", "#0071e3", "#d2d2d7"


def _fmt(v: float) -> str:
    return f"฿{v:,.0f}"


def _nice_ceiling(v: float) -> float:
    """Round up to 1/2/2.5/5 × 10^n so axis ticks land on round numbers."""
    import math

    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * exp:
            return m * exp
    return 10 * exp


def _hbar_svg(rows: list[tuple[str, float, float | None, float | None, bool]], *, value_label, width=720) -> str:
    """rows: (label, value, range_lo, range_hi, highlight). Horizontal bars, longest label column auto-sized."""
    row_h, top, bottom = 30, 14, 34
    label_w = min(200, 16 + 7 * max(len(r[0]) for r in rows))
    chart_w = width - label_w - 90
    height = top + row_h * len(rows) + bottom
    vmax = _nice_ceiling(max((r[3] or r[1]) for r in rows) or 1)
    x0 = label_w
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'font-family="{FONT}" font-size="12">'
    ]
    # gridlines
    for i in range(5):
        x = x0 + chart_w * i / 4
        out.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height - bottom + 6}" stroke="{LINE}" stroke-width="1"/>'
        )
        out.append(
            f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle" fill="{INK2}" font-size="10">{escape(value_label(vmax * i / 4))}</text>'
        )
    for i, (label, value, lo, hi, hl) in enumerate(rows):
        y = top + i * row_h
        cy = y + row_h / 2
        out.append(
            f'<text x="{x0 - 10}" y="{cy + 4}" text-anchor="end" fill="{INK}" font-weight="{600 if hl else 400}">{escape(label[:28])}</text>'
        )
        if lo is not None and hi is not None and hi > lo:
            out.append(
                f'<rect x="{x0 + chart_w * lo / vmax:.1f}" y="{cy - 3}" width="{chart_w * (hi - lo) / vmax:.1f}" height="6" rx="3" fill="{RANGE}"/>'
            )
        w = max(chart_w * value / vmax, 2)
        out.append(f'<rect x="{x0}" y="{cy - 9}" width="{w:.1f}" height="18" rx="5" fill="{ACCENT if hl else INK}"/>')
        out.append(
            f'<text x="{x0 + w + 8:.1f}" y="{cy + 4}" fill="{INK}" font-size="11">{escape(value_label(value))}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def price_chart_svg(products: list[ExtractedProduct], highlight: list[str], max_brands: int = 12) -> str | None:
    rows = [r for r in brand_price_table(products) if r["median_price"] is not None][:max_brands]
    if len(rows) < 2:
        return None
    hl = {h.lower() for h in highlight}
    data = [(r["brand"], r["median_price"], r["min_price"], r["max_price"], r["brand"].lower() in hl) for r in rows]
    return _hbar_svg(data, value_label=_fmt)


def channel_chart_svg(products: list[ExtractedProduct], max_channels: int = 8) -> str | None:
    counts = Counter(c.channel_name.strip() for p in products for c in p.sales_channels if c.channel_name.strip())
    rows = counts.most_common(max_channels)
    if len(rows) < 2:
        return None
    data = [(name, float(n), None, None, False) for name, n in rows]
    return _hbar_svg(data, value_label=lambda v: f"{v:.0f}", width=560)


def write_charts(products: list[ExtractedProduct], highlight: list[str], out_dir: Path) -> dict[str, str]:
    """Write chart files; return {name: relative filename} for the ones that had enough data."""
    out_dir.mkdir(parents=True, exist_ok=True)
    charts: dict[str, str] = {}
    for name, svg in (("prices", price_chart_svg(products, highlight)), ("channels", channel_chart_svg(products))):
        if svg:
            (out_dir / f"chart-{name}.svg").write_text(svg, encoding="utf-8")
            charts[name] = f"chart-{name}.svg"
    return charts
