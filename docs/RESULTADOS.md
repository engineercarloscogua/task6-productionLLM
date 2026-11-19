# Resultados y estado de validación

## Evidencia disponible

Las pruebas automatizadas verifican de forma local y sin consumo de API la extracción y fragmentación de PDF, la recuperación TF-IDF con citas por página, la herramienta documental, el filtro de alcance, el catálogo de modelos, la cadena LCEL y el paso de un `thread_id` independiente al agente. El filtro rechaza PQR, desarrollo de código, creación de medios, cálculos, extracción de secretos, inyección de prompt, copia masiva y preguntas ajenas al corpus antes de invocar OpenRouter. Los fragmentos recuperados se delimitan como datos no confiables y las respuestas sin herramienta o cita verificable no se muestran.

Validación local del 17 de noviembre de 2026:

| Evidencia | Resultado |
|---|---|
| Suite determinista | 42 pruebas aprobadas |
| Compilación de módulos | Correcta |
| Arranque de Streamlit | Correcto en puerto local de prueba |
| Endpoint de salud | HTTP 200 y respuesta `ok` |
| Instalación limpia de producción | Correcta con Python 3.12 y `requirements.txt` |
| Ejecución de celdas del notebook sin API | Correcta |
| Auditoría OCR del corpus actual | 216 páginas con texto y 0 errores |
| Consulta real a OpenRouter | Aprobada con `openrouter/free` |
| Despliegue público | NO REALIZADO |

## Rendimiento y cargas de trabajo

Estado: **NO MEDIDO**.

La prueba histórica de cálculo del 16 de noviembre ya no representa el alcance
actual. El agente ahora expone únicamente `consultar_documentos`; las solicitudes
no documentales se resuelven con un rechazo local y cero tokens. Debe ejecutarse
una nueva prueba de integración documental antes de cerrar la entrega.

El script `scripts/benchmark.py` permite observar el comportamiento con cargas
controladas. El notebook de entrega utiliza tres solicitudes con concurrencias 1,
2 y 5 y presenta éxitos, fallos y tiempo promedio. Estos niveles son una decisión
metodológica del equipo y no un requisito literal de la rúbrica. La ejecución
requiere `OPENROUTER_API_KEY` en el entorno; mientras no se realice, no se afirma
rendimiento real ni escalabilidad.

## Limitaciones de interpretación

- Los modelos gratuitos y sus cuotas cambian; una medición sólo describe el modelo, fecha y condiciones registradas.
- Una muestra pequeña no demuestra capacidad de producción sostenida.
- `InMemorySaver` conserva contexto de corto plazo en el proceso, pero lo pierde al reiniciar la aplicación.
- TF-IDF funciona bien para coincidencias léxicas, pero entiende mal sinónimos y puede recuperar fragmentos poco pertinentes.
- La calidad depende de que los PDF tengan texto extraíble, estén vigentes y cubran la pregunta.
- Los PDF escaneados como imágenes requieren OCR antes de ser indexados.
