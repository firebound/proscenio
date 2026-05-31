"""Pure tests for planar proximity weight computation (the bind work)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.planar_proximity import compute_proximity_weights  # noqa: E402


def test_two_equidistant_bones_get_equal_weight():
    out = compute_proximity_weights(
        (0.5, 0.0),
        [((0.0, 0.0), (0.0, 0.0), "A"), ((1.0, 0.0), (1.0, 0.0), "B")],
    )
    assert set(out.keys()) == {"A", "B"}
    assert math.isclose(out["A"], 0.5)
    assert math.isclose(out["B"], 0.5)


def test_closer_bone_gets_higher_weight_inverse_square():
    out = compute_proximity_weights(
        (0.0, 0.0),
        [((1.0, 0.0), (1.0, 0.0), "A"), ((2.0, 0.0), (2.0, 0.0), "B")],
        falloff_power=2.0,
    )
    assert math.isclose(out["A"], 0.8)
    assert math.isclose(out["B"], 0.2)


def test_falloff_power_one_is_inverse_linear():
    out = compute_proximity_weights(
        (0.0, 0.0),
        [((1.0, 0.0), (1.0, 0.0), "A"), ((2.0, 0.0), (2.0, 0.0), "B")],
        falloff_power=1.0,
    )
    assert math.isclose(out["A"], 2.0 / 3.0)
    assert math.isclose(out["B"], 1.0 / 3.0)


def test_bone_beyond_max_distance_filtered():
    out = compute_proximity_weights(
        (0.0, 0.0),
        [((100.0, 0.0), (100.0, 0.0), "far")],
        max_distance=1.0,
    )
    assert out == {}


def test_vert_on_bone_gets_full_weight():
    out = compute_proximity_weights(
        (0.0, 0.0),
        [((0.0, 0.0), (1.0, 0.0), "on"), ((10.0, 0.0), (10.0, 0.0), "far")],
    )
    assert math.isclose(out["on"], 1.0, abs_tol=1e-3)
    assert out["far"] < 1e-3


def test_max_distance_partial_filter():
    out = compute_proximity_weights(
        (0.0, 0.0),
        [
            ((0.5, 0.0), (0.5, 0.0), "near"),
            ((5.0, 0.0), (5.0, 0.0), "far"),
        ],
        max_distance=1.0,
    )
    assert set(out.keys()) == {"near"}
    assert math.isclose(out["near"], 1.0)
