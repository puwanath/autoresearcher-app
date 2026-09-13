"""Download a handful of product images for the report (PRD FR-3.3 / §5.3 Image Asset schema).

Heuristics only in Phase 1 (dimension / aspect ratio); vision-model validation arrives in Phase 2.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
from pathlib import Path

import httpx
from PIL import Image

from app.schemas.research import ExtractedProduct, ImageAsset

log = logging.getLogger(__name__)

MAX_SIDE = 480
MIN_SIDE = 120
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36"}


async def _download(client: httpx.AsyncClient, url: str) -> Image.Image | None:
    try:
        r = await client.get(url)
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
            return None
        if len(r.content) > 8_000_000:
            return None
        img = Image.open(io.BytesIO(r.content))
        img.load()
    except Exception as e:  # network / decode errors are expected on the open web
        log.debug("image skipped %s: %s", url, e)
        return None
    w, h = img.size
    if min(w, h) < MIN_SIDE or not 0.4 <= w / h <= 2.5:
        return None  # banners, icons, tracking pixels
    return img


def _save(img: Image.Image, path: Path) -> tuple[int, int, int]:
    img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    img.save(path, "JPEG", quality=82, optimize=True)
    return img.width, img.height, path.stat().st_size


async def fetch_product_images(
    products: list[ExtractedProduct],
    out_dir: Path,
    *,
    max_images: int = 8,
    per_brand: int = 1,
    client: httpx.AsyncClient | None = None,
) -> list[ImageAsset]:
    """One image per brand (cheapest priced product first), up to `max_images`; files land in out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[ExtractedProduct] = []
    seen_brand: dict[str, int] = {}
    for p in sorted(products, key=lambda p: (not p.image_urls, p.price.amount is None, p.price.amount or 0)):
        if not p.image_urls:
            continue
        key = (p.brand_name or p.product_name).lower()
        if seen_brand.get(key, 0) >= per_brand:
            continue
        seen_brand[key] = seen_brand.get(key, 0) + 1
        candidates.append(p)
        if len(candidates) >= max_images * 2:  # allow for download failures
            break

    own = client is None
    client = client or httpx.AsyncClient(headers=_HEADERS, follow_redirects=True, timeout=15)
    sem = asyncio.Semaphore(4)

    async def download_first(p: ExtractedProduct) -> tuple[str, Image.Image] | None:
        async with sem:
            for url in p.image_urls[:3]:
                img = await _download(client, url)
                if img is not None:
                    return url, img
        return None

    try:
        downloads = await asyncio.gather(*(download_first(p) for p in candidates))
    finally:
        if own:
            await client.aclose()

    # dedupe sequentially in candidate (price) order so results are deterministic
    assets: list[ImageAsset] = []
    used_urls: set[str] = set()
    used_hashes: set[str] = set()
    for p, hit in zip(candidates, downloads, strict=True):
        if hit is None:
            continue
        url, img = hit
        digest = hashlib.sha1(img.tobytes()).hexdigest()
        if url in used_urls or digest in used_hashes:
            continue  # same listing image reused across products / same picture at another URL
        used_urls.add(url)
        used_hashes.add(digest)
        w, h, size = await asyncio.to_thread(_save, img, out_dir / f"{digest[:12]}.jpg")
        assets.append(
            ImageAsset(
                brand_name=p.brand_name,
                product_name=p.product_name,
                image_url=url,
                local_file_path=f"{out_dir.name}/{digest[:12]}.jpg",
                image_type="Product Photo",
                alt_text=f"{p.brand_name or ''} {p.product_name}".strip(),
                width_px=w,
                height_px=h,
                file_size_kb=size // 1024,
            )
        )
        if len(assets) >= max_images:
            break
    return assets
