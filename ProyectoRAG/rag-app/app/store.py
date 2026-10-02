"""Persistencia y consulta sobre ChromaDB (colección persistente)."""
from __future__ import annotations

import chromadb

from . import config

_client = None


def get_collection():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=config.CHROMA_PATH)
    return _client.get_or_create_collection(name=config.COLLECTION_NAME)


def add_chunks(
    ids: list[str],
    texts: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    """Alta de chunks. Los vectores ya vienen calculados por Google AI."""
    col = get_collection()
    col.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def query(
    embedding: list[float],
    top_k: int,
    where: dict | None = None,
) -> dict:
    """Recupera los top-k vecinos más cercanos al embedding de la pregunta."""
    col = get_collection()
    return col.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
    )


def count() -> int:
    return get_collection().count()


def list_sources() -> list[str]:
    metadatas = get_collection().get(include=["metadatas"])["metadatas"]
    sources = sorted({m.get("source", "") for m in metadatas if m})
    return sources
