"""Cliente de embeddings de Google AI (gemini-embedding-001)."""
from __future__ import annotations

import time

from . import config

_client = None

_BATCH_SIZE = 20
_MAX_RETRIES = 6


def get_client():
    global _client
    if _client is None:
        if not config.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY no configurada. Copia .env.example a .env y "
                "rellena la clave."
            )
        from google import genai

        _client = genai.Client(api_key=config.GOOGLE_API_KEY)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Incrusa una lista de textos con el MISMO modelo (documentos y preguntas).

    Devuelve una lista de vectores (list[float]) en el mismo orden.
    """
    if not texts:
        return []
    client = get_client()
    out: list[list[float]] = []
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        result = None
        for attempt in range(_MAX_RETRIES):
            try:
                result = client.models.embed_content(
                    model=config.EMBEDDING_MODEL,
                    contents=batch,
                )
                break
            except Exception as e:
                if "429" not in str(e) and "RESOURCE_EXHAUSTED" not in str(e):
                    raise
                wait = 2 ** attempt
                time.sleep(wait)
        if result is None:
            raise RuntimeError("Cuota de Google AI agotada (429 persistente)")
        out.extend(e.values for e in result.embeddings)
        time.sleep(2.0)
    return out
