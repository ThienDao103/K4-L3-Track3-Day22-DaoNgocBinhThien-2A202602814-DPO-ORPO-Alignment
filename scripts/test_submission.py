"""Check the student's loss and detect invalid or stale Colab evidence."""
import ast
import copy
import json
import math
from pathlib import Path

import pytest
import torch

from submission_evidence import validate_run

ROOT = Path(__file__).resolve().parent.parent


def test_student_loss_matches_formula_and_initialization():
    source = ast.parse((ROOT / "notebooks/00_dpo_loss_from_scratch.py").read_text(encoding="utf-8"))
    node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "my_dpo_loss")
    namespace = {"torch": torch}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "my_dpo_loss", "exec"), namespace)
    loss = namespace["my_dpo_loss"]
    pc, pr = torch.tensor([-12., -30.]), torch.tensor([-15., -28.])
    rc, rr = torch.tensor([-13., -29.]), torch.tensor([-14., -29.])
    for beta in (0.05, 0.1, 0.5):
        expected = torch.logaddexp(torch.zeros_like(pc), -beta * ((pc-pr)-(rc-rr))).mean()
        assert torch.allclose(loss(pc, pr, rc, rr, beta), expected, atol=1e-6)
        assert loss(pc, pr, pc, pr, beta).item() == pytest.approx(math.log(2), abs=1e-6)


@pytest.fixture
def run():
    return json.loads((ROOT / "colab/Lab22_DPO_T4_executed.ipynb").read_text(encoding="utf-8"))


def test_exported_run_is_complete_and_matches_saved_metrics(run):
    assert validate_run(ROOT, run) == []


@pytest.mark.parametrize("change", ["unexecuted", "error", "source", "metrics"])
def test_exported_run_rejects_invalid_evidence(run, change):
    run = copy.deepcopy(run)
    cell = next(c for c in run["cells"] if c["cell_type"] == "code")
    if change == "unexecuted":
        cell["execution_count"] = None
    elif change == "error":
        cell["outputs"] = [{"output_type": "error", "ename": "RuntimeError", "evalue": "failed"}]
    elif change == "source":
        cell["source"] = ["print('different configuration')"]
    else:
        cell = next(c for c in run["cells"] if "metrics = {" in "".join(c["source"]))
        cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": ['{"diagnosis":"FAILURE"}']}]
    assert validate_run(ROOT, run)
