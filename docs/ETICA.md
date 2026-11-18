# Consideraciones éticas y mitigaciones

## Alcance de la información

La aplicación usa los PDF que el responsable coloca en `data/pdfs/`. Cargar un documento real no garantiza que esté vigente, completo o autorizado para todos los usos. La interfaz identifica el archivo y la página para facilitar la verificación. El agente recibe la instrucción de no inventar plazos, requisitos, teléfonos ni fuentes y de reconocer cuando el contexto no contiene la respuesta.

## Riesgos principales

**Alucinaciones.** El modelo puede presentar una inferencia como un hecho. La mitigación combina recuperación local, citas por archivo y página, temperatura cero, instrucciones restrictivas y pruebas sobre información ausente. Ninguna de estas medidas elimina el riesgo; una respuesta importante debe verificarse en el PDF original.

**Sesgo y cobertura.** El asistente sólo conoce los PDF cargados, que pueden omitir grupos, excepciones o versiones recientes. TF-IDF además favorece coincidencias literales, por lo que una persona que use sinónimos puede recibir peor recuperación. La mitigación es declarar el corpus, no extrapolar y revisar fechas, cobertura y procedencia antes de usarlo.

**Privacidad.** No deben cargarse PDF confidenciales, expedientes, identificadores ni datos sensibles sin una base legítima y controles adecuados. Los fragmentos recuperados se envían a OpenRouter para generar la respuesta. La clave se mantiene en variables de entorno o Secrets de Streamlit y no debe aparecer en el navegador, notebook, logs o repositorio. La memoria es efímera y se separa mediante un `thread_id` por sesión.

**Coste y disponibilidad.** Los modelos gratuitos tienen cuotas y disponibilidad variables. La aplicación debe comunicar errores 401, 429 y de tiempo de espera sin prometer servicio continuo. Los reintentos son limitados para no amplificar carga o coste.

## Uso responsable

Este prototipo sirve para demostrar LangChain, RAG, herramientas y memoria. No debe decidir beneficios, sanciones, admisiones ni otros asuntos de alto impacto. Una adaptación institucional necesitaría documentos oficiales, gobierno de datos, evaluación con usuarios diversos, monitoreo, accesibilidad, revisión humana y un canal de corrección.
