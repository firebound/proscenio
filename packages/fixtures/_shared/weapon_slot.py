"""Shared weapon-slot character builder for the slot fixtures.

``slot_swap`` and ``slot_multi_anim`` build the SAME pseudo-arm-with-weapon
character and differ only in the animation they author on top of it:

- a lateral ``arm`` bone in the XZ picture plane (tail along +X, in the plane),
- the visible ``arm`` sprite mesh skinned to that bone,
- a ``weapon`` slot Empty object-parented at the bone tip and bound to the bone
  via the ``Proscenio Slot Follow`` constraint,
- N attachment meshes parented to the slot Empty (the default shown, the rest
  hidden so the Blender preview matches the runtime one-visible-at-a-time rule).

This module holds that shared construction once so the two builders cannot
drift apart; each fixture keeps only its unique animation authoring. It also
owns the small ``require_layers`` / ``finalize_blend`` scaffolding both builders
share around the save.

Runs only inside Blender (``blender --background --python ...``).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import bpy

from blend_utils import rewrite_images_to_relpath

if TYPE_CHECKING:
    from collections.abc import Sequence

PIXELS_PER_UNIT = 100.0

ARM_W_PX = 32
ARM_H_PX = 8
WEAPON_W_PX = 32
WEAPON_H_PX = 32

ARM_BONE = "arm"
SLOT_NAME = "weapon"


@dataclass(frozen=True)
class AttachmentSpec:
    """One attachment mesh bound to the weapon slot.

    ``draw_order`` is the Y Location (Draw Order) layer: stamped as the
    ``proscenio_y_draw_order`` Custom Property (the writer negates it into the
    Godot z_index) and used to stagger the attachment along the bone-Y axis so
    attachments never exactly share the picture plane.
    """

    name: str
    image_path: Path
    is_default: bool
    draw_order: int


@dataclass
class WeaponSlotCharacter:
    """The objects a slot fixture animates after the shared build."""

    armature: bpy.types.Object
    arm_mesh: bpy.types.Object
    slot_empty: bpy.types.Object
    attachments: dict[str, bpy.types.Object]


def build_weapon_slot_character(
    *,
    arm_image: Path,
    attachments: Sequence[AttachmentSpec],
) -> WeaponSlotCharacter:
    """Wipe the file and build the shared arm + slot + attachment character.

    Builds, in order, the ``arm_rig`` armature, the skinned ``arm`` mesh, the
    ``weapon`` slot Empty (its ``slot_default`` taken from the attachment flagged
    ``is_default``), then each attachment mesh in ``attachments`` order. Returns
    the objects the caller animates; the caller authors the actions and calls
    ``finalize_blend``.
    """
    _wipe_blend()
    armature = _build_armature()
    arm_mesh = _build_arm_mesh(armature, arm_image)
    slot_default = next(spec.name for spec in attachments if spec.is_default)
    slot_empty = _build_slot_empty(armature, slot_default)
    built = {spec.name: _build_attachment(spec, slot_empty) for spec in attachments}
    return WeaponSlotCharacter(
        armature=armature,
        arm_mesh=arm_mesh,
        slot_empty=slot_empty,
        attachments=built,
    )


def require_layers(paths: Sequence[Path], log_prefix: str) -> None:
    """Exit non-zero if any required PNG layer is missing."""
    for path in paths:
        if not path.exists():
            print(
                f"{log_prefix} missing {path} - run draw_layers.py first",
                file=sys.stderr,
            )
            sys.exit(1)


def finalize_blend(blend_path: Path, log_prefix: str) -> None:
    """Save the .blend, rewrite image paths ``//``-relative, save again.

    Mirrors the tail every builder shares: ``save_as_mainfile`` puts the file on
    disk so ``bpy.path.relpath`` has a base, ``rewrite_images_to_relpath`` makes
    the image paths machine-independent, and the final ``save_mainfile`` bakes
    them in.
    """
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    rewrite_images_to_relpath(log_prefix)
    bpy.ops.wm.save_mainfile()
    print(f"{log_prefix} wrote {blend_path}")


def _wipe_blend() -> None:
    for collection in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.actions,
    ):
        while collection:
            collection.remove(collection[0])


def _build_armature() -> bpy.types.Object:
    """Single lateral arm bone, in the XZ picture plane (+X, never into depth).

    The bone points +X (shoulder at origin, hand at the tip); the arm mesh is
    skinned to it so a pose rotation swings the whole arm in the plane.
    """
    arm_data = bpy.data.armatures.new("arm_rig")
    arm_obj = bpy.data.objects.new("arm_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    bone = arm_data.edit_bones.new(ARM_BONE)
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.32, 0.0, 0.0)

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _quad_mesh(name: str, w_px: int, h_px: int) -> bpy.types.Mesh:
    w = w_px / PIXELS_PER_UNIT
    h = h_px / PIXELS_PER_UNIT
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        vertices=[
            (-w / 2, 0.0, -h / 2),
            (w / 2, 0.0, -h / 2),
            (w / 2, 0.0, h / 2),
            (-w / 2, 0.0, h / 2),
        ],
        edges=[],
        faces=[(0, 1, 2, 3)],
    )
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    uv.data[0].uv = (0.0, 0.0)
    uv.data[1].uv = (1.0, 0.0)
    uv.data[2].uv = (1.0, 1.0)
    uv.data[3].uv = (0.0, 1.0)
    return mesh


def _build_material(name: str, image_path: Path) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(image_path), check_existing=True)
    tex.interpolation = "Closest"  # pixel-art: nearest-neighbor, no bilinear blur
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _stamp_polygon_props(obj: bpy.types.Object) -> None:
    """Set element_type=mesh on PG and CP mirrors."""
    obj["proscenio_type"] = "mesh"
    obj["proscenio_centered"] = True


def _build_arm_mesh(
    armature_obj: bpy.types.Object, arm_image: Path
) -> bpy.types.Object:
    mesh = _quad_mesh("arm", ARM_W_PX, ARM_H_PX)
    obj = bpy.data.objects.new("arm", mesh)
    bpy.context.scene.collection.objects.link(obj)
    # Skinned (not bone-parented): object-parent to the armature and weight every
    # vertex 1.0 to the arm bone. The mesh stays flat in the plane and follows
    # the bone`s swing; bone-parenting to the in-plane bone would tilt it out of
    # plane and collapse it. Centred on the bone (shoulder 0 -> hand 0.32).
    obj.location = (0.16, 0.0, 0.0)
    obj.parent = armature_obj
    obj.parent_type = "OBJECT"
    vg = obj.vertex_groups.new(name=ARM_BONE)
    vg.add([v.index for v in mesh.vertices], 1.0, "REPLACE")
    arm_mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    arm_mod.object = armature_obj
    mat = _build_material("arm.mat", arm_image)
    mesh.materials.append(mat)
    _stamp_polygon_props(obj)
    return obj


def _build_slot_empty(
    armature_obj: bpy.types.Object, slot_default: str
) -> bpy.types.Object:
    """Empty at the hand, flagged as a slot that follows the arm bone.

    Object-parented (not bone-parented) so the attachment quads stay flat in the
    plane; `slot_bone="arm"` tells the importer to parent the slot Node2D under
    the arm Bone2D, so the weapon follows the swinging arm in Godot.
    """
    empty = bpy.data.objects.new(SLOT_NAME, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = armature_obj
    empty.parent_type = "OBJECT"
    empty.location = (0.32, 0.0, 0.0)

    empty["proscenio_is_slot"] = True
    empty["proscenio_slot_default"] = slot_default
    empty["proscenio_slot_bone"] = ARM_BONE

    # Author the Blender-side follow so the weapon swings with the arm in the
    # viewport, mirroring the Godot importer. Baked at rest (no action yet), so
    # the writer's rest read leaves the golden unchanged. Name matches
    # core.bpy_helpers.slot.bone_follow.SLOT_FOLLOW_CONSTRAINT.
    con = empty.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Slot Follow"
    con.target = armature_obj
    con.subtarget = ARM_BONE
    bpy.context.view_layer.update()
    pose_bone = armature_obj.pose.bones[ARM_BONE]
    con.inverse_matrix = (armature_obj.matrix_world @ pose_bone.matrix).inverted()
    return empty


def _build_attachment(
    spec: AttachmentSpec, slot_empty: bpy.types.Object
) -> bpy.types.Object:
    """Polygon mesh attachment parented to the slot Empty.

    Non-default attachments are hidden in the viewport + render so the Blender
    preview matches the slot's runtime semantics (only one attachment visible at
    a time). Animation tracks toggle visibility at runtime via the
    ``slot_attachment`` track in the .proscenio output.

    ``spec.draw_order`` staggers the attachment along the bone-Y axis (order *
    the default 0.001 spacing) so attachments never exactly share the picture
    plane - protects against Eevee z-fight if two end up visible at once (e.g.
    the user unhides one for inspection).
    """
    mesh = _quad_mesh(spec.name, WEAPON_W_PX, WEAPON_H_PX)
    obj = bpy.data.objects.new(spec.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = slot_empty
    obj.parent_type = "OBJECT"
    obj.location = (0.0, spec.draw_order * 0.001, 0.0)
    obj["proscenio_y_draw_order"] = spec.draw_order
    mat = _build_material(f"{spec.name}.mat", spec.image_path)
    mesh.materials.append(mat)
    _stamp_polygon_props(obj)
    if not spec.is_default:
        obj.hide_viewport = True
        obj.hide_render = True
    return obj
