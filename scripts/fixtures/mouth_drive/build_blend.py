"""Assemble mouth_drive.blend (2-bone fixture with driver + action).

Run with::

    blender --background --python scripts/fixtures/mouth_drive/build_blend.py

Loads PNGs produced by ``draw_layers.py`` and builds:

- **Armature** ``mouth_rig`` with two bones laid out for 2D cutout
  authoring (front-ortho view, bones lying along world X so their
  local Y axis sits in the camera plane and a pose-mode R Y rotation
  feels like rotating "in the picture"):
  - ``mouth_pos`` - positions the mouth in 2D space; sprite mesh is
    parented to this bone, so translating / rotating it moves the
    mouth without affecting which sprite cell is shown.
  - ``mouth_drive`` - driver source bone; rotation around its local
    Z axis (which equals world Z viewed from front-ortho) is wired to
    ``mouth.proscenio.frame``. Animating its Z rotation cycles through
    the 4-frame mouth spritesheet.
- **Sprite_frame mesh** ``mouth`` referencing
  ``mouth_spritesheet.png`` with ``hframes=4``, ``vframes=1``.
  Parented to ``mouth_pos`` so the position bone moves it, and the
  driver bone changes which cell it shows.
- **Driver** on ``mouth.proscenio.frame``: scripted expression
  ``var * 2 + 2`` reading ``mouth_drive`` Z rotation in world space.
  - World space + XYZ Euler so ``var`` is radians, not quaternion
    components.
  - The expression maps [-pi/2, +pi/2] rad -> [1, 5] - with the
    IntProperty's [0, hframes*vframes-1] = [0, 3] clamp, that yields
    a clean cell sweep across the rotation range.
- **Action** ``mouth_drive_anim`` keyframing ``mouth_drive`` Z rotation
  -pi/2 -> +pi/2 -> 0 over 24 frames, plus a small translation cycle
  on ``mouth_pos`` to demonstrate position-vs-driver separation.

The fixture exists to validate end-to-end:

1. Pose-mode authoring (translate, rotate, drive) round-trips through
   the writer.
2. The Drive-from-Bone operator's defaults match what this fixture
   builds programmatically (same ``transform_space``, ``rotation_mode``,
   ``expression`` shape).
3. ``apps/blender/tests/run_tests.py`` re-exports the .blend and the
   .proscenio matches the committed golden.

Image filepath stored as ``//pillow_layers/...`` so cross-machine.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "mouth_drive"
SHEET_PATH = FIXTURE_DIR / "pillow_layers" / "mouth_spritesheet.png"
BLEND_PATH = FIXTURE_DIR / "mouth_drive.blend"

FRAME_W = 32
FRAME_H = 32
HFRAMES = 4
VFRAMES = 1
PIXELS_PER_UNIT = 100.0

POS_BONE = "mouth_pos"
DRIVE_BONE = "mouth_drive"


def main() -> None:
    if not SHEET_PATH.exists():
        print(
            f"[build_mouth_drive] missing {SHEET_PATH} - run draw_layers.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    sprite_obj = _build_sprite_frame_plane(armature_obj)
    _install_driver(sprite_obj, armature_obj)
    _build_action(armature_obj)
    _save_blend()
    _rewrite_image_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_mouth_drive] wrote {BLEND_PATH}")


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
    """Two bones perpendicular to the XZ picture plane, pointing
    TOWARD the Front Ortho camera.

    Blender's Front Orthographic view looks along world -Y, so the
    camera sits at +Y. Bones with tail at -Y from the head point at
    the viewer - the Spine / 2D-cutout convention - and appear as
    small octahedral dots from the front. A pose-mode R Y rotates the
    bone around the camera axis, the visible "rotation in the picture"
    that animators expect; reading it back via WORLD_SPACE + ROT_Y on
    a driver picks up the same value.

    Bones are spaced apart on world X so they remain selectable
    individually from front-ortho even though they overlap visually.
    """
    arm_data = bpy.data.armatures.new("mouth_rig")
    arm_obj = bpy.data.objects.new("mouth_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    pos = arm_data.edit_bones.new(POS_BONE)
    pos.head = (-0.2, 0.0, 0.0)
    pos.tail = (-0.2, -0.3, 0.0)

    drive = arm_data.edit_bones.new(DRIVE_BONE)
    drive.head = (0.2, 0.0, 0.0)
    drive.tail = (0.2, -0.3, 0.0)

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_frame_plane(armature_obj: bpy.types.Object) -> bpy.types.Object:
    w = FRAME_W / PIXELS_PER_UNIT
    h = FRAME_H / PIXELS_PER_UNIT
    mesh = bpy.data.meshes.new("mouth")
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

    obj = bpy.data.objects.new("mouth", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = armature_obj
    obj.parent_type = "BONE"
    obj.parent_bone = POS_BONE

    mat = bpy.data.materials.new(name="mouth.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(SHEET_PATH), check_existing=True)
    tex.interpolation = "Closest"  # pixel-art: nearest-neighbor, no bilinear blur
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)

    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = "sprite_frame"
        obj.proscenio.hframes = HFRAMES
        obj.proscenio.vframes = VFRAMES
        obj.proscenio.frame = 0
        obj.proscenio.centered = True
    obj["proscenio_type"] = "sprite_frame"
    obj["proscenio_hframes"] = HFRAMES
    obj["proscenio_vframes"] = VFRAMES
    obj["proscenio_frame"] = 0
    obj["proscenio_centered"] = True
    return obj


def _install_driver(sprite_obj: bpy.types.Object, armature_obj: bpy.types.Object) -> None:
    """Wire ``mouth_drive`` Z rotation to ``sprite.proscenio.frame``.

    Mirrors what the ``Drive from Bone`` panel operator does:
    delete any pre-existing driver, drop the seed keyframes Blender
    inserts, then write a SCRIPTED driver in WORLD_SPACE / XYZ Euler.
    """
    data_path = "proscenio.frame"
    if (
        sprite_obj.animation_data is not None
        and sprite_obj.animation_data.drivers.find(data_path) is not None
    ):
        sprite_obj.driver_remove(data_path)

    fcurve = sprite_obj.driver_add(data_path)
    while fcurve.keyframe_points:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0])

    driver = fcurve.driver
    driver.type = "SCRIPTED"
    driver.expression = "var * 2 + 2"
    var = driver.variables[0] if driver.variables else driver.variables.new()
    var.name = "var"
    var.type = "TRANSFORMS"
    target = var.targets[0]
    target.id = armature_obj
    target.bone_target = DRIVE_BONE
    target.transform_type = "ROT_Y"
    target.transform_space = "WORLD_SPACE"
    target.rotation_mode = "XYZ"

    if hasattr(sprite_obj, "proscenio"):
        sprite_obj.proscenio.driver_target = "frame"
        sprite_obj.proscenio.driver_source_armature = armature_obj
        sprite_obj.proscenio.driver_source_bone = DRIVE_BONE
        sprite_obj.proscenio.driver_source_axis = "ROT_Y"
        sprite_obj.proscenio.driver_expression = "var * 2 + 2"


def _build_action(armature_obj: bpy.types.Object) -> None:
    """Animate ``mouth_drive`` Z rotation -pi/2 -> +pi/2 -> 0 over 24 frames.

    Only the driver bone is animated. ``mouth_pos`` exists to demonstrate
    the position-vs-driver split structurally (sprite is parented to it),
    but it stays at rest - the writer's pose-location channel currently
    drops the Z component for bones whose Y axis is not aligned with
    world Z (see tests/BUGS_FOUND.md), so a translation here would not
    round-trip into the .proscenio golden. Once that writer fix lands,
    keyframes on ``mouth_pos`` can be added back.
    """
    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="mouth_drive_anim")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    drive_pose = armature_obj.pose.bones[DRIVE_BONE]
    drive_pose.rotation_mode = "XYZ"

    drive_keys = (
        (1, 0.0),
        (8, -math.pi / 2),
        (16, math.pi / 2),
        (24, 0.0),
    )
    for frame, value in drive_keys:
        bpy.context.scene.frame_set(frame)
        drive_pose.rotation_euler = (0.0, value, 0.0)
        drive_pose.keyframe_insert(data_path="rotation_euler", frame=frame, index=1)


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_image_to_relpath() -> None:
    """After save_as, rewrite image filepath to ``//pillow_layers/...``."""
    rel = bpy.path.relpath(str(SHEET_PATH))
    for img in bpy.data.images:
        if img.filepath:
            img.filepath = rel


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_mouth_drive] FAILED: {exc}", file=sys.stderr)
        raise
