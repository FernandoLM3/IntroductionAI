# RAG Liga MX

Sistema **RAG** sobre estadísticas de la Liga MX. Ciclo completo:

```
incrustar (Google AI) → indexar (ChromaDB) → recuperar top-k → generar (Gemini)
```

- **UI:** Streamlit (puerto `8501`) — solo cliente HTTP.
- **API:** FastAPI (puerto `8000`) — `/health`, `/ingest`, `/query`, `/sources`.
- **Índice:** ChromaDB persistente en `chroma/`.
- **Embeddings:** Google AI `gemini-embedding-2` (el mismo modelo para documentos y preguntas).
- **Generación:** Gemini `gemini-3.8-flash`, en español, con citas `[n]`.

## 1. Crear el entorno virtual

```bash
cd rag-app
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Obtener y configurar la clave de Google AI

1. Entra a https://aistudio.google.com/apikey y crea una API key.
2. Copia el `.env.example` a `.env`:

```bash
cp .env.example .env
```

3. Edita `.env` y pega tu clave:

```
GOOGLE_API_KEY=tu_clave_aqui
```

> `.env` y `chroma/` están en `.gitignore`. No subas la clave al repositorio.

## 3. Añadir el corpus

El corpus ya viene incluido en `data/liga_mx/` (7 PDFs con texto seleccionable,
extraídos de Wikipedia y reescalados, con atribución y fecha de corte a 2026):

- `Primera_Division_de_Mexico.pdf`, `75.pdf`
- `Club_America.pdf`, `Club_Deportivo_Guadalajara.pdf`
- `Club_Universidad_Nacional.pdf`, `Club_de_Futbol_Cruz_Azul.pdf`
- `HistoriadeCampeonesdelaPrimeraDivisiondeMexico.pdf`

Para usar tus propios documentos, colócalos (PDF con texto, Markdown o TXT) en
`data/liga_mx/`. Ver `data/liga_mx/README.md` para los requisitos.

Hay tres formas de indexar:

1. **UI (pocos archivos):** pestaña *Ingesta* → sube los archivos → *Indexar*.
2. **API por carpeta:** `POST /ingest/folder` con `{"folder": "data/liga_mx"}`.
3. **Script local (recomendado para el corpus completo):** indexa por lotes,
   con reintentos ante el límite de cuota gratuita, y es reanudable:

```bash
python scripts/ingest_local.py
```

> La cuota gratuita de la API de embeddings es baja. Si subes los 7 PDFs de
> golpe por la UI puedes toparte con errores 429. El script (opción 3) maneja
> eso automáticamente; puedes repetirlo hasta que el log termine con
> `Listo. Chroma tiene 789 chunks.`

## 4. Levantar la API

```bash
uvicorn app.main:app --reload --port 8000
```

Comprueba en http://localhost:8000/docs que aparecen `/health`, `/ingest` y `/query`.

## 5. Levantar la UI (otra terminal)

```bash
streamlit run ui/streamlit_app.py
```

Abre http://localhost:8501.

## 6. Probar una pregunta

Si usaste el script de ingesta, el índice ya está listo. Si no, indexa primero
desde la pestaña **Ingesta** de la UI. Después, en la pestaña **Preguntar**
escribe, por ejemplo:
   - *¿Qué equipo tiene más títulos de Liga MX?*
   - *¿Quién es el máximo goleador histórico?*
   - *¿Cómo funciona la liguilla?*
   - Pregunta fuera de dominio: *¿Quién ganó la Champions 2024?* → debe **abstenerse**.

## Regla de abstención

Se combinan dos criterios:

1. **Umbral de score** (`MIN_SCORE`, por defecto `0.35`): si ningún chunk
   recuperado supera ese score, la API responde directamente
   "No tengo evidencia suficiente" sin llamar a Gemini.
2. **Instrucción al modelo**: el prompt obliga a Gemini a responder solo con
   el contexto y a decir "No tengo evidencia suficiente" si el dato no está.
   Si la respuesta contiene ese marcador, `abstained` se marca `true`.

El score se calcula como `1 - distancia_coseno` de ChromaDB.

## Parámetros configurables (`.env`)

| Variable | Default | Descripción |
|---|---|---|
| `EMBEDDING_MODEL` | `gemini-embedding-2` | Modelo de embeddings |
| `GENERATION_MODEL` | `gemini-3.8-flash` | Modelo de generación |
| `CHUNK_SIZE` | `300` | Palabras por chunk |
| `CHUNK_OVERLAP` | `60` | Palabras de solape |
| `DEFAULT_TOP_K` | `4` | k por defecto |
| `MIN_SCORE` | `0.35` | Umbral de abstención |

## Retos opcionales implementados

Además de lo obligatorio, incluye tres extras:

### 1. Filtro por `source` (consultar solo un documento)

`POST /query` acepta un campo opcional `source`; si se envía, la búsqueda se
restringe a los chunks de ese archivo:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué equipos fueron campeones en la era de torneos largos?",
       "top_k": 3,
       "source": "HistoriadeCampeonesdelaPrimeraDivisiondeMexico.pdf"}'
```

La UI tiene un desplegable "Filtrar por documento" (se alimenta de
`GET /sources`).

### 2. Reindexar un documento sin reconstruir todo

Sirve para **actualizar el contenido** de un PDF que ya estaba indexado. El
script borra los chunks viejos de ese archivo y vuelve a incrustar el nuevo,
sin tocar el resto de la colección.

Pasos:

1. **Reemplaza el archivo** en `data/liga_mx/` manteniendo el **mismo nombre**
   (los chunks se identifican por `fuente + índice`, no por contenido).

2. **Ejecuta el script** con la ruta del archivo:

```bash
source .venv/bin/activate
python scripts/reindex.py data/liga_mx/HistoriadeCampeonesdelaPrimeraDivisiondeMexico.pdf
```

3. El script imprime cuántos chunks borró, cuántos reindexó y el total en
   Chroma. Si la API ya estaba corriendo, el índice queda actualizado en disco
   (no hace falta reiniciar, pero sí puedes hacerlo para verlo en `/docs`).

> Nota: si no borras los chunks viejos primero, la ingesta normal
> (`scripts/ingest_local.py`) los **salta** porque ya existen. Por eso este
> script hace el borrado + reindexado en un solo paso.

### 3. Histórico de preguntas en la sesión de Streamlit

La pestaña **Preguntar** guarda cada pregunta y su respuesta (con citas y
scores) en `st.session_state` y las muestra en un historial. El botón
**Borrar historial** reinicia la sesión.
