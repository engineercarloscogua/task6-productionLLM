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


def build_definition_chain(model: Any) -> Runnable:
    """Build the explicit LCEL chain required by the academic exercise."""
    return DEFINITION_PROMPT | model | StrOutputParser()
