from langchain_core.documents import Document

from src.knowledge import KnowledgeBase


DOCUMENTS = [
    Document(
        page_content="El apoyo de transporte requiere matrícula activa.",
        metadata={"fuente": "manual.pdf", "pagina": 2},
    ),
    Document(
        page_content="El préstamo de computadores puede renovarse una vez.",
        metadata={"fuente": "reglamento.pdf", "pagina": 7},
    ),
]


def test_search_finds_transport_document() -> None:
    results = KnowledgeBase(DOCUMENTS).search("requisitos para el apoyo de transporte")

    assert results
    assert results[0].document.metadata["fuente"] == "manual.pdf"


def test_search_returns_empty_for_unrelated_words() -> None:
    results = KnowledgeBase(DOCUMENTS).search("astronomía cuántica oceánica")

    assert results == []


def test_context_contains_source_and_score() -> None:
    context = KnowledgeBase(DOCUMENTS).context("renovar préstamo de computadores")

    assert "reglamento.pdf, página 7" in context
    assert "Similitud TF-IDF" in context


def test_empty_knowledge_base_has_no_results() -> None:
    assert KnowledgeBase([]).search("cualquier pregunta") == []


def test_search_normalizes_bienestar_program_name_and_common_typo() -> None:
    documents = [
        Document(
            page_content="El Programa Bien-Estar Contigo ofrece apoyo de alimentacion.",
            metadata={"fuente": "bienestar.pdf", "pagina": 1},
        ),
        Document(
            page_content="Renta Joven promueve la permanencia en educacion superior.",
            metadata={"fuente": "renta-joven.pdf", "pagina": 2},
        ),
    ]
    knowledge = KnowledgeBase(documents)

    for query in ("Que es Bienestar Contigo?", "bienestar contgio"):
        results = knowledge.search(query)
        assert results[0].document.metadata["fuente"] == "bienestar.pdf"
