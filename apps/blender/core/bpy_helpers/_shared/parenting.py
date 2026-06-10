"""Object-parenting helpers.

bpy-bound, but only manipulates attributes on the passed objects, so the
module needs no runtime bpy import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


def parent_keep_world(child: bpy.types.Object, parent: bpy.types.Object) -> None:
    """Parent ``child`` to ``parent`` in OBJECT mode without moving it.

    Snapshots the child's world matrix, sets the OBJECT-mode parent, then
    restores the world transform via ``matrix_parent_inverse`` + a
    world-matrix write-back so the child stays exactly where it was on
    screen - the programmatic form of Blender's "Set Parent (Keep
    Transform)".
    """
    world = child.matrix_world.copy()
    child.parent = parent
    child.parent_type = "OBJECT"
    child.matrix_parent_inverse = parent.matrix_world.inverted()
    child.matrix_world = world
