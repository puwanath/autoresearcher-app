# AutoResearch Agent

Autonomous competitor & market research for Thai e-commerce. Give it a keyword, URL, SKU or competitor
name → it plans searches, scrapes the web, extracts prices/products/channels with an LLM, analyses the
competitive landscape and writes a report (Markdown + PDF, Thai-language).

Powered by a self-hosted **vLLM** endpoint (OpenAI-compatible, Qwen3.6), **LangGraph** for the agentic
loop, **FastAPI** + **Celery** for the service, **PostgreSQL** for storage, **Playwright** for
JS-rendered pages.

Full PRD & 24-week plan: [`AutoResearch_PRD_and_Plan.md`](AutoResearch_PRD_and_Plan.md).
Current status: **Phase 1 (MVP) complete** — see [Roadmap](#roadmap).

## How it works

```
plan → search → scrape → extract ─┬─(enough data)→ analyze → write → report.md / report.pdf
                                  └─ refine ──────→ search   (bounded loop, MAX_ITERATIONS)
```

| Stage | Agent role (LLM) | Implementation |
|---|---|---|
| Plan | classify input, expand queries, pick channels | `app/agents/graph.py::plan_node` |
| Search | — | DuckDuckGo (`ddgs`), region `th-th` |
| Scrape | — | httpx → Playwright fallback, JSON-LD + image extraction |
| Extract | page text → structured products/prices/promos | guided JSON decoding into `ExtractedProduct` |
| Analyze | SWOT, price positioning, channel & sentiment insight | Python computes stats, LLM reasons over them |
| Write | — | Jinja2 Markdown template → WeasyPrint PDF |

## Quick start

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Docker, a reachable vLLM server.

```bash
cp .env.example .env                 # set VLLM_ENDPOINT / VLLM_MODEL
docker compose up -d postgres redis  # host ports 5433 / 6380

cd backend
uv sync --all-groups
uv run playwright install chromium   # once

# 1) CLI — no DB/queue needed; reports land in ../data/reports/<task_id>/
uv run autoresearch run "ครีมกันแดด SPF50+" -c "Anessa,Biore,Mizumi" --our-brand "SS Sun" -f md,pdf

# 2) API + worker
uv run uvicorn app.main:app --port 8010 --reload
uv run celery -A app.worker.celery_app worker --loglevel=info --concurrency=2
```

```bash
curl -X POST localhost:8010/api/v1/research -H 'content-type: application/json' \
  -d '{"query":"กาแฟดริป","target_competitors":["Doi Chaang","Pacamara"],"output_formats":["md","pdf"]}'
curl localhost:8010/api/v1/research/<task_id>                                   # status, events, analysis JSON
curl -o report.pdf "localhost:8010/api/v1/research/<task_id>/report?format=pdf"
```

Swagger UI: http://localhost:8010/docs

### Full stack in Docker

```bash
docker compose up --build   # api :8010, worker, postgres, redis (image includes Chromium + Thai fonts)
```

## Configuration

All settings come from `.env` (see `.env.example`):

| Variable | Default | Notes |
|---|---|---|
| `VLLM_ENDPOINT` / `VLLM_MODEL` | `http://192.168.3.238:8000/v1` / `Qwen3.6-35B-A3B-FP8` | any OpenAI-compatible server |
| `VLLM_ENABLE_THINKING` | `false` | Qwen3 thinking mode; only used for the analysis call |
| `MAX_SEARCH_RESULTS` / `MAX_PAGES` / `MAX_ITERATIONS` | 8 / 12 / 2 | research budget per task |
| `USE_PLAYWRIGHT` | `true` | browser fallback for JS / bot-protected pages |
| `DATABASE_URL` / `REDIS_URL` | localhost:5433 / :6380 | overridden inside Docker Compose |
| `DATA_DIR` | `./data` | reports + raw HTML (MinIO in Phase 2) |

## Project structure

```
backend/app/
  agents/     LangGraph loop (graph.py), prompts, deterministic stats
  llm/        vLLM client (retry, guided JSON, thinking toggle)
  scraper/    search.py · fetch.py · parse.py
  reports/    Markdown template + PDF renderer
  schemas/    Pydantic models (PRD §5 schemas)
  db/         SQLAlchemy models, session, repository
  api/        FastAPI routes      main.py  worker.py (Celery)  cli.py
backend/tests/  unit tests with fake LLM / search / fetch (no network)
```

## Tests & lint

```bash
cd backend
uv run pytest
uv run ruff check . && uv run ruff format .
```

## Roadmap

- **Phase 1 — MVP** ✅ infra, vLLM module, scraper, agentic loop, Postgres schema, Markdown + PDF, CLI/API
- **Phase 2** image scraping & vision analysis, Shopee / Lazada / TikTok Shop integrations, price history,
  sentiment & trend analysis, basic dashboard, MinIO
- **Phase 3** full web UI (Next.js), auth & RBAC, sharing/comments, PPTX & Excel export, custom templates,
  hardening, monitoring, UAT
