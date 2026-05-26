"""Pure tests for authoring stage dataclasses (SPEC 013.2 interactive-modal, T12)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.authoring_stages import (  # noqa: E402
    AuthoringStage,
    StageOutput,
    StageParams,
)


def test_authoring_stage_enum_order():
    assert AuthoringStage.OUTER == 0
    assert AuthoringStage.INNER_LOOPS == 1
    assert AuthoringStage.USER_STEINERS == 2
    assert AuthoringStage.STEINER_PREVIEW == 3
    assert AuthoringStage.APPLY == 4


def test_stage_params_frozen_equality():
    a = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=2,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    b = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=2,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    assert a == b

    import pytest

    with pytest.raises(AttributeError):
        a.resolution = 0.5


def test_stage_output_defaults_empty_lists():
    out = StageOutput()
    assert out.outer == []
    assert out.inner_loops == []
    assert out.user_steiners == []
    assert out.all_steiners == []
