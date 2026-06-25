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

from ...core.skinning.authoring_stages import (  # type: ignore[import-not-found]
    AuthoringStage,
    stage_tools,
    tool_is_pen,
)
from .._status_bar import chord

# Display labels for the per-stage tools (spec 066). The active one is bracketed
# in the Tab cycle so the artist sees what LMB will do.
_TOOL_LABELS = {
    "auto": "Auto",
    "contour": "Manual contour",
    "extend": "Extend",
    "cut": "Cut",
    "fold": "Fold",
    "point": "Point",
}


def emit_authoring_chord_layout(
    layout: bpy.types.UILayout, stage_label: str, stage: AuthoringStage, active_tool: str
) -> None:
    """Render per-stage gesture chords with native EVENT_*/MOUSE_* icons.

    ``stage_label`` is the already-formatted ``"N/M Name"`` title; ``active_tool``
    is the stage's currently armed tool (bare Tab cycles it). The cycle shows the
    stage's tools with the active one bracketed, then the gesture chords for that
    tool.
    """
    chord(layout, ("MOD_REMESH", f"Automesh: {stage_label}"))
    tools = stage_tools(stage)
    if tools:
        cycle = " | ".join(
            f"[{_TOOL_LABELS[t]}]" if t == active_tool else _TOOL_LABELS[t] for t in tools
        )
        chord(layout, ("EVENT_TAB", "tool:"), ("", cycle))
        if tool_is_pen(active_tool):
            chord(layout, ("MOUSE_LMB", "vert / drag=draw"))
            chord(layout, ("EVENT_X", "/"), ("EVENT_Z", "axis lock"))
            chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv"))
            chord(layout, ("MOUSE_RMB", "/"), ("EVENT_RETURN", "finish"))
            chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "undo"))
        elif active_tool == "point":
            chord(layout, ("MOUSE_LMB", "point"))
        if stage in {AuthoringStage.EDIT_OUTLINE, AuthoringStage.EDIT_INTERIOR_POINTS}:
            chord(layout, ("EVENT_ALT", "+"), ("MOUSE_LMB", "delete"))
    chord(layout, ("EVENT_RETURN", "next"))
    chord(layout, ("EVENT_BACKSPACE", "back"))
    chord(layout, ("EVENT_ESC", "cancel"))
