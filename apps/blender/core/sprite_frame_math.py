"""Sprite-frame UV slicing math (SPEC 009 wave 9.10 split).

Pure-Python helpers that compute the UV slicing constants for a
spritesheet cell at ``frame`` index in an ``hframes`` x ``vframes``
grid. Bpy-free - the shader graph builder in
``core/bpy_helpers/sprite_frame_shader.py`` consumes these values to
seed driver inputs, but the math itself runs without Blender.

Why a separate module: the math is independent of Blender's shader
graph and is the part that pytest exercises directly. Keeping it on
the bpy-free side of ``core/`` lets the unit tests import it without
mocking ``bpy``.
"""

from __future__ import annotations


def cell_size(hframes: int, vframes: int) -> tuple[float, float]:
    """Per-cell UV span as ``(width, height)``.

    Falls back to ``(1, 1)`` when either dimension is non-positive so
    the shader graph never divides by zero. The validation pass
    surfaces the user-facing error separately.
    """
    safe_h = max(1, int(hframes))
    safe_v = max(1, int(vframes))
    return (1.0 / safe_h, 1.0 / safe_v)


def cell_offset_x(frame: int, hframes: int) -> float:
    """U origin of the cell at ``frame`` in a ``hframes``-wide grid."""
    safe_h = max(1, int(hframes))
    column = int(frame) % safe_h
    return column / safe_h


def cell_offset_y(frame: int, hframes: int, vframes: int) -> float:
    """V origin of the cell at ``frame`` in an ``hframes`` x ``vframes`` grid.

    Returns the *Blender* UV origin (bottom-up). Frames advance
    left-to-right then top-to-bottom; the V origin flips so frame 0
    sits at the top of the atlas, matching how authors usually paint
    spritesheets.
    """
    safe_h = max(1, int(hframes))
    safe_v = max(1, int(vframes))
    row = (int(frame) // safe_h) % safe_v
    cell_h = 1.0 / safe_v
    return 1.0 - (row + 1) * cell_h
