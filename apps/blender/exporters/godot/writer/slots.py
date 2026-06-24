"""Slot emission - bpy walker delegating to core/slot/slot_emit."""

from __future__ import annotations

import bpy
from proscenio_models import Slot

from ....core._shared.cp_keys import PROSCENIO_SLOT_BONE, PROSCENIO_SLOT_DEFAULT
from ....core._shared.pg_cp_fallback import read_field
from ....core.bpy_helpers._shared._bpy_compat import iter_objects
from ....core.slot.slot_emit import SlotInput, build_slots, is_slot_empty


def build_slots_for_scene(scene: bpy.types.Scene) -> list[Slot]:
    """Walk Empty objects flagged with ``proscenio.is_slot`` and emit slots[].

    Bpy walker - delegates the schema-shaped projection to
    ``core.slot.slot_emit.build_slots`` so the slot logic can be exercised
    under plain pytest. Per the slot system, ``bone`` is the Empty's
    ``slot_bone`` field (the object-parent + Child Of follow convention),
    falling back to ``parent_bone`` when it is bone-parented the old way.
    Attachments are mesh names only - the meshes themselves still emit
    normally in ``elements[]``.
    """
    slot_inputs: list[SlotInput] = []
    for obj in iter_objects(scene):
        if not is_slot_empty(obj):
            continue
        # Prefer an explicit `slot_bone` (object-parented Empty - keeps the
        # attachment quads flat); fall back to the Empty's parent_bone when it
        # is bone-parented the old way.
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
