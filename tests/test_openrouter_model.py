import pytest
from langchain_core.messages import HumanMessage

from src.openrouter_model import OpenRouterChatModel, OpenRouterRateLimitError


def test_model_parses_openrouter_tool_call(monkeypatch) -> None:
    model = OpenRouterChatModel(model_name="modelo-prueba", api_key="secreto")
    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "model": "modelo-prueba",
                "choices": [
                    {
                        "finish_reason": "tool_calls",
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "function": {
                                        "name": "calcular_transporte",
                                        "arguments": '{"viajes_por_dia":2,"dias":5,"costo_por_viaje":3000}',
                                    },
                                }
                            ],
                        },
                    }
                ],
            }

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr("src.openrouter_model.requests.post", fake_post)

    result = model.invoke([HumanMessage(content="calcula")])

    assert result.tool_calls[0]["name"] == "calcular_transporte"
    assert result.tool_calls[0]["args"]["dias"] == 5
    assert captured["json"]["messages"][0]["role"] == "user"
    assert captured["headers"]["Authorization"] == "Bearer secreto"


def test_rate_limit_is_user_friendly_and_is_not_retried(monkeypatch) -> None:
    model = OpenRouterChatModel(
        model_name="modelo-prueba",
        api_key="secreto",
        max_retries=2,
    )
    calls = 0

    class Response:
        status_code = 429
        headers = {}

        def json(self) -> dict:
            return {
                "error": {
                    "metadata": {
                        "headers": {"X-RateLimit-Reset": "1795305600000"}
                    }
                }
            }

    def fake_post(*args, **kwargs):
        nonlocal calls
        calls += 1
        return Response()

    monkeypatch.setattr("src.openrouter_model.requests.post", fake_post)

    with pytest.raises(OpenRouterRateLimitError) as captured:
        model._post({"messages": []})

    assert calls == 1
    assert "21/11/2026 a las 19:00" in str(captured.value)
    assert "Cambiar a otro modelo gratuito no evita" in str(captured.value)
