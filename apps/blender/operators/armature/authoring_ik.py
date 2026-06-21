"""IK chain toggle authoring shortcut (the authoring panel.1.b)."""

from __future__ import annotations

import math
from typing import ClassVar

import bpy
from bpy.props import IntProperty, StringProperty
from mathutils import Vector

from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]

_IK_CONSTRAINT_NAME = "Proscenio IK"
_IK_TARGET_SUFFIX = ".IK"
_MIN_TARGET_SIZE = 0.1
# Rigify-style affordances: control bones live in one named, theme-colored bone
# collection so they read as controls in the viewport / Bone Collections panel,
# not as deform bones. A custom shape is deferred (the costliest part).
_CONTROLS_COLLECTION = "Proscenio Controls"
_CONTROLS_THEME = "THEME01"
# Small in-plane pre-bend (radians) seeded on interior chain bones when the
# in-plane lock is engaged, so a perfectly straight chain still has an elbow
# direction for the solver. Picture-plane rigs swing about local Y.
_INPLANE_PREBEND = math.radians(5.0)


def _ik_target_name(bone_name: str) -> str:
    """Deterministic control-bone name for a constrained bone."""
    return f"{bone_name}{_IK_TARGET_SUFFIX}"


def _is_proscenio_target(name: str) -> bool:
    """True for a control bone this operator created, so toggle-off only ever
    deletes our own scaffolding - a hand-retargeted constraint is left alone."""
    return bool(name) and name.endswith(_IK_TARGET_SUFFIX)


def _rest_target_placement(pose_bone: bpy.types.PoseBone) -> tuple[Vector, Vector]:
    """Head/tail (armature rest space) for a control bone at the chain tip.

    The control sits at the constrained bone's rest tail so toggling IK on does
    not jump the chain; it points up the in-plane Z axis with a visible length
    derived from the source bone (floored so a zero-length bone still yields a
    selectable handle).
    """
    head = Vector(pose_bone.bone.tail_local)
    size = max(pose_bone.bone.length * 0.5, _MIN_TARGET_SIZE)
    tail = head + Vector((0.0, 0.0, size))
    return head, tail


def _create_target_bone(armature: bpy.types.Object, name: str, head: Vector, tail: Vector) -> None:
    """Create (or reposition) the non-deforming control bone in Edit Mode.

    Unparented so it floats free as the IK goal, and ``use_deform`` off so it
    never adds a vertex group to bound meshes.
    """
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        edit_bones = armature.data.edit_bones
        edit_bone = edit_bones.get(name) or edit_bones.new(name)
        edit_bone.head = head
        edit_bone.tail = tail
        edit_bone.parent = None
        edit_bone.use_deform = False
    finally:
        bpy.ops.object.mode_set(mode="POSE")


def _delete_bone(armature: bpy.types.Object, name: str) -> None:
    """Remove a control bone by name in Edit Mode (no-op when absent)."""
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        edit_bones = armature.data.edit_bones
        edit_bone = edit_bones.get(name)
        if edit_bone is not None:
            edit_bones.remove(edit_bone)
    finally:
        bpy.ops.object.mode_set(mode="POSE")


def _ensure_controls_collection(armature_data: bpy.types.Armature) -> bpy.types.BoneCollection:
    """Return the "Proscenio Controls" bone collection, creating it once."""
    collections = armature_data.collections
    existing = collections.get(_CONTROLS_COLLECTION)
    if existing is not None:
        return existing
    return collections.new(_CONTROLS_COLLECTION)


def _mark_as_control(armature: bpy.types.Object, bone_name: str) -> None:
    """Group a control bone into the controls collection and tint it.

    Called in Pose Mode (after the create round-trip) so the pose + data bones
    exist; the collection assignment and the theme color both read as "this is a
    control" in the viewport, the affordance an artist notices first. Tolerant
    of a build that exposes the color on the data Bone vs the PoseBone.
    """
    collection = _ensure_controls_collection(armature.data)
    bone = armature.data.bones.get(bone_name)
    if bone is not None:
        collection.assign(bone)
        if hasattr(bone, "color"):
            bone.color.palette = _CONTROLS_THEME
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is not None and hasattr(pose_bone, "color"):
        pose_bone.color.palette = _CONTROLS_THEME


class PROSCENIO_OT_toggle_ik_chain(bpy.types.Operator):
    """Add or remove a Proscenio-owned IK chain on the active pose bone.

    Not a state toggle: it creates the whole chain (constraint + control bone)
    when none exists and removes both when one does. The Skeleton panel resolves
    the button label ("Add IK Chain" / "Remove IK Chain") from the same state
    this operator reads, so the button names the action it performs.
    """

    bl_idname = "proscenio.toggle_ik_chain"
    bl_label = "Proscenio: Add / Remove IK Chain"
    bl_description = (
        "Adds an IK chain to the active pose bone - an IK constraint named "
        "'Proscenio IK' (chain length 2) wired to a control bone created at the "
        "chain tip, so the chain solves on its own - or removes both when one is "
        "already present. Hand-added constraints and retargeted ones are left "
        "untouched"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    chain_length: IntProperty(  # type: ignore[valid-type]
        name="Chain length",
        default=2,
        min=0,
        soft_max=8,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode != "POSE":
            return False
        bone = getattr(context, "active_pose_bone", None)
        return bone is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = context.active_object
        bone = context.active_pose_bone
        bone_name = bone.name
        existing = bone.constraints.get(_IK_CONSTRAINT_NAME)
        if existing is not None:
            subtarget = existing.subtarget
            bone.constraints.remove(existing)
            if _is_proscenio_target(subtarget):
                _delete_bone(armature, subtarget)
            report_info(self, f"removed IK from '{bone_name}'")
            return {"FINISHED"}

        target_name = _ik_target_name(bone_name)
        head, tail = _rest_target_placement(bone)
        _create_target_bone(armature, target_name, head, tail)

        # The mode round-trip can invalidate the pose-bone handle - re-fetch by name.
        pose_bone = armature.pose.bones[bone_name]
        ik = pose_bone.constraints.new(type="IK")
        ik.name = _IK_CONSTRAINT_NAME
        ik.chain_count = self.chain_length
        ik.target = armature
        ik.subtarget = target_name
        # Group + tint the control so it reads as a control, not a deform bone.
        _mark_as_control(armature, target_name)
        report_info(
            self,
            f"added IK to '{bone_name}' (chain={self.chain_length}) targeting '{target_name}'",
        )
        return {"FINISHED"}


def _chain_member_bones(
    pose_bone: bpy.types.PoseBone, chain_count: int
) -> list[bpy.types.PoseBone]:
    """Pose bones in the IK chain: the constrained bone plus parents.

    ``chain_count`` counts bones from the constrained bone toward the root;
    0 means the whole parent chain.
    """
    members: list[bpy.types.PoseBone] = []
    current: bpy.types.PoseBone | None = pose_bone
    remaining = chain_count if chain_count > 0 else -1
    while current is not None and remaining != 0:
        members.append(current)
        current = current.parent
        if remaining > 0:
            remaining -= 1
    return members


def _set_bone_select(pose_bone: bpy.types.PoseBone, selected: bool) -> None:
    """Set viewport selection, tolerant of the 4.x Bone vs 5.1 PoseBone layout.

    Blender 5.1 exposes the select flag on PoseBone; older builds kept it on the
    data Bone. ``nla.bake(only_selected=True)`` reads this to scope the bake to
    the IK chain.
    """
    if hasattr(pose_bone, "select"):
        pose_bone.select = selected
    elif hasattr(pose_bone.bone, "select"):
        pose_bone.bone.select = selected


def _get_bone_select(pose_bone: bpy.types.PoseBone) -> bool:
    """Read the same selection flag ``_set_bone_select`` writes."""
    if hasattr(pose_bone, "select"):
        return bool(pose_bone.select)
    if hasattr(pose_bone.bone, "select"):
        return bool(pose_bone.bone.select)
    return False


def _bake_frame_range(armature: bpy.types.Object, scene: bpy.types.Scene) -> tuple[int, int]:
    """Action frame range when the rig carries one, else the scene play range."""
    anim = armature.animation_data
    action = anim.action if anim is not None else None
    if action is not None:
        frame_range = action.frame_range
        return int(frame_range[0]), int(frame_range[1])
    return scene.frame_start, scene.frame_end


class PROSCENIO_OT_bake_ik_chain(bpy.types.Operator):
    """Bake the active pose bone's IK chain to bone keyframes over the action range."""

    bl_idname = "proscenio.bake_ik_chain"
    bl_label = "Proscenio: Bake IK to Keyframes"
    bl_description = (
        "Bakes the active pose bone's IK chain to bone keyframes across the "
        "action range (visual keying) and clears the IK constraint, so the "
        "exporter reads real bone motion instead of flat fcurves. Requires Pose "
        "Mode and an IK constraint on the active bone."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode != "POSE":
            return False
        bone = getattr(context, "active_pose_bone", None)
        return bone is not None and any(c.type == "IK" for c in bone.constraints)

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = context.active_object
        bone = context.active_pose_bone
        ik = next((c for c in bone.constraints if c.type == "IK"), None)
        if ik is None:
            report_warn(self, f"'{bone.name}' has no IK constraint to bake")
            return {"CANCELLED"}

        # Snapshot selection: the bake scopes to the IK chain by selecting only
        # those bones, so restore the artist's original per-bone selection after.
        selection_snapshot = {pb.name: _get_bone_select(pb) for pb in armature.pose.bones}
        chain_names = {pb.name for pb in _chain_member_bones(bone, ik.chain_count)}
        for pose_bone in armature.pose.bones:
            _set_bone_select(pose_bone, pose_bone.name in chain_names)
        frame_start, frame_end = _bake_frame_range(armature, context.scene)
        try:
            bpy.ops.nla.bake(
                frame_start=frame_start,
                frame_end=frame_end,
                only_selected=True,
                visual_keying=True,
                clear_constraints=True,
                use_current_action=True,
                bake_types={"POSE"},
            )
        finally:
            # Restore on every exit path: a bake that throws must not leave the
            # artist's selection stuck on the chain-only set.
            for pose_bone in armature.pose.bones:
                _set_bone_select(pose_bone, selection_snapshot.get(pose_bone.name, False))
        report_info(
            self,
            f"baked IK chain from '{bone.name}' over frames {frame_start}-{frame_end}",
        )
        return {"FINISHED"}


class PROSCENIO_OT_key_ik_influence(bpy.types.Operator):
    """Insert a keyframe on the active Proscenio IK chain's influence.

    The IK/FK-blend seed: influence is the one animatable constraint property,
    so keying it from the panel is the first step of an IK-to-FK blend.
    """

    bl_idname = "proscenio.key_ik_influence"
    bl_label = "Proscenio: Key IK Influence"
    bl_description = (
        "Inserts a keyframe on the active Proscenio IK chain's influence at the "
        "current frame - the seed of an IK/FK blend"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode != "POSE":
            return False
        bone = getattr(context, "active_pose_bone", None)
        return bone is not None and bone.constraints.get(_IK_CONSTRAINT_NAME) is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        bone = context.active_pose_bone
        ik = bone.constraints.get(_IK_CONSTRAINT_NAME)
        if ik is None:
            report_warn(self, f"'{bone.name}' has no Proscenio IK chain", always=True)
            return {"CANCELLED"}
        frame = context.scene.frame_current
        ik.keyframe_insert(data_path="influence", frame=frame)
        report_info(self, f"keyed IK influence on '{bone.name}' at frame {frame}")
        return {"FINISHED"}


def _set_inplane_lock(pose_bone: bpy.types.PoseBone, *, locked: bool) -> None:
    """Lock (or free) a chain bone's out-of-plane rotation DOFs.

    Picture-plane rigs swing about local Y, so locking X and Z keeps the IK
    solve in the 2D plane; unlocking clears all three.
    """
    pose_bone.lock_ik_x = locked
    pose_bone.lock_ik_z = locked
    pose_bone.lock_ik_y = False


def _seed_inplane_prebend(pose_bone: bpy.types.PoseBone) -> None:
    """Nudge a straight interior chain bone so the solver has a bend direction.

    Only applied when the bone is at rest about its in-plane (Y) axis - never
    overwrites a pose the artist already set. Bones in a non-Euler rotation mode
    are skipped rather than coerced to ``XYZ``: forcing the mode would clobber
    the bone's existing rotation representation (the dedicated
    ``convert_rotation_to_euler`` operator is the intentional path for that).
    """
    if pose_bone.rotation_mode in {"QUATERNION", "AXIS_ANGLE"}:
        return
    if abs(pose_bone.rotation_euler.y) < 1e-4:
        pose_bone.rotation_euler.y = _INPLANE_PREBEND


class PROSCENIO_OT_toggle_ik_inplane_lock(bpy.types.Operator):
    """Toggle the in-plane DOF lock on the active bone's Proscenio IK chain."""

    bl_idname = "proscenio.toggle_ik_inplane_lock"
    bl_label = "Proscenio: Toggle IK In-Plane Lock"
    bl_description = (
        "Locks the active Proscenio IK chain's out-of-plane rotation so the "
        "solve stays in the 2D picture plane, seeding a small bend on a straight "
        "chain so it has an elbow direction. Click again to unlock. Opt-in: the "
        "lock is hidden bone state otherwise"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode != "POSE":
            return False
        bone = getattr(context, "active_pose_bone", None)
        return bone is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = context.active_object
        name = self.bone_name or context.active_pose_bone.name
        pose_bone = armature.pose.bones.get(name)
        if pose_bone is None:
            report_warn(self, f"bone '{name}' not found", always=True)
            return {"CANCELLED"}
        ik = pose_bone.constraints.get(_IK_CONSTRAINT_NAME)
        if ik is None:
            report_warn(self, f"'{name}' has no Proscenio IK chain to lock", always=True)
            return {"CANCELLED"}

        members = _chain_member_bones(pose_bone, ik.chain_count)
        currently_locked = bool(pose_bone.lock_ik_x and pose_bone.lock_ik_z)
        lock = not currently_locked
        for member in members:
            _set_inplane_lock(member, locked=lock)
        if lock:
            # Seed a bend on the interior bones only (skip the tip and the root
            # anchor) so the solver picks a consistent elbow direction.
            for member in members[1:]:
                _seed_inplane_prebend(member)
        report_info(
            self,
            f"{'locked' if lock else 'unlocked'} IK chain from '{name}' in-plane",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_toggle_ik_chain,
    PROSCENIO_OT_bake_ik_chain,
    PROSCENIO_OT_key_ik_influence,
    PROSCENIO_OT_toggle_ik_inplane_lock,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
