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
    tool_is_island,
    tool_is_pen,
)
from .._status_bar import chord

# Display labels for the per-stage tools. The active one is bracketed in the Tab
# cycle so the artist sees what LMB will do. (spec 070 renamed the silhouette
# tools: ADD island / KNIFE / REMOVE island.)
_TOOL_LABELS = {
    "auto": "Auto",
    "add": "Add",
    "knife": "Knife",
    "remove": "Remove",
    "fold": "Fold",
    "point": "Point",
    "delete": "Delete",
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
        if tool_is_island(active_tool):
            # Closed-loop island pen (spec 070): LMB places, RMB drags, DEL drops
            # the last, clicking the first vert closes + commits.
            chord(layout, ("MOUSE_LMB", "place vert"))
            chord(layout, ("MOUSE_RMB", "drag vert"))
            chord(layout, ("EVENT_X", "/"), ("EVENT_Z", "axis lock"))
            chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv"))
            chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "/ Del = last vert"))
            chord(layout, ("", "click 1st vert = close"))
        elif tool_is_pen(active_tool):
            chord(layout, ("MOUSE_LMB", "vert / drag=draw"))
            chord(layout, ("EVENT_X", "/"), ("EVENT_Z", "axis lock"))
            chord(layout, ("MOUSE_MMB", "/ 0-9 = subdiv"))
            chord(layout, ("MOUSE_RMB", "/"), ("EVENT_RETURN", "finish"))
            chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "undo"))
        elif active_tool == "point":
            chord(layout, ("MOUSE_LMB", "point"))
            chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "undo"))
        elif active_tool == "delete":
            chord(layout, ("MOUSE_LMB", "remove stroke"))
            chord(layout, ("EVENT_CTRL", "+"), ("EVENT_Z", "undo"))
    chord(layout, ("EVENT_RETURN", "next"))
    chord(layout, ("EVENT_BACKSPACE", "back"))
    chord(layout, ("EVENT_ESC", "cancel"))
