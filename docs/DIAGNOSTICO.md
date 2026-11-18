# Diagnóstico y trazabilidad de la Actividad 6

## Estado general

La migración desde el prototipo de la Actividad 5 está completa para ejecución local. La solución separa interfaz, agente, cadena LCEL, conocimiento, herramientas y catálogo de modelos. La validación determinista y el arranque de Streamlit están aprobados. Las mediciones contra OpenRouter y el despliegue público siguen pendientes porque requieren credenciales locales y autorización externa.

## Matriz requisito evidencia resultado pendiente

| Requisito | Archivo principal | Prueba o evidencia | Resultado | Pendiente |
|---|---|---|---|---|
| Aplicación web | `app.py` | Inicio local y endpoint de salud | Aprobado | URL pública |
| Modelo en OpenRouter | `src/agent.py`, `src/models.py` | Catálogo filtrado y configuración segura | Aprobado con llamada real | Ejecutar benchmark completo |
| Cadena LCEL | `src/chains.py` | `tests/test_chains.py` | Aprobado | Incorporar salida real al notebook si se autoriza API |
| RAG desde PDF | `src/pdf_knowledge.py`, `src/knowledge.py` | Extracción, páginas, fragmentos y TF-IDF | Aprobado | Evaluación con los PDF definitivos |
| Herramientas | `src/tools.py` | `tests/test_tools.py` | Cálculo aprobado también con agente real | Probar consulta mixta con ambas tools |
| Agente y memoria | `src/agent.py` | `tests/test_agent.py` y `thread_id` por sesión | Agente aprobado con OpenRouter | Prueba conversacional de seguimiento |
| Aislamiento por sesión | `app.py` | UUID por sesión y prueba de configuración | Aprobado de forma local | Prueba de dos navegadores tras despliegue |
| Rendimiento 1 2 5 | `scripts/benchmark.py` | CSV y JSON p50 p95 éxitos y errores | Preparado | Ejecutar; estado actual NO MEDIDO |
| Ética y sesgos | `docs/ETICA.md` | Riesgos y mitigaciones documentados | Completo | Revisar después de resultados reales |
| Resultados y conclusiones | `docs/RESULTADOS.md` | Evidencia local y limitaciones | Parcial | Añadir benchmark y URL verificada |
| Notebook de entrega | `notebooks/Actividad6_Entrega.ipynb` | Ejecución local de todas las celdas sin API | Aprobado | Añadir métricas y enlace público |
| Seguridad de secretos | `.gitignore`, Streamlit Secrets | Búsqueda local sin claves reales | Aprobado | Escaneo del historial antes del push |

## Riesgos abiertos

- Los modelos gratuitos de OpenRouter pueden cambiar, rechazar tools o responder con HTTP 429.
- La prueba local no sustituye la verificación del despliegue desde una sesión incógnita.
- La carga 1/2/5 debe ejecutarse con límites prudentes y conservar modelo, fecha, errores y cuota observada.
- El notebook debe actualizarse con resultados reales antes de la entrega; no deben copiarse cifras estimadas.
