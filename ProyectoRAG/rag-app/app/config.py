"""Configuración central: lee el .env y expone constantes."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
GENERATION_MODEL = os.getenv("GENERATION_MODEL", "gemini-3.8-flash")
GENERATION_MODEL_FALLBACKS = [
    m.strip()
    for m in os.getenv(
        "GENERATION_MODEL_FALLBACKS", "gemini-3.5-flash,gemini-flash-latest"
    ).split(",")
    if m.strip()
]

CHROMA_PATH = os.getenv("CHROMA_PATH", str(BASE_DIR / "chroma"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "liga_mx")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "60"))

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "4"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.35"))
