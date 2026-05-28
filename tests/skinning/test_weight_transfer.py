"""Pure tests for weight transfer KNN (O7)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))


def test_identical_meshes_copy_weights_one_to_one():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    source_positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    source_weights = [{"a": 1.0}, {"a": 0.5, "b": 0.5}, {"b": 1.0}]
    target_positions = list(source_positions)
    out = transfer_weights_by_nearest(source_positions, source_weights, target_positions, max_distance=0.1)
    assert out == source_weights


def test_target_beyond_max_distance_returns_empty_dict():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    out = transfer_weights_by_nearest(
        [(0.0, 0.0, 0.0)], [{"a": 1.0}],
        target_positions=[(10.0, 10.0, 10.0)],
        max_distance=0.5,
    )
    assert out == [{}]


def test_empty_source_returns_empty_weights_for_all_targets():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    out = transfer_weights_by_nearest([], [], [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)], max_distance=1.0)
    assert out == [{}, {}]


def test_negative_max_distance_raises():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    with pytest.raises(ValueError, match="max_distance"):
        transfer_weights_by_nearest([(0.0, 0.0, 0.0)], [{"a": 1.0}], [(0.0, 0.0, 0.0)], max_distance=-1.0)


def test_nearest_wins_when_multiple_in_range():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    source_positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]
    source_weights = [{"left": 1.0}, {"right": 1.0}]
    # Target at 0.4 -> nearest is left (0.0)
    out = transfer_weights_by_nearest(source_positions, source_weights, [(0.4, 0.0, 0.0)], max_distance=2.0)
    assert out == [{"left": 1.0}]
