"""Charts, product images and the PDF front matter (cover + TOC)."""

import io
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.reports import Cover, fetch_product_images, render_pdf, write_charts
from app.reports.charts import price_chart_svg
from app.schemas.research import ExtractedProduct, Price, SalesChannel


def _p(name, brand, amount, channel="Shopee", images=()):
    return ExtractedProduct(
        product_name=name,
        brand_name=brand,
        price=Price(amount=amount),
        sales_channels=[SalesChannel(channel_name=channel)],
        image_urls=list(images),
    )


PRODUCTS = [_p("a1", "Anessa", 999), _p("a2", "Anessa", 950, "Lazada"), _p("b1", "Biore", 260), _p("m1", "Mizumi", 99)]


def test_price_chart_highlights_targets_and_orders_by_median():
    svg = price_chart_svg(PRODUCTS, highlight=["biore"])
    assert svg and svg.startswith("<svg")
    assert svg.index(">Mizumi<") < svg.index(">Biore<") < svg.index(">Anessa<")  # cheapest first
    assert svg.count('fill="#0071e3"') == 1  # exactly one highlighted bar
    assert "฿974" in svg  # Anessa median


def test_price_chart_needs_two_brands():
    assert price_chart_svg([_p("x", "Only", 10)], []) is None


def test_write_charts(tmp_path):
    charts = write_charts(PRODUCTS, [], tmp_path)
    assert charts == {"prices": "chart-prices.svg", "channels": "chart-channels.svg"}
    assert (tmp_path / "chart-channels.svg").read_text().count("<rect") >= 2


def _png(w, h, color=(200, 30, 30)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_fetch_product_images_filters_and_dedupes(tmp_path):
    served = {
        "https://img/a.png": _png(600, 600),
        "https://img/banner.png": _png(1200, 200),  # wrong aspect ratio → skipped
        "https://img/tiny.png": _png(40, 40),  # too small → skipped
        "https://img/a-copy.png": _png(600, 600),  # identical pixels → deduped
        "https://img/b.png": _png(300, 400, (0, 0, 255)),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = served.get(str(request.url))
        return httpx.Response(200, content=body, headers={"content-type": "image/png"}) if body else httpx.Response(404)

    products = [
        _p("A", "Anessa", 999, images=["https://img/banner.png", "https://img/a.png"]),
        _p("A2", "Anessa", 900, images=["https://img/a.png"]),  # same brand → per_brand cap
        _p("C", "Copycat", 500, images=["https://img/a-copy.png"]),
        _p("B", "Biore", 260, images=["https://img/tiny.png", "https://img/b.png"]),
        _p("D", "Dead", 100, images=["https://img/missing.png"]),
    ]
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        assets = await fetch_product_images(products, tmp_path / "images", client=client)

    # candidate order is by price: Biore(260) → Copycat(500) → Anessa(900); Anessa's image duplicates Copycat's
    assert [a.brand_name for a in assets] == ["Biore", "Copycat"]
    for a in assets:
        assert (tmp_path / a.local_file_path).exists() and a.local_file_path.startswith("images/")
        assert a.width_px <= 480 and a.file_size_kb >= 0


def test_pdf_has_cover_and_toc_with_page_numbers(tmp_path):
    md = "# Title\n\n## บทสรุปผู้บริหาร\n\ntext\n\n## ส่วนที่ 1: ภาพรวม\n\n### รายละเอียด\n\n" + ("text\n\n" * 400)
    cover = Cover(title="รายงานทดสอบ", subtitle="sub", query="q", competitors=["A"], our_brand="Me", confidence="สูง")
    out = render_pdf(md, tmp_path / "r.pdf", "t", cover)
    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(str(out))
    assert len(reader.pages) >= 4  # cover, toc, body...
    assert "รายงานทดสอบ" in reader.pages[0].extract_text()
    toc = reader.pages[1].extract_text()
    assert "สารบัญ" in toc and "3" in toc  # first heading lands on page 3
    assert "Title" not in reader.pages[2].extract_text()[:20]  # h1 hidden in body (it lives on the cover)


def test_pdf_without_cover_is_plain(tmp_path):
    out = render_pdf("# T\n\n## H\n\ntext", tmp_path / "p.pdf", "t")
    assert Path(out).stat().st_size > 1000
