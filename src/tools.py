from __future__ import annotations

from langchain_core.tools import tool

from src.pdf_knowledge import pdf_knowledge_store


@tool
def consultar_documentos(pregunta: str) -> str:
    """Busca información y fuentes en los documentos PDF cargados por el usuario."""
    return pdf_knowledge_store.context(pregunta)


@tool
def calcular_transporte(
    viajes_por_dia: int,
    dias: int,
    costo_por_viaje: float,
) -> float:
    """Calcula el gasto de transporte en pesos con datos suministrados por el usuario."""
    if viajes_por_dia < 0 or dias < 0 or costo_por_viaje < 0:
        raise ValueError("Los valores deben ser no negativos.")
    return round(viajes_por_dia * dias * costo_por_viaje, 2)


TOOLS = [consultar_documentos, calcular_transporte]
