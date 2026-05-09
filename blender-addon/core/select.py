"""bpy-bound selection helpers (SPEC 009 wave 9.1).

Replaces the 5+ inline copies of the deselect-all-then-select-one
idiom across operators (select_issue_object, select_outliner_object,
create_ortho_camera, reproject_sprite_uv, create_slot, etc).

Lives in ``core/`` for now; will move to ``core/bpy_helpers/`` once
wave 9.6 lands. The bpy import here is intentional and acknowledged
via the file docstring rather than the package-level "bpy-free"
contract.
"""

from __future__ import annotations

import bpy


def select_only(context: bpy.types.Context, obj: bpy.types.Object) -> None:
    """Deselect everything in the scene, then select + activate ``obj``.

    Mirrors the pattern Blender's UI uses for Outliner-driven
    activation: a single click selects exactly one object and makes it
    active. Suitable for operator paths that want the post-selection
    state to be unambiguous (the selected object is always the active
    one).
    """
    for other in context.scene.objects:
        other.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
