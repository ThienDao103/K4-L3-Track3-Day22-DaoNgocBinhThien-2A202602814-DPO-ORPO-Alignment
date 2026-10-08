"""Validate an exported Colab run without requiring ignored model weights."""
from __future__ import annotations

import json
from pathlib import Path

from build_colab import render


def output_text(cell: dict) -> str:
    return "".join("".join(o.get("text", [])) for o in cell.get("outputs", []))


def validate_run(repo: Path, notebook: dict) -> list[str]:
    problems = []
    expected = [c for c in render("T4")["cells"] if c["cell_type"] == "code"]
    actual = [c for c in notebook.get("cells", []) if c.get("cell_type") == "code"]
    if len(actual) < len(expected):
        return ["RUN: executed Colab notebook is missing core code cells"]
    for i, (want, got) in enumerate(zip(expected, actual), 1):
        if "".join(want["source"]) != "".join(got.get("source", [])):
            problems.append(f"RUN: code cell {i} differs from the reproducible T4 source")
        if got.get("execution_count") is None:
            problems.append(f"RUN: core code cell {i} was not executed")
        if any(o.get("output_type") == "error" for o in got.get("outputs", [])):
            problems.append(f"RUN: core code cell {i} contains an error")
    all_text = "\n".join(output_text(c) for c in actual[:len(expected)])
    for marker in (
        "✓ Khớp tham chiếu:", "loss at init = 0.6931",
        "Saved merged 16-bit → /content/lab22/models/sft-merged",
        "train=800  eval=100  (no prompt overlap)", "=== Cặp 3 ===",
        "precompute_ref=True", "8 fixed + 50 held-out prompts",
    ):
        if marker not in all_text:
            problems.append(f"RUN: missing recorded evidence: {marker}")
    for fragment, path in (
        ("metrics = {", repo / "adapters/dpo/dpo_metrics.json"),
        ("summary = {", repo / "data/eval/judge_summary.json"),
    ):
        matches = [c for c in actual if fragment in "".join(c.get("source", []))]
        try:
            text = output_text(matches[0])
            recorded = json.loads(text[text.index("{"):].strip())
            saved = json.loads(path.read_text(encoding="utf-8"))
            if recorded != saved:
                problems.append(f"RUN: {path.name} differs from the recorded Colab output")
        except (IndexError, OSError, ValueError):
            problems.append(f"RUN: cannot verify recorded {path.name}")
    return problems


def check_exported_run(repo: Path, problems: list[str]) -> bool:
    path = repo / "colab/Lab22_DPO_T4_executed.ipynb"
    if not path.exists():
        return False
    try:
        errors = validate_run(repo, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors = [f"RUN: invalid executed notebook: {exc}"]
    problems.extend(errors)
    return not errors
