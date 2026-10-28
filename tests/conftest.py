from __future__ import annotations

import pytest

from whats_priced_in import load_example


@pytest.fixture
def synth():
    return load_example("synth")
