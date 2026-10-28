"""The README and the golden file stay tied to the engine."""

from __future__ import annotations

from check import run_checks


def test_readme_and_golden_do_not_drift():
    failures = run_checks()
    assert not failures, "\n".join(failures)
