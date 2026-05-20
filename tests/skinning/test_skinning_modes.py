"""Pure tests for skinning mode dispatcher (SPEC 013.2 bind, D5)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.skinning_modes import bind_weights_for_mode  # noqa: E402


def test_empty_mode_zero_weights_per_vert_per_bone():
    out = bind_weights_for_mode(
        "EMPTY",
        [(0.0, 0.0), (1.0, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A")],
    )
    assert out == {"A": [0.0, 0.0]}


def test_single_nearest_picks_one_bone_per_vert():
    out = bind_weights_for_mode(
        "SINGLE_NEAREST",
        [(0.1, 0.0), (1.9, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A"), ((2.0, 0.0), (2.0, 0.0), "B")],
    )
    assert out["A"] == [1.0, 0.0]
    assert out["B"] == [0.0, 1.0]


def test_single_nearest_tie_breaks_first_bone():
    out = bind_weights_for_mode(
        "SINGLE_NEAREST",
        [(0.5, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A"), ((1.0, 0.0), (1.0, 0.0), "B")],
    )
    assert out["A"] == [1.0]
    assert out["B"] == [0.0]


def test_proximity_normalizes_per_vert():
    out = bind_weights_for_mode(
        "PROXIMITY",
        [(0.5, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A"), ((1.0, 0.0), (1.0, 0.0), "B")],
    )
    assert math.isclose(out["A"][0] + out["B"][0], 1.0)


def test_envelope_inside_radius_full_outside_zero():
    out = bind_weights_for_mode(
        "ENVELOPE",
        [(0.0, 0.0), (5.0, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A")],
        envelope_radii={"A": 1.0},
    )
    assert out["A"] == [1.0, 0.0]


def test_envelope_two_overlapping_bones_split_weight():
    # vert at origin sits inside BOTH bone envelopes (radius 2.0 covers
    # both bones at distance 0 and 1). Per-vert sum must = 1.0 (D5 +
    # SPEC bind-design 119); each bone gets 0.5 (1/N share).
    out = bind_weights_for_mode(
        "ENVELOPE",
        [(0.0, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A"), ((1.0, 0.0), (1.0, 0.0), "B")],
        envelope_radii={"A": 2.0, "B": 2.0},
    )
    assert math.isclose(out["A"][0], 0.5)
    assert math.isclose(out["B"][0], 0.5)


def test_envelope_missing_radius_dict_defaults_zero():
    out = bind_weights_for_mode(
        "ENVELOPE",
        [(0.0, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A")],
        envelope_radii=None,
    )
    assert out["A"] == [0.0]


def test_proximity_orphan_vert_gets_zero_in_all_groups():
    out = bind_weights_for_mode(
        "PROXIMITY",
        [(100.0, 100.0)],
        [((0.0, 0.0), (0.0, 0.0), "A")],
        max_distance=1.0,
    )
    assert out["A"] == [0.0]


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        bind_weights_for_mode(
            "BOGUS",  # type: ignore[arg-type]
            [(0.0, 0.0)],
            [((0.0, 0.0), (0.0, 0.0), "A")],
        )


def test_bone_heat_mode_returns_none():
    # BONE_HEAT is a sentinel; bpy caller delegates to Blender's
    # parent_set ARMATURE_AUTO instead of computing weights here.
    out = bind_weights_for_mode(
        "BONE_HEAT",
        [(0.0, 0.0)],
        [((0.0, 0.0), (0.0, 0.0), "A")],
    )
    assert out is None
