"""Slot emission - bpy walker delegating to core/slot/slot_emit."""

from __future__ import annotations

import bpy
from proscenio_models import Slot

from ....core._shared.bone_follow_resolve import SLOT_FOLLOW_CONSTRAINT, follow_subtarget
from ....core._shared.cp_keys import PROSCENIO_SLOT_BONE, PROSCENIO_SLOT_DEFAULT
from ....core._shared.pg_cp_fallback import read_field
from ....core.bpy_helpers._shared._bpy_compat import iter_objects
from ....core.slot.slot_emit import SlotInput, build_slots, is_slot_empty


def build_slots_for_scene(scene: bpy.types.Scene) -> list[Slot]:
    """Walk Empty objects flagged with ``proscenio.is_slot`` and emit slots[].

    Bpy walker - delegates the schema-shaped projection to
    ``core.slot.slot_emit.build_slots`` so the slot logic can be exercised
    under plain pytest. ``bone`` resolves constraint-first (spec 080 D5: the
    Proscenio Child Of IS the binding), then the legacy ``slot_bone`` field
    for pre-080 files, then ``parent_bone`` when the Empty is bone-parented
    the old way. Attachments are mesh names only - the meshes themselves
    still emit normally in ``elements[]``.
    """
    slot_inputs: list[SlotInput] = []
    for obj in iter_objects(scene):
        if not is_slot_empty(obj):
            continue
        bone = follow_subtarget(obj, SLOT_FOLLOW_CONSTRAINT)
        if not bone:
            # Legacy read-fallbacks: the pre-080 `slot_bone` field, then a raw
            # bone parent.
            bone = str(read_field(obj, cp_key=PROSCENIO_SLOT_BONE, default=""))
        if not bone and obj.parent_type == "BONE":
            bone = str(obj.parent_bone)
        attachments = tuple(child.name for child in obj.children if child.type == "MESH")
        slot_inputs.append(
            SlotInput(
                name=obj.name,
                bone=str(bone),
                slot_default=read_slot_default(obj),
                attachments=attachments,
            )
        )
    return build_slots(slot_inputs)


def read_slot_default(obj: bpy.types.Object) -> str:
    """Read slot_default from PG, fall back to ``proscenio_slot_default`` CP."""
    return str(read_field(obj, cp_key=PROSCENIO_SLOT_DEFAULT, default=""))
