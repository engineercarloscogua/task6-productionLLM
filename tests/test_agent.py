from types import SimpleNamespace

from src.agent import _tool_names, run_agent


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


def test_run_agent_passes_isolated_thread_id() -> None:
    fake_agent = FakeAgent(
        [
            message("human", "hola"),
            message("ai", "respuesta"),
        ]
    )

    response = run_agent(fake_agent, "hola", "sesion-a", "modelo-prueba")

    assert fake_agent.config == {"configurable": {"thread_id": "sesion-a"}}
    assert fake_agent.payload == {"messages": [{"role": "user", "content": "hola"}]}
    assert response.text == "respuesta"
    assert response.model_id == "modelo-prueba"
    assert response.tools == []
    assert response.latency_seconds >= 0
