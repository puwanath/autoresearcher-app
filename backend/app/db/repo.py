"""Persistence helpers used by the worker: task lifecycle + storing a ResearchResult."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Competitor, PriceRecord, Product, Result, ScrapedSource, Task, TaskStatus
from app.schemas.research import ResearchRequest, ResearchResult, ScrapedPage


async def create_task(session: AsyncSession, request: ResearchRequest, project_id: str | None = None) -> Task:
    task = Task(payload=request.model_dump(mode="json"), project_id=project_id, events=[])
    session.add(task)
    await session.commit()
    return task


async def get_task(session: AsyncSession, task_id: str) -> Task | None:
    return await session.get(Task, task_id)


async def mark_running(session: AsyncSession, task_id: str) -> None:
    task = await session.get(Task, task_id)
    if task:
        task.status = TaskStatus.running
        task.started_at = datetime.now(UTC)
        await session.commit()


async def append_event(session: AsyncSession, task_id: str, line: str) -> None:
    task = await session.get(Task, task_id)
    if task:
        task.events = [*(task.events or []), line]  # reassign so JSON change is detected
        await session.commit()


async def mark_failed(session: AsyncSession, task_id: str, error: str) -> None:
    task = await session.get(Task, task_id)
    if task:
        task.status = TaskStatus.failed
        task.error = error[:4000]
        task.finished_at = datetime.now(UTC)
        await session.commit()


async def _upsert_competitor(session: AsyncSession, brand_name: str, **fields) -> Competitor:
    key = brand_name.strip().lower()
    comp = (await session.execute(select(Competitor).where(Competitor.brand_key == key))).scalar_one_or_none()
    if comp is None:
        comp = Competitor(brand_name=brand_name.strip(), brand_key=key)
        session.add(comp)
        await session.flush()
    for k, v in fields.items():
        if v and not getattr(comp, k):
            setattr(comp, k, v)
    return comp


async def save_result(session: AsyncSession, result: ResearchResult, pages: list[ScrapedPage] | None = None) -> None:
    task = await session.get(Task, result.task_id)
    if task is None:
        raise ValueError(f"task {result.task_id} not found")

    for c in result.competitors:
        await _upsert_competitor(
            session,
            c.brand_name,
            website_url=c.website_url,
            market_segment=c.market_segment,
            description=c.description,
            target_audience=c.target_audience,
        )

    for p in result.products:
        comp = await _upsert_competitor(session, p.brand_name) if p.brand_name else None
        pkey = "|".join(x.strip().lower() for x in (p.brand_name or "", p.product_name, p.variant or ""))[:600]
        prod = (await session.execute(select(Product).where(Product.product_key == pkey))).scalar_one_or_none()
        if prod is None:
            prod = Product(
                competitor_id=comp.id if comp else None,
                product_name=p.product_name[:500],
                product_key=pkey,
                variant=p.variant,
                category=p.category,
                specs=p.specs,
                image_urls=p.image_urls,
            )
            session.add(prod)
            await session.flush()
        session.add(
            PriceRecord(
                task_id=task.id,
                product_id=prod.id,
                amount=p.price.amount,
                currency=p.price.currency,
                original_price=p.price.original_price,
                discount_percentage=p.price.discount_percentage,
                unit_price=p.price.unit_price,
                sales_channels=[c.model_dump() for c in p.sales_channels],
                promotions=[pr.model_dump() for pr in p.promotions],
                rating=p.rating,
                review_count=p.review_count,
                data_source_url=p.data_source_url[:1000],
            )
        )

    for pg in pages or []:
        session.add(
            ScrapedSource(
                task_id=task.id,
                url=pg.url[:1000],
                final_url=pg.final_url[:1000],
                title=pg.title[:500],
                status_code=pg.status_code,
                fetched_with=pg.fetched_with,
                raw_path=pg.raw_path,
                error=pg.error,
            )
        )

    if result.plan:
        session.add(Result(task_id=task.id, data_type="plan", content=result.plan.model_dump(mode="json")))
    if result.analysis:
        session.add(Result(task_id=task.id, data_type="analysis", content=result.analysis.model_dump(mode="json")))
    if result.products:
        session.add(
            Result(
                task_id=task.id,
                data_type="products",
                content={"items": [pr.model_dump(mode="json") for pr in result.products]},
            )
        )
    if result.price_stats:
        session.add(
            Result(task_id=task.id, data_type="price_stats", content=result.price_stats.model_dump(mode="json"))
        )
    for a in result.artifacts:
        session.add(
            Result(
                task_id=task.id,
                data_type=f"report_{a.format.value}",
                raw_file_url=a.path,
                content={"size_bytes": a.size_bytes},
            )
        )

    task.status = TaskStatus.completed
    task.finished_at = datetime.now(UTC)
    task.events = list(result.events)
    if result.errors:
        task.error = "\n".join(result.errors)[:4000]
    await session.commit()
