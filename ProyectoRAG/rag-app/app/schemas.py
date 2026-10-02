"""Modelos Pydantic para los endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=4, ge=1, le=10)
    source: str | None = None


class Citation(BaseModel):
    id: str
    source: str
    text: str
    score: float
    page: int | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    abstained: bool


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    sources: list[str]


class IngestFolderRequest(BaseModel):
    folder: str
