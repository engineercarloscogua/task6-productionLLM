from __future__ import annotations

import ssl  # Initialize Python TLS before LangChain loads native dependencies on Windows.
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from src.openrouter_model import OpenRouterChatModel
from src.tools import TOOLS


SYSTEM_PROMPT = """Eres un asistente documental universitario.
Para responder sobre el contenido de los PDF debes usar consultar_documentos.
Si la herramienta no encuentra el dato, indica claramente que no está disponible.
Nunca inventes plazos, teléfonos, requisitos, políticas ni fuentes.
Para presupuestos usa calcular_transporte con los números dados por el usuario.
Una pregunta combinada puede requerir ambas herramientas.
Responde de forma breve y clara en español, y cita siempre el archivo y la página.
Aclara que la respuesta se genera a partir de los documentos cargados y que debe
verificarse contra el PDF original cuando la decisión sea importante.
"""


@dataclass(frozen=True, slots=True)
class AgentResponse:
    text: str
    tools: list[str]
    latency_seconds: float
    model_id: str


def build_agent(api_key: str, model_id: str) -> Any:
    """Create an OpenRouter-backed LangChain agent with short-term memory."""
    if not api_key.strip():
        raise ValueError("OPENROUTER_API_KEY es obligatoria.")
    model = OpenRouterChatModel(
        model_name=model_id,
        api_key=api_key,
        temperature=0,
        max_retries=2,
        timeout_seconds=60,
    )
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def _tool_names(messages: list[Any]) -> list[str]:
    """Return tools requested after the most recent user message only."""
    start = max(
        (
            index
            for index, message in enumerate(messages)
            if getattr(message, "type", None) in {"human", "user"}
            or getattr(message, "role", None) == "user"
        ),
        default=-1,
    )
    names: list[str] = []
    for message in messages[start + 1 :]:
        for call in getattr(message, "tool_calls", None) or []:
            name = call.get("name")
            if name and name not in names:
                names.append(name)
    return names


def _message_text(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        return "\n".join(part for part in parts if part)
    return str(content)


def run_agent(agent: Any, message: str, thread_id: str, model_id: str) -> AgentResponse:
    """Invoke the agent and return observability data for the UI."""
    started = perf_counter()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    latency = perf_counter() - started
    messages = result["messages"]
    return AgentResponse(
        text=_message_text(messages[-1]),
        tools=_tool_names(messages),
        latency_seconds=latency,
        model_id=model_id,
    )
