# Asistente universitario con LangChain y Streamlit

Proyecto de la Actividad 6 de la asignatura de LLM de la Maestría en
Inteligencia Artificial de la Universidad de La Salle.

La aplicación transforma el prototipo de la Actividad 5 en un asistente web con:

- selección dinámica de modelos gratuitos de OpenRouter compatibles con herramientas;
- agente de LangChain limitado a consultas RAG sobre el corpus y memoria conversacional;
- filtro local que rechaza creación de contenido, código y medios sin consumir tokens;
- historial aislado por sesión de Streamlit;
- recuperación de información desde documentos PDF locales con citas por página;
- medición básica de latencia y herramientas utilizadas.

## Requisitos

- Python 3.11 o superior.
- Una API key de OpenRouter y, opcionalmente, una API key de pago de OpenAI.

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
   OPENAI_API_KEY = "tu_clave_de_openai_opcional"
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

   En la barra lateral puedes elegir **OpenRouter** para usar modelos gratuitos o
   **OpenAI** para usar la cuenta de pago. El cambio siempre es manual para evitar
   cargos inesperados. GPT-6 Luna es la opción de OpenAI seleccionada por defecto
   por su menor costo relativo.

6. En la barra lateral, confirma que aparezcan los archivos y pulsa **Recargar
   documentos** después de cualquier cambio.

7. Con una clave válida y autorización para consumir la API, ejecuta la prueba de
   rendimiento con diferentes cargas de trabajo:

   ```powershell
   $env:OPENROUTER_API_KEY = "tu_clave"
   uv run python scripts/benchmark.py --concurrency 1 2 5
   ```

   El script escribe las muestras y el resumen en `results/`, una carpeta ignorada
   por Git. Copia únicamente resultados revisados al notebook de entrega. Los
   niveles 1, 2 y 5 son una metodología del equipo, no valores impuestos por la
   rúbrica.

## Despliegue en Streamlit Community Cloud

1. Selecciona el repositorio `engineercarloscogua/task6-productionLLM`, la rama
   `main` y el archivo principal `app.py`.
2. En **Advanced settings**, elige Python 3.12 para reproducir el entorno usado
   durante las pruebas.
3. Agrega el secreto sin comillas adicionales:

   ```toml
   OPENROUTER_API_KEY = "tu_clave_de_openrouter"
   ```

4. Despliega o reinicia la aplicación y revisa los logs de instalación. Community
   Cloud debe detectar `requirements.txt` como la única fuente de dependencias.
5. Verifica la aplicación desde una ventana privada y confirma que el catálogo de
   modelos, los PDF y una consulta documental funcionen correctamente.

Si una aplicación ya fue creada con otra versión de Python, Community Cloud exige
eliminarla y volverla a desplegar para cambiar esa versión.

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
src/chains.py              Cadenas LCEL de definición y respuesta RAG documental
src/knowledge.py           Índice y recuperación TF-IDF local
src/pdf_knowledge.py       Extracción, fragmentación y recarga de PDF
src/models.py              Catálogo de modelos gratuitos de OpenRouter
src/tools.py               Herramientas del agente
data/pdfs/                 Carpeta donde se cargan los documentos del RAG
scripts/benchmark.py       Prueba controlada con diferentes cargas de trabajo
docs/                      Resultados, seguridad, limitaciones y reflexión ética
notebooks/Actividad6_Entrega_Colab.ipynb  Notebook reproducible de entrega
tests/                     Pruebas deterministas sin consumo de API
```

## Estado del despliegue

La aplicación y sus dependencias están validadas localmente con Python 3.12 y se
encuentra publicada en https://fomento-socioeconomico.streamlit.app/. La medición
del 20 de noviembre de 2026 registró 9/9 consultas correctas con concurrencias 1,
2 y 5; sus resultados e interpretación se conservan en `docs/RESULTADOS.md` y en
el notebook de entrega.
