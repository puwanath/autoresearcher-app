from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_session, repo
from app.db.models import PriceRecord, Result, Task, TaskStatus
from app.schemas.research import OutputFormat, ResearchRequest

router = APIRouter(prefix="/research", tags=["research"])


class TaskCreated(BaseModel):
    task_id: str
    status: TaskStatus


class TaskSummary(BaseModel):
    task_id: str
    status: TaskStatus
    query: str
    target_competitors: list[str]
    created_at: str
    finished_at: str | None
    products: int = 0


class TaskView(BaseModel):
    task_id: str
    status: TaskStatus
    request: ResearchRequest
    events: list[str]
    error: str | None
    created_at: str
    finished_at: str | None
    plan: dict | None = None
    analysis: dict | None = None
    price_stats: dict | None = None
    products: list[dict] = []
    images: list[dict] = []
    charts: list[str] = []
    artifacts: dict[str, str] = {}


@router.post("", response_model=TaskCreated, status_code=202)
async def create_research(req: ResearchRequest, session: AsyncSession = Depends(get_session)):
    from app.worker import run_research_task

    task = await repo.create_task(session, req)
    run_research_task.delay(task.id)
    return TaskCreated(task_id=task.id, status=task.status)


@router.post("/{task_id}/retry", response_model=TaskCreated, status_code=202)
async def retry_research(task_id: str, session: AsyncSession = Depends(get_session)):
    """Re-run a task with the same request as a new task (the original record is kept for history)."""
    from app.worker import run_research_task

    original = await repo.get_task(session, task_id)
    if original is None:
        raise HTTPException(404, "task not found")
    if original.status in (TaskStatus.pending, TaskStatus.running):
        raise HTTPException(409, "task is still running")
    task = await repo.create_task(session, ResearchRequest.model_validate(original.payload), original.project_id)
    run_research_task.delay(task.id)
    return TaskCreated(task_id=task.id, status=task.status)


@router.get("", response_model=list[TaskSummary])
async def list_research(limit: int = Query(20, le=100), session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Task).order_by(Task.created_at.desc()).limit(limit))).scalars().all()
    counts = (
        dict(
            (
                await session.execute(
                    select(PriceRecord.task_id, func.count())
                    .where(PriceRecord.task_id.in_([t.id for t in rows]))
                    .group_by(PriceRecord.task_id)
                )
            ).all()
        )
        if rows
        else {}
    )
    return [
        TaskSummary(
            task_id=t.id,
            status=t.status,
            query=t.payload.get("query", ""),
            target_competitors=t.payload.get("target_competitors", []),
            created_at=t.created_at.isoformat(),
            finished_at=t.finished_at.isoformat() if t.finished_at else None,
            products=counts.get(t.id, 0),
        )
        for t in rows
    ]


def _report_dir(task_id: str) -> Path:
    return get_settings().reports_dir / task_id


async def _task_view(session: AsyncSession, task_id: str) -> TaskView:
    task = await repo.get_task(session, task_id)
    if task is None:
        raise HTTPException(404, "task not found")
    results = (await session.execute(select(Result).where(Result.task_id == task_id))).scalars().all()
    by_type = {r.data_type: r for r in results}
    return TaskView(
        task_id=task.id,
        status=task.status,
        request=ResearchRequest.model_validate(task.payload),
        events=task.events or [],
        error=task.error,
        created_at=task.created_at.isoformat(),
        finished_at=task.finished_at.isoformat() if task.finished_at else None,
        plan=by_type["plan"].content if "plan" in by_type else None,
        analysis=by_type["analysis"].content if "analysis" in by_type else None,
        price_stats=by_type["price_stats"].content if "price_stats" in by_type else None,
        products=(by_type["products"].content or {}).get("items", []) if "products" in by_type else [],
        images=(by_type["images"].content or {}).get("items", []) if "images" in by_type else [],
        charts=sorted(p.name for p in _report_dir(task.id).glob("chart-*.svg")),
        artifacts={k.removeprefix("report_"): r.raw_file_url for k, r in by_type.items() if k.startswith("report_")},
    )


@router.get("/{task_id}", response_model=TaskView)
async def get_research(task_id: str, session: AsyncSession = Depends(get_session)):
    return await _task_view(session, task_id)


@router.get("/{task_id}/report")
async def download_report(
    task_id: str, format: OutputFormat = OutputFormat.markdown, session: AsyncSession = Depends(get_session)
):
    view = await _task_view(session, task_id)
    path = view.artifacts.get(format.value)
    if not path or not Path(path).exists():
        raise HTTPException(404, f"no {format.value} report for this task (status={view.status})")
    media = {
        OutputFormat.pdf: "application/pdf",
        OutputFormat.pptx: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        OutputFormat.xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(format, "text/markdown; charset=utf-8")
    return FileResponse(path, media_type=media, filename=Path(path).name)


@router.get("/{task_id}/assets/{path:path}")
async def report_asset(task_id: str, path: str):
    """Serve chart SVGs and downloaded product images that belong to a report."""
    base = _report_dir(task_id).resolve()
    target = (base / path).resolve()
    if not target.is_relative_to(base) or not target.is_file() or target.suffix not in {".svg", ".jpg", ".png"}:
        raise HTTPException(404, "asset not found")
    return FileResponse(target)
