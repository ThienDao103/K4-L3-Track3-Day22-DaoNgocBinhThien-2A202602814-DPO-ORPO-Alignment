"""Recover tabular training logs and render the eight actual NB4 examples.

No training, network access, generated answers, or changes to raw metrics.
Run after importing the Colab results: python scripts/report_results.py
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import textwrap
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.rows = []
        self.row = []
        self.text = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.rows = []
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.text = []

    def handle_data(self, data):
        if self.text is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.text is not None:
            self.row.append("".join(self.text).strip())
            self.text = None
        elif tag == "tr":
            self.rows.append(self.row)
        elif tag == "table":
            self.tables.append(self.rows)


def logs(cell):
    tables = Tables()
    for out in cell.get("outputs", []):
        tables.feed("".join(out.get("data", {}).get("text/html", [])))
    rows = tables.tables[0]
    return [{k: float(v) for k, v in zip(rows[0], row)} for row in rows[1:]]


def main():
    path = ROOT / "colab/Lab22_DPO_T4_executed.ipynb"
    nb = json.loads(path.read_text(encoding="utf-8"))
    training = [c for c in nb["cells"] if "result = trainer.train()" in "".join(c["source"])]
    history = {"sft": logs(training[0]), "dpo_heldout": logs(training[1])}
    (ROOT / "data/eval/training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    text = "\n".join("".join(o.get("text", [])) for c in nb["cells"] for o in c.get("outputs", []))
    html = "\n".join("".join(o.get("data", {}).get("text/html", [])) for c in training for o in c.get("outputs", []))
    records = [json.loads(line) for line in (ROOT / "data/eval/side_by_side.jsonl").read_text(encoding="utf-8").splitlines()]
    run = {
        "executed_notebook": str(path.relative_to(ROOT)).replace("\\", "/"),
        "executed_notebook_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "gpu": "Tesla T4",
        "gpu_memory_reported_gb": float(re.search(r"Max memory: ([\d.]+) GB", text).group(1)),
        "peak_vram": None,
        "peak_vram_note": "Not measured in the original run; GPU capacity is not peak allocation.",
        "training_progress_elapsed": re.findall(r"\[(?:125/125|100/100) ([\d:]+), Epoch", html),
        "elapsed_note": "Progress display: SFT then DPO; excludes setup, reference precomputation and NB4.",
        "sft_average_train_loss": float(re.search(r"Final SFT loss: ([\d.]+)", text).group(1)),
        "exact_identical_answers": sum(r["sft"] == r["dpo"] for r in records),
        "total_prompts": len(records),
        "answers_with_tool_call_tags": {key: sum("tool_call>" in r[key] for r in records) for key in ("sft", "dpo")},
    }
    (ROOT / "submission/run_summary.json").write_text(json.dumps(run, indent=2), encoding="utf-8")

    verdicts = json.loads((ROOT / "data/eval/judge_results_rm.json").read_text(encoding="utf-8"))
    by_id = {r["id"]: r["winner"] for r in verdicts["records"]}
    fixed = [r for r in records if r["category"] != "heldout"]
    md = ["# NB4 — Tám câu hỏi cố định", "", "Nguồn: `data/eval/side_by_side.jsonl`; giữ nguyên câu trả lời và các thẻ tool_call.", ""]
    for r in fixed:
        md.extend([f"## {r['id']} — {r['category']} — {by_id[r['id']]}", "", r["prompt"], "", "### SFT", "", "```text", r["sft"], "```", "", "### SFT+DPO", "", "```text", r["dpo"], "```", ""])
    (ROOT / "submission/SIDE_BY_SIDE.md").write_text("\n".join(md), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cells = []
    heights = []
    for r in fixed:
        row = [r["id"] + "\n" + by_id[r["id"]], textwrap.fill(r["prompt"], 32), textwrap.fill(r["sft"], 80), textwrap.fill(r["dpo"], 80)]
        cells.append(row)
        heights.append(max(v.count("\n") + 1 for v in row) * 0.25 + 0.40)
    total_height = sum(heights) + 0.8
    fig, ax = plt.subplots(figsize=(22, total_height))
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=["ID / verdict", "Prompt", "SFT", "SFT+DPO"], cellLoc="left", colWidths=[0.05, 0.15, 0.40, 0.40], bbox=[0, 0, 1, 0.96])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (i, j), cell in table.get_celld().items():
        cell.set_height((0.35 if i == 0 else heights[i - 1]) / total_height)
        if i == 0:
            cell.set_facecolor("#2e548a")
            cell.set_text_props(color="white", weight="bold")
        elif i % 2 == 0:
            cell.set_facecolor("#f1f5fa")
    ax.set_title("NB4: 8 fixed prompts — complete original answers — retained judge: Llama 3.2 3B", fontsize=14, pad=12)
    target = ROOT / "submission/screenshots/04-side-by-side-table.png"
    original = target.with_name("04-side-by-side-table-colab.png")
    if not original.exists():
        shutil.copyfile(target, original)
    fig.savefig(target, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print("Recovered training tables; saved run summary and complete eight-prompt comparison.")


if __name__ == "__main__":
    main()
