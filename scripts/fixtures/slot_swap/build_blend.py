"""Assemble slot_swap.blend (slot system minimal fixture).

Run with::

    blender --background --python scripts/fixtures/slot_swap/build_blend.py

Loads PNGs produced by ``draw_layers.py`` and builds a minimal slot
system fixture: a pseudo-arm swinging while its weapon attachment
swaps mid-animation.

Layout:

- **Armature** ``arm_rig`` with a single bone ``arm`` perpendicular
  to the XZ picture plane (tail along -Y, toward the Front Ortho
  camera -- Spine convention).
- **Polygon mesh** ``arm`` parented to the bone -- the visible 16x32
  arm sprite.
- **Empty** ``weapon`` parented to the bone tip; flagged
  ``proscenio.is_slot = True`` with default attachment ``axe``.
- **Two attachment meshes** parented to the slot Empty:
  - ``axe`` -- 32x32 polygon mesh with axe.png material
  - ``sword`` -- 32x32 polygon mesh with sword.png material
- **Two actions named ``swing``** that share a name so the writer
  merges them into a single animation with two tracks:
  - On the armature: keyframes the arm bone's local Y rotation
    -pi/6 -> +pi/6 -> 0 over 24 frames (gentle swing).
  - On the slot Empty: keyframes ``proscenio_slot_index`` 0 (axe)
    -> 1 (sword) -> 0 (axe) over the same 24 frames, constant
    interpolation. Swap happens at the apex of the swing.

The fixture exercises:

1. Slot Empty + N attachments + slot_default round-trip through the
   writer into a ``slots[]`` entry.
2. Slot index keyframes round-trip into a ``slot_attachment`` track.
3. Bone rotation animation co-exists with slot animation under a
   shared action name (writer's merge logic).
4. ``apps/blender/tests/run_tests.py`` re-exports the .blend and
   the result matches the committed golden.

Image filepaths stored as ``//pillow_layers/...`` so the fixture
works cross-machine. Materials use ``Closest`` interpolation so
pixel-art edges stay crisp in Eevee Material Preview.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "slot_swap"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
ARM_PATH = LAYERS_DIR / "arm.png"
AXE_PATH = LAYERS_DIR / "axe.png"
SWORD_PATH = LAYERS_DIR / "sword.png"
BLEND_PATH = FIXTURE_DIR / "slot_swap.blend"

PIXELS_PER_UNIT = 100.0

ARM_W_PX = 16
ARM_H_PX = 32
WEAPON_W_PX = 32
WEAPON_H_PX = 32

ARM_BONE = "arm"
SLOT_NAME = "weapon"


def main() -> None:
    for path in (ARM_PATH, AXE_PATH, SWORD_PATH):
        if not path.exists():
            print(
                f"[build_slot_swap] missing {path} -- run draw_layers.py first",
                file=sys.stderr,
            )
            sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    _build_arm_mesh(armature_obj)
    slot_empty = _build_slot_empty(armature_obj)
    _build_attachment("axe", AXE_PATH, slot_empty, is_default=True)
    _build_attachment("sword", SWORD_PATH, slot_empty, is_default=False)
    _build_swing_action(armature_obj)
    _build_swap_action(slot_empty)
    _save_blend()
    _rewrite_images_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_slot_swap] wrote {BLEND_PATH}")


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
    """Single horizontal bone perpendicular to the XZ picture plane."""
    arm_data = bpy.data.armatures.new("arm_rig")
    arm_obj = bpy.data.objects.new("arm_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    bone = arm_data.edit_bones.new(ARM_BONE)
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, -0.3, 0.0)

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
    """Set sprite_type=polygon on PG and CP mirrors."""
    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = "polygon"
        obj.proscenio.centered = True
    obj["proscenio_type"] = "polygon"
    obj["proscenio_centered"] = True


def _build_arm_mesh(armature_obj: bpy.types.Object) -> bpy.types.Object:
    mesh = _quad_mesh("arm", ARM_W_PX, ARM_H_PX)
    obj = bpy.data.objects.new("arm", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = armature_obj
    obj.parent_type = "BONE"
    obj.parent_bone = ARM_BONE
    mat = _build_material("arm.mat", ARM_PATH)
    mesh.materials.append(mat)
    _stamp_polygon_props(obj)
    return obj


def _build_slot_empty(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """Empty parented to the arm bone tip; flagged as a slot.

    Offset slightly toward the Front Ortho camera (-Y) so attachments
    sit in front of the arm sprite when both are rendered, instead of
    z-fighting at Y=0.
    """
    empty = bpy.data.objects.new(SLOT_NAME, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = armature_obj
    empty.parent_type = "BONE"
    empty.parent_bone = ARM_BONE
    empty.location = (0.0, -0.05, 0.0)

    if hasattr(empty, "proscenio"):
        empty.proscenio.is_slot = True
        empty.proscenio.slot_default = "axe"
    empty["proscenio_is_slot"] = True
    empty["proscenio_slot_default"] = "axe"
    empty["proscenio_slot_index"] = 0
    return empty


def _build_attachment(
    name: str,
    image_path: Path,
    slot_empty: bpy.types.Object,
    *,
    is_default: bool,
) -> bpy.types.Object:
    """Polygon mesh attachment parented to the slot Empty.

    Non-default attachments are hidden in the viewport + render so the
    Blender preview matches the slot's runtime semantics (only one
    attachment visible at a time). Animation tracks toggle visibility
    at runtime via the slot_attachment track in the .proscenio output.
    """
    mesh = _quad_mesh(name, WEAPON_W_PX, WEAPON_H_PX)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = slot_empty
    obj.parent_type = "OBJECT"
    mat = _build_material(f"{name}.mat", image_path)
    mesh.materials.append(mat)
    _stamp_polygon_props(obj)
    if not is_default:
        obj.hide_viewport = True
        obj.hide_render = True
    return obj


def _build_swing_action(armature_obj: bpy.types.Object) -> None:
    """Gentle Y rotation swing on the arm bone over 24 frames.

    Action name ``swing`` is shared with the slot Empty's swap action
    so the writer merges both into a single animation with one
    ``bone_transform`` track + one ``slot_attachment`` track.
    """
    import math

    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="swing")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    arm_pose = armature_obj.pose.bones[ARM_BONE]
    arm_pose.rotation_mode = "XYZ"

    # Y rotation = camera-axis rotation in Blender Front Ortho =
    # visible 2D rotation (per the project convention codified in
    # scripts/fixtures/README.md).
    swing_keys = (
        (1, -math.pi / 6),
        (12, math.pi / 6),
        (24, -math.pi / 6),
    )
    for frame, value in swing_keys:
        bpy.context.scene.frame_set(frame)
        arm_pose.rotation_euler = (0.0, value, 0.0)
        arm_pose.keyframe_insert(data_path="rotation_euler", frame=frame, index=1)


def _build_swap_action(slot_empty: bpy.types.Object) -> None:
    """Keyframe slot_index 0 -> 1 -> 0 over 24 frames, constant interp.

    Mirrors the SPEC 004 D5 contract: keys are sampled at the action's
    fcurve-key timestamps; the writer expands them into
    ``slot_attachment`` tracks with constant interpolation.

    Action name matches ``_build_swing_action`` (``swing``) so the
    writer's merge logic collapses bone tracks + slot tracks under a
    single ``swing`` animation entry.
    """
    slot_empty.animation_data_create()
    action = bpy.data.actions.new(name="swing")
    slot_empty.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    for frame, idx in ((1, 0), (12, 1), (24, 0)):
        bpy.context.scene.frame_set(frame)
        slot_empty["proscenio_slot_index"] = idx
        slot_empty.keyframe_insert(data_path='["proscenio_slot_index"]', frame=frame)


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_images_to_relpath() -> None:
    """Rewrite every image filepath to ``//pillow_layers/<name>``."""
    for img in bpy.data.images:
        if img.filepath:
            img.filepath = bpy.path.relpath(str(LAYERS_DIR / img.name))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_slot_swap] FAILED: {exc}", file=sys.stderr)
        raise
