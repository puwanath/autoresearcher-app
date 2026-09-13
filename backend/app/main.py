import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.research import router as research_router
from app.config import get_settings
from app.db import init_db
from app.llm import get_llm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AutoResearch Agent API",
    version="0.1.0",
    description="Autonomous competitor research: plan → search → scrape → extract → analyze → report",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(research_router, prefix="/api/v1")


@app.get("/health", tags=["ops"])
async def health():
    s = get_settings()
    out: dict = {"status": "ok", "model": s.vllm_model, "vllm": None}
    try:
        out["vllm"] = await get_llm().healthcheck()
    except Exception as e:  # report but don't fail the probe
        out["status"] = "degraded"
        out["vllm"] = f"unreachable: {e}"
    return out
