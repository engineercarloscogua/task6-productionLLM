# Resultados y estado de validación

## Evidencia disponible

Las pruebas automatizadas verifican de forma local y sin consumo de API la extracción y fragmentación de PDF, la recuperación TF-IDF con citas por página, la herramienta documental, el filtro de alcance, el catálogo de modelos, la cadena LCEL y el paso de un `thread_id` independiente al agente. El filtro rechaza PQR, desarrollo de código, creación de medios, cálculos, extracción de secretos, inyección de prompt, copia masiva y preguntas ajenas al corpus antes de invocar OpenRouter. Los fragmentos recuperados se delimitan como datos no confiables. Las citas redactadas por el modelo se eliminan y se sustituyen por fuentes recuperadas de manera determinista.

Validación local actualizada el 20 de noviembre de 2026:

| Evidencia | Resultado |
|---|---|
| Suite determinista | 47 pruebas aprobadas |
| Compilación de módulos | Correcta |
| Arranque de Streamlit | Correcto en puerto local de prueba |
| Endpoint de salud | HTTP 200 y respuesta `ok` |
| Instalación limpia de producción | Correcta con Python 3.12 y `requirements.txt` |
| Ejecución de celdas del notebook sin API | Correcta |
| Auditoría OCR del corpus actual | 216 páginas con texto y 0 errores |
| Consulta real a OpenRouter | 9/9 consultas correctas con `nvidia/nemotron-3.5-lightning:free` |
| Tool documental en el benchmark | `consultar_documentos` utilizada en 9/9 consultas |
| Despliegue público | Publicado en https://fomento-socioeconomico.streamlit.app/ |

## Rendimiento y cargas de trabajo

Estado: **MEDIDO EL 20 DE NOVIEMBRE DE 2026**.

La medición utilizó `nvidia/nemotron-3.5-lightning:free`, tres solicitudes por
nivel y consultas documentales aceptadas por el filtro local. Una muestra solo se
contabilizó como exitosa cuando el modelo fue invocado y el agente utilizó
`consultar_documentos`.

| Concurrencia | Solicitudes | Éxitos | Fallos | Promedio (s) | P50 (s) | P95 (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 3 | 3 | 0 | 12.606 | 10.130 | 25.343 |
| 2 | 3 | 3 | 0 | 4.747 | 5.746 | 5.823 |
| 5 | 3 | 3 | 0 | 6.962 | 8.502 | 9.712 |

Las nueve solicitudes fueron correctas. La concurrencia 2 presentó el menor
promedio en esta muestra. Al pasar de 2 a 5 aumentó la latencia promedio, aunque
se mantuvo por debajo de la ejecución secuencial, influida por una primera
respuesta de 25.343 s. Estos resultados demuestran funcionamiento bajo las tres
cargas probadas, pero no capacidad sostenida ni un acuerdo de disponibilidad.

El resumen verificable se conserva en
`docs/evidence/benchmark_summary_2026-11-20.json`. Los niveles 1, 2 y 5 son una
decisión metodológica del equipo y no valores impuestos literalmente por la
rúbrica.

## Limitaciones de interpretación

- Los modelos gratuitos y sus cuotas cambian; una medición sólo describe el modelo, fecha y condiciones registradas.
- Una muestra pequeña no demuestra capacidad de producción sostenida.
- `InMemorySaver` conserva contexto de corto plazo en el proceso, pero lo pierde al reiniciar la aplicación.
- TF-IDF funciona bien para coincidencias léxicas, pero entiende mal sinónimos y puede recuperar fragmentos poco pertinentes.
- La calidad depende de que los PDF tengan texto extraíble, estén vigentes y cubran la pregunta.
- Los PDF escaneados como imágenes requieren OCR antes de ser indexados.
