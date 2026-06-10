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

    Uses Blender's native ``EVENT_*`` / ``MOUSE_*`` icons via the shared
    ``chord`` primitive so the hint visually matches Blender's own modal
    status bar (knife tool, loop cut, etc).
    """
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
    chord(layout, ("EVENT_RETURN", ""), ("", "confirm"))
    chord(layout, ("EVENT_ESC", ""), ("", "exit"))
