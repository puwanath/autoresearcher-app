"""LangGraph agentic loop: plan → search → scrape → extract → (refine ↺) → analyze → write.

The graph is deliberately cyclic: if extraction yields too little data the Planner refines the
queries and the loop re-runs (bounded by MAX_ITERATIONS). All side-effecting dependencies
(LLM, event sink) are injected through `Deps` so nodes can be tested with fakes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from slugify import slugify

from app.agents import prompts
from app.agents.state import ResearchState
from app.agents.stats import (
    brand_price_table,
    channel_matrix,
    channel_stats,
    dedupe_competitors,
    dedupe_products,
    price_stats,
    promo_type_counts,
    spec_frequency,
    usage_corpus,
)
from app.config import Settings, get_settings
from app.llm import LLMClient, get_llm
from app.reports import (
    Cover,
    fetch_product_images,
    render_markdown,
    render_pdf,
    render_pptx,
    render_xlsx,
    write_charts,
)
from app.schemas.research import (
    AnalysisReport,
    CompetitorInfo,
    DeepAnalysis,
    OutputFormat,
    PageExtraction,
    ReportArtifact,
    ResearchPlan,
    ResearchRequest,
    ResearchResult,
    ScrapedPage,
    SearchResult,
)
from app.scraper import fetch_pages, web_search

log = logging.getLogger(__name__)
_URL_RE = re.compile(r"https?://[^\s,]+")
_MIN_PRODUCTS_FOR_ANALYSIS = 3


class _RefinedQueries(BaseModel):
    search_queries: list[str]
    rationale: str


@dataclass
class Deps:
    llm: LLMClient = field(default_factory=get_llm)
    settings: Settings = field(default_factory=get_settings)
    on_event: Callable[[str, str], Awaitable[None]] | None = None  # (stage, message)
    search: Callable[..., Awaitable[list[SearchResult]]] = web_search
    fetch: Callable[..., Awaitable[list[ScrapedPage]]] = fetch_pages
    fetch_images: bool = True  # tests turn this off (network)


def _deps(config: RunnableConfig) -> Deps:
    return config["configurable"]["deps"]


async def _emit(deps: Deps, stage: str, msg: str) -> str:
    line = f"[{datetime.now():%H:%M:%S}] {stage}: {msg}"
    log.info(line)
    if deps.on_event:
        await deps.on_event(stage, msg)
    return line


def _lang(req: ResearchRequest) -> str:
    return prompts.LANG_NOTE[req.language]


# ---------------------------------------------------------------- nodes


async def plan_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    req = state["request"]
    user = json.dumps(
        {
            "input": req.query,
            "target_competitors": req.target_competitors,
            "product_category_hint": req.product_category,
            "our_brand": req.our_brand,
        },
        ensure_ascii=False,
    )
    plan = await deps.llm.chat_json(
        [{"role": "system", "content": prompts.PLANNER.format(lang=_lang(req))}, {"role": "user", "content": user}],
        ResearchPlan,
        max_tokens=2000,
    )
    # URLs typed by the user are always scraped directly
    plan.direct_urls = list(dict.fromkeys(plan.direct_urls + _URL_RE.findall(req.query)))
    ev = await _emit(
        deps, "plan", f"{plan.input_type} · {len(plan.search_queries)} queries · {len(plan.direct_urls)} direct URLs"
    )
    return {
        "plan": plan,
        "iteration": 0,
        "events": [ev],
        "visited_urls": [],
        "pages": [],
        "products": [],
        "competitors": [],
    }


async def refine_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    req, plan = state["request"], state["plan"]
    found_brands = sorted({p.brand_name for p in state.get("products", []) if p.brand_name})[:15]
    user = json.dumps(
        {
            "topic": req.query,
            "product_category": plan.product_category,
            "queries_already_used": plan.search_queries,
            "brands_found_so_far": found_brands,
            "products_found": len(state.get("products", [])),
        },
        ensure_ascii=False,
    )
    refined = await deps.llm.chat_json(
        [{"role": "system", "content": prompts.REFINER.format(lang=_lang(req))}, {"role": "user", "content": user}],
        _RefinedQueries,
        max_tokens=1200,
    )
    new_q = [q for q in refined.search_queries if q not in plan.search_queries]
    plan = plan.model_copy(update={"search_queries": plan.search_queries + new_q, "direct_urls": []})
    ev = await _emit(deps, "refine", f"iteration {state['iteration'] + 1}: +{len(new_q)} queries")
    return {"plan": plan, "iteration": state["iteration"] + 1, "events": [ev], "_new_queries": new_q}


async def search_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    plan = state["plan"]
    queries = state.get("_new_queries") or plan.search_queries
    results = await deps.search(queries, deps.settings.max_search_results)
    ev = await _emit(deps, "search", f"{len(queries)} queries → {len(results)} unique results")
    return {"search_results": results, "events": [ev]}


async def scrape_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    visited = set(state.get("visited_urls", []))
    candidates = [u for u in state["plan"].direct_urls if u not in visited]
    candidates += [r.url for r in state.get("search_results", []) if r.url not in visited and r.url not in candidates]
    budget = deps.settings.max_pages
    urls = candidates[:budget]
    pages = await deps.fetch(urls, state["task_id"]) if urls else []
    ok = [p for p in pages if p.ok]
    ev = await _emit(
        deps,
        "scrape",
        f"{len(ok)}/{len(pages)} pages ok ({sum(p.fetched_with == 'playwright' for p in pages)} via browser)",
    )
    errors = [f"scrape {p.url}: {p.error}" for p in pages if p.error]
    return {
        "pages": state.get("pages", []) + pages,
        "visited_urls": list(visited | set(urls)),
        "events": [ev],
        "errors": errors,
    }


async def extract_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    req, plan = state["request"], state["plan"]
    new_pages = [p for p in state["pages"] if p.ok and p.url not in state.get("_extracted_urls", [])]
    sem = asyncio.Semaphore(deps.settings.llm_concurrency)
    system = prompts.EXTRACTOR.format(lang=_lang(req))

    async def one(page: ScrapedPage) -> tuple[ScrapedPage, PageExtraction | None]:
        payload = {
            "research_topic": req.query,
            "product_category": plan.product_category,
            "page_url": page.final_url,
            "page_title": page.title,
            "json_ld": page.json_ld,
            "image_urls": page.image_urls[:20],
            "page_text": page.text,
        }
        async with sem:
            try:
                ext = await deps.llm.chat_json(
                    [
                        {"role": "system", "content": system},
                        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                    ],
                    PageExtraction,
                    max_tokens=6000,
                    temperature=0.1,
                )
                return page, ext
            except Exception as e:
                log.warning("extraction failed for %s: %s", page.url, e)
                return page, None

    results = await asyncio.gather(*(one(p) for p in new_pages))
    products, competitors, errors = list(state.get("products", [])), list(state.get("competitors", [])), []
    page_insights = list(state.get("page_insights", []))
    relevant = 0
    for page, ext in results:
        if ext is None:
            errors.append(f"extract {page.url}: LLM failed")
            continue
        if not ext.is_relevant:
            continue
        relevant += 1
        page_insights.extend(ext.consumer_insights)
        single_product_page = ext.page_type == "product" and len(ext.products) == 1
        for prod in ext.products:
            prod.data_source_url = prod.data_source_url or page.final_url
            # page-level images (og:image etc.) only identify the product on a dedicated product page
            if not prod.image_urls and page.image_urls and single_product_page:
                prod.image_urls = page.image_urls[:3]
        products.extend(ext.products)
        competitors.extend(ext.competitors)
    products = dedupe_products(products)
    # every brand seen on a product is a competitor even if the page had no brand blurb
    known = {c.brand_name.lower() for c in competitors}
    competitors += [
        CompetitorInfo(brand_name=b) for b in {p.brand_name for p in products if p.brand_name} if b.lower() not in known
    ]
    competitors = dedupe_competitors(competitors)
    ev = await _emit(
        deps,
        "extract",
        f"{relevant}/{len(new_pages)} relevant pages → {len(products)} products, {len(competitors)} brands",
    )
    return {
        "products": products,
        "competitors": competitors,
        "page_insights": page_insights,
        "_extracted_urls": state.get("_extracted_urls", []) + [p.url for p in new_pages],
        "events": [ev],
        "errors": errors,
    }


def after_refine(state: ResearchState) -> Literal["search", "analyze"]:
    """No genuinely new queries → searching again would only revisit known URLs."""
    return "search" if state.get("_new_queries") else "analyze"


def should_refine(state: ResearchState, config: RunnableConfig) -> Literal["refine", "analyze"]:
    deps = _deps(config)
    enough = len(state.get("products", [])) >= _MIN_PRODUCTS_FOR_ANALYSIS
    if not enough and state["iteration"] < deps.settings.max_iterations:
        return "refine"
    return "analyze"


async def analyze_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    req = state["request"]
    products = state["products"]
    stats = price_stats(products)
    lang = _lang(req)
    base = {
        "research_topic": req.query,
        "our_brand": req.our_brand,
        "target_competitors": req.target_competitors,
        "product_category": state["plan"].product_category,
    }
    main_payload = {
        **base,
        "price_stats": stats.model_dump(),
        "brand_summary": brand_price_table(products),
        "competitors": [c.model_dump() for c in state["competitors"]],
        "products": [
            p.model_dump(exclude={"image_urls", "specs", "target_users", "use_cases", "key_claims"})
            for p in products[:80]
        ],
        "pages_analyzed": len([p for p in state["pages"] if p.ok]),
    }
    ch_stats = channel_stats(products)
    deep_payload = {
        **base,
        "channel_matrix": channel_matrix(products),
        "channel_stats": [c.model_dump() for c in ch_stats],
        "promo_type_counts": promo_type_counts(products),
        "spec_frequency": spec_frequency(products),
        "consumer_signals": usage_corpus(products, state.get("page_insights", [])),
    }

    async def main_call() -> AnalysisReport:
        return await deps.llm.chat_json(
            [
                {"role": "system", "content": prompts.ANALYST.format(lang=lang)},
                {"role": "user", "content": json.dumps(main_payload, ensure_ascii=False)},
            ],
            AnalysisReport,
            max_tokens=8000,
            think=deps.settings.vllm_enable_thinking,
        )

    async def deep_call() -> DeepAnalysis | None:
        try:
            return await deps.llm.chat_json(
                [
                    {"role": "system", "content": prompts.DEEP_ANALYST.format(lang=lang)},
                    {"role": "user", "content": json.dumps(deep_payload, ensure_ascii=False)},
                ],
                DeepAnalysis,
                max_tokens=8000,
            )
        except Exception as e:  # the core report must still ship without the deep dive
            log.exception("deep analysis failed")
            return e  # type: ignore[return-value]

    analysis, deep = await asyncio.gather(main_call(), deep_call())
    errors: list[str] = []
    if isinstance(deep, DeepAnalysis):
        deep.channel_analysis.matrix = deep_payload["channel_matrix"]
        deep.channel_analysis.stats = ch_stats
        deep.promotion_analysis.promo_type_counts = deep_payload["promo_type_counts"]
        analysis.channel_analysis = deep.channel_analysis
        analysis.usage_insights = deep.usage_insights
        analysis.promotion_analysis = deep.promotion_analysis
        analysis.feature_comparison = deep.feature_comparison
    elif deep is not None:
        errors.append(f"deep analysis: {deep}")
    ev = await _emit(
        deps,
        "analyze",
        f"{len(analysis.competitors)} competitors · {len(ch_stats)} channels · confidence={analysis.confidence}"
        + ("" if isinstance(deep, DeepAnalysis) else " · deep-dive skipped"),
    )
    return {"analysis": analysis, "price_stats": stats, "events": [ev], "errors": errors}


async def write_node(state: ResearchState, config: RunnableConfig) -> dict:
    deps = _deps(config)
    req, analysis, products = state["request"], state["analysis"], state["products"]
    out_dir = deps.settings.reports_dir / state["task_id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []

    # visuals are best-effort: a chart or image failure must never block the report
    charts: dict[str, str] = {}
    images = []
    try:
        charts = write_charts(products, req.target_competitors, out_dir)
    except Exception as e:
        log.exception("charts failed")
        errors.append(f"charts: {e}")
    if deps.fetch_images:
        try:
            images = await fetch_product_images(products, out_dir / "images")
        except Exception as e:
            log.exception("images failed")
            errors.append(f"images: {e}")

    md = render_markdown(
        request=req,
        analysis=analysis,
        products=products,
        stats=state.get("price_stats"),
        pages=state["pages"],
        charts=charts,
        images=images,
    )
    stem = slugify(req.query, max_length=40, allow_unicode=False) or "report"
    artifacts: list[ReportArtifact] = []
    md_path = out_dir / f"{stem}.md"
    md_path.write_text(md, encoding="utf-8")
    artifacts.append(ReportArtifact(format=OutputFormat.markdown, path=str(md_path), size_bytes=md_path.stat().st_size))
    if OutputFormat.pdf in req.output_formats:
        stats = state.get("price_stats")
        cover = Cover(
            title=analysis.title,
            subtitle=analysis.key_findings[0] if analysis.key_findings else "",
            query=req.query,
            competitors=req.target_competitors,
            our_brand=req.our_brand,
            confidence={"low": "ต่ำ", "medium": "ปานกลาง", "high": "สูง"}.get(analysis.confidence, analysis.confidence),
            stats={
                "แหล่งข้อมูล": f"{len([p for p in state['pages'] if p.ok])} หน้าเว็บ · {len(products)} รายการสินค้า",
                "ราคามัธยฐานตลาด": f"฿{stats.median:,.0f}" if stats and stats.median else "ไม่พบข้อมูลราคา",
            },
        )
        try:
            pdf_path = await asyncio.to_thread(render_pdf, md, out_dir / f"{stem}.pdf", analysis.title, cover)
            artifacts.append(
                ReportArtifact(format=OutputFormat.pdf, path=str(pdf_path), size_bytes=pdf_path.stat().st_size)
            )
        except Exception as e:
            log.exception("pdf failed")
            errors.append(f"pdf: {e}")
    if OutputFormat.pptx in req.output_formats:
        try:
            pptx_path = await asyncio.to_thread(
                render_pptx,
                request=req,
                analysis=analysis,
                products=products,
                stats=state.get("price_stats"),
                images=images,
                report_dir=out_dir,
                out_path=out_dir / f"{stem}.pptx",
            )
            artifacts.append(
                ReportArtifact(format=OutputFormat.pptx, path=str(pptx_path), size_bytes=pptx_path.stat().st_size)
            )
        except Exception as e:
            log.exception("pptx failed")
            errors.append(f"pptx: {e}")
    if OutputFormat.xlsx in req.output_formats:
        try:
            xlsx_path = await asyncio.to_thread(
                render_xlsx,
                request=req,
                analysis=analysis,
                products=products,
                stats=state.get("price_stats"),
                pages=state["pages"],
                out_path=out_dir / f"{stem}.xlsx",
            )
            artifacts.append(
                ReportArtifact(format=OutputFormat.xlsx, path=str(xlsx_path), size_bytes=xlsx_path.stat().st_size)
            )
        except Exception as e:
            log.exception("xlsx failed")
            errors.append(f"xlsx: {e}")
    ev = await _emit(
        deps,
        "write",
        ", ".join(a.format.value for a in artifacts) + f" · {len(charts)} charts · {len(images)} images",
    )
    return {"report_markdown": md, "artifacts": artifacts, "images": images, "events": [ev], "errors": errors}


# ---------------------------------------------------------------- graph


def build_graph():
    g = StateGraph(ResearchState)
    g.add_node("plan", plan_node)
    g.add_node("search", search_node)
    g.add_node("scrape", scrape_node)
    g.add_node("extract", extract_node)
    g.add_node("refine", refine_node)
    g.add_node("analyze", analyze_node)
    g.add_node("write", write_node)
    g.set_entry_point("plan")
    g.add_edge("plan", "search")
    g.add_edge("search", "scrape")
    g.add_edge("scrape", "extract")
    g.add_conditional_edges("extract", should_refine, {"refine": "refine", "analyze": "analyze"})
    g.add_conditional_edges("refine", after_refine, {"search": "search", "analyze": "analyze"})
    g.add_edge("analyze", "write")
    g.add_edge("write", END)
    return g.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def run_research(request: ResearchRequest, task_id: str, deps: Deps | None = None) -> ResearchResult:
    deps = deps or Deps()
    initial: dict[str, Any] = {"task_id": task_id, "request": request, "events": [], "errors": []}
    final: ResearchState = await get_graph().ainvoke(
        initial, config={"configurable": {"deps": deps}, "recursion_limit": 50}
    )
    return ResearchResult(
        task_id=task_id,
        request=request,
        plan=final.get("plan"),
        pages_fetched=len([p for p in final.get("pages", []) if p.ok]),
        products=final.get("products", []),
        competitors=final.get("competitors", []),
        price_stats=final.get("price_stats"),
        analysis=final.get("analysis"),
        report_markdown=final.get("report_markdown"),
        artifacts=final.get("artifacts", []),
        images=final.get("images", []),
        events=final.get("events", []),
        errors=final.get("errors", []),
        pages=final.get("pages", []),
    )
