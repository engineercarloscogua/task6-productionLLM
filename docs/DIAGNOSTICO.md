# Diagnóstico y trazabilidad de la Actividad 6

## Estado general

La migración desde el prototipo de la Actividad 5 está completa. La solución separa interfaz, agente, cadenas LCEL, conocimiento, herramientas y catálogo de modelos. La validación determinista, el arranque de Streamlit, el despliegue público y la medición controlada contra OpenRouter están documentados. Antes de entregar solo falta ejecutar desde cero la versión final del Colab, retirar la clave temporal y conservar sus salidas.

## Matriz requisito evidencia resultado pendiente

| Requisito | Archivo principal | Prueba o evidencia | Resultado | Pendiente |
|---|---|---|---|---|
| Aplicación web | `app.py` | Inicio local, salud HTTP 200/`ok` y URL pública | Aprobado | Verificación visual final en incógnito |
| Modelo en OpenRouter | `src/agent.py`, `src/models.py` | 9/9 consultas reales correctas | Aprobado | Revocar la clave temporal al cerrar la entrega |
| Cadena LCEL | `src/chains.py` | Cadenas de definición y RAG; `tests/test_chains.py` | Aprobado | Ejecutar la demostración final en Colab |
| RAG desde PDF | `src/pdf_knowledge.py`, `src/knowledge.py` | 216 páginas y 551 chunks en la ejecución de Colab | Aprobado | Ninguno para la muestra actual |
| Herramienta RAG y alcance | `src/tools.py`, `src/guardrails.py` | 9/9 consultas del benchmark usaron `consultar_documentos` | Aprobado | Ninguno |
| Agente y memoria | `src/agent.py` | `tests/test_agent.py`, `thread_id` y demostración preparada en Colab | Aprobado | Ejecutar los dos turnos finales en Colab |
| Aislamiento por sesión | `app.py` | UUID por sesión y prueba de configuración | Aprobado de forma local | Prueba de dos navegadores tras despliegue |
| Rendimiento con cargas diferentes | `scripts/benchmark.py` | Concurrencias 1, 2 y 5; 9/9 éxitos | Medido | Repetir solo si cambia el modelo o el código |
| Ética y sesgos | `docs/ETICA.md` | Riesgos y mitigaciones documentados | Completo | Revisar después de resultados reales |
| Resultados y conclusiones | `docs/RESULTADOS.md` | Métricas, interpretación y limitaciones | Completo | Ninguno |
| Notebook de entrega | `notebooks/Actividad6_Entrega_Colab.ipynb` | RAG, LangChain, producción, métricas, ética y conclusiones | Preparado | Ejecutar de arriba abajo y guardar salidas |
| Seguridad de secretos | `.gitignore`, Streamlit Secrets | Búsqueda local sin claves reales | Aprobado | Escaneo del historial antes del push |

## Riesgos abiertos

- Los modelos gratuitos de OpenRouter pueden cambiar, rechazar tools o responder con HTTP 429.
- La prueba local y el HTTP 200 no sustituyen la verificación visual desde una sesión incógnita.
- La muestra de nueve solicitudes no demuestra capacidad sostenida ni disponibilidad futura.
- El notebook final todavía debe ejecutarse de arriba abajo en Colab y guardarse sin una clave activa.
