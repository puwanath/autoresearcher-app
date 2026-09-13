"""CLI for running research without the API/queue (PRD deliverable 1.8)."""

from __future__ import annotations

import asyncio
import logging
import uuid

import typer
from rich.console import Console
from rich.table import Table

from app.schemas.research import OutputFormat, ResearchRequest

app = typer.Typer(help="AutoResearch Agent CLI", no_args_is_help=True)
console = Console()


@app.command()
def run(
    query: str = typer.Argument(..., help="Keyword, URL, SKU or competitor name"),
    competitors: str = typer.Option("", "--competitors", "-c", help="Comma-separated competitor names"),
    category: str | None = typer.Option(None, "--category"),
    our_brand: str | None = typer.Option(None, "--our-brand"),
    formats: str = typer.Option("md,pdf", "--formats", "-f", help="md,pdf"),
    language: str = typer.Option("th", "--lang"),
    verbose: bool = typer.Option(False, "-v"),
):
    """Run the full agentic loop and write reports to DATA_DIR/reports/<task_id>/."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    from app.agents import Deps, run_research

    req = ResearchRequest(
        query=query,
        target_competitors=[c.strip() for c in competitors.split(",") if c.strip()],
        product_category=category,
        our_brand=our_brand,
        language=language,  # type: ignore[arg-type]
        output_formats=[OutputFormat(f.strip()) for f in formats.split(",") if f.strip()],
    )
    task_id = uuid.uuid4().hex[:12]

    async def on_event(stage: str, msg: str):
        console.print(f"[bold cyan]{stage:8}[/] {msg}")

    console.rule(f"AutoResearch · task {task_id}")
    result = asyncio.run(run_research(req, task_id, Deps(on_event=on_event)))

    if result.price_stats and result.price_stats.sample_size:
        s = result.price_stats
        console.print(f"\nPrice stats (THB): min {s.min} · median {s.median} · max {s.max} · n={s.sample_size}")
    t = Table("brand", "product", "price", "channel", title=f"{len(result.products)} products")
    for p in result.products[:15]:
        t.add_row(
            p.brand_name or "-",
            p.product_name[:50],
            str(p.price.amount),
            ", ".join(c.channel_name for c in p.sales_channels),
        )
    console.print(t)
    if result.analysis:
        console.print(f"\n[bold]{result.analysis.title}[/]\n{result.analysis.executive_summary}\n")
    for a in result.artifacts:
        console.print(f"[green]✔[/] {a.format.value}: {a.path} ({a.size_bytes:,} bytes)")
    if result.errors:
        console.print(f"[yellow]{len(result.errors)} warnings[/] (use -v for details)")
        if verbose:
            for e in result.errors:
                console.print(f"  - {e}")


@app.command()
def health():
    """Check vLLM connectivity."""
    from app.llm import get_llm

    console.print(asyncio.run(get_llm().healthcheck()))


if __name__ == "__main__":
    app()
