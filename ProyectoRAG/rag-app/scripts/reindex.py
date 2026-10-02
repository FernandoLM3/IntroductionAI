"""Reindexa un documento: borra sus chunks viejos y los vuelve a incrustar.

Uso:
    python scripts/reindex.py data/liga_mx/HistoriadeCampeonesdelaPrimeraDivisiondeMexico.pdf

Sirve para actualizar el contenido de un PDF que ya estaba indexado.
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunk import chunk_document
from app.embed import embed_texts
from app.store import count, get_collection

_BATCH = 20
_MAX_ATTEMPTS = 6


def chunk_id(source: str, index: int) -> str:
    digest = hashlib.md5(f"{source}::{index}".encode()).hexdigest()[:16]
    return f"{source}::{digest}"


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/reindex.py <ruta/al/archivo.pdf>")
        sys.exit(1)

    path = Path(sys.argv[1]).resolve()
    if not path.is_file():
        print(f"No existe: {path}")
        sys.exit(1)

    chunks = chunk_document(path)
    source = path.name
    col = get_collection()

    old = col.get(where={"source": source})["ids"]
    if old:
        col.delete(ids=old)
        print(f"Borrados {len(old)} chunks viejos de '{source}'.")

    ids = [chunk_id(source, c.chunk_index) for c in chunks]
    texts = [c.text for c in chunks]
    metas = [
        {"source": source, "page": c.page, "chunk_index": c.chunk_index}
        for c in chunks
    ]

    for start in range(0, len(texts), _BATCH):
        b_ids = ids[start : start + _BATCH]
        b_texts = texts[start : start + _BATCH]
        b_metas = metas[start : start + _BATCH]
        emb = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                emb = embed_texts(b_texts)
                break
            except Exception as e:
                msg = str(e)
                if "429" not in msg and "RESOURCE" not in msg:
                    raise
                time.sleep(10 * (attempt + 1))
        if emb is None:
            print("No se pudo indexar por cuota (429). Reintenta el comando.")
            sys.exit(1)
        col.add(ids=b_ids, documents=b_texts, embeddings=emb, metadatas=b_metas)

    print(f"Reindexados {len(chunks)} chunks de '{source}'.")
    print(f"Total en Chroma: {count()} chunks.")


if __name__ == "__main__":
    main()
