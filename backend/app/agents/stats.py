"""Deterministic aggregation done in Python so the LLM only reasons over verified numbers."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from app.schemas.research import ChannelStats, CompetitorInfo, ExtractedProduct, PriceStats


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


def channel_matrix(products: list[ExtractedProduct], max_brands: int = 12) -> list[dict]:
    """Rows = brands (by listing count), columns = channels; cell = number of listings."""
    counts: dict[str, Counter] = defaultdict(Counter)
    for p in products:
        for c in p.sales_channels:
            if c.channel_name.strip():
                counts[(p.brand_name or "Unknown").strip()][c.channel_name.strip()] += 1
    channels = [ch for ch, _ in Counter(ch for b in counts.values() for ch in b.elements()).most_common(8)]
    rows = []
    for brand, ctr in sorted(counts.items(), key=lambda kv: -sum(kv[1].values()))[:max_brands]:
        rows.append({"brand": brand, **{ch: ctr.get(ch, 0) for ch in channels}, "total": sum(ctr.values())})
    return rows


def channel_stats(products: list[ExtractedProduct], max_channels: int = 8) -> list[ChannelStats]:
    by_ch: dict[str, list[tuple[ExtractedProduct, float | None]]] = defaultdict(list)
    for p in products:
        for c in p.sales_channels:
            if c.channel_name.strip():
                by_ch[c.channel_name.strip()].append((p, c.seller_rating))
    out = []
    for ch, items in sorted(by_ch.items(), key=lambda kv: -len(kv[1]))[:max_channels]:
        prices = [p.price.amount for p, _ in items if p.price.amount]
        ratings = [r for _, r in items if r]
        out.append(
            ChannelStats(
                channel_name=ch,
                listing_count=len(items),
                brand_count=len({p.brand_name for p, _ in items if p.brand_name}),
                brands=sorted({p.brand_name for p, _ in items if p.brand_name})[:10],
                price_min=min(prices) if prices else None,
                price_max=max(prices) if prices else None,
                price_median=round(statistics.median(prices), 2) if prices else None,
                avg_seller_rating=round(statistics.fmean(ratings), 2) if ratings else None,
                promo_count=sum(len(p.promotions) for p, _ in items),
            )
        )
    return out


def promo_type_counts(products: list[ExtractedProduct]) -> list[dict]:
    ctr: Counter = Counter()
    brands: dict[str, set] = defaultdict(set)
    for p in products:
        for pr in p.promotions:
            key = pr.promo_type.strip()
            if key:
                ctr[key] += 1
                if p.brand_name:
                    brands[key].add(p.brand_name)
    return [{"promo_type": k, "count": n, "brands": sorted(brands[k])[:8]} for k, n in ctr.most_common(10)]


def spec_frequency(products: list[ExtractedProduct], max_keys: int = 15) -> list[dict]:
    """Which spec keys appear across products, with example values — input for the feature comparison."""
    ctr: Counter = Counter()
    examples: dict[str, dict[str, str]] = defaultdict(dict)
    for p in products:
        for k, v in p.specs.items():
            key = k.strip().lower()
            if key:
                ctr[key] += 1
                if p.brand_name and len(examples[key]) < 6:
                    examples[key][p.brand_name] = str(v)[:40]
    return [{"spec": k, "count": n, "by_brand": examples[k]} for k, n in ctr.most_common(max_keys)]


def usage_corpus(products: list[ExtractedProduct], page_insights: list[str], limit: int = 80) -> dict:
    """Consumer-behaviour raw material for the usage analysis."""
    return {
        "target_users": Counter(u for p in products for u in p.target_users).most_common(20),
        "use_cases": Counter(u for p in products for u in p.use_cases).most_common(20),
        "key_claims": Counter(u for p in products for u in p.key_claims).most_common(20),
        "review_highlights": [f"[{p.brand_name or '-'}] {h}" for p in products for h in p.review_highlights][:limit],
        "page_insights": page_insights[:40],
        "rating_by_brand": {
            b: round(statistics.fmean(r), 2)
            for b, r in _group(products, lambda p: p.brand_name, lambda p: p.rating).items()
        },
    }


def _group(products, key, value) -> dict[str, list[float]]:
    out: dict[str, list[float]] = defaultdict(list)
    for p in products:
        k, v = key(p), value(p)
        if k and v:
            out[k].append(v)
    return out


def chart_brands(products: list[ExtractedProduct], highlight: list[str], max_brands: int = 12) -> list[dict]:
    """Brand rows for charts: target competitors always included, then the most-listed brands, sorted by median."""
    rows = [r for r in brand_price_table(products) if r["median_price"] is not None]
    hl = {h.lower() for h in highlight}
    targets = [r for r in rows if r["brand"].lower() in hl]
    others = sorted((r for r in rows if r["brand"].lower() not in hl), key=lambda r: -r["products"])
    picked = (targets + others)[:max_brands]
    return sorted(picked, key=lambda r: r["median_price"])
