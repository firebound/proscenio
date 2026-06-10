"""Shared status-bar chord primitive for modal operators.

A "chord" is one aligned row of icon/text labels in a modal operator's
STATUSBAR (or 3D-viewport header) hint - the bottom-bar cheatsheet that
mirrors Blender's own knife / loop-cut status bars. The per-operator
``_status_bar`` modules own their chord *vocabulary* (which gestures to
list, in what order); this module owns the one primitive that renders a
row so the icon/text layout never drifts between operators.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable

import bpy


def chord(layout: bpy.types.UILayout, *parts: tuple[str, str]) -> None:
    """Emit one aligned chord row. Each part is ``(icon, text)``; an empty
    icon prints text only, an empty text prints the icon only. Uses
    Blender's native ``EVENT_*`` / ``MOUSE_*`` icons so the hint visually
    matches Blender's own modal status bars (knife / loop cut)."""
    row = layout.row(align=True)
    for icon, text in parts:
        row.label(text=text, icon=icon or "NONE")


def append_statusbar_draw(operator_cls: type, draw_fn: Callable[..., None]) -> None:
    """Prepend ``draw_fn`` to the STATUSBAR header once for ``operator_cls``.

    Idempotent via the operator's ``_statusbar_appended`` class flag, so a
    re-entered modal does not stack duplicate header callbacks. The flag is
    read with ``getattr`` so the helper stays self-contained even for a
    class that has not declared it yet (the first append sets it).
    """
    if not getattr(operator_cls, "_statusbar_appended", False):
        bpy.types.STATUSBAR_HT_header.prepend(draw_fn)
        operator_cls._statusbar_appended = True


def remove_statusbar_draw(operator_cls: type, draw_fn: Callable[..., None]) -> None:
    """Remove ``draw_fn`` from the STATUSBAR header for ``operator_cls``.

    Clears the ``_statusbar_appended`` flag and suppresses the ValueError /
    RuntimeError Blender raises when the callback was already detached (e.g.
    an addon reload between invoke and cancel).
    """
    if getattr(operator_cls, "_statusbar_appended", False):
        with contextlib.suppress(ValueError, RuntimeError):
            bpy.types.STATUSBAR_HT_header.remove(draw_fn)
        operator_cls._statusbar_appended = False
