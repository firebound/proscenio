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

if TYPE_CHECKING:
    from .quick_armature import PROSCENIO_OT_quick_armature


def emit_chord_layout(
    layout: bpy.types.UILayout,
    cls: type[PROSCENIO_OT_quick_armature],
) -> None:
    """Shared chord rendering for the STATUSBAR + 3D viewport headers.

    Uses Blender's native ``EVENT_*`` / ``MOUSE_*`` icons via
    ``layout.label(icon=...)`` so the hint visually matches Blender's own
    modal status bar (knife tool, loop cut, etc).
    """
    if cls._default_chain:
        connect_label = "connected"
        unparented_label = "unparented"
    else:
        connect_label = "unparented"
        unparented_label = "connected"

    row = layout.row(align=True)
    row.label(text="", icon="MOUSE_LMB_DRAG")
    row.label(text=connect_label)

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_SHIFT")
    row.label(text="+")
    row.label(text="", icon="MOUSE_LMB_DRAG")
    row.label(text=unparented_label)

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ALT")
    row.label(text="+")
    row.label(text="", icon="MOUSE_LMB_DRAG")
    row.label(text="disconnected")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_X")
    row.label(text="/")
    row.label(text="", icon="EVENT_Z")
    row.label(text="axis lock")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_CTRL")
    row.label(text="grid snap")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_CTRL")
    row.label(text="+")
    row.label(text="", icon="EVENT_Z")
    row.label(text="undo")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_RETURN")
    row.label(text="confirm")

    row = layout.row(align=True)
    row.label(text="", icon="EVENT_ESC")
    row.label(text="exit")
