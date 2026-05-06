"""Doll armature build — 37-bone humanoid (SPEC 007 step 3).

Hierarchy locked by SPEC 007 STUDY.md. ``DOLL_BONES`` is the source of
truth: ``(name, head_xz, tail_xz, parent_or_None)``. World coords are
Blender XZ (Z up), in meters. Pixels-per-unit conversion is at the
sprite layer, not the armature.
"""

from __future__ import annotations

import bpy

# Body proportions, in Blender meters (1.0 unit = pixels_per_unit pixels).
# Total height ~2.0 — fits a 200×100 px atlas comfortably with PPU=100.
DOLL_BONES: tuple[
    tuple[str, tuple[float, float], tuple[float, float], str | None], ...
] = (
    ("root", (0.0, 0.0), (0.0, 0.05), None),
    # Pelvis split — asymmetric L/R for hip motion
    ("pelvis.L", (-0.08, 0.05), (-0.08, 0.30), "root"),
    ("pelvis.R", (0.08, 0.05), (0.08, 0.30), "root"),
    # Legs
    ("thigh.L", (-0.08, 0.05), (-0.08, -0.40), "root"),
    ("shin.L", (-0.08, -0.40), (-0.08, -0.80), "thigh.L"),
    ("foot.L", (-0.08, -0.80), (-0.16, -0.85), "shin.L"),
    ("thigh.R", (0.08, 0.05), (0.08, -0.40), "root"),
    ("shin.R", (0.08, -0.40), (0.08, -0.80), "thigh.R"),
    ("foot.R", (0.08, -0.80), (0.16, -0.85), "shin.R"),
    # Spine chain
    ("spine", (0.0, 0.05), (0.0, 0.30), "root"),
    ("spine.001", (0.0, 0.30), (0.0, 0.55), "spine"),
    ("spine.002", (0.0, 0.55), (0.0, 0.80), "spine.001"),
    ("spine.003", (0.0, 0.80), (0.0, 1.05), "spine.002"),
    # Breasts
    ("breast.L", (-0.10, 0.85), (-0.10, 0.95), "spine.003"),
    ("breast.R", (0.10, 0.85), (0.10, 0.95), "spine.003"),
    # Left arm
    ("shoulder.L", (-0.18, 1.00), (-0.30, 1.00), "spine.003"),
    ("upper_arm.L", (-0.30, 1.00), (-0.30, 0.65), "shoulder.L"),
    ("forearm.L", (-0.30, 0.65), (-0.30, 0.30), "upper_arm.L"),
    ("hand.L", (-0.30, 0.30), (-0.30, 0.20), "forearm.L"),
    ("finger.001.L", (-0.30, 0.20), (-0.30, 0.14), "hand.L"),
    ("finger.002.L", (-0.30, 0.14), (-0.30, 0.10), "finger.001.L"),
    # Right arm
    ("shoulder.R", (0.18, 1.00), (0.30, 1.00), "spine.003"),
    ("upper_arm.R", (0.30, 1.00), (0.30, 0.65), "shoulder.R"),
    ("forearm.R", (0.30, 0.65), (0.30, 0.30), "upper_arm.R"),
    ("hand.R", (0.30, 0.30), (0.30, 0.20), "forearm.R"),
    ("finger.001.R", (0.30, 0.20), (0.30, 0.14), "hand.R"),
    ("finger.002.R", (0.30, 0.14), (0.30, 0.10), "finger.001.R"),
    # Neck → head → face
    ("neck", (0.0, 1.05), (0.0, 1.18), "spine.003"),
    ("head", (0.0, 1.18), (0.0, 1.40), "neck"),
    ("face", (0.0, 1.20), (0.0, 1.38), "head"),
    ("brow.L", (-0.06, 1.32), (-0.06, 1.34), "face"),
    ("brow.R", (0.06, 1.32), (0.06, 1.34), "face"),
    ("ear.L", (-0.12, 1.28), (-0.14, 1.32), "face"),
    ("ear.R", (0.12, 1.28), (0.14, 1.32), "face"),
    ("eye.L", (-0.05, 1.28), (-0.05, 1.30), "face"),
    ("eye.R", (0.05, 1.28), (0.05, 1.30), "face"),
    ("jaw", (0.0, 1.22), (0.0, 1.20), "face"),
    ("lip.T", (0.0, 1.24), (0.0, 1.25), "face"),
    ("lip.B", (0.0, 1.22), (0.0, 1.23), "face"),
)


def build(name: str = "doll.armature") -> bpy.types.Object:
    """Create the doll armature object + edit bones, return the Object."""
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    edit_bones = arm_data.edit_bones
    name_to_bone: dict[str, bpy.types.EditBone] = {}
    for bone_name, head_xz, tail_xz, parent in DOLL_BONES:
        bone = edit_bones.new(bone_name)
        bone.head = (head_xz[0], 0.0, head_xz[1])
        bone.tail = (tail_xz[0], 0.0, tail_xz[1])
        if parent and parent in name_to_bone:
            bone.parent = name_to_bone[parent]
        name_to_bone[bone_name] = bone

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj
