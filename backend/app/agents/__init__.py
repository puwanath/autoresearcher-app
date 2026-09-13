"""Lazy re-exports: `app.reports` imports `app.agents.stats`, and `graph` imports `app.reports`,
so importing the graph eagerly here would create an import cycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.graph import Deps, run_research

__all__ = ["Deps", "run_research"]


def __getattr__(name: str):
    if name in __all__:
        from app.agents import graph

        return getattr(graph, name)
    raise AttributeError(name)
