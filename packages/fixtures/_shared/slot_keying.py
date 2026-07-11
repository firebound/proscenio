"""Shared slot-visibility keying for the fixture ``build_blend.py`` scripts.

Every slot fixture (``slot_cycle``, ``slot_swap``, ``slot_multi_anim``) authors
attachment visibility the same way: bind a mesh to an action, hard-cut-key its
``hide_render`` + ``hide_viewport`` at a frame, and force CONSTANT interpolation
so the swap is an instant show/hide, never a fade. This module holds that logic
once so the three builders cannot drift apart.

``object_fcurves_in_action`` is the parameterized (action-taking) form: it reads
the curves ``obj`` owns *within a given action*, matched to the object's own
action slot on a Blender 4.4+ layered action. Taking the action explicitly is
what ``slot_multi_anim`` needs (a mesh keyed across two animations holds a
channelbag in each), and it is behaviorally identical to reading the active
action for the single-animation ``slot_cycle`` / ``slot_swap`` fixtures, where
the action passed in is always the mesh's active binding at key time.

Runs only inside Blender; ``bpy`` is referenced solely in type annotations
(deferred via ``from __future__ import annotations``) so the module imports on a
host without Blender for inspection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


def object_fcurves_in_action(
    obj: bpy.types.Object, action: bpy.types.Action
) -> list[bpy.types.FCurve]:
    """The fcurves ``obj`` owns within ``action`` (its slot channelbag on 4.4+).

    A legacy flat action exposes its curves as a bare ``fcurves`` collection
    bound to one datablock. A 4.4+ layered action nests them under
    layers > strips > channelbags; only the channelbag whose ``slot_handle``
    matches ``obj``'s own action slot belongs to ``obj``, so siblings sharing
    the action never cross-read.
    """
    flat = getattr(action, "fcurves", None)
    if flat:
        return list(flat)
    anim = obj.animation_data
    slot = getattr(anim, "action_slot", None)
    handle = getattr(slot, "handle", None) if slot is not None else None
    out: list[bpy.types.FCurve] = []
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                if (
                    handle is not None
                    and getattr(channelbag, "slot_handle", None) != handle
                ):
                    continue
                out.extend(channelbag.fcurves)
    return out


def key_show_only(
    mesh: bpy.types.Object,
    action: bpy.types.Action,
    *,
    visible: bool,
    frame: int,
) -> None:
    """Bind ``mesh`` to ``action`` and hard-cut-key its visibility at ``frame``."""
    mesh.animation_data_create()
    if mesh.animation_data.action is not action:
        mesh.animation_data.action = action
    mesh.hide_viewport = not visible
    mesh.hide_render = not visible
    mesh.keyframe_insert(data_path="hide_viewport", frame=frame)
    mesh.keyframe_insert(data_path="hide_render", frame=frame)
    for fcurve in object_fcurves_in_action(mesh, action):
        if fcurve.data_path in ("hide_render", "hide_viewport"):
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "CONSTANT"
            fcurve.update()
