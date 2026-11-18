# Resultados y estado de validación

## Evidencia disponible

Las pruebas automatizadas verifican de forma local y sin consumo de API la extracción y fragmentación de PDF, la recuperación TF-IDF con citas por página, las dos herramientas, el filtrado del catálogo de modelos, la cadena LCEL y el paso de un `thread_id` independiente al agente. Los resultados deben actualizarse después de ejecutar `pytest`; no se incluyen valores inventados.

Validación local del 16 de noviembre de 2026:

| Evidencia | Resultado |
|---|---|
| Suite determinista | 17 pruebas aprobadas |
| Compilación de módulos | Correcta |
| Arranque de Streamlit | Correcto en puerto local de prueba |
| Endpoint de salud | HTTP 200 y respuesta `ok` |
| Ejecución de celdas del notebook sin API | Correcta |
| Auditoría OCR del corpus actual | 216 páginas con texto y 0 errores |
| Consulta real a OpenRouter | Aprobada con `openrouter/free` |
| Despliegue público | NO REALIZADO |

## Rendimiento contra OpenRouter

Estado: **NO MEDIDO**.

La prueba de integración mínima del 16 de noviembre de 2026 sí fue ejecutada:
el agente utilizó `calcular_transporte`, obtuvo 30.000 pesos y respondió en
15,87 segundos con `openrouter/free`. Esta única solicitud confirma la conexión
y el tool-calling, pero no sustituye el benchmark de concurrencia.

El script `scripts/benchmark.py` ejecuta cargas controladas con concurrencia 1, 2 y 5, y guarda muestras CSV y un resumen JSON con tasa de éxito, errores, latencia media, p50 y p95. Requiere `OPENROUTER_API_KEY` en el entorno. Hasta ejecutar ese script con autorización y una clave válida, no se afirma rendimiento real ni escalabilidad.

## Limitaciones de interpretación

- Los modelos gratuitos y sus cuotas cambian; una medición sólo describe el modelo, fecha y condiciones registradas.
- Una muestra pequeña no demuestra capacidad de producción sostenida.
- `InMemorySaver` conserva contexto de corto plazo en el proceso, pero lo pierde al reiniciar la aplicación.
- TF-IDF funciona bien para coincidencias léxicas, pero entiende mal sinónimos y puede recuperar fragmentos poco pertinentes.
- La calidad depende de que los PDF tengan texto extraíble, estén vigentes y cubran la pregunta.
- Los PDF escaneados como imágenes requieren OCR antes de ser indexados.
