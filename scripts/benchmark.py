from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from time import perf_counter
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import build_agent, run_agent


PROMPTS = [
    "¿Cuál es el tema principal de los documentos cargados?",
    "¿Qué requisitos se mencionan en los documentos?",
    "¿Qué fechas o plazos importantes aparecen?",
    "¿Qué apoyos de transporte aparecen en los documentos y cuáles son sus requisitos?",
    "Resume las conclusiones principales e indica archivo y página.",
]


@dataclass(frozen=True, slots=True)
class Sample:
    concurrency: int
    request: int
    success: bool
    latency_seconds: float
    tools: str
    error_type: str
    error_message: str


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def execute_request(api_key: str, model_id: str, concurrency: int, request: int) -> Sample:
    prompt = PROMPTS[(request - 1) % len(PROMPTS)]
    started = perf_counter()
    try:
        agent = build_agent(api_key=api_key, model_id=model_id)
        response = run_agent(agent, prompt, str(uuid4()), model_id)
    except Exception as error:  # The benchmark must record provider failures verbatim.
        return Sample(
            concurrency=concurrency,
            request=request,
            success=False,
            latency_seconds=perf_counter() - started,
            tools="",
            error_type=type(error).__name__,
            error_message=str(error)[:500],
        )
    return Sample(
        concurrency=concurrency,
        request=request,
        success=True,
        latency_seconds=response.latency_seconds,
        tools=",".join(response.tools),
        error_type="",
        error_message="",
    )


def summarize(samples: list[Sample], model_id: str) -> dict:
    groups = []
    for concurrency in sorted({sample.concurrency for sample in samples}):
        selected = [sample for sample in samples if sample.concurrency == concurrency]
        successful = [sample.latency_seconds for sample in selected if sample.success]
        groups.append(
            {
                "concurrency": concurrency,
                "requests": len(selected),
                "successes": sum(sample.success for sample in selected),
                "failures": sum(not sample.success for sample in selected),
                "success_rate": round(sum(sample.success for sample in selected) / len(selected), 4),
                "latency_mean_seconds": round(mean(successful), 3) if successful else None,
                "latency_p50_seconds": round(percentile(successful, 0.50), 3) if successful else None,
                "latency_p95_seconds": round(percentile(successful, 0.95), 3) if successful else None,
            }
        )
    return {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model_id,
        "note": "Medición real contra OpenRouter; no extrapolar como garantía de escalabilidad.",
        "groups": groups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark controlado del agente en OpenRouter")
    parser.add_argument("--model", default=os.getenv("OPENROUTER_MODEL", "openrouter/free"))
    parser.add_argument("--concurrency", nargs="+", type=int, default=[1, 2, 5])
    parser.add_argument("--requests-per-level", type=int, default=5)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        parser.error("Define OPENROUTER_API_KEY en el entorno; la clave no se acepta por argumento.")
    if args.requests_per_level < 1 or any(level < 1 for level in args.concurrency):
        parser.error("La concurrencia y el número de solicitudes deben ser positivos.")

    samples: list[Sample] = []
    for level in args.concurrency:
        with ThreadPoolExecutor(max_workers=level) as executor:
            futures = [
                executor.submit(execute_request, api_key, args.model, level, request)
                for request in range(1, args.requests_per_level + 1)
            ]
            samples.extend(future.result() for future in as_completed(futures))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "benchmark_samples.csv"
    json_path = args.output_dir / "benchmark_summary.json"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(asdict(samples[0])))
        writer.writeheader()
        writer.writerows(asdict(sample) for sample in samples)
    json_path.write_text(
        json.dumps(summarize(samples, args.model), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Muestras: {csv_path}")
    print(f"Resumen: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
