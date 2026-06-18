"""Sprite-frame grid math (pure, no bpy)."""

from __future__ import annotations


def clamp_frame_index(frame: int, hframes: int, vframes: int) -> int:
    """Clamp a sprite frame index into the valid ``[0, hframes*vframes-1]`` grid.

    The grid has ``hframes * vframes`` cells, so the last valid index is
    ``hframes*vframes - 1`` (a 1x1 grid clamps everything to 0). Used by the
    frame property update callback so shrinking the grid pulls a now-out-of-
    range initial frame back in instead of exporting an index Godot rejects.
    """
    max_index = max(0, int(hframes) * int(vframes) - 1)
    return max(0, min(int(frame), max_index))
