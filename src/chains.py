from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


DEFINITION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Explica conceptos de PLN en español sencillo, en un máximo de tres frases.",
        ),
        ("human", "¿Qué es {concepto}?"),
    ]
)

RAG_ANSWER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente documental universitario. Responde en español "
            "utilizando únicamente el contexto recuperado. Si el contexto no "
            "contiene la respuesta, indícalo claramente. No inventes datos ni "
            "fuentes.",
        ),
        (
            "human",
            "Pregunta:\n{question}\n\nContexto documental:\n{context}\n\n"
            "Redacta una respuesta breve, concreta y verificable.",
        ),
    ]
)


def build_definition_chain(model: Any) -> Runnable:
    """Build the explicit LCEL chain required by the academic exercise."""
    return DEFINITION_PROMPT | model | StrOutputParser()


def build_rag_answer_chain(model: Any) -> Runnable:
    """Build an LCEL chain that answers strictly from retrieved PDF context."""
    return RAG_ANSWER_PROMPT | model | StrOutputParser()
