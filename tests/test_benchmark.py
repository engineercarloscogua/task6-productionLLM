from types import SimpleNamespace

import scripts.benchmark as benchmark
from scripts.benchmark import Sample, execute_request, percentile, summarize


def test_percentile_and_summary_use_only_successful_latencies() -> None:
    samples = [
        Sample(1, 1, True, 1.0, "consultar_documentos", "", ""),
        Sample(1, 2, True, 3.0, "calcular_transporte", "", ""),
        Sample(1, 3, False, 0.5, "", "TimeoutError", "timeout"),
    ]

    result = summarize(samples, "modelo-prueba")["groups"][0]

    assert percentile([1.0, 3.0], 0.5) == 1.0
    assert result["requests"] == 3
    assert result["successes"] == 2
    assert result["failures"] == 1
    assert result["success_rate"] == 0.6667
    assert result["latency_mean_seconds"] == 2.0


def test_percentile_returns_none_without_measurements() -> None:
    assert percentile([], 0.95) is None


def test_execute_request_does_not_count_local_filter_as_success(monkeypatch) -> None:
    monkeypatch.setattr(benchmark, "build_agent", lambda **kwargs: object())
    monkeypatch.setattr(
        benchmark,
        "run_agent",
        lambda *args, **kwargs: SimpleNamespace(
            model_invoked=False,
            latency_seconds=0.01,
            tools=[],
        ),
    )

    sample = execute_request("key", "model", concurrency=1, request=1)

    assert sample.success is False
    assert sample.error_type == "FilteredRequest"


def test_execute_request_requires_document_tool(monkeypatch) -> None:
    monkeypatch.setattr(benchmark, "build_agent", lambda **kwargs: object())
    monkeypatch.setattr(
        benchmark,
        "run_agent",
        lambda *args, **kwargs: SimpleNamespace(
            model_invoked=True,
            latency_seconds=0.02,
            tools=[],
        ),
    )

    sample = execute_request("key", "model", concurrency=1, request=1)

    assert sample.success is False
    assert sample.error_type == "RequiredToolMissing"
