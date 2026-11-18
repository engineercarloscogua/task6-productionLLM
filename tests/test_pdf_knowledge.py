from pathlib import Path

from src.pdf_knowledge import (
    PDFKnowledgeStore,
    load_pdf_documents,
    split_text,
)


def test_split_text_uses_overlap() -> None:
    chunks = split_text("uno dos tres cuatro cinco seis", chunk_words=4, overlap_words=2)

    assert chunks == ["uno dos tres cuatro", "tres cuatro cinco seis", "cinco seis"]


def test_load_pdf_documents_keeps_file_and_page(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "manual.pdf"
    pdf_path.write_bytes(b"contenido de prueba")

    class Page:
        def __init__(self, text: str) -> None:
            self.text = text

        def extract_text(self) -> str:
            return self.text

    class Reader:
        is_encrypted = False
        pages = [Page("Primera página con requisitos."), Page("Segunda página.")]

    monkeypatch.setattr("src.pdf_knowledge.PdfReader", lambda path: Reader())

    documents, errors, pages = load_pdf_documents(tmp_path)

    assert errors == []
    assert pages == 2
    assert documents[0].metadata["fuente"] == "manual.pdf"
    assert documents[1].metadata["pagina"] == 2


def test_store_explains_when_no_pdfs_are_loaded(tmp_path: Path) -> None:
    store = PDFKnowledgeStore(tmp_path)

    assert store.status().files == ()
    assert "No hay documentos PDF cargados" in store.context("pregunta")
