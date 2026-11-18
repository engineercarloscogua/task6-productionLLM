from src.models import ModelOption, parse_free_tool_models


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
