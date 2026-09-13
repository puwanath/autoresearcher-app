"""Markdown → HTML → PDF via WeasyPrint.

Layout: cover page (no running header) → table of contents with page numbers (CSS `target-counter`) →
report body. Thai font stack; charts/images referenced relatively from the report directory (`base_url`).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import datetime
from html import escape
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode

_TEMPLATES = Path(__file__).parent / "templates"
_LOGO_URI = "data:image/svg+xml;base64," + base64.b64encode((_TEMPLATES / "logo.svg").read_bytes()).decode()
_LOGO_LARGE_URI = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(
        (_TEMPLATES / "logo.svg").read_bytes().replace(b'width="14" height="14"', b'width="72" height="72"')
    ).decode()
)

FONT_STACK = '"Sarabun", "Noto Sans Thai", "Loma", "Garuda", "Noto Sans", sans-serif'

CSS = f"""
@page {{
  size: A4; margin: 22mm 18mm 20mm 18mm;
  font-family: {FONT_STACK};
  @top-left {{ content: url("{_LOGO_URI}") "  AutoResearch Agent — Puwanath Baibua"; font-size: 8pt; color: #888;
              vertical-align: middle; }}
  @top-right {{ content: string(doctitle); font-size: 8pt; color: #888; }}
  @bottom-center {{ content: "หน้า " counter(page) " / " counter(pages); font-size: 8pt; color: #888; }}
}}
@page cover {{ margin: 0; @top-left {{ content: none }} @top-right {{ content: none }} @bottom-center {{ content: none }} }}
@page toc {{ @top-right {{ content: "สารบัญ" }} }}

body {{ font-family: {FONT_STACK}; font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; }}

/* ---- cover ---- */
.cover {{ page: cover; width: 210mm; height: 297mm; box-sizing: border-box; padding: 34mm 26mm 24mm;
          background: linear-gradient(160deg, #0b3d5c 0%, #06263b 60%, #041826 100%); color: #fff;
          display: flex; flex-direction: column; page-break-after: always; }}
.cover .brand {{ display: flex; align-items: center; gap: 10px; font-size: 11pt; letter-spacing: .04em; opacity: .85; }}
.cover .brand img {{ width: 26px; height: 26px; }}
.cover .eyebrow {{ margin-top: 60mm; font-size: 9.5pt; letter-spacing: .14em; text-transform: uppercase; opacity: .7; }}
.cover h1 {{ string-set: doctitle content(); font-size: 30pt; line-height: 1.2; margin: 10px 0 18px; color: #fff;
             border: 0; padding: 0; font-weight: 700; }}
.cover .subtitle {{ font-size: 13pt; opacity: .85; line-height: 1.5; }}
.cover .meta {{ margin-top: auto; display: grid; grid-template-columns: 1fr 1fr; gap: 8px 24px; font-size: 9.5pt;
                border-top: 1px solid rgba(255,255,255,.25); padding-top: 14px; }}
.cover .meta b {{ display: block; font-size: 8pt; letter-spacing: .08em; text-transform: uppercase; opacity: .6; margin-bottom: 2px; }}
.cover .footer {{ margin-top: 18px; font-size: 8.5pt; opacity: .55; }}

/* ---- table of contents ---- */
.toc {{ page: toc; page-break-after: always; }}
.toc h2 {{ margin-top: 0; }}
.toc table {{ border: 0; font-size: 10.5pt; }}
.toc td {{ border: 0; border-bottom: 1px dotted #c8c8cc; padding: 5px 2px; }}
.toc td.n {{ text-align: right; width: 34px; color: #555; font-variant-numeric: tabular-nums; white-space: nowrap; }}
.toc tr.l2 td {{ font-weight: 600; padding-top: 9px; }}
.toc tr.l3 td.t {{ padding-left: 18px; color: #444; }}
.toc a {{ color: inherit; text-decoration: none; }}
.toc td.n a::after {{ content: target-counter(attr(href), page); }}

/* ---- body ---- */
.body > h1:first-child {{ display: none; }}   /* title lives on the cover */
h1 {{ font-size: 22pt; color: #0b3d5c; border-bottom: 3px solid #0b3d5c; padding-bottom: 6px; margin-top: 0; }}
h2 {{ font-size: 15pt; color: #0b3d5c; margin-top: 22px; page-break-after: avoid; }}
h3 {{ font-size: 12pt; color: #333; margin-top: 16px; page-break-after: avoid; }}
table {{ border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9pt; page-break-inside: auto; }}
th, td {{ border: 1px solid #cfd8dc; padding: 4px 6px; vertical-align: top; }}
th {{ background: #e8f0f5; text-align: left; }}
tr {{ page-break-inside: avoid; }}
a {{ color: #0b5c8a; text-decoration: none; word-break: break-all; }}
hr {{ border: 0; border-top: 1px solid #ccc; margin: 18px 0; }}
ul, ol {{ padding-left: 20px; }}
img {{ max-width: 100%; }}
p > img {{ display: block; margin: 6px auto 4px; }}          /* charts */
.gallery td {{ text-align: center; width: 25%; border: 0; font-size: 8.5pt; color: #444; vertical-align: top; }}
.gallery img {{ height: 34mm; width: auto; max-width: 100%; object-fit: contain; border-radius: 6px;
                border: 1px solid #e3e3e8; background: #fff; display: block; margin: 0 auto 4px; }}
input[type=checkbox] {{ margin-right: 6px; }}
"""


@dataclass
class Cover:
    title: str
    subtitle: str = ""
    query: str = ""
    competitors: list[str] = field(default_factory=list)
    our_brand: str | None = None
    confidence: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    stats: dict[str, str] = field(default_factory=dict)  # extra label → value pairs


_THAI_MONTHS = [
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]


def _thai_date(d: datetime) -> str:
    return f"{d.day} {_THAI_MONTHS[d.month - 1]} {d.year + 543} · {d:%H:%M} น."


def _cover_html(c: Cover) -> str:
    meta = [("วันที่", _thai_date(c.generated_at)), ("หัวข้อวิจัย", c.query)]
    if c.competitors:
        meta.append(("คู่แข่งเป้าหมาย", ", ".join(c.competitors)))
    if c.our_brand:
        meta.append(("แบรนด์ของเรา", c.our_brand))
    if c.confidence:
        meta.append(("ความเชื่อมั่นของข้อมูล", c.confidence))
    meta += list(c.stats.items())
    cells = "".join(f"<div><b>{escape(k)}</b>{escape(v)}</div>" for k, v in meta)
    return (
        '<section class="cover">'
        f'<div class="brand"><img src="{_LOGO_LARGE_URI}" alt="">AutoResearch Agent</div>'
        '<div class="eyebrow">Competitor &amp; Market Research Report</div>'
        f"<h1>{escape(c.title)}</h1>"
        f'<div class="subtitle">{escape(c.subtitle)}</div>'
        f'<div class="meta">{cells}</div>'
        '<div class="footer">จัดทำโดย AutoResearch Agent — Puwanath Baibua · สร้างอัตโนมัติด้วย LLM โปรดตรวจสอบตัวเลขก่อนนำไปใช้</div>'
        "</section>"
    )


def _toc_html(md: markdown.Markdown) -> str:
    """Flatten python-markdown's toc_tokens (h2/h3 only) into a table; page numbers come from CSS."""
    rows: list[str] = []

    def walk(tokens):
        for t in tokens:
            if t["level"] in (2, 3):  # t["name"] is already HTML-escaped by python-markdown
                rows.append(
                    f'<tr class="l{t["level"]}"><td class="t"><a href="#{t["id"]}">{t["name"]}</a></td>'
                    f'<td class="n"><a href="#{t["id"]}"></a></td></tr>'
                )
            walk(t.get("children", []))

    walk(md.toc_tokens)
    return f'<section class="toc"><h2>สารบัญ</h2><table>{"".join(rows)}</table></section>'


def markdown_to_html(md_text: str, title: str, cover: Cover | None = None) -> str:
    md = markdown.Markdown(
        extensions=["tables", "sane_lists", "toc", "attr_list", "md_in_html"],
        extension_configs={"toc": {"toc_depth": "2-3", "slugify": slugify_unicode}},
    )
    body = md.convert(md_text)
    front = (_cover_html(cover) + _toc_html(md)) if cover else ""
    return (
        f"<!doctype html><html lang='th'><head><meta charset='utf-8'><title>{escape(title)}</title>"
        f"<style>{CSS}</style></head><body>{front}<div class='body'>{body}</div></body></html>"
    )


def render_pdf(md: str, out_path: Path, title: str = "AutoResearch Report", cover: Cover | None = None) -> Path:
    from weasyprint import HTML  # heavy import, keep lazy

    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=markdown_to_html(md, title, cover), base_url=str(out_path.parent)).write_pdf(str(out_path))
    return out_path
