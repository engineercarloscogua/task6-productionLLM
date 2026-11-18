from __future__ import annotations

import json
import ssl  # Keep the standard TLS runtime loaded before optional native packages.
from time import sleep
from typing import Any, Sequence

import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import Field, SecretStr


OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterChatModel(BaseChatModel):
    """Minimal LangChain chat model for OpenRouter's OpenAI-compatible REST API."""

    model_name: str
    api_key: SecretStr = Field(exclude=True)
    temperature: float = 0
    timeout_seconds: float = 60
    max_retries: int = 2

    @property
    def _llm_type(self) -> str:
        return "openrouter-rest"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model": self.model_name, "temperature": self.temperature}

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | BaseTool],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> Any:
        formatted = [convert_to_openai_tool(tool) for tool in tools]
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        return self.bind(tools=formatted, **kwargs)

    @staticmethod
    def _message_payload(message: BaseMessage) -> dict[str, Any]:
        role_by_type = {
            "system": "system",
            "human": "user",
            "ai": "assistant",
            "tool": "tool",
        }
        payload: dict[str, Any] = {
            "role": role_by_type.get(message.type, message.type),
            "content": message.content,
        }
        if isinstance(message, AIMessage) and message.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call["args"], ensure_ascii=False),
                    },
                }
                for call in message.tool_calls
            ]
        if isinstance(message, ToolMessage):
            payload["tool_call_id"] = message.tool_call_id
        return payload

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/carloscogua/task6-productionLLM",
            "X-Title": "Asistente universitario Actividad 6",
        }
        for attempt in range(self.max_retries + 1):
            response = requests.post(
                OPENROUTER_CHAT_URL,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            if response.status_code != 429 and response.status_code < 500:
                response.raise_for_status()
                return response.json()
            if attempt == self.max_retries:
                response.raise_for_status()
            sleep(0.5 * (2**attempt))
        raise RuntimeError("OpenRouter no devolvió una respuesta.")

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": [self._message_payload(message) for message in messages],
            "temperature": self.temperature,
        }
        if stop:
            payload["stop"] = stop
        for name in ("tools", "tool_choice", "parallel_tool_calls", "response_format"):
            if name in kwargs and kwargs[name] is not None:
                payload[name] = kwargs[name]

        data = self._post(payload)
        returned = data["choices"][0]["message"]
        tool_calls = []
        for call in returned.get("tool_calls") or []:
            arguments = call["function"].get("arguments") or "{}"
            try:
                parsed_arguments = json.loads(arguments)
            except json.JSONDecodeError:
                parsed_arguments = {"entrada": arguments}
            tool_calls.append(
                {
                    "name": call["function"]["name"],
                    "args": parsed_arguments,
                    "id": call.get("id") or "tool-call",
                    "type": "tool_call",
                }
            )
        message = AIMessage(
            content=returned.get("content") or "",
            tool_calls=tool_calls,
            response_metadata={
                "model": data.get("model", self.model_name),
                "finish_reason": data["choices"][0].get("finish_reason"),
            },
        )
        return ChatResult(generations=[ChatGeneration(message=message)])
