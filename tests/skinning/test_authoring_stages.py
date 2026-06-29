"""Pure tests for authoring stage dataclasses."""

from __future__ import annotations

from core.skinning.authoring_stages import (
    AuthoringStage,
    StageOutput,
    StageParams,
    default_tool,
    next_tool,
    stage_tools,
    tool_is_pen,
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


def test_stage_tools_per_stage():
    # Spec 070: OUTER is auto-only (no replace-the-trace contour); the silhouette
    # edits are the additive islands + the knife; stages without interaction
    # return an empty tuple.
    assert stage_tools(AuthoringStage.OUTER) == ("auto",)
    assert stage_tools(AuthoringStage.EDIT_OUTLINE) == (
        "add",
        "knife",
        "remove",
        "delete",
    )
    assert stage_tools(AuthoringStage.EDIT_INTERIOR_POINTS) == (
        "point",
        "fold",
        "delete",
    )
    assert stage_tools(AuthoringStage.INNER_LOOPS) == ()
    assert stage_tools(AuthoringStage.PREVIEW_INTERIOR) == ()
    assert stage_tools(AuthoringStage.APPLY) == ()


def test_default_tool_is_first_or_empty():
    assert default_tool(AuthoringStage.OUTER) == "auto"
    assert default_tool(AuthoringStage.EDIT_OUTLINE) == "add"
    assert default_tool(AuthoringStage.EDIT_INTERIOR_POINTS) == "point"
    assert default_tool(AuthoringStage.APPLY) == ""


def test_next_tool_cycles_and_wraps():
    assert (
        next_tool(AuthoringStage.OUTER, "auto") == "auto"
    )  # single tool wraps to itself
    assert next_tool(AuthoringStage.EDIT_INTERIOR_POINTS, "point") == "fold"
    assert next_tool(AuthoringStage.EDIT_INTERIOR_POINTS, "fold") == "delete"
    assert next_tool(AuthoringStage.EDIT_INTERIOR_POINTS, "delete") == "point"  # wrap
    assert next_tool(AuthoringStage.EDIT_OUTLINE, "add") == "knife"
    assert next_tool(AuthoringStage.EDIT_OUTLINE, "knife") == "remove"
    assert next_tool(AuthoringStage.EDIT_OUTLINE, "remove") == "delete"
    assert next_tool(AuthoringStage.EDIT_OUTLINE, "delete") == "add"  # wrap


def test_next_tool_no_tools_keeps_current():
    # A stage with no interactive tools leaves the tool unchanged.
    assert next_tool(AuthoringStage.APPLY, "anything") == "anything"


def test_next_tool_stale_tool_resets_to_first():
    # A tool not in the stage (e.g. left over from a previous stage) resets to
    # the stage's first tool rather than raising.
    assert next_tool(AuthoringStage.EDIT_OUTLINE, "fold") == "add"


def test_tool_is_pen_classification():
    # Open-stroke pens use the click/free-draw machine; islands + singles do not.
    for pen in ("knife", "fold"):
        assert tool_is_pen(pen) is True
    for non_pen in ("auto", "point", "add", "remove", "delete", ""):
        assert tool_is_pen(non_pen) is False


def test_tool_is_island_classification():
    from core.skinning.authoring_stages import tool_is_island  # type: ignore[import-not-found]

    for island in ("add", "remove"):
        assert tool_is_island(island) is True
    for non_island in ("auto", "knife", "fold", "point", "delete", ""):
        assert tool_is_island(non_island) is False
