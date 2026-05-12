"""Slot emission (SPEC 004 D8) - bpy walker delegating to core/slot_emit."""

from __future__ import annotations

import bpy

from ....core.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_IS_SLOT,
    PROSCENIO_SLOT_DEFAULT,
)
from ....core.pg_cp_fallback import read_bool_flag  # type: ignore[import-not-found]
from ....core.slot_emit import (  # type: ignore[import-not-found]
    SlotInput,
    build_slots,
)


def build_slots_for_scene(scene: bpy.types.Scene) -> list[dict[str, object]]:
    """Walk Empty objects flagged with ``proscenio.is_slot`` and emit slots[].

    Bpy walker - delegates the schema-shaped projection to
    ``core.slot_emit.build_slots`` so the slot logic can be exercised
    under plain pytest. Per SPEC 004 D3, ``bone`` is the Empty's
    ``parent_bone`` when ``parent_type == "BONE"``. Per D6, attachments
    are mesh names only - the meshes themselves still emit normally
    in ``sprites[]``.
    """
    slot_inputs: list[SlotInput] = []
    for obj in scene.objects:
        if obj.type != "EMPTY":
            continue
        if not is_slot_empty(obj):
            continue
        bone = obj.parent_bone if obj.parent_type == "BONE" else ""
        attachments = tuple(child.name for child in obj.children if child.type == "MESH")
        slot_inputs.append(
            SlotInput(
                name=obj.name,
                bone=str(bone),
                slot_default=read_slot_default(obj),
                attachments=attachments,
            )
        )
    result: list[dict[str, object]] = build_slots(slot_inputs)
    return result


def is_slot_empty(obj: bpy.types.Object) -> bool:
    """True when ``obj`` is a slot-flagged Empty.

    Reads PropertyGroup first (canonical post-SPEC 005), Custom Property
    ``proscenio_is_slot`` as legacy fallback. The fallback matters in
    headless contexts where the addon's PropertyGroup is not registered
    - CI runs Blender without the addon enabled. Delegates to
    ``read_bool_flag`` so an explicit ``is_slot=False`` on the PG
    suppresses a stale CP-True (PG-first contract).
    """
    return bool(read_bool_flag(obj, pg_field="is_slot", cp_key=PROSCENIO_IS_SLOT))


def read_slot_default(obj: bpy.types.Object) -> str:
    """Read slot_default from PG, fall back to ``proscenio_slot_default`` CP."""
    props = getattr(obj, "proscenio", None)
    if props is not None:
        value = getattr(props, "slot_default", "")
        if value:
            return str(value)
    if hasattr(obj, "get"):
        cp_value = obj.get(PROSCENIO_SLOT_DEFAULT, "")
        if cp_value:
            return str(cp_value)
    return ""
