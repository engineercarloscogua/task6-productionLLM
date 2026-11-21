from __future__ import annotations

import ssl  # Load Python's TLS runtime before native numerical dependencies on Windows.
from dataclasses import dataclass
from typing import Any

from src.tls import configure_system_trust_store


configure_system_trust_store()

import requests


OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_MODEL_ID = "nvidia/nemotron-3.5-lightning:free"


@dataclass(frozen=True, slots=True)
class ModelOption:
    """A model that can be safely offered to the agent interface."""

    id: str
    name: str
    context_length: int | None

    @classmethod
    def free_router(cls) -> "ModelOption":
        return cls(
            id="openrouter/free",
            name="OpenRouter Free Router",
            context_length=None,
        )


def _is_free_variant(model: dict[str, Any]) -> bool:
    """Only accept explicit free variants that do not require account credits."""
    return str(model.get("id", "")).endswith(":free")


def _supports_text_and_tools(model: dict[str, Any]) -> bool:
    parameters = set(model.get("supported_parameters") or [])
    architecture = model.get("architecture") or {}
    output_modalities = set(architecture.get("output_modalities") or ["text"])
    return "tools" in parameters and "text" in output_modalities


def parse_free_tool_models(payload: dict[str, Any]) -> list[ModelOption]:
    """Parse OpenRouter's catalog into stable UI options."""
    options = []
    for model in payload.get("data") or []:
        if not _is_free_variant(model) or not _supports_text_and_tools(model):
            continue
        options.append(
            ModelOption(
                id=str(model["id"]),
                name=str(model.get("name") or model["id"]),
                context_length=model.get("context_length"),
            )
        )

    options.sort(key=lambda item: item.name.casefold())
    return [ModelOption.free_router(), *options]


def fetch_free_tool_models() -> list[ModelOption]:
    """Fetch free, text-output, tool-capable models from OpenRouter."""
    response = requests.get(
        OPENROUTER_MODELS_URL,
        params={"output_modalities": "text", "sort": "most-popular"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return parse_free_tool_models(response.json())


def default_model_index(options: list[ModelOption]) -> int:
    """Return the preferred model position, with a safe catalog fallback."""
    return next(
        (index for index, option in enumerate(options) if option.id == DEFAULT_MODEL_ID),
        0,
    )
