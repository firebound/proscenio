"""Edit Weights modal session state.

EditWeightsSession captures the world state at invoke so _finish
can restore it via try/finally even on exception.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

import bpy

from ...skinning.paint_preset_2d import PaintPresetSnapshot
from .._shared.select import restore_selection
from .bone_collection_visibility import BoneCollectionSnapshot
from .bone_collection_visibility import restore as restore_bone_visibility
from .paint_preset_bind import restore_paint_preset


@dataclass(frozen=True)
class EditWeightsSession:
    """Container for prior state captured at modal invoke."""

    prior_active: bpy.types.Object | None
    prior_selected_names: list[str] = field(default_factory=list)
    prior_obj_mode: str = "OBJECT"
    prior_armature_mode: str = "OBJECT"
    prior_paint_preset: PaintPresetSnapshot | None = None
    prior_bone_collections: BoneCollectionSnapshot | None = None
    prior_overlay_flag: bool = False
    armature_name: str | None = None
    mesh_name: str | None = None


def capture(
    context: bpy.types.Context,
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    paint_preset: PaintPresetSnapshot,
    bone_collections: BoneCollectionSnapshot,
    overlay_flag: bool,
) -> EditWeightsSession:
    """Snapshot everything needed to restore on exit."""
    return EditWeightsSession(
        prior_active=context.view_layer.objects.active,
        prior_selected_names=[o.name for o in context.selected_objects],
        prior_obj_mode=obj.mode,
        prior_armature_mode=armature.mode,
        prior_paint_preset=paint_preset,
        prior_bone_collections=bone_collections,
        prior_overlay_flag=overlay_flag,
        armature_name=armature.name,
        mesh_name=obj.name,
    )


def restore(context: bpy.types.Context, session: EditWeightsSession) -> None:
    """Reapply prior state in safe order. Errors logged, never raised."""
    obj = bpy.data.objects.get(session.mesh_name) if session.mesh_name else None
    armature = bpy.data.objects.get(session.armature_name) if session.armature_name else None
    if obj is not None:
        with contextlib.suppress(RuntimeError):
            context.view_layer.objects.active = obj
            if obj.mode != session.prior_obj_mode:
                bpy.ops.object.mode_set(mode=session.prior_obj_mode)
    if armature is not None and armature.mode != session.prior_armature_mode:
        with contextlib.suppress(RuntimeError):
            context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode=session.prior_armature_mode)
    if session.prior_paint_preset is not None:
        with contextlib.suppress(RuntimeError, AttributeError):
            restore_paint_preset(context, session.prior_paint_preset)
    if armature is not None and session.prior_bone_collections is not None:
        with contextlib.suppress(RuntimeError):
            restore_bone_visibility(armature, session.prior_bone_collections)
    restore_selection(context, session.prior_selected_names, session.prior_active)
    _restore_overlay_flag(context, session.prior_overlay_flag)


def _restore_overlay_flag(context: bpy.types.Context, prior: bool) -> None:
    scene_props = getattr(context.scene, "proscenio", None)
    skinning = getattr(scene_props, "skinning", None) if scene_props else None
    if skinning is not None and hasattr(skinning, "show_provenance_overlay"):
        skinning.show_provenance_overlay = prior
