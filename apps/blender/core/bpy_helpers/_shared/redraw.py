"""Shared area-redraw walker.

bpy-bound, but only operates on the duck-typed window manager passed in,
so the module stays importable without bpy. One place that walks every
window's areas and tags the matching ones for redraw - the depsgraph
handler (VIEW_3D only) and the automesh authoring modal (VIEW_3D +
STATUSBAR) both route their window walk through here so the iteration
lives once.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


def tag_redraw_areas(
    window_manager: bpy.types.WindowManager | None,
    area_types: set[str],
) -> None:
    """Tag every area whose ``type`` is in ``area_types`` for redraw, across
    every window of ``window_manager``.

    No-op when ``window_manager`` is None (e.g. a depsgraph callback firing
    before the UI exists) or a window has no screen yet. Callers pass the
    window manager directly so the walker stays agnostic about whether it
    came from an operator ``context`` or ``bpy.context``.
    """
    if window_manager is None:
        return
    for window in window_manager.windows:
        screen = getattr(window, "screen", None)
        if screen is None:
            continue
        for area in screen.areas:
            if area.type in area_types:
                area.tag_redraw()
