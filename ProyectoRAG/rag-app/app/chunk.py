"""Partición de documentos en chunks con overlap."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import config

_WORD_RE = re.compile(r"\S+")


@dataclass
class Chunk:
    text: str
    source: str
    chunk_index: int
    page: int | None = None
    title: str | None = None


def _extract_pdf(path: Path) -> list[str]:
    """Devuelve una lista con el texto de cada página del PDF.

    Usa pdfplumber (mejor para tablas de stats); si falla, cae a pypdf.
    """
    try:
        import pdfplumber

        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    pages.append(text)
        if pages:
            return pages
    except Exception:
        pass

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return pages


def extract_pages(path: Path) -> list[str]:
    """Extrae el texto de un archivo, una entrada por página (PDF) o el
    documento completo (txt/md)."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in {".txt", ".md", ".markdown"}:
        return [path.read_text(encoding="utf-8")]
    raise ValueError(f"Formato no soportado: {ext}")


def _split_words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def chunk_document(
    path: Path,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """Trocea un documento en chunks de ~chunk_size palabras con solape.

    No mezcla páginas: cada chunk pertenece a una sola página, lo que hace
    las citas más precisas.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP
    pages = extract_pages(path)
    source = path.name

    chunks: list[Chunk] = []
    idx = 0
    step = max(chunk_size - overlap, 1)

    for page_no, page_text in enumerate(pages, start=1):
        words = _split_words(page_text)
        if not words:
            continue
        for start in range(0, len(words), step):
            window = words[start : start + chunk_size]
            if len(window) < 20:
                continue
            text = " ".join(window)
            chunks.append(
                Chunk(
                    text=text,
                    source=source,
                    chunk_index=idx,
                    page=page_no,
                )
            )
            idx += 1
    return chunks
