from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session, repo
from app.db.models import Result, Task, TaskStatus
from app.schemas.research import OutputFormat, ResearchRequest

router = APIRouter(prefix="/research", tags=["research"])


class TaskCreated(BaseModel):
    task_id: str
    status: TaskStatus


class TaskView(BaseModel):
    task_id: str
    status: TaskStatus
    request: ResearchRequest
    events: list[str]
    error: str | None
    created_at: str
    finished_at: str | None
    analysis: dict | None = None
    price_stats: dict | None = None
    artifacts: dict[str, str] = {}


@router.post("", response_model=TaskCreated, status_code=202)
async def create_research(req: ResearchRequest, session: AsyncSession = Depends(get_session)):
    from app.worker import run_research_task

    task = await repo.create_task(session, req)
    run_research_task.delay(task.id)
    return TaskCreated(task_id=task.id, status=task.status)


@router.get("", response_model=list[TaskCreated])
async def list_research(limit: int = Query(20, le=100), session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(select(Task).order_by(Task.created_at.desc()).limit(limit))).scalars()
    return [TaskCreated(task_id=t.id, status=t.status) for t in rows]


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
        analysis=by_type["analysis"].content if "analysis" in by_type else None,
        price_stats=by_type["price_stats"].content if "price_stats" in by_type else None,
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
    media = "application/pdf" if format == OutputFormat.pdf else "text/markdown; charset=utf-8"
    return FileResponse(path, media_type=media, filename=Path(path).name)
