"""Generación de respuesta con Gemini, anclada a los chunks recuperados."""
from __future__ import annotations

import time

from . import config
from .embed import get_client

_ABSTENTION_MARKERS = (
    "no tengo evidencia",
    "no tengo suficiente",
    "no puedo responder",
    "no aparece en",
    "no se menciona",
)


def _build_prompt(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[{i}] {c['text']}" for i, c in enumerate(chunks, start=1)
    )
    return (
        "Eres un asistente que responde preguntas sobre la Liga MX usando "
        "ÚNICAMENTE los fragmentos de contexto que se te proporcionan abajo, "
        "numerados como [1], [2], etc.\n\n"
        "REGLAS ESTRICTAS:\n"
        "1. Responde en español, de forma concisa y directa.\n"
        "2. Cita la evidencia con el número del fragmento entre corchetes, "
        "por ejemplo [1] o [2][3].\n"
        "3. NO uses conocimiento previo ni inventes datos. Si el dato concreto "
        "(número, cifra, fecha, nombre) no está en el contexto, di "
        "exactamente: \"No tengo evidencia suficiente para responder.\"\n"
        "4. No repitas fragmentos completos; redacta con tus palabras usando "
        "solo la información de los fragmentos.\n\n"
        f"CONTEXTO:\n{context}\n\n"
        f"PREGUNTA: {question}\n"
    )


def generate_answer(question: str, chunks: list[dict]) -> tuple[str, bool]:
    """Devuelve (respuesta, abstained).

    `chunks` debe ser una lista de dicts con la clave `text`.
    Prueba el modelo principal y, si la cuota/demanda lo impide, los de
    respaldo.
    """
    prompt = _build_prompt(question, chunks)
    client = get_client()
    models = [config.GENERATION_MODEL] + config.GENERATION_MODEL_FALLBACKS

    for model in models:
        response = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                break
            except Exception as e:
                msg = str(e)
                if "429" not in msg and "503" not in msg and "UNAVAILABLE" not in msg:
                    raise
                time.sleep(2 ** attempt)
        if response is not None:
            answer = (response.text or "").strip()
            lowered = answer.lower()
            abstained = any(marker in lowered for marker in _ABSTENTION_MARKERS)
            return answer, abstained

    raise RuntimeError("Ningún modelo de Gemini respondió (cuota/demanda)")
