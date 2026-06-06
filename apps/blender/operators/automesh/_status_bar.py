"""Status-bar chord layout for the automesh authoring modal.

Pure rendering: takes a ``UILayout`` plus the current stage label and
stage enum and emits the per-stage gesture chords (the bottom-bar hint
that mirrors Blender's own knife / loop-cut status bars). The operator
owns the registered header callback (it reads the live class-level stage
state); this module owns only the chord vocabulary so the operator file
stays focused on the modal state machine.
"""

from __future__ import annotations

import bpy

from ...core.skinning.authoring_stages import AuthoringStage  # type: ignore[import-not-found]


def chord(layout: bpy.types.UILayout, *parts: tuple[str, str]) -> None:
    """Emit one aligned chord row. Each part is ``(icon, text)``; an empty
    icon prints text only, an empty text prints the icon only. Mirrors
    ``quick_armature`` so the hint matches Blender's own modal status
    bars (knife / loop cut)."""
    row = layout.row(align=True)
    for icon, text in parts:
        row.label(text=text, icon=icon or "NONE")


def emit_authoring_chord_layout(
    layout: bpy.types.UILayout, stage_label: str, stage: AuthoringStage
) -> None:
    """Render per-stage gesture chords with native EVENT_*/MOUSE_* icons.

    ``stage_label`` is the already-formatted ``"N/M Name"`` title the
    operator computes from the active stage + interior mode.
    """
    chord(layout, ("MOD_REMESH", f"Automesh: {stage_label}"))
    if stage in {AuthoringStage.EDIT_OUTLINE, AuthoringStage.EDIT_INTERIOR_POINTS}:
        #  toggle pen: tap a modifier to enter draw mode (no holding).
        verb = "extend" if stage == AuthoringStage.EDIT_OUTLINE else "fold"
        if stage == AuthoringStage.EDIT_INTERIOR_POINTS:
            chord(layout, ("MOUSE_LMB", "point"))
        chord(layout, ("EVENT_SHIFT", "tap"), ("", f"{verb}-pen"))
        chord(layout, ("EVENT_CTRL", "tap"), ("", "cut-pen"))
        chord(layout, ("MOUSE_LMB", "vert / drag=draw"))
        chord(layout, ("EVENT_X", "/"), ("EVENT_Z", "axis lock"))
        chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv"))
        chord(layout, ("MOUSE_RMB", "/"), ("EVENT_RETURN", "finish"))
        chord(layout, ("EVENT_ALT", "+"), ("MOUSE_LMB", "delete"))
        chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "undo"))
    chord(layout, ("EVENT_RETURN", "next"))
    chord(layout, ("EVENT_BACKSPACE", "back"))
    chord(layout, ("EVENT_ESC", "cancel"))
