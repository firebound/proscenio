"""Pure-logic tests for the authoring modal tooltip and overlay color resolvers.

The tooltip and GPU draw handlers require a Blender viewport and cannot be
tested headlessly. These tests cover the pure text-selection and color-selection
logic that maps (stage, modifier state, mouse location) / (kind, context) to
intent strings and RGBA colors, expressed as standalone pure functions that
mirror the operator and overlay module logic.

Run from repo root:
    pytest tests/automesh/test_tooltip_overlay.py
"""

from __future__ import annotations


def resolve_tooltip(
    stage: str,
    *,
    ctrl: bool,
    shift: bool,
    inside: bool,
) -> str:
    """Pure mirror of the operator's tooltip-text resolvers.

    stage: "user_outer" or "user_steiners"
    ctrl / shift: modifier key state
    inside: whether mouse is inside the outer silhouette (USER_OUTER only)
    """
    if stage == "user_steiners":
        if ctrl:
            return "Delete stroke (hover + click)"
        if shift:
            return "Cut stroke"
        return "Fold-line stroke"
    if stage == "user_outer":
        if ctrl:
            return "Delete outer stroke (hover + click)"
        if inside:
            return "Cut silhouette"
        return "Extend outer"
    return ""


# --- Stage 4 (USER_STEINERS) ---


def test_tooltip_stage4_no_modifier():
    assert resolve_tooltip("user_steiners", ctrl=False, shift=False, inside=True) == "Fold-line stroke"


def test_tooltip_stage4_shift():
    assert resolve_tooltip("user_steiners", ctrl=False, shift=True, inside=True) == "Cut stroke"


def test_tooltip_stage4_ctrl():
    assert resolve_tooltip("user_steiners", ctrl=True, shift=False, inside=True) == "Delete stroke (hover + click)"


def test_tooltip_stage4_ctrl_takes_priority_over_shift():
    # Ctrl wins when both are held
    assert resolve_tooltip("user_steiners", ctrl=True, shift=True, inside=False) == "Delete stroke (hover + click)"


# --- Stage 2 (USER_OUTER) ---


def test_tooltip_stage2_inside_no_modifier():
    assert resolve_tooltip("user_outer", ctrl=False, shift=False, inside=True) == "Cut silhouette"


def test_tooltip_stage2_outside_no_modifier():
    assert resolve_tooltip("user_outer", ctrl=False, shift=False, inside=False) == "Extend outer"


def test_tooltip_stage2_ctrl():
    assert resolve_tooltip("user_outer", ctrl=True, shift=False, inside=False) == "Delete outer stroke (hover + click)"


def test_tooltip_stage2_ctrl_inside():
    # Ctrl always shows delete regardless of inside/outside
    assert resolve_tooltip("user_outer", ctrl=True, shift=False, inside=True) == "Delete outer stroke (hover + click)"


# --- Unknown stage ---


def test_tooltip_unknown_stage_returns_empty():
    assert resolve_tooltip("unknown", ctrl=False, shift=False, inside=False) == ""


# ---------------------------------------------------------------------------
# Stroke overlay color resolver (AS-AM9-REV)
# Mirror of authoring_overlay._resolve_stroke_color; tested as pure logic.
# ---------------------------------------------------------------------------

_USER_DOT_COLOR = (1.0, 1.0, 0.2, 0.95)
_STROKE_VERT_COLOR_FOLD = (0.3, 0.7, 1.0, 1.0)
_STROKE_VERT_COLOR_CUT_RIP = (1.0, 0.3, 0.3, 1.0)
_STROKE_VERT_COLOR_CUT_REMOVE = (1.0, 0.6, 0.2, 1.0)


def resolve_stroke_color(
    kind: str,
    stage_context: str,
) -> tuple[float, float, float, float]:
    """Pure mirror of authoring_overlay._resolve_stroke_color."""
    if kind == "point":
        return _USER_DOT_COLOR
    if kind == "cut":
        if stage_context == "outer":
            return _STROKE_VERT_COLOR_CUT_REMOVE
        return _STROKE_VERT_COLOR_CUT_RIP
    return _STROKE_VERT_COLOR_FOLD


def test_overlay_color_for_stage4_cut_is_red():
    """Stage 4 rip-cut strokes must render RED so artists distinguish them from fold-lines."""
    color = resolve_stroke_color("cut", "interior")
    assert color == _STROKE_VERT_COLOR_CUT_RIP, f"Expected RED {_STROKE_VERT_COLOR_CUT_RIP}, got {color}"


def test_overlay_color_for_stage2_cut_is_orange():
    """Stage 2 chunk-remove strokes must render ORANGE so artists distinguish them from rip-cuts."""
    color = resolve_stroke_color("cut", "outer")
    assert color == _STROKE_VERT_COLOR_CUT_REMOVE, f"Expected ORANGE {_STROKE_VERT_COLOR_CUT_REMOVE}, got {color}"


def test_overlay_color_for_fold_stroke_is_blue():
    color = resolve_stroke_color("stroke", "interior")
    assert color == _STROKE_VERT_COLOR_FOLD


def test_overlay_color_for_point_is_yellow():
    color = resolve_stroke_color("point", "interior")
    assert color == _USER_DOT_COLOR
