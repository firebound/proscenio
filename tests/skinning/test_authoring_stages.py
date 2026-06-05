"""Pure tests for authoring stage dataclasses."""

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
    assert AuthoringStage.EDIT_OUTLINE == 1
    assert AuthoringStage.INNER_LOOPS == 2
    assert AuthoringStage.EDIT_INTERIOR_POINTS == 3
    assert AuthoringStage.PREVIEW_INTERIOR == 4
    assert AuthoringStage.APPLY == 5


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


def test_authoring_stage_has_six_values_in_workflow_order():
    assert AuthoringStage.OUTER < AuthoringStage.EDIT_OUTLINE
    assert AuthoringStage.EDIT_OUTLINE < AuthoringStage.INNER_LOOPS
    assert AuthoringStage.INNER_LOOPS < AuthoringStage.EDIT_INTERIOR_POINTS
    assert AuthoringStage.EDIT_INTERIOR_POINTS < AuthoringStage.PREVIEW_INTERIOR
    assert AuthoringStage.PREVIEW_INTERIOR < AuthoringStage.APPLY
    assert len(list(AuthoringStage)) == 6


def test_stage_output_has_user_outer_strokes_field():
    out = StageOutput()
    assert out.user_outer_strokes == []
