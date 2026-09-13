"""HTML → clean text / JSON-LD / image URLs. Pure functions, easy to unit-test."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_NOISE_TAGS = ("script", "style", "noscript", "svg", "iframe", "nav", "footer", "header", "form", "aside")
_IMG_EXT = re.compile(r"\.(jpe?g|png|webp)(\?|$)", re.I)
_IMG_SKIP = re.compile(r"(logo|icon|sprite|banner|avatar|pixel|tracking|1x1|blank|spacer)", re.I)


def parse_html(html: str, base_url: str, max_chars: int) -> tuple[str, str, list[dict], list[str]]:
    soup = BeautifulSoup(html, "lxml")
    title = (soup.title.get_text(strip=True) if soup.title else "")[:300]

    json_ld = _extract_json_ld(soup)
    image_urls = _extract_images(soup, base_url)

    for tag in soup(_NOISE_TAGS):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    text = root.get_text("\n", strip=True)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return title, text[:max_chars], json_ld, image_urls


def _extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    """JSON-LD Product/Offer blocks are the most reliable price source on e-commerce pages."""
    out: list[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            graph = item.get("@graph")
            for node in graph if isinstance(graph, list) else [item]:
                t = node.get("@type") if isinstance(node, dict) else None
                types = t if isinstance(t, list) else [t]
                if any(x in ("Product", "Offer", "AggregateOffer", "Organization", "Brand") for x in types):
                    out.append(node)
    return out[:10]


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    urls: list[str] = []
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        urls.append(urljoin(base_url, og["content"]))
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        if not src or src.startswith("data:"):
            continue
        full = urljoin(base_url, src)
        if _IMG_EXT.search(full) and not _IMG_SKIP.search(full):
            urls.append(full)
    seen: set[str] = set()
    return [u for u in urls if not (u in seen or seen.add(u))][:20]
