"""Web search provider. Phase 1 uses DuckDuckGo (no API key); swap via SEARCH_PROVIDER later."""

from __future__ import annotations

import asyncio
import logging

from ddgs import DDGS

from app.config import get_settings
from app.schemas.research import SearchResult

log = logging.getLogger(__name__)

_BLOCKED_DOMAINS = ("youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com", "tiktok.com")


def _ddgs_search(query: str, max_results: int, region: str) -> list[SearchResult]:
    try:
        rows = DDGS().text(query, region=region, safesearch="off", max_results=max_results)
    except Exception as e:  # ddgs raises a family of custom exceptions; treat as empty
        log.warning("search failed for %r: %s", query, e)
        return []
    out = []
    for r in rows or []:
        url = r.get("href") or r.get("url") or ""
        if not url or any(d in url for d in _BLOCKED_DOMAINS):
            continue
        out.append(SearchResult(title=r.get("title", ""), url=url, snippet=r.get("body", ""), query=query))
    return out


async def web_search(queries: list[str], max_results: int | None = None) -> list[SearchResult]:
    """Run several queries, dedupe by URL, preserve rank order."""
    s = get_settings()
    n = max_results or s.max_search_results
    results = await asyncio.gather(*(asyncio.to_thread(_ddgs_search, q, n, s.search_region) for q in queries))
    seen: set[str] = set()
    merged: list[SearchResult] = []
    # interleave so every query contributes its top hits first
    for rank in range(n):
        for per_query in results:
            if rank < len(per_query) and per_query[rank].url not in seen:
                seen.add(per_query[rank].url)
                merged.append(per_query[rank])
    return merged
