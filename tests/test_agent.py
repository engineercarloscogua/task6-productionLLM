from types import SimpleNamespace

from src.agent import (
    NO_DOCUMENT_RESPONSE,
    UNVERIFIED_RESPONSE,
    _contextualize_question,
    _tool_names,
    build_agent,
    run_agent,
)


class FakeAgent:
    def __init__(self, messages: list[SimpleNamespace]) -> None:
        self.messages = messages
        self.payload = None
        self.config = None

    def invoke(self, payload: dict, config: dict) -> dict:
        self.payload = payload
        self.config = config
        return {"messages": self.messages}


def message(
    kind: str,
    content: str = "",
    tool_calls: list[dict[str, str]] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(type=kind, content=content, tool_calls=tool_calls or [])


def test_tool_names_only_include_current_turn() -> None:
    messages = [
        message("human", "pregunta anterior"),
        message("ai", tool_calls=[{"name": "consultar_documentos"}]),
        message("human", "pregunta actual"),
        message("ai", tool_calls=[{"name": "calcular_transporte"}]),
        message("tool"),
        message("ai", "respuesta"),
    ]

    assert _tool_names(messages) == ["calcular_transporte"]


def test_program_context_is_preserved_for_ambiguous_follow_up() -> None:
    thread_id = "sesion-contexto-programa"

    assert _contextualize_question("¿Qué es Bien-Estar Contigo?", thread_id) == (
        "¿Qué es Bien-Estar Contigo?"
    )
    contextualized = _contextualize_question(
        "¿Necesito tener Sisbén para participar?",
        thread_id,
    )

    assert "Programa de referencia: Bien-Estar Contigo." in contextualized


def test_ambiguous_first_question_searches_both_programs() -> None:
    contextualized = _contextualize_question(
        "¿Necesito tener Sisbén para participar?",
        "sesion-sin-contexto-previo",
    )

    assert "Renta Joven y Bien-Estar Contigo" in contextualized


def test_build_agent_uses_openai_responses_api(monkeypatch) -> None:
    captured = {}

    class FakeOpenAIModel:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("src.agent.ChatOpenAI", FakeOpenAIModel)
    monkeypatch.setattr(
        "src.agent.create_agent",
        lambda **kwargs: kwargs,
    )

    result = build_agent(
        api_key="clave-openai",
        model_id="gpt-6-luna",
        provider="openai",
    )

    assert captured["model"] == "gpt-6-luna"
    assert captured["use_responses_api"] is True
    assert captured["store"] is False
    assert captured["max_retries"] == 0
    assert result["model"].__class__ is FakeOpenAIModel


def test_build_agent_rejects_unknown_provider() -> None:
    import pytest

    with pytest.raises(ValueError, match="Proveedor no compatible"):
        build_agent("clave", "modelo", provider="desconocido")


def test_run_agent_passes_isolated_thread_id() -> None:
    fake_agent = FakeAgent(
        [
            message("human", "pregunta"),
            message("ai", tool_calls=[{"name": "consultar_documentos"}]),
            message(
                "tool",
                "Fuente: manual.pdf, página 4\nContenido: requisitos del programa",
            ),
            message("ai", "Respuesta respaldada (manual.pdf, página 4)."),
        ]
    )

    question = "¿Cuáles son los requisitos de Renta Joven?"
    response = run_agent(fake_agent, question, "sesion-a", "modelo-prueba")

    assert fake_agent.config == {"configurable": {"thread_id": "sesion-a"}}
    assert fake_agent.payload == {"messages": [{"role": "user", "content": question}]}
    assert "Respuesta respaldada." in response.text
    assert "`manual.pdf`, página 4" in response.text
    assert response.model_id == "modelo-prueba"
    assert response.tools == ["consultar_documentos"]
    assert response.latency_seconds >= 0
    assert response.model_invoked is True


def test_run_agent_blocks_pqr_without_invoking_model() -> None:
    fake_agent = FakeAgent([])

    response = run_agent(
        fake_agent,
        "¿Puedes redactar una PQR para el programa Renta Joven?",
        "sesion-pqr",
        "modelo-prueba",
    )

    assert fake_agent.payload is None
    assert response.model_invoked is False
    assert response.tools == []
    assert "no consumió tokens" in response.text


def test_run_agent_hides_answer_without_document_tool() -> None:
    fake_agent = FakeAgent(
        [message("human", "pregunta"), message("ai", "respuesta inventada")]
    )

    response = run_agent(
        fake_agent,
        "¿Cuáles son los requisitos de Renta Joven?",
        "sesion-sin-tool",
        "modelo-prueba",
    )

    assert response.text == UNVERIFIED_RESPONSE


def test_run_agent_replaces_model_citation_with_retrieved_source() -> None:
    fake_agent = FakeAgent(
        [
            message("human", "pregunta"),
            message("ai", tool_calls=[{"name": "consultar_documentos"}]),
            message("tool", "Fuente: manual.pdf, página 4\nContenido: texto"),
            message("ai", "Según otro.pdf, página 99, la respuesta es inventada."),
        ]
    )

    response = run_agent(
        fake_agent,
        "¿Cuáles son los requisitos de Renta Joven?",
        "sesion-cita-falsa",
        "modelo-prueba",
    )

    assert "otro.pdf" not in response.text
    assert "página 99" not in response.text
    assert "manual.pdf" in response.text
    assert "página 4" in response.text


def test_run_agent_appends_retrieved_sources_when_model_omits_citation() -> None:
    fake_agent = FakeAgent(
        [
            message("human", "pregunta"),
            message("ai", tool_calls=[{"name": "consultar_documentos"}]),
            message(
                "tool",
                "Fuente: manual renta joven.pdf, página 27\nContenido: requisitos",
            ),
            message("ai", "Debes cumplir los requisitos indicados por el programa."),
        ]
    )

    response = run_agent(
        fake_agent,
        "¿Qué requisitos debo cumplir para aplicar a Renta Joven?",
        "sesion-sin-formato-cita",
        "modelo-prueba",
    )

    assert "Debes cumplir los requisitos" in response.text
    assert "manual renta joven.pdf" in response.text
    assert "página 27" in response.text
    assert response.text != UNVERIFIED_RESPONSE


def test_run_agent_hides_sensitive_output() -> None:
    fake_agent = FakeAgent(
        [
            message("human", "pregunta"),
            message("ai", tool_calls=[{"name": "consultar_documentos"}]),
            message("tool", "Fuente: manual.pdf, página 4\nContenido: texto"),
            message(
                "ai",
                "OPENROUTER_API_KEY="
                + "sk-or-v1-"
                + "secreto (manual.pdf, página 4).",
            ),
        ]
    )

    response = run_agent(
        fake_agent,
        "¿Cuáles son los requisitos de Renta Joven?",
        "sesion-secreto",
        "modelo-prueba",
    )

    assert response.text == UNVERIFIED_RESPONSE


def test_run_agent_uses_deterministic_message_when_retrieval_is_empty() -> None:
    fake_agent = FakeAgent(
        [
            message("human", "pregunta"),
            message("ai", tool_calls=[{"name": "consultar_documentos"}]),
            message("tool", "No se encontraron documentos relacionados con la pregunta."),
            message("ai", "Creo que la respuesta podría ser inventada."),
        ]
    )

    response = run_agent(
        fake_agent,
        "¿Cuáles son los requisitos de Renta Joven?",
        "sesion-sin-resultados",
        "modelo-prueba",
    )

    assert response.text == NO_DOCUMENT_RESPONSE
