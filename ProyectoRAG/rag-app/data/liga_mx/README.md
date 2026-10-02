# Corpus: estadísticas de la Liga MX

Coloca aquí tus documentos. Formatos soportados: **PDF**, **Markdown** y **TXT**.

## Requisito indispensable del PDF

El PDF **debe tener texto seleccionable**. Es decir, si abres el PDF y puedes
seleccionar/copiar el texto con el cursor, sirve. Si es un **escaneo** (solo
imagen), no tiene texto y el sistema no podrá extraerlo → necesitarías OCR
y, según el proyecto, mejor no contarlo como documento.

Cómo comprobarlo: abre el PDF y trata de seleccionar una frase. O usa:

```bash
python -c "import pdfplumber; print(pdfplumber.open('tu_archivo.pdf').pages[0].extract_text())"
```

Si imprime texto → OK. Si imprime `None` → es escaneado.

## Reglas del corpus

- Al menos **5 documentos** distintos y coherentes.
- **Varios miles de palabras** en total.
- Incluye una pregunta **imposible** de responder (p. ej. de otro deporte o
  de una liga distinta) para probar la abstención.
- Anota la **fecha de corte** en cada archivo (las stats caducan).

## Sugerencia de documentos

- `01_historia_y_formato.pdf` — origen, Apertura/Clausura, liguilla.
- `02_equipos_y_palmares.pdf` — títulos por club.
- `03_goleadores_y_records.pdf` — goleadores históricos y récords.
- `04_temporada_2024_2025.pdf` — campeones y tabla general.
- `05_clausura_2025_detalle.pdf` — liguilla y final.
- `06_reglamento_basico.pdf` — puntos, desempates, VAR.
