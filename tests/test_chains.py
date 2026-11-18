from langchain_core.language_models.fake_chat_models import FakeListChatModel

from src.chains import build_definition_chain


def test_definition_chain_formats_prompt_and_parses_text() -> None:
    model = FakeListChatModel(responses=["Un agente decide qué acción ejecutar."])

    result = build_definition_chain(model).invoke({"concepto": "un agente"})

    assert result == "Un agente decide qué acción ejecutar."
