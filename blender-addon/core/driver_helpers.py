"""Pure-Python helpers for the SPEC 005.1.d.1 driver shortcut.

Bpy-free. The operator that wires up a Blender driver lives in
``operators/__init__.py``; the bits that decide *what* defaults to use
and *which* armature/bone in a selection are factored out here so they
can be exercised under plain pytest without booting Blender.
"""

from __future__ import annotations

from typing import Protocol


class _ProscenioPropsLike(Protocol):
    """Minimal shape we read off ``Object.proscenio`` for default picking."""

    sprite_type: str


class _ArmatureBonesLike(Protocol):
    """Minimal shape of ``Armature.data.bones`` we touch (just ``active``)."""

    active: object  # has ``name`` when present, ``None`` when no active bone


class _ArmatureDataLike(Protocol):
    bones: _ArmatureBonesLike | None


class _ObjectLike(Protocol):
    """Subset of ``bpy.types.Object`` we depend on for selection sniffing."""

    type: str
    data: object


def default_target_for_sprite(props: _ProscenioPropsLike | None) -> str:
    """Pick the most useful driver target for the sprite kind.

    sprite_frame meshes drive on ``frame`` (animate cell index from a bone
    rotation); polygon meshes drive on ``region_x`` (the most useful UV
    nudge for slot-style sprite swaps).
    """
    sprite_type = str(getattr(props, "sprite_type", "polygon")) if props is not None else "polygon"
    return "frame" if sprite_type == "sprite_frame" else "region_x"


def find_armature_with_active_bone(
    selection: list[_ObjectLike],
) -> tuple[_ObjectLike | None, str]:
    """Return ``(armature_obj, active_bone_name)`` from ``selection``.

    Walks ``selection`` in order, skipping non-armature objects and
    armatures with no active bone. Returns ``(None, "")`` when no usable
    armature is in the selection — the operator surfaces a friendly
    error in that case.
    """
    for obj in selection:
        if obj.type != "ARMATURE":
            continue
        bones = getattr(obj.data, "bones", None)
        if bones is None:
            continue
        active = getattr(bones, "active", None)
        if active is None:
            continue
        name = getattr(active, "name", "")
        if not name:
            continue
        return obj, name
    return None, ""
