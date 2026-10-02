"""FastAPI: /health, /ingest, /query."""
from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .chunk import chunk_document
from .embed import embed_texts
from .generate import generate_answer
from .schemas import (
    Citation,
    IngestFolderRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from .store import add_chunks, count, list_sources, query

app = FastAPI(
    title="RAG Liga MX",
    description="Sistema RAG: Google AI embeddings + ChromaDB + Gemini.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    try:
        n = count()
        chroma_ok = True
    except Exception:
        n = 0
        chroma_ok = False
    return {
        "status": "ok",
        "chroma_ok": chroma_ok,
        "documents": n,
        "google_api_key_set": bool(config.GOOGLE_API_KEY),
    }


def _chunk_id(source: str, index: int) -> str:
    digest = hashlib.md5(f"{source}::{index}".encode()).hexdigest()[:16]
    return f"{source}::{digest}"


def _ingest_paths(paths: list[Path]) -> IngestResponse:
    if not config.GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY no configurada")

    all_chunks = []
    for p in paths:
        try:
            all_chunks.extend(chunk_document(p))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No se pudo extraer texto")

    ids = [_chunk_id(c.source, c.chunk_index) for c in all_chunks]
    texts = [c.text for c in all_chunks]
    metadatas = [
        {"source": c.source, "page": c.page, "chunk_index": c.chunk_index}
        for c in all_chunks
    ]

    embeddings = embed_texts(texts)
    add_chunks(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)

    sources = sorted({c.source for c in all_chunks})
    return IngestResponse(
        documents=len(sources),
        chunks=len(all_chunks),
        sources=sources,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest(files: list[UploadFile] = File(...)) -> IngestResponse:
    """Recibe archivos (PDF/MD/TXT), chunkifica, incrusta y persiste."""
    if not files:
        raise HTTPException(status_code=400, detail="No se recibieron archivos")

    tmpdir = Path(tempfile.mkdtemp())
    saved: list[Path] = []
    try:
        for f in files:
            name = Path(f.filename or "documento").name
            dest = tmpdir / name
            with dest.open("wb") as out:
                shutil.copyfileobj(f.file, out)
            saved.append(dest)
        return _ingest_paths(saved)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.post("/ingest/folder", response_model=IngestResponse)
def ingest_folder(body: IngestFolderRequest) -> IngestResponse:
    """Indexa todos los PDF/MD/TXT de una carpeta local."""
    folder = Path(body.folder).expanduser()
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"No existe la carpeta: {folder}")
    exts = {".pdf", ".md", ".txt"}
    paths = sorted(p for p in folder.iterdir() if p.suffix.lower() in exts)
    if not paths:
        raise HTTPException(status_code=400, detail="No hay documentos soportados")
    return _ingest_paths(paths)


@app.get("/sources")
def sources() -> dict:
    """Lista los documentos (fuentes) disponibles en el índice."""
    return {"sources": list_sources()}


@app.post("/query", response_model=QueryResponse)
def run_query(body: QueryRequest) -> QueryResponse:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="La pregunta está vacía")

    where = {"source": body.source} if body.source else None
    q_embedding = embed_texts([body.question])[0]
    result = query(q_embedding, top_k=body.top_k, where=where)

    ids = result["ids"][0]
    distances = result["distances"][0]
    metadatas = result["metadatas"][0]
    documents = result["documents"][0]

    citations: list[Citation] = []
    for i in range(len(ids)):
        score = 1.0 - float(distances[i])
        m = metadatas[i] or {}
        citations.append(
            Citation(
                id=ids[i],
                source=m.get("source", ""),
                text=documents[i] or "",
                score=round(score, 4),
                page=m.get("page"),
            )
        )

    valid = [c for c in citations if c.score >= config.MIN_SCORE]

    if not valid:
        return QueryResponse(
            answer="No tengo evidencia suficiente para responder.",
            citations=citations,
            abstained=True,
        )

    chunks_for_gen = [{"text": c.text} for c in valid]
    try:
        answer, model_abstained = generate_answer(body.question, chunks_for_gen)
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail="El modelo de generación no está disponible por cuota o "
            "demanda. Inténtalo de nuevo en unos segundos.",
        )

    return QueryResponse(
        answer=answer,
        citations=citations,
        abstained=model_abstained,
    )
