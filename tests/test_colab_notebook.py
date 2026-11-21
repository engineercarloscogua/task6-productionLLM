from __future__ import annotations

import json
from pathlib import Path


NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "Actividad6_Entrega_Colab.ipynb"
)


def _notebook() -> dict:
    return json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))


def test_python_cells_compile() -> None:
    for index, cell in enumerate(_notebook()["cells"]):
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") != "code" or source.lstrip().startswith(("!", "%")):
            continue
        compile(source, f"cell-{index}", "exec")


def test_notebook_protects_free_openrouter_quota() -> None:
    notebook_source = "\n".join(
        "".join(cell.get("source", [])) for cell in _notebook()["cells"]
    )

    assert "OpenRouterRateLimitError" in notebook_source
    assert "response.status_code == 429" in notebook_source
    assert "max_retries=0" in notebook_source
    assert "RUN_LANGCHAIN_DEMOS = False" in notebook_source
    assert "display(Markdown" in notebook_source
