"""Pure tests for SPEC 013 interior_mode (AS-AM14)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.authoring_stages import StageParams  # noqa: E402


def _params(**kw: object) -> StageParams:
    base: dict[str, object] = dict(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=0,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    base.update(kw)
    return StageParams(**base)  # type: ignore[arg-type]


def test_interior_mode_defaults_to_dense_for_backcompat() -> None:
    assert _params().interior_mode == "DENSE"


def test_interior_mode_accepts_simple() -> None:
    assert _params(interior_mode="SIMPLE").interior_mode == "SIMPLE"


def test_stageparams_frozen_equality_includes_interior_mode() -> None:
    assert _params(interior_mode="SIMPLE") != _params(interior_mode="DENSE")
