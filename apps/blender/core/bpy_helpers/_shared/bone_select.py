"""bpy-bound bone-selection helpers for the Skeleton-list multi-select.

The object lists drive :mod:`select`; bones need their own trio because bone
selection lives on a different datablock per mode - ``PoseBone.select`` in POSE,
``EditBone.select`` in EDIT - and ``Armature.bones.active`` (``edit_bones.active``
in EDIT) drives the Properties-editor highlight. ``bone_select_only`` /
``bone_select_add`` / ``bone_select_toggle`` mirror the object trio in
:mod:`select` so the Skeleton list's Shift/Ctrl routing reads the same as the
Outliner's. OBJECT mode has no per-bone viewport selection, so the helpers
no-op the selection flag there and only move the active bone.
"""

from __future__ import annotations

import bpy

#: Modes where a bone carries a real, per-bone selection flag.
BONE_SELECT_MODES = frozenset({"POSE", "EDIT_ARMATURE"})


def _select_collection(armature: bpy.types.Object, mode: str) -> bpy.types.AnyType | None:
    """The per-mode bone collection that carries ``.select``, or None.

    POSE -> pose bones, EDIT_ARMATURE -> edit bones, anything else -> None
    (no per-bone selection outside those modes). ``edit_bones`` is only
    populated while the armature is in edit mode; outside it the attribute
    reads as an empty collection, which the callers treat as "nothing to do".
    """
    if mode == "POSE" and armature.pose is not None:
        return armature.pose.bones
    if mode == "EDIT_ARMATURE":
        return getattr(armature.data, "edit_bones", None)
    return None


def _get_select(bone: bpy.types.AnyType) -> bool:
    if hasattr(bone, "select"):
        return bool(bone.select)
    inner = getattr(bone, "bone", None)
    return bool(getattr(inner, "select", False))


def _set_select(bone: bpy.types.AnyType, value: bool) -> None:
    # Edit bones track head/tail selection too; set them so a bone reads as
    # fully (de)selected in the viewport rather than half-selected. Pose bones
    # only have ``select`` (with a 4.x fallback to the wrapped ``bone``).
    touched = False
    for attr in ("select", "select_head", "select_tail"):
        if hasattr(bone, attr):
            setattr(bone, attr, value)
            touched = touched or attr == "select"
    if not touched:
        inner = getattr(bone, "bone", None)
        if inner is not None and hasattr(inner, "select"):
            inner.select = value


def set_active_bone(armature: bpy.types.Object, bone_name: str, mode: str) -> None:
    """Point the armature's active bone at ``bone_name`` for the current mode."""
    if mode == "EDIT_ARMATURE":
        edit_bones = getattr(armature.data, "edit_bones", None)
        if edit_bones is not None and edit_bones.get(bone_name) is not None:
            edit_bones.active = edit_bones[bone_name]
        return
    bones = getattr(armature.data, "bones", None)
    if bones is not None and bones.get(bone_name) is not None:
        bones.active = bones[bone_name]


def bone_is_selected(armature: bpy.types.Object, bone_name: str, mode: str) -> bool:
    """Whether ``bone_name`` carries a live selection flag in ``mode``."""
    collection = _select_collection(armature, mode)
    if collection is None:
        return False
    bone = collection.get(bone_name)
    return _get_select(bone) if bone is not None else False


def bone_select_only(armature: bpy.types.Object, bone_name: str, mode: str) -> None:
    """Deselect every bone, select ``bone_name``, make it active (plain click)."""
    collection = _select_collection(armature, mode)
    if collection is not None:
        for bone in collection:
            _set_select(bone, bone.name == bone_name)
    set_active_bone(armature, bone_name, mode)


def bone_select_add(armature: bpy.types.Object, bone_name: str, mode: str) -> None:
    """Add ``bone_name`` to the selection and make it active (Shift)."""
    collection = _select_collection(armature, mode)
    if collection is not None:
        bone = collection.get(bone_name)
        if bone is not None:
            _set_select(bone, True)
    set_active_bone(armature, bone_name, mode)


def bone_select_toggle(armature: bpy.types.Object, bone_name: str, mode: str) -> bool:
    """Flip ``bone_name``'s selection; activate it when it becomes selected (Ctrl).

    Returns the new selection state. Deselecting leaves the active bone alone -
    matching the object toggle, where a Ctrl-deselect does not blank the active.
    Outside a bone-select mode there is no flag to flip: the active bone still
    moves so the list highlight tracks the click, and the call reports unselected.
    """
    collection = _select_collection(armature, mode)
    bone = collection.get(bone_name) if collection is not None else None
    if bone is None:
        set_active_bone(armature, bone_name, mode)
        return False
    new_state = not _get_select(bone)
    _set_select(bone, new_state)
    if new_state:
        set_active_bone(armature, bone_name, mode)
    return new_state
