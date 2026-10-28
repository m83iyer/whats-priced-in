import difflib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = (ROOT / "docs" / "LAUNCH_RECEIPTS.md").read_text()
PATTERN = re.compile(r"```bash\n(.*?)\n```\n\n```text\n(.*?)\n```", re.S)


def _run(command):
    argv = command.replace("python -m", f"{sys.executable} -m", 1).split()
    completed = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
    return completed


def test_svg_cards_match_the_receipts():
    from whats_priced_in.api import solve_growth
    from whats_priced_in.assumptions import load_assumptions, load_example
    from whats_priced_in.card import svg_for
    from whats_priced_in.earnings_assumption_diff import diff_assumptions

    blocks = re.findall(r"```xml\n(.*?)```", RECEIPTS, re.S)
    growth = solve_growth(load_example("synth"))
    diff = diff_assumptions(
        load_assumptions(ROOT / "examples/diff/pre.yaml"),
        load_assumptions(ROOT / "examples/diff/post.yaml"),
    )
    assert svg_for(growth).strip() == blocks[0].strip()
    assert svg_for(diff).strip() == blocks[1].strip()


def test_receipt_transcripts():
    blocks = PATTERN.findall(RECEIPTS)
    assert len(blocks) >= 16
    for command, expected in blocks:
        completed = _run(command)
        actual = completed.stdout.rstrip("\n")
        assert completed.returncode == 0, completed.stderr
        if actual.startswith("{") and expected.startswith("{"):
            _compare_json(command, expected, actual)
        else:
            if actual != expected:
                diff = "\n".join(
                    difflib.unified_diff(
                        expected.splitlines(),
                        actual.splitlines(),
                        fromfile="receipt",
                        tofile="actual",
                        lineterm="",
                    )
                )
                raise AssertionError(f"{command}\n{diff}")


def _compare_json(command, expected, actual):
    left = json.loads(expected)
    right = json.loads(actual)
    _walk(command, left, right)


def _walk(where, left, right):
    if isinstance(left, dict):
        assert isinstance(right, dict), where
        assert set(left) == set(right), f"{where} keys {set(left) ^ set(right)}"
        for key in left:
            _walk(f"{where}.{key}", left[key], right[key])
        return
    if isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right), where
        for index, (item, other) in enumerate(zip(left, right)):
            _walk(f"{where}[{index}]", item, other)
        return
    if isinstance(left, float):
        assert isinstance(right, (int, float)), where
        assert math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-8), f"{where}: {left} vs {right}"
        return
    assert left == right, f"{where}: {left!r} vs {right!r}"
