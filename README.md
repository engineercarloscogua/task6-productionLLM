# Asistente universitario con LangChain y Streamlit

Proyecto de la Actividad 6 de la asignatura de LLM de la Maestría en
Inteligencia Artificial de la Universidad de La Salle.

La aplicación transforma el prototipo de la Actividad 5 en un asistente web con:

- selección dinámica de modelos gratuitos de OpenRouter compatibles con herramientas;
- agente de LangChain con RAG, cálculo y memoria conversacional;
- historial aislado por sesión de Streamlit;
- recuperación de información desde documentos PDF locales con citas por página;
- medición básica de latencia y herramientas utilizadas.

## Requisitos

- Python 3.11 o superior.
- Una API key de OpenRouter.

Los modelos terminados en `:free` no tienen costo por tokens, pero OpenRouter
aplica límites de solicitudes y su disponibilidad puede cambiar.

## Configuración local

1. Crea el entorno e instala las dependencias:

   ```powershell
   uv venv
   uv pip install -r requirements-dev.txt
   ```

2. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` y
   agrega tu clave:

   ```toml
   OPENROUTER_API_KEY = "tu_clave"
   ```

   El archivo real está ignorado por Git y no debe publicarse.

3. Ejecuta las pruebas:

   ```powershell
   uv run pytest
   ```

4. Copia los documentos que utilizará el RAG en:

   ```text
   data/pdfs/
   ```

   Los PDF deben contener texto seleccionable. Si son escaneados como imágenes,
   aplica OCR antes de cargarlos. Puedes usar subcarpetas.

   El proyecto incluye una utilidad OCR local opcional:

   ```powershell
   uv pip install -r requirements-ocr.txt
   uv run python scripts/ocr_pdf.py entrada.pdf salida.pdf
   ```

   Esta utilidad usa RapidOCR en español y conserva visualmente las páginas.

5. Inicia la aplicación:

   ```powershell
   uv run streamlit run app.py
   ```

6. En la barra lateral, confirma que aparezcan los archivos y pulsa **Recargar
   documentos** después de cualquier cambio.

7. Con una clave válida y autorización para consumir la API, ejecuta el benchmark:

   ```powershell
   $env:OPENROUTER_API_KEY = "tu_clave"
   uv run python scripts/benchmark.py --concurrency 1 2 5
   ```

   El script escribe las muestras y el resumen en `results/`, una carpeta ignorada
   por Git. Copia únicamente resultados revisados al notebook de entrega.

## Alcance de los datos

La aplicación responde usando únicamente los PDF que el usuario coloca en
`data/pdfs/`. Cada fragmento conserva el nombre del archivo y su página para que
la respuesta pueda citar la fuente. Los documentos deben estar autorizados para
su uso y no deben contener información confidencial.

El LLM puede interpretar incorrectamente un fragmento incluso cuando la fuente
es real. Las decisiones importantes deben verificarse directamente en el PDF.

## Estructura

```text
app.py                     Interfaz Streamlit
src/agent.py               Agente, memoria y observabilidad
src/chains.py              Cadena LCEL explícita para la evidencia académica
src/knowledge.py           Índice y recuperación TF-IDF local
src/pdf_knowledge.py       Extracción, fragmentación y recarga de PDF
src/models.py              Catálogo de modelos gratuitos de OpenRouter
src/tools.py               Herramientas del agente
data/pdfs/                 Carpeta donde se cargan los documentos del RAG
scripts/benchmark.py       Carga controlada y métricas p50/p95
docs/                      Resultados, limitaciones y reflexión ética
notebooks/                 Notebook académico reproducible de entrega
tests/                     Pruebas deterministas sin consumo de API
```

## Estado del despliegue

La aplicación está validada localmente. El benchmark contra OpenRouter y el
despliegue público permanecen marcados como **NO MEDIDOS / NO REALIZADOS** hasta
contar con una clave válida y autorización explícita para consumir la API y
publicar el repositorio.
