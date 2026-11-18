# Diagnóstico y trazabilidad de la Actividad 6

## Estado general

La migración desde el prototipo de la Actividad 5 está completa para ejecución local. La solución separa interfaz, agente, cadena LCEL, conocimiento, herramientas y catálogo de modelos. La validación determinista y el arranque de Streamlit están aprobados. Las mediciones contra OpenRouter y el despliegue público siguen pendientes porque requieren credenciales locales y autorización externa.

## Matriz requisito evidencia resultado pendiente

| Requisito | Archivo principal | Prueba o evidencia | Resultado | Pendiente |
|---|---|---|---|---|
| Aplicación web | `app.py` | Inicio local y endpoint de salud | Aprobado | URL pública |
| Modelo en OpenRouter | `src/agent.py`, `src/models.py` | Catálogo filtrado y configuración segura | Aprobado con llamada real | Ejecutar la prueba final de cargas |
| Cadena LCEL | `src/chains.py` | `tests/test_chains.py` | Aprobado | Incorporar salida real al notebook si se autoriza API |
| RAG desde PDF | `src/pdf_knowledge.py`, `src/knowledge.py` | Extracción, páginas, fragmentos y TF-IDF | Aprobado | Evaluación con los PDF definitivos |
| Herramientas | `src/tools.py` | `tests/test_tools.py` | Cálculo aprobado también con agente real | Probar consulta mixta con ambas tools |
| Agente y memoria | `src/agent.py` | `tests/test_agent.py` y `thread_id` por sesión | Agente aprobado con OpenRouter | Prueba conversacional de seguimiento |
| Aislamiento por sesión | `app.py` | UUID por sesión y prueba de configuración | Aprobado de forma local | Prueba de dos navegadores tras despliegue |
| Rendimiento con cargas diferentes | `scripts/benchmark.py` | Solicitudes, éxitos, fallos y tiempo promedio | Preparado | Ejecutar; estado actual NO MEDIDO |
| Ética y sesgos | `docs/ETICA.md` | Riesgos y mitigaciones documentados | Completo | Revisar después de resultados reales |
| Resultados y conclusiones | `docs/RESULTADOS.md` | Evidencia local y limitaciones | Parcial | Añadir la prueba de cargas y la URL verificada |
| Notebook de entrega | `notebooks/Actividad6_Entrega.ipynb` | Ejecución local de todas las celdas sin API | Aprobado | Añadir métricas y enlace público |
| Seguridad de secretos | `.gitignore`, Streamlit Secrets | Búsqueda local sin claves reales | Aprobado | Escaneo del historial antes del push |

## Riesgos abiertos

- Los modelos gratuitos de OpenRouter pueden cambiar, rechazar tools o responder con HTTP 429.
- La prueba local no sustituye la verificación del despliegue desde una sesión incógnita.
- Las cargas seleccionadas deben ejecutarse con límites prudentes y conservar modelo, fecha, errores y cuota observada.
- El notebook debe actualizarse con resultados reales antes de la entrega; no deben copiarse cifras estimadas.
