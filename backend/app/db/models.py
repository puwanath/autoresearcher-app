"""Relational schema (PRD §4.3). Users table arrives with auth in Phase 3."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    tasks: Mapped[list[Task]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), index=True)
    type: Mapped[str] = mapped_column(String(50), default="research")
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.pending, index=True
    )
    payload: Mapped[dict] = mapped_column(JSON)  # ResearchRequest
    events: Mapped[list] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project | None] = relationship(back_populates="tasks")
    results: Mapped[list[Result]] = relationship(back_populates="task", cascade="all, delete-orphan")
    sources: Mapped[list[ScrapedSource]] = relationship(back_populates="task", cascade="all, delete-orphan")
    price_records: Mapped[list[PriceRecord]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Result(Base):
    """One row per output of a task: plan, analysis (JSON), report file (md/pdf)."""

    __tablename__ = "results"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    data_type: Mapped[str] = mapped_column(String(40))  # plan | analysis | price_stats | report_md | report_pdf
    content: Mapped[dict | None] = mapped_column(JSON)
    raw_file_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    task: Mapped[Task] = relationship(back_populates="results")


class ScrapedSource(Base):
    __tablename__ = "scraped_sources"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    final_url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500), default="")
    status_code: Mapped[int] = mapped_column(Integer, default=0)
    fetched_with: Mapped[str] = mapped_column(String(20))
    raw_path: Mapped[str | None] = mapped_column(String(500))
    error: Mapped[str | None] = mapped_column(String(300))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    task: Mapped[Task] = relationship(back_populates="sources")


class Competitor(Base):
    __tablename__ = "competitors"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    brand_name: Mapped[str] = mapped_column(String(200), index=True)
    brand_key: Mapped[str] = mapped_column(String(200), unique=True)  # lower-cased for dedupe across tasks
    website_url: Mapped[str | None] = mapped_column(String(500))
    market_segment: Mapped[str | None] = mapped_column(String(100))
    target_audience: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    products: Mapped[list[Product]] = relationship(back_populates="competitor")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    competitor_id: Mapped[str | None] = mapped_column(ForeignKey("competitors.id"), index=True)
    product_name: Mapped[str] = mapped_column(String(500))
    product_key: Mapped[str] = mapped_column(String(600), unique=True)  # brand|name|variant lower-cased
    variant: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(200))
    specs: Mapped[dict] = mapped_column(JSON, default=dict)
    image_urls: Mapped[list] = mapped_column(JSON, default=list)
    competitor: Mapped[Competitor | None] = relationship(back_populates="products")
    price_records: Mapped[list[PriceRecord]] = relationship(back_populates="product")


class PriceRecord(Base):
    """Time series of observed prices — Phase 2 price-history tracking builds on this."""

    __tablename__ = "price_records"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="THB")
    original_price: Mapped[float | None] = mapped_column(Float)
    discount_percentage: Mapped[float | None] = mapped_column(Float)
    unit_price: Mapped[float | None] = mapped_column(Float)
    sales_channels: Mapped[list] = mapped_column(JSON, default=list)
    promotions: Mapped[list] = mapped_column(JSON, default=list)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    data_source_url: Mapped[str] = mapped_column(String(1000))
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    task: Mapped[Task] = relationship(back_populates="price_records")
    product: Mapped[Product] = relationship(back_populates="price_records")
