from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pymupdf
from rapidocr import ModelType, RapidOCR


def build_engine() -> RapidOCR:
    """Create an offline OCR engine configured for Spanish documents."""
    return RapidOCR(
        params={
            "Det.lang_type": "es",
            "Rec.lang_type": "es",
            "Det.model_type": ModelType.TINY,
            "Rec.model_type": ModelType.TINY,
        }
    )


def ocr_pdf(input_path: Path, output_path: Path, dpi: int = 200) -> tuple[int, int]:
    """Add an invisible OCR text layer while preserving every original page image."""
    document = pymupdf.open(input_path)
    engine = build_engine()
    recognized_pages = 0
    recognized_lines = 0
    matrix = pymupdf.Matrix(dpi / 72, dpi / 72)

    for page_number, page in enumerate(document, start=1):
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
            pixmap.height,
            pixmap.width,
            pixmap.n,
        )
        result = engine(image)
        lines = [text.strip() for text in result.txts if text and text.strip()]
        if lines:
            recognized_pages += 1
            recognized_lines += len(lines)
            remaining = page.insert_textbox(
                page.rect,
                "\n".join(lines),
                fontsize=2.5,
                lineheight=1.0,
                fontname="helv",
                encoding=0,
                render_mode=3,
                overlay=True,
            )
            if remaining < 0:
                raise RuntimeError(
                    f"La capa OCR no cupo en la página {page_number} de {input_path.name}."
                )
        print(
            f"{input_path.name}: página {page_number}/{len(document)} "
            f"({len(lines)} líneas)",
            flush=True,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document.save(output_path, garbage=4, deflate=True, clean=True)
    document.close()
    return recognized_pages, recognized_lines


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agrega una capa OCR local en español a un PDF escaneado."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dpi", type=int, default=200)
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"No existe el PDF: {args.input}")
    if args.input.resolve() == args.output.resolve():
        parser.error("El archivo de salida debe ser diferente del original.")

    pages, lines = ocr_pdf(args.input, args.output, dpi=args.dpi)
    print(f"OCR terminado: {pages} páginas y {lines} líneas reconocidas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
