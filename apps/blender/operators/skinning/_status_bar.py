"""Status-bar chord layout for the Edit Weights modal.

Pure rendering: takes a ``UILayout`` and emits the gesture cheatsheet
shared by the STATUSBAR (the canonical modal-hint home) and the optional
N-panel mirror (``panels/weight_paint.py`` while the modal runs). The
operator owns the registered header callback (it binds the concrete class
and is referenced by register / sweep); this module owns only the chord
vocabulary so the operator file stays focused on the modal state machine.
"""

from __future__ import annotations

import bpy

from .._status_bar import chord


def emit_edit_weights_chords(layout: bpy.types.UILayout) -> None:
    """Shared chord rendering for the STATUSBAR + the panel mirror.

    Edit Weights has no sub-modes: the only gestures are the hard exit and
    the mirror-source read-out. Uses Blender's native ``EVENT_*`` icons via
    the shared ``chord`` primitive so the hint matches Blender's own modal
    status bar (each gesture is one attached ``(icon, text)`` part).
    """
    chord(layout, ("EVENT_ESC", "exit"))
    chord(layout, ("MOD_MIRROR", "mirror = target.proscenio_mirror_x"))
