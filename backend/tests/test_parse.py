from app.scraper.parse import parse_html
from tests.conftest import FIXTURES


def test_parse_html_extracts_text_jsonld_images():
    html = (FIXTURES / "product_page.html").read_text()
    title, text, json_ld, images = parse_html(html, "https://shop.example.com/p/1", max_chars=5000)

    assert title.startswith("Anessa Perfect UV")
    assert "ราคา 999 บาท" in text and "รีวิว" in text
    assert "noise that must not appear" not in text
    assert "nav noise" not in text and "footer noise" not in text

    assert len(json_ld) == 1 and json_ld[0]["@type"] == "Product"
    assert json_ld[0]["offers"]["price"] == "999"

    assert images[0] == "https://shop.example.com/img/anessa-main.jpg"  # og:image first, absolutised
    assert "https://cdn.example.com/p/anessa-1.jpg" in images
    assert not any("logo" in u or u.startswith("data:") for u in images)


def test_parse_html_truncates():
    _, text, _, _ = parse_html("<html><body><p>" + "ก" * 1000 + "</p></body></html>", "https://x", max_chars=100)
    assert len(text) == 100
