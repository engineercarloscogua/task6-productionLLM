from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from langchain_core.documents import Document
from pypdf import PdfReader

from src.knowledge import KnowledgeBase


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PDF_DIRECTORY = PROJECT_ROOT / "data" / "pdfs"


def split_text(text: str, chunk_words: int = 220, overlap_words: int = 40) -> list[str]:
    """Split extracted page text into overlapping, retrieval-friendly chunks."""
    words = re.sub(r"\s+", " ", text).strip().split()
    if not words:
        return []
    if chunk_words < 1 or overlap_words < 0 or overlap_words >= chunk_words:
        raise ValueError("La configuración de fragmentos no es válida.")
    step = chunk_words - overlap_words
    return [
        " ".join(words[start : start + chunk_words])
        for start in range(0, len(words), step)
        if words[start : start + chunk_words]
    ]


def load_pdf_documents(directory: Path) -> tuple[list[Document], list[str], int]:
    """Extract page-aware chunks from every PDF below a directory."""
    documents: list[Document] = []
    errors: list[str] = []
    pages_with_text = 0
    for path in sorted(directory.rglob("*.pdf"), key=lambda item: str(item).casefold()):
        try:
            reader = PdfReader(str(path))
            if reader.is_encrypted and reader.decrypt("") == 0:
                raise ValueError("el archivo está cifrado")
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                chunks = split_text(text)
                if chunks:
                    pages_with_text += 1
                for chunk_number, chunk in enumerate(chunks, start=1):
                    documents.append(
                        Document(
                            page_content=chunk,
                            metadata={
                                "fuente": path.name,
                                "ruta": str(path.relative_to(directory)),
                                "pagina": page_number,
                                "fragmento": chunk_number,
                            },
                        )
                    )
        except Exception as error:
            errors.append(f"{path.name}: {type(error).__name__}: {error}")
    return documents, errors, pages_with_text


@dataclass(frozen=True, slots=True)
class PDFStatus:
    files: tuple[str, ...]
    chunks: int
    pages_with_text: int
    errors: tuple[str, ...]


class PDFKnowledgeStore:
    """Reload the local PDF index only when the source files change."""

    def __init__(self, directory: Path = PDF_DIRECTORY) -> None:
        self.directory = directory
        self._lock = RLock()
        self._signature: tuple[tuple[str, int, int], ...] | None = None
        self._knowledge_base = KnowledgeBase([])
        self._status = PDFStatus((), 0, 0, ())

    def _current_signature(self) -> tuple[tuple[str, int, int], ...]:
        self.directory.mkdir(parents=True, exist_ok=True)
        return tuple(
            (
                str(path.relative_to(self.directory)),
                path.stat().st_size,
                path.stat().st_mtime_ns,
            )
            for path in sorted(
                self.directory.rglob("*.pdf"), key=lambda item: str(item).casefold()
            )
        )

    def refresh(self, force: bool = False) -> PDFStatus:
        with self._lock:
            signature = self._current_signature()
            if not force and signature == self._signature:
                return self._status
            documents, errors, pages_with_text = load_pdf_documents(self.directory)
            self._knowledge_base = KnowledgeBase(documents)
            self._signature = signature
            self._status = PDFStatus(
                files=tuple(item[0] for item in signature),
                chunks=len(documents),
                pages_with_text=pages_with_text,
                errors=tuple(errors),
            )
            return self._status

    def status(self) -> PDFStatus:
        return self.refresh()

    def context(self, query: str, k: int = 3) -> str:
        status = self.refresh()
        if not status.files:
            return (
                "No hay documentos PDF cargados. Agrega archivos en data/pdfs y "
                "vuelve a intentar."
            )
        if not status.chunks:
            return (
                "Los PDF cargados no contienen texto extraíble. Si son documentos "
                "escaneados, necesitan OCR antes de usarlos."
            )
        return self._knowledge_base.context(query, k=k)


pdf_knowledge_store = PDFKnowledgeStore()
