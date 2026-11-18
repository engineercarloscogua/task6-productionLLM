# Documentos para el RAG

Copia en esta carpeta los archivos PDF que utilizará el asistente.

- Se admiten varios PDF y subcarpetas.
- Los archivos deben contener texto seleccionable.
- Cada respuesta citará el nombre del archivo y la página recuperada.
- Si un PDF es una imagen escaneada, aplícale OCR antes de cargarlo.
- No incluyas documentos confidenciales ni archivos sin autorización de uso.

Después de agregar o reemplazar documentos, pulsa **Recargar documentos** en la
barra lateral de la aplicación.

Para aplicar OCR local en español:

```powershell
uv pip install -r requirements-ocr.txt
python scripts/ocr_pdf.py documento_escaneado.pdf documento_con_ocr.pdf
```

El script conserva la imagen visible y agrega una capa de texto invisible.
