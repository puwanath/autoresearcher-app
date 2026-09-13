import pytest

from app.agents.graph import Deps, run_research
from app.schemas.research import OutputFormat, ResearchRequest
from tests.conftest import FakeLLM, fake_fetch, fake_search


@pytest.mark.asyncio
async def test_full_loop_without_refine(settings):
    llm = FakeLLM(products_per_page=2)
    deps = Deps(llm=llm, settings=settings, search=fake_search, fetch=fake_fetch)
    req = ResearchRequest(query="ครีมกันแดด https://brand.example.com/sun", output_formats=[OutputFormat.markdown])

    result = await run_research(req, "t1", deps)

    assert result.plan and "https://brand.example.com/sun" in result.plan.direct_urls
    assert llm.refine_calls == 0  # 4 pages × 2 products ≥ threshold
    assert result.pages_fetched == settings.max_pages
    assert len(result.products) == 8 and all(p.data_source_url for p in result.products)
    assert {p.brand_name for p in result.products} == {"BrandA"}
    assert result.price_stats.sample_size == 8
    assert result.analysis.title == "Report"
    assert "## บทสรุปผู้บริหาร" in result.report_markdown and "| BrandA |" in result.report_markdown
    assert len(result.artifacts) == 1 and result.artifacts[0].path.endswith(".md")
    assert any(e.split("] ")[1].startswith("analyze") for e in result.events)


@pytest.mark.asyncio
async def test_loop_refines_when_data_is_thin(settings):
    llm = FakeLLM(products_per_page=0)
    deps = Deps(llm=llm, settings=settings, search=fake_search, fetch=fake_fetch)
    fetched: list[list[str]] = []

    async def counting_fetch(urls, task_id):
        fetched.append(urls)
        return await fake_fetch(urls, task_id)

    deps.fetch = counting_fetch
    result = await run_research(ResearchRequest(query="niche thing"), "t2", deps)

    assert llm.refine_calls == settings.max_iterations  # bounded loop
    assert len(fetched) == settings.max_iterations + 1
    assert not set(fetched[0]) & set(fetched[1])  # refined pass only visits new URLs
    assert result.analysis is not None  # still produces a report on thin data
    assert result.price_stats.sample_size == 0


@pytest.mark.asyncio
async def test_refine_with_no_new_queries_skips_to_analysis(settings):
    llm = FakeLLM(products_per_page=0)
    orig = llm.chat_json

    async def same_queries(messages, schema, **kw):
        out = await orig(messages, schema, **kw)
        if schema.__name__ == "_RefinedQueries":
            out.search_queries = ["q1"]  # already used by the planner
        return out

    llm.chat_json = same_queries
    fetched = []

    async def counting_fetch(urls, task_id):
        fetched.append(urls)
        return await fake_fetch(urls, task_id)

    deps = Deps(llm=llm, settings=settings, search=fake_search, fetch=counting_fetch)
    result = await run_research(ResearchRequest(query="niche"), "t4", deps)
    assert llm.refine_calls == 1 and len(fetched) == 1 and result.analysis is not None


@pytest.mark.asyncio
async def test_pdf_artifact(settings):
    deps = Deps(llm=FakeLLM(), settings=settings, search=fake_search, fetch=fake_fetch)
    req = ResearchRequest(query="กาแฟดริป", output_formats=[OutputFormat.markdown, OutputFormat.pdf])
    result = await run_research(req, "t3", deps)
    formats = {a.format for a in result.artifacts}
    assert formats == {OutputFormat.markdown, OutputFormat.pdf}
    pdf = next(a for a in result.artifacts if a.format == OutputFormat.pdf)
    assert open(pdf.path, "rb").read(5) == b"%PDF-"
