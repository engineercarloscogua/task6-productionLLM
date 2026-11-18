from src.models import (
    DEFAULT_MODEL_ID,
    ModelOption,
    default_model_index,
    parse_free_tool_models,
)


def test_catalog_keeps_only_free_text_tool_models() -> None:
    payload = {
        "data": [
            {
                "id": "example/good:free",
                "name": "Good model",
                "context_length": 128000,
                "supported_parameters": ["tools", "temperature"],
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": "example/no-tools:free",
                "name": "No tools",
                "supported_parameters": ["temperature"],
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": "example/paid",
                "name": "Paid",
                "supported_parameters": ["tools"],
                "architecture": {"output_modalities": ["text"]},
            },
        ]
    }

    options = parse_free_tool_models(payload)

    assert options == [
        ModelOption.free_router(),
        ModelOption("example/good:free", "Good model", 128000),
    ]


def test_nemotron_is_selected_by_default_when_available() -> None:
    options = [
        ModelOption.free_router(),
        ModelOption(DEFAULT_MODEL_ID, "Nemotron 3.5 Lightning", 1_000_000),
    ]

    assert default_model_index(options) == 1


def test_default_model_falls_back_to_first_catalog_option() -> None:
    assert default_model_index([ModelOption.free_router()]) == 0
