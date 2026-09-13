"""Deterministic aggregation done in Python so the LLM only reasons over verified numbers."""

from __future__ import annotations

import statistics
from collections import defaultdict

from app.schemas.research import CompetitorInfo, ExtractedProduct, PriceStats


def canonical_brands(products: list[ExtractedProduct]) -> dict[str, str]:
    """Map lower-cased brand → display form. Prefer Title/Mixed case over ALL CAPS (e.g. 'Anessa' over 'ANESSA')."""
    forms: dict[str, list[str]] = defaultdict(list)
    for p in products:
        if p.brand_name and p.brand_name.strip():
            forms[p.brand_name.strip().lower()].append(p.brand_name.strip())
    return {k: sorted(v, key=lambda f: (f.isupper(), f.islower(), -v.count(f)))[0] for k, v in forms.items()}


def normalize_products(products: list[ExtractedProduct]) -> list[ExtractedProduct]:
    """Clean LLM output: drop non-positive prices, unify brand casing."""
    canon = canonical_brands(products)
    for p in products:
        # ≤ 0 is a parse failure; < 5 THB on a consumer product is a coupon/voucher/placeholder, not a price
        if p.price.amount is not None and (p.price.amount <= 0 or (p.price.currency == "THB" and p.price.amount < 5)):
            p.price.amount = None
        if p.price.original_price is not None and p.price.original_price <= 0:
            p.price.original_price = None
        if p.brand_name:
            p.brand_name = canon.get(p.brand_name.strip().lower(), p.brand_name.strip())
    return products


def dedupe_products(products: list[ExtractedProduct]) -> list[ExtractedProduct]:
    products = normalize_products(products)
    seen: set[tuple] = set()
    out = []
    for p in products:
        key = (
            (p.brand_name or "").strip().lower(),
            p.product_name.strip().lower(),
            (p.variant or "").strip().lower(),
            p.price.amount,
            p.data_source_url,
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def dedupe_competitors(competitors: list[CompetitorInfo]) -> list[CompetitorInfo]:
    by_name: dict[str, CompetitorInfo] = {}
    for c in competitors:
        k = c.brand_name.strip().lower()
        if not k:
            continue
        if k not in by_name:
            by_name[k] = c
        else:  # merge: keep first non-empty values
            cur = by_name[k]
            cur.website_url = cur.website_url or c.website_url
            cur.market_segment = cur.market_segment or c.market_segment
            cur.description = cur.description or c.description
            cur.target_audience = list(dict.fromkeys(cur.target_audience + c.target_audience))
    return list(by_name.values())


def price_stats(products: list[ExtractedProduct], currency: str = "THB") -> PriceStats:
    amounts = [
        p.price.amount for p in products if p.price.amount and p.price.currency == currency and p.price.amount > 0
    ]
    if not amounts:
        return PriceStats(currency=currency)
    return PriceStats(
        currency=currency,
        min=min(amounts),
        max=max(amounts),
        median=round(statistics.median(amounts), 2),
        mean=round(statistics.fmean(amounts), 2),
        sample_size=len(amounts),
    )


def brand_price_table(products: list[ExtractedProduct]) -> list[dict]:
    """Per-brand summary rows handed to the analyst and rendered in the report."""
    groups: dict[str, list[ExtractedProduct]] = defaultdict(list)
    for p in products:
        groups[(p.brand_name or "Unknown").strip()].append(p)
    rows = []
    for brand, items in groups.items():
        amounts = [p.price.amount for p in items if p.price.amount]
        channels = sorted({c.channel_name for p in items for c in p.sales_channels})
        promos = sorted({pr.promo_type for p in items for pr in p.promotions})
        rows.append(
            {
                "brand": brand,
                "products": len(items),
                "min_price": min(amounts) if amounts else None,
                "max_price": max(amounts) if amounts else None,
                "median_price": round(statistics.median(amounts), 2) if amounts else None,
                "channels": channels,
                "promotions": promos,
                "avg_rating": round(statistics.fmean([p.rating for p in items if p.rating]), 2)
                if any(p.rating for p in items)
                else None,
            }
        )
    rows.sort(key=lambda r: (r["median_price"] is None, r["median_price"] or 0))
    return rows
