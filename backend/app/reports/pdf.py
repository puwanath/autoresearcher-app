"""Markdown → HTML → PDF via WeasyPrint, with Thai font stack and page header/footer."""

from __future__ import annotations

from pathlib import Path

import markdown

CSS = """
@page {
  size: A4; margin: 22mm 18mm 20mm 18mm;
  @top-left { content: "AutoResearch Agent — Siam Sindhorn Co., Ltd."; font-size: 8pt; color: #888; }
  @top-right { content: string(doctitle); font-size: 8pt; color: #888; }
  @bottom-center { content: "หน้า " counter(page) " / " counter(pages); font-size: 8pt; color: #888; }
}
body { font-family: "Sarabun", "Noto Sans Thai", "Loma", "Garuda", "Noto Sans", sans-serif;
       font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; }
h1 { string-set: doctitle content(); font-size: 22pt; color: #0b3d5c; border-bottom: 3px solid #0b3d5c;
     padding-bottom: 6px; margin-top: 0; }
h2 { font-size: 15pt; color: #0b3d5c; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 12pt; color: #333; margin-top: 16px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9pt; page-break-inside: auto; }
th, td { border: 1px solid #cfd8dc; padding: 4px 6px; vertical-align: top; }
th { background: #e8f0f5; text-align: left; }
tr { page-break-inside: avoid; }
a { color: #0b5c8a; text-decoration: none; word-break: break-all; }
hr { border: 0; border-top: 1px solid #ccc; margin: 18px 0; }
ul, ol { padding-left: 20px; }
input[type=checkbox] { margin-right: 6px; }
"""


def markdown_to_html(md: str, title: str) -> str:
    body = markdown.markdown(
        md, extensions=["tables", "sane_lists", "pymdownx.tasklist"] if _has_pymdownx() else ["tables", "sane_lists"]
    )
    return (
        f"<!doctype html><html lang='th'><head><meta charset='utf-8'><title>{title}</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )


def _has_pymdownx() -> bool:
    try:
        import pymdownx  # noqa: F401

        return True
    except ImportError:
        return False


def render_pdf(md: str, out_path: Path, title: str = "AutoResearch Report") -> Path:
    from weasyprint import HTML  # heavy import, keep lazy

    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=markdown_to_html(md, title), base_url=str(out_path.parent)).write_pdf(str(out_path))
    return out_path
