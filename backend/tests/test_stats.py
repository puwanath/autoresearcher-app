from app.agents.stats import brand_price_table, dedupe_competitors, dedupe_products, price_stats
from app.schemas.research import CompetitorInfo, ExtractedProduct, Price


def _p(name, brand, amount, variant=None, src="u"):
    return ExtractedProduct(
        product_name=name, brand_name=brand, variant=variant, price=Price(amount=amount), data_source_url=src
    )


def test_dedupe_products_normalises_brand_case_and_zero_prices():
    products = dedupe_products(
        [
            _p("A", "ANESSA", 999),
            _p("A", "Anessa", 999),
            _p("B", "anessa", 0),
            _p("C", "Anessa", 1),
            _p("A", "ANESSA", 999),
        ]
    )
    assert len(products) == 3  # case variants of the same product collapse into one
    assert {p.brand_name for p in products} == {"Anessa"}  # mixed-case form wins over ALL CAPS
    assert [p.price.amount for p in products if p.product_name in ("B", "C")] == [None, None]  # 0 / ฿1 → None


def test_price_stats_and_brand_table():
    products = [_p("A", "X", 100), _p("B", "X", 300), _p("C", "Y", 200), _p("D", "Y", None)]
    s = price_stats(products)
    assert (s.min, s.max, s.median, s.sample_size) == (100, 300, 200, 3)
    rows = brand_price_table(products)
    assert [r["brand"] for r in rows] == ["X", "Y"]  # sorted by median
    assert rows[0]["median_price"] == 200 and rows[1]["products"] == 2


def test_price_stats_empty():
    assert price_stats([]).sample_size == 0


def test_dedupe_competitors_merges():
    out = dedupe_competitors(
        [
            CompetitorInfo(brand_name="Biore", market_segment=None),
            CompetitorInfo(brand_name="biore", market_segment="Mass", website_url="https://biore.co.th"),
        ]
    )
    assert len(out) == 1 and out[0].market_segment == "Mass" and out[0].website_url
