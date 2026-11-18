import pytest

from src.tools import calcular_transporte, consultar_documentos


def test_transport_calculation() -> None:
    result = calcular_transporte.invoke(
        {"viajes_por_dia": 2, "dias": 5, "costo_por_viaje": 3000}
    )

    assert result == 30000


def test_transport_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="no negativos"):
        calcular_transporte.invoke(
            {"viajes_por_dia": -1, "dias": 5, "costo_por_viaje": 3000}
        )


def test_document_tool_returns_pdf_source(monkeypatch) -> None:
    monkeypatch.setattr(
        "src.tools.pdf_knowledge_store.context",
        lambda pregunta: "Fuente: manual.pdf, página 4\nContenido: texto",
    )
    result = consultar_documentos.invoke({"pregunta": "talleres de escritura"})

    assert "manual.pdf, página 4" in result
