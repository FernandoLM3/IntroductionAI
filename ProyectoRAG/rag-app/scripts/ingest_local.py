"""Ingesta local de data/liga_mx con reintentos por cuota (429).

Indexa por lotes y persiste cada lote en Chroma, de modo que si se corta,
puede reanudarse (los ids son deterministas por source+chunk_index).
Uso: python scripts/ingest_local.py
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunk import chunk_document
from app.embed import embed_texts
from app.store import add_chunks, count, get_collection

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "liga_mx"
BATCH = 20
DELAY = 8.0
MAX_ATTEMPTS = 6


def chunk_id(source: str, index: int) -> str:
    digest = hashlib.md5(f"{source}::{index}".encode()).hexdigest()[:16]
    return f"{source}::{digest}"


def main() -> None:
    files = sorted(p for p in DATA_DIR.glob("*.pdf"))
    print(f"{len(files)} archivos por indexar", flush=True)

    col = get_collection()
    existing = set()
    try:
        existing = set(col.get()["ids"])
    except Exception:
        pass

    total_chunks = len(existing)
    print(f"Ya hay {total_chunks} chunks en Chroma (se saltarán)", flush=True)

    for f in files:
        chunks = chunk_document(f)
        ids = [chunk_id(c.source, c.chunk_index) for c in chunks]
        texts = [c.text for c in chunks]
        metas = [
            {"source": c.source, "page": c.page, "chunk_index": c.chunk_index}
            for c in chunks
        ]

        for start in range(0, len(texts), BATCH):
            b_ids = ids[start : start + BATCH]
            b_texts = texts[start : start + BATCH]
            b_metas = metas[start : start + BATCH]

            if all(i in existing for i in b_ids):
                continue

            emb = None
            for attempt in range(MAX_ATTEMPTS):
                try:
                    emb = embed_texts(b_texts)
                    break
                except Exception as e:
                    msg = str(e)
                    if "429" not in msg and "RESOURCE" not in msg:
                        raise
                    wait = 30 * (attempt + 1)
                    print(
                        f"    429 en {f.name}[{start}], reintento {attempt + 1}"
                        f" en {wait}s", flush=True,
                    )
                    time.sleep(wait)
            if emb is None:
                print(f"  !! No se pudo indexar {f.name}[{start}]", flush=True)
                continue
            add_chunks(ids=b_ids, texts=b_texts, embeddings=emb, metadatas=b_metas)
            total_chunks += len(b_ids)
            print(f"    +{len(b_ids)} chunks (total {total_chunks})", flush=True)
            time.sleep(DELAY)

    print(f"\nListo. Chroma tiene {count()} chunks.", flush=True)


if __name__ == "__main__":
    main()
