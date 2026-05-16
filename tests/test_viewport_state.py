"""Unit tests for SPEC 012.1 viewport-state helpers.

bpy-free. Verifies the Front-Orthographic detection used by
``operators/quick_armature.py`` to decide whether to call
``view3d.view_axis(type="FRONT")``.

Run from the repo root:

    pytest tests/test_viewport_state.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.viewport_state import is_front_ortho  # noqa: E402  - sys.path setup above


_IDENTITY = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
]

_FRONT_ORTHO_ROTATED = [
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0],
]


def test_perspective_never_qualifies() -> None:
    assert is_front_ortho("PERSP", _IDENTITY) is False


def test_camera_view_never_qualifies() -> None:
    assert is_front_ortho("CAMERA", _IDENTITY) is False


def test_identity_ortho_is_front() -> None:
    assert is_front_ortho("ORTHO", _IDENTITY) is True


def test_rotated_ortho_is_not_front() -> None:
    assert is_front_ortho("ORTHO", _FRONT_ORTHO_ROTATED) is False


def test_tiny_jitter_under_tolerance_still_counts_as_front() -> None:
    jittered = [
        [1.0 + 1e-6, 1e-6, 0.0],
        [-1e-6, 1.0, 1e-6],
        [0.0, -1e-6, 1.0],
    ]
    assert is_front_ortho("ORTHO", jittered) is True


def test_above_tolerance_does_not_count_as_front() -> None:
    drifted = [
        [1.0, 0.01, 0.0],
        [-0.01, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    assert is_front_ortho("ORTHO", drifted, tolerance=1e-4) is False


def test_short_matrix_returns_false() -> None:
    assert is_front_ortho("ORTHO", [[1.0, 0.0, 0.0]]) is False
    assert is_front_ortho("ORTHO", [[1.0], [0.0], [0.0]]) is False
