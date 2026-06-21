"""Status-bar chord layout for the Quick Armature modal.

Pure rendering: takes a ``UILayout`` plus the operator class (for the
chord-direction flag) and emits the gesture cheatsheet shared by the
STATUSBAR and the 3D viewport header. The operator owns the registered
header callbacks (they bind the concrete class and are referenced by
register / sweep); this module owns only the chord vocabulary so the
operator file stays focused on the modal state machine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from .._status_bar import chord

if TYPE_CHECKING:
    from .quick_armature import PROSCENIO_OT_quick_armature


def emit_chord_layout(
    layout: bpy.types.UILayout,
    cls: type[PROSCENIO_OT_quick_armature],
) -> None:
    """Shared chord rendering for the STATUSBAR + 3D viewport headers.

    The cheatsheet swaps per modal sub-mode (Tab cycles Draw / Reparent) so
    only the active mode's gestures show - mirroring the per-stage automesh
    authoring status bar. Uses Blender's native ``EVENT_*`` / ``MOUSE_*``
    icons via the shared ``chord`` primitive so the hint visually matches
    Blender's own modal status bar (knife tool, loop cut, etc).
    """
    if cls._mode == "REPARENT":
        _emit_reparent_rows(layout)
    else:
        _emit_draw_rows(layout, cls)
    # Tab cycles the mode; the label names the OTHER mode (where Tab lands).
    other = "draw" if cls._mode == "REPARENT" else "reparent"
    chord(layout, ("EVENT_TAB", ""), ("", f"{other} mode"))
    _emit_exit_rows(layout, cls)


def _emit_draw_rows(
    layout: bpy.types.UILayout,
    cls: type[PROSCENIO_OT_quick_armature],
) -> None:
    """Draw-mode chords: the click-drag bone authoring vocabulary."""
    if cls._default_chain:
        connect_label = "connected"
        unparented_label = "unparented"
    else:
        connect_label = "unparented"
        unparented_label = "connected"

    chord(layout, ("MOUSE_LMB_DRAG", ""), ("", connect_label))
    chord(layout, ("EVENT_SHIFT", ""), ("", "+"), ("MOUSE_LMB_DRAG", ""), ("", unparented_label))
    chord(layout, ("EVENT_ALT", ""), ("", "+"), ("MOUSE_LMB_DRAG", ""), ("", "disconnected"))
    chord(layout, ("EVENT_X", ""), ("", "/"), ("EVENT_Z", ""), ("", "axis lock"))
    chord(layout, ("EVENT_CTRL", ""), ("", "grid snap"))
    chord(layout, ("EVENT_CTRL", ""), ("", "+"), ("EVENT_Z", ""), ("", "undo"))


def _emit_reparent_rows(layout: bpy.types.UILayout) -> None:
    """Reparent-mode chords: click a bone tip to pick the next chain parent."""
    chord(layout, ("MOUSE_LMB", ""), ("", "pick bone tip = parent"))


def _emit_exit_rows(
    layout: bpy.types.UILayout,
    cls: type[PROSCENIO_OT_quick_armature],
) -> None:
    """Confirm / exit chords, shared across modes.

    Confirm / exit read as synonyms and never change, so the two gestures
    looked identical. Relabel and make the Esc hint track session state: a
    bare Esc discards the empty auto-rig, but once a bone is authored both
    Esc and Enter keep the bones (only the report verb differs today). The
    session-state-aware label persists across both modes' cheatsheets.
    """
    chord(layout, ("EVENT_RETURN", ""), ("", "finish"))
    if cls._last_bone_name:
        chord(layout, ("EVENT_ESC", ""), ("", "exit (keeps bones)"))
    else:
        chord(layout, ("EVENT_ESC", ""), ("", "cancel (discards empty rig)"))
