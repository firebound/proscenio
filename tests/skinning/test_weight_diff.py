"""Pure tests for weight diff (SPEC 013.2 paint, T6)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.weight_diff import diff_weights  # noqa: E402


def test_identical_dicts_return_empty_set():
    before = {0: 0.5, 1: 1.0, 2: 0.0}
    after = {0: 0.5, 1: 1.0, 2: 0.0}
    assert diff_weights(before, after) == set()


def test_single_vert_changed_returns_singleton():
    before = {0: 0.5, 1: 1.0}
    after = {0: 0.8, 1: 1.0}
    assert diff_weights(before, after) == {0}


def test_eps_threshold_respected():
    before = {0: 0.5}
    after = {0: 0.5 + 1e-5}  # below default eps=1e-4
    assert diff_weights(before, after) == set()


def test_missing_vert_in_after_counts_as_changed():
    before = {0: 0.7, 1: 1.0}
    after = {1: 1.0}  # vert 0 dropped (weight removed by paint)
    assert diff_weights(before, after) == {0}


def test_negative_eps_raises():
    import pytest

    with pytest.raises(ValueError, match="eps"):
        diff_weights({0: 0.5}, {0: 0.5}, eps=-0.1)
