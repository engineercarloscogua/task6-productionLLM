from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.chains import build_definition_chain, build_rag_answer_chain


def test_definition_chain_formats_prompt_and_parses_text() -> None:
    model = FakeListChatModel(responses=["Un agente decide qué acción ejecutar."])

    result = build_definition_chain(model).invoke({"concepto": "un agente"})

    assert result == "Un agente decide qué acción ejecutar."


def test_rag_chain_formats_context_and_parses_answer() -> None:
    model = FakeListChatModel(
        responses=["Renta Joven apoya la permanencia en educación superior."]
    )

    result = build_rag_answer_chain(model).invoke(
        {
            "question": "¿Qué es Renta Joven?",
            "context": "Fuente: manual.pdf, página 2\nContenido: apoyo de permanencia",
        }
    )

    assert result == "Renta Joven apoya la permanencia en educación superior."
