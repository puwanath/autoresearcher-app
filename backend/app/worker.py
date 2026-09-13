"""Celery worker: runs the agentic loop for a task row and persists the outcome."""

from __future__ import annotations

import asyncio
import logging

from celery import Celery

from app.config import get_settings

log = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery("autoresearch", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # research tasks are long; don't hoard
    task_time_limit=60 * 30,
    task_soft_time_limit=60 * 25,
    broker_connection_retry_on_startup=True,
)


async def _run(task_id: str) -> dict:
    from app.agents import Deps, run_research
    from app.db import SessionLocal, init_db, repo
    from app.schemas.research import ResearchRequest

    await init_db()
    async with SessionLocal() as session:
        task = await repo.get_task(session, task_id)
        if task is None:
            raise ValueError(f"task {task_id} not found")
        request = ResearchRequest.model_validate(task.payload)
        await repo.mark_running(session, task_id)

    async def on_event(stage: str, msg: str):
        async with SessionLocal() as s:
            await repo.append_event(s, task_id, f"{stage}: {msg}")

    try:
        result = await run_research(request, task_id, Deps(on_event=on_event))
    except Exception as e:
        log.exception("research task %s failed", task_id)
        async with SessionLocal() as s:
            await repo.mark_failed(s, task_id, f"{type(e).__name__}: {e}")
        raise
    async with SessionLocal() as s:
        await repo.save_result(s, result, pages=result.pages)
    return {"task_id": task_id, "products": len(result.products), "artifacts": [a.path for a in result.artifacts]}


@celery_app.task(name="research.run", bind=True, max_retries=0)
def run_research_task(self, task_id: str) -> dict:
    return asyncio.run(_run(task_id))
