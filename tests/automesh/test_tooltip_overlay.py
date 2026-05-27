"""Pure-logic tests for the authoring modal tooltip text resolver (AS-AM9).

The tooltip draw handler itself requires a Blender viewport (GPU + blf) and
cannot be tested headlessly. These tests cover the text-selection logic that
maps (stage, modifier state, mouse location) to an intent string, expressed
as a standalone pure function that mirrors the operator methods.

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
