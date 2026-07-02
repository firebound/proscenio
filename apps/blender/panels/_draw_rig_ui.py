"""Rig UI swatch/theme rendering for the Skeleton Rig UI subpanel.

The per-row eye and the three-column theme selector (dot | number | picker),
pulled out of ``skeleton.py`` so the panel module keeps just the panel
definitions. Alignment across rows is the whole point - see :func:`draw_swatch`.
"""

from __future__ import annotations

import bpy

from ..core.bpy_helpers._shared.bone_collections import (  # type: ignore[import-not-found]
    collection_theme_label,
)

# Rig UI rows are a fixed eye, a flexible middle the select button(s) split
# equally, and a theme selector of three fixed columns (dot | number | picker).
# Alignment across rows is the constraint: ``ui_units_x`` is only a *minimum*, so
# it cannot cap a wider widget - the columns line up only because every row draws
# the IDENTICAL widget in each slot (see draw_swatch). No color field: it (and a
# text button) stretches and grabs the row's spare width on a wide panel. All
# GUI-tunable.
_RIG_UI_EYE_UNITS = 1.4
_RIG_UI_DOT_UNITS = 0.9
_RIG_UI_NUM_UNITS = 1.2
_RIG_UI_PICK_UNITS = 1.4
# Neutral fill for the dot on a row with no shared theme (an "empty" circle).
# Drawing a socket on every row - never a label - keeps the dot column one width,
# so the theme selector lines up and the middle buttons stay aligned. GUI-tunable.
_RIG_UI_NO_THEME_DOT = (0.18, 0.18, 0.18)


def _theme_bone_color_set(theme_label: str) -> bpy.types.ThemeBoneColorSet | None:
    """The theme's bone color set for a ``"1"``..``"15"`` theme label, or None.

    ``THEME0N`` maps to ``bone_color_sets[N - 1]`` on the active theme; the set's
    ``normal`` color is what the Rig UI swatch draws as a fixed colored dot. Any
    gap - empty label, no themes, out-of-range - is a clean None.
    """
    if not theme_label:
        return None
    try:
        idx = int(theme_label) - 1
    except ValueError:
        return None
    themes = getattr(bpy.context.preferences, "themes", None)
    sets = themes[0].bone_color_sets if themes else None
    if sets is None or not (0 <= idx < len(sets)):
        return None
    return sets[idx]


def draw_eye(row: bpy.types.UILayout, collection: bpy.types.BoneCollection | None) -> None:
    if collection is None:
        # The view row named a collection the data no longer has; keep the
        # column width with a disabled placeholder so the row still aligns.
        sub = row.row(align=True)
        sub.enabled = False
        sub.label(text="", icon="HIDE_ON")
        return
    row.prop(
        collection,
        "is_visible",
        text="",
        icon="HIDE_OFF" if collection.is_visible else "HIDE_ON",
        toggle=True,
    )


def draw_swatch(
    layout: bpy.types.UILayout,
    arm_name: str,
    collection_name: str,
    is_top_level: bool,
) -> None:
    """Draw the theme selector - the three fixed columns ``o`` ``x`` ``p``.

    Alignment is the whole point: every row draws the SAME three widgets so
    the dot / number / picker columns line up and the middle buttons end at
    the same x on every row. ``ui_units_x`` is only a *minimum*, so it cannot
    cap a wide widget - the earlier bug was a themed row using a
    ``template_node_socket`` dot (wider than the no-theme spacer) while other
    rows used a non-breaking-space label, so the selectors were different
    widths. The fix is to use the identical widget in each slot on every row:

    - ``o`` dot: always a ``template_node_socket`` circle (the theme color on a
      themed top-level row, a neutral fill otherwise - an empty circle), never
      a label, so its width never changes between rows;
    - ``x`` number: always a right-aligned label (the ``THEME##`` number on a
      themed top-level row, a non-breaking space otherwise);
    - ``p`` picker: always the ``color_bone_collection`` operator button - the
      live ``COLOR`` picker on a top-level row, an inert ``BLANK1`` (disabled)
      on a nested row, so the column is reserved at the same width but only a
      top-level click colors (the subtree).
    """
    armature = bpy.data.objects.get(arm_name)
    label = collection_theme_label(armature, collection_name) if is_top_level and armature else ""
    color_set = _theme_bone_color_set(label)
    theme = layout.row(align=True)
    # o - dot: the same socket widget on every row (theme color, or neutral
    # for an empty circle), so the dot column is one width everywhere.
    dot = theme.row(align=True)
    dot.ui_units_x = _RIG_UI_DOT_UNITS
    if hasattr(dot, "template_node_socket"):
        normal = tuple(color_set.normal) if color_set is not None else _RIG_UI_NO_THEME_DOT
        dot.template_node_socket(color=(*normal[:3], 1.0))
    else:
        dot.label(text="\u00a0")
    # x - number: a non-breaking space when there is no number, NOT "" -
    # an empty label collapses (ui_units_x is only a minimum, ignored for
    # empty content), which would make no-theme rows narrower.
    num = theme.row(align=True)
    num.ui_units_x = _RIG_UI_NUM_UNITS
    num.alignment = "RIGHT"
    num.label(text=label or "\u00a0")
    # p - picker: the same operator widget on every row; nested rows draw it
    # disabled with a BLANK1 icon, so the column is reserved at one width but
    # only a top-level picker is live (and colors the whole subtree).
    pick = theme.row(align=True)
    pick.ui_units_x = _RIG_UI_PICK_UNITS
    pick.enabled = is_top_level
    op = pick.operator(
        "proscenio.color_bone_collection",
        text="",
        icon="COLOR" if is_top_level else "BLANK1",
    )
    op.armature_name = arm_name
    op.collection_name = collection_name
