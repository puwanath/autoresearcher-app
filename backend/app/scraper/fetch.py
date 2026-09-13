"""Fetch pages with httpx first; fall back to Playwright for JS-rendered / bot-protected pages.

Raw HTML is saved under DATA_DIR/raw/<task_id>/ (MinIO replaces this in Phase 2).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.config import get_settings
from app.schemas.research import ScrapedPage
from app.scraper.parse import parse_html

log = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
}
# Marketplaces are SPA + heavily bot-protected: go straight to the browser.
_BROWSER_FIRST = ("shopee.", "lazada.", "tiktok.com", "central.co.th", "jd.co.th")
_MIN_TEXT = 400


def _needs_browser(url: str, status: int, text: str) -> bool:
    host = urlparse(url).netloc.lower()
    if any(k in host for k in _BROWSER_FIRST):
        return True
    return status in (403, 429, 503) or len(text) < _MIN_TEXT


async def _fetch_httpx(client: httpx.AsyncClient, url: str) -> tuple[int, str, str]:
    r = await client.get(url)
    return r.status_code, str(r.url), r.text


async def _fetch_playwright(url: str, timeout: float) -> tuple[int, str, str]:
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, locale="th-TH", viewport={"width": 1366, "height": 900})
        page = await ctx.new_page()
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            await page.wait_for_timeout(2500)  # let client-side price widgets render
            html = await page.content()
            return (resp.status if resp else 0), page.url, html
        finally:
            await browser.close()


def _save_raw(task_id: str, url: str, html: str) -> str:
    s = get_settings()
    d: Path = s.raw_dir / task_id
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{hashlib.sha1(url.encode()).hexdigest()[:16]}.html"
    path.write_text(html, encoding="utf-8", errors="ignore")
    return str(path)


async def fetch_page(client: httpx.AsyncClient, url: str, task_id: str) -> ScrapedPage:
    s = get_settings()
    status, final_url, html, used = 0, url, "", "httpx"
    host = urlparse(url).netloc.lower()
    try:
        if not any(k in host for k in _BROWSER_FIRST):
            status, final_url, html = await _fetch_httpx(client, url)
        title, text, json_ld, images = parse_html(html, final_url, s.page_text_chars) if html else ("", "", [], [])
        if s.use_playwright and _needs_browser(url, status, text):
            try:
                status, final_url, html = await _fetch_playwright(url, s.scrape_timeout)
                used = "playwright"
                title, text, json_ld, images = parse_html(html, final_url, s.page_text_chars)
            except Exception as e:  # browser failures shouldn't kill the run
                log.warning("playwright failed for %s: %s", url, e)
                if not html:
                    raise
        raw_path = _save_raw(task_id, url, html) if html else None
        page = ScrapedPage(
            url=url,
            final_url=final_url,
            title=title,
            text=text,
            json_ld=json_ld,
            image_urls=images,
            status_code=status,
            fetched_with=used,
            raw_path=raw_path,
        )
        if status >= 400:
            page.error = f"HTTP {status}"
        elif len(text) < 200:
            page.error = "empty page"
        return page
    except Exception as e:
        log.warning("fetch failed for %s: %s", url, e)
        return ScrapedPage(url=url, final_url=url, error=f"{type(e).__name__}: {e}"[:300])


async def fetch_pages(urls: list[str], task_id: str) -> list[ScrapedPage]:
    s = get_settings()
    sem = asyncio.Semaphore(s.scrape_concurrency)
    async with httpx.AsyncClient(
        headers=HEADERS, follow_redirects=True, timeout=s.scrape_timeout, http2=False
    ) as client:

        async def one(u: str) -> ScrapedPage:
            async with sem:
                return await fetch_page(client, u, task_id)

        return list(await asyncio.gather(*(one(u) for u in urls)))
