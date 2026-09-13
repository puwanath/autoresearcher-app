# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**AutoResearch Agent** (Siam Sindhorn Co., Ltd.) — autonomous competitor/market research for Thai e-commerce.
Input (keyword / URL / SKU / competitor names) → LangGraph agentic loop → Markdown + PDF report.
`AutoResearch_PRD_and_Plan.md` is the Thai-language PRD and 24-week plan; the repo is in **Phase 1 (MVP)**.
Thai is first-class: prompts instruct the LLM to write Thai, reports/templates are Thai, PDF needs Thai fonts.

Layout: `backend/` (Python 3.12, managed with **uv**), `docker-compose.yml`, `.env` at repo root
(`Settings` reads `.env` from cwd or `../`, so commands work from either `backend/` or the root).
`frontend/` (Next.js) is planned for Phase 2–3 and does not exist yet.

## Commands

All from `backend/` unless noted.

```bash
uv sync --all-groups                      # install (dev group includes pytest, ruff)
uv run playwright install chromium        # once; browser fallback for JS/bot-protected pages
uv run pytest                             # full suite, no network (fakes for LLM/search/fetch)
uv run pytest tests/test_graph.py::test_loop_refines_when_data_is_thin   # single test
uv run ruff check . && uv run ruff format .

uv run autoresearch run "ครีมกันแดด SPF50+" -c "Anessa,Biore" --our-brand "X" -f md,pdf -v   # end-to-end, no DB
uv run autoresearch health                # vLLM reachability

docker compose up -d postgres redis       # from repo root; host ports 5433 / 6380 (8000/5432 are taken by another project)
uv run uvicorn app.main:app --port 8010 --reload
uv run celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
docker compose up --build                 # full stack; API on :8010
```

Real runs take ~1.5–2 min and hit the live vLLM server + live web; `data/` (reports, raw HTML) is gitignored.

## Architecture

**Agentic loop** — `app/agents/graph.py` (LangGraph `StateGraph` over `ResearchState`, `app/agents/state.py`):

```
plan → search → scrape → extract ─┬─(≥3 products or iterations exhausted)→ analyze → write → END
                                  └─ refine ─(new queries?)─┬─ yes → search
                                                            └─ no  → analyze
```

- Every node gets its collaborators from `Deps` (`config["configurable"]["deps"]`): `llm`, `settings`,
  `search`, `fetch`, `on_event`. Tests swap these for fakes (`tests/conftest.py::FakeLLM`) — keep new
  side effects behind `Deps`, not module globals.
- State keys prefixed `_` (`_new_queries`, `_extracted_urls`) are loop bookkeeping, never exposed in
  `ResearchResult`. `events`/`errors` use `operator.add` reducers so nodes return only their delta.
- Prompts live in `app/agents/prompts.py`; deterministic aggregation (dedupe, brand-case canonicalisation,
  price stats, per-brand table) lives in `app/agents/stats.py` so the LLM only reasons over verified numbers.
- `run_research(request, task_id, deps)` is the single entry point used by both the CLI and the Celery worker.

**LLM** — `app/llm/client.py` wraps `AsyncOpenAI` pointed at vLLM (`VLLM_ENDPOINT`, model
`Qwen3.6-35B-A3B-FP8`). Two non-obvious facts:
1. Qwen3 *thinks by default* and burns the whole `max_tokens` budget in `reasoning_content`; the client
   sends `chat_template_kwargs.enable_thinking=false` unless `think=True` is passed (or
   `VLLM_ENABLE_THINKING=true`, used only for the analysis call).
2. `chat_json(messages, PydanticModel)` uses vLLM guided decoding (`response_format=json_schema`), so
   outputs always parse; a Pydantic validation failure is fed back to the model once. All agent I/O goes
   through `chat_json` with models from `app/schemas/research.py` — add fields there, not ad-hoc dicts.
- openai SDK ≥3 uses the vendored `httpx2`; mock it with `httpx2.MockTransport` via the `http_client`
  constructor arg (see `tests/test_llm_client.py`), not `respx`.

**Scraping** — `app/scraper/`: `search.py` (DuckDuckGo via `ddgs`, no API key, region `th-th`, social
domains blocked), `fetch.py` (httpx first; Playwright when host is a marketplace in `_BROWSER_FIRST`,
status 403/429/503, or text < 400 chars), `parse.py` (pure functions: main-content text, JSON-LD
Product/Offer blocks — the most reliable price source — and product image URLs). Raw HTML is saved to
`DATA_DIR/raw/<task_id>/`; MinIO replaces this in Phase 2.

**Schemas** — `app/schemas/research.py` mirrors PRD §5 (`ExtractedProduct` = Product Price schema,
`CompetitorInfo`, `AnalysisReport`, `ResearchResult`). `ResearchResult.pages` is `exclude=True`: persisted
by the worker but never serialised to the API.

**Reports** — `app/reports/markdown.py` renders `templates/report.md.j2` (fixed PRD §5.5 section order:
Executive Summary → Competitor Landscape → Price & Promotion → Sales Channel → Strategic Recommendations/SWOT).
`pdf.py` converts Markdown → HTML → PDF with WeasyPrint; the CSS font stack is
`Sarabun, Noto Sans Thai, Loma, Garuda` — the Dockerfile installs `fonts-thai-tlwg`; on a bare host only
`Loma` may exist. Single newlines in Markdown collapse, so multi-line metadata must be list items.

**Service** — `app/main.py` (FastAPI, `/api/v1/research` in `app/api/research.py`, `/health` probes vLLM),
`app/worker.py` (Celery task `research.run`, Redis broker, `acks_late`, 30-min hard limit),
`app/db/models.py` (SQLAlchemy 2 async: `projects → tasks → results`, `competitors → products →
price_records` (append-only price time series for Phase 2 history), `scraped_sources`), `app/db/repo.py`
(task lifecycle + `save_result`, which upserts competitors/products by lower-cased key).
Tables are created by `init_db()` at startup — no Alembic yet; add migrations once the schema stabilises.

## Phase scope

Phase 1 (current): FastAPI + Postgres + Redis + Compose, vLLM module, HTML scraper, text-only loop,
Markdown + PDF, CLI/API e2e. Phase 2: images/vision, Shopee/Lazada/TikTok integrations, price history,
sentiment, dashboard, MinIO. Phase 3: full UI, auth/RBAC, sharing, PPTX/Excel, templates, hardening.
Keep changes inside the active phase — scope creep is a tracked risk in the PRD.
