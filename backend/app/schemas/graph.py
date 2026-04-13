"""Schemas for the graph visualization API."""

from __future__ import annotations

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    tags: list[str] = []
    # Optional fields depending on type
    date: str | None = None
    status: str | None = None
    progress: int | None = None

    model_config = {"from_attributes": True}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    tag: str | None = None

    model_config = {"from_attributes": True}


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
