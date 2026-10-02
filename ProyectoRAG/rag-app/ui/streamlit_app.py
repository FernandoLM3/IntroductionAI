"""UI Streamlit: cliente HTTP de la API FastAPI."""
from __future__ import annotations

import httpx
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="RAG Liga MX", page_icon="⚽", layout="wide")
st.title("RAG Liga MX ⚽")
st.caption("Recuperación con embeddings de Google AI + ChromaDB, generación con Gemini.")


def _health() -> dict | None:
    try:
        r = httpx.get(f"{API_URL}/health", timeout=5.0)
        return r.json() if r.status_code == 200 else None
    except httpx.ConnectError:
        return None


with st.sidebar:
    st.header("Estado del sistema")
    h = _health()
    if h is None:
        st.error("API caída. Levanta FastAPI en :8000.")
    else:
        st.success("API en línea")
        if not h.get("google_api_key_set"):
            st.warning("Clave de Google AI ausente. Configura GOOGLE_API_KEY en .env.")
        if h.get("documents", 0) == 0:
            st.warning("Corpus vacío: indexa documentos primero.")
        else:
            st.info(f"{h['documents']} chunks indexados.")


def _post_files(files: list) -> None:
    to_upload = [
        ("files", (f.name, f.getvalue(), f.type)) for f in files
    ]
    try:
        with httpx.Client(timeout=180.0) as client:
            r = client.post(f"{API_URL}/ingest", files=to_upload)
        if r.status_code == 200:
            data = r.json()
            st.success(
                f"Indexados {data['documents']} documento(s) y "
                f"{data['chunks']} chunks."
            )
        else:
            st.error(f"Error {r.status_code}: {r.text}")
    except httpx.ConnectError:
        st.error("No se pudo conectar con la API. ¿Está corriendo FastAPI en :8000?")


def _sources() -> list[str]:
    try:
        r = httpx.get(f"{API_URL}/sources", timeout=5.0)
        return r.json().get("sources", []) if r.status_code == 200 else []
    except httpx.ConnectError:
        return []


tab_ingest, tab_query = st.tabs(["Ingesta de documentos", "Preguntar"])

with tab_ingest:
    st.header("Subir e indexar documentos")
    st.markdown("Formatos soportados: **PDF**, **Markdown** y **TXT**.")
    files = st.file_uploader(
        "Elige tus archivos",
        type=["pdf", "md", "txt"],
        accept_multiple_files=True,
    )
    if st.button("Indexar", type="primary", disabled=not files):
        _post_files(list(files))

    st.divider()
    st.subheader("Estado de la API")
    if st.button("Consultar /health"):
        try:
            r = httpx.get(f"{API_URL}/health", timeout=10.0)
            st.json(r.json())
        except httpx.ConnectError:
            st.error("API caída en :8000.")


with tab_query:
    st.header("Hacer una pregunta")

    col_q, col_opts = st.columns([2, 1])
    with col_q:
        question = st.text_input("Pregunta sobre la Liga MX")
    with col_opts:
        top_k = st.slider("top-k", min_value=1, max_value=10, value=4)
        avail = _sources()
        source = st.selectbox("Filtrar por documento", ["Todos"] + avail)

    if "history" not in st.session_state:
        st.session_state.history = []

    if st.button("Preguntar", type="primary", disabled=not question.strip()):
        source_arg = None if source == "Todos" else source
        with st.spinner("Recuperando y generando..."):
            try:
                with httpx.Client(timeout=120.0) as client:
                    r = client.post(
                        f"{API_URL}/query",
                        json={
                            "question": question,
                            "top_k": top_k,
                            "source": source_arg,
                        },
                    )
            except httpx.ConnectError:
                st.error("No se pudo conectar con la API. ¿Está corriendo FastAPI en :8000?")
                st.stop()

            if r.status_code != 200:
                st.error(f"Error {r.status_code}: {r.text}")
                st.stop()

            data = r.json()

            if not data["citations"]:
                st.warning("Corpus vacío: indexa documentos antes de preguntar.")
                st.stop()

            st.session_state.history.append(
                {
                    "question": question,
                    "source": source,
                    "answer": data["answer"],
                    "abstained": data["abstained"],
                    "citations": data["citations"],
                }
            )

    st.divider()
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.subheader("Historial de preguntas")
    with col_h2:
        if st.session_state.history and st.button("Borrar historial"):
            st.session_state.history = []

    if not st.session_state.history:
        st.caption("Todavía no has hecho preguntas.")
    for item in reversed(st.session_state.history):
        src = "" if item["source"] == "Todos" else f"  ·  fuente: {item['source']}"
        st.markdown(f"**P:** {item['question']}{src}")
        if item["abstained"]:
            st.warning(item["answer"])
        else:
            st.write(item["answer"])
        for i, c in enumerate(item["citations"], start=1):
            with st.expander(
                f"[{i}] {c['source']} (pág. {c['page']}) — score {c['score']}"
            ):
                st.write(c["text"])
