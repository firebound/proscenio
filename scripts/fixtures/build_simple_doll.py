"""Build the simple_doll test fixture from scratch (SPEC 007).

Run with::

    blender --background --python scripts/fixtures/build_simple_doll.py

Idempotent: deletes the existing ``examples/simple_doll/`` outputs and
rewrites them deterministically. Generates:

- ``layers/head.png``, ``torso.png``, ``arm.L.png``, ``arm.R.png``, ``legs.png``
  — solid colored squares with thin black borders, deterministic seeds.
- ``simple_doll.blend`` — 5 polygon meshes + 6-bone armature + weights +
  2 actions (``idle``, ``wave``).

The fixture exercises the ``1 sprite = 1 PNG`` workflow (the common case
for the Photoshop-first pipeline). Pack Atlas + Apply in this fixture
should produce a packed atlas with the 5 sources side-by-side, no
slicing required.

NOT a unit-tested module — a fixture builder. Re-run whenever the
fixture spec changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "examples" / "simple_doll"
LAYERS_DIR = FIXTURE_DIR / "layers"
BLEND_PATH = FIXTURE_DIR / "simple_doll.blend"

# (name, width_px, height_px, RGB color 0..1, parent_bone)
SPRITES: tuple[tuple[str, int, int, tuple[float, float, float], str], ...] = (
    ("head", 64, 64, (0.85, 0.20, 0.20), "head"),
    ("torso", 96, 128, (0.20, 0.30, 0.85), "spine"),
    ("arm.L", 32, 96, (0.30, 0.75, 0.30), "arm.L"),
    ("arm.R", 32, 96, (0.30, 0.75, 0.30), "arm.R"),
    ("legs", 80, 96, (0.85, 0.65, 0.20), "legs"),
)

# (bone_name, head_position_xz, tail_position_xz, parent_bone or None)
BONES: tuple[tuple[str, tuple[float, float], tuple[float, float], str | None], ...] = (
    ("root", (0.0, 0.0), (0.0, 0.5), None),
    ("spine", (0.0, 0.5), (0.0, 1.5), "root"),
    ("head", (0.0, 1.5), (0.0, 2.0), "spine"),
    ("arm.L", (-0.5, 1.4), (-0.5, 0.6), "spine"),
    ("arm.R", (0.5, 1.4), (0.5, 0.6), "spine"),
    ("legs", (0.0, 0.5), (0.0, -0.5), "root"),
)

PIXELS_PER_UNIT = 100.0


def main() -> None:
    """Entry point — invoked by Blender's --python flag."""
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _wipe_blend()
    _generate_pngs()
    armature_obj = _build_armature()
    sprite_objs = _build_sprite_planes(armature_obj)
    _wire_weights(sprite_objs, armature_obj)
    _build_actions(armature_obj)
    _save_blend()
    print(f"[simple_doll] wrote {BLEND_PATH}")
    print(f"[simple_doll] wrote {len(SPRITES)} PNG(s) under {LAYERS_DIR}")


def _wipe_blend() -> None:
    """Reset the current blend to a known empty state."""
    for collection in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.actions,
    ):
        for item in list(collection):
            collection.remove(item)


def _generate_pngs() -> None:
    """Solid colored squares with a 1px black border, saved as PNGs."""
    for name, w, h, color, _bone in SPRITES:
        img = bpy.data.images.new(name=name, width=w, height=h, alpha=True)
        pixels = [0.0] * (w * h * 4)
        r, g, b = color
        for y in range(h):
            for x in range(w):
                i = (y * w + x) * 4
                on_border = x == 0 or y == 0 or x == w - 1 or y == h - 1
                if on_border:
                    pixels[i : i + 4] = [0.0, 0.0, 0.0, 1.0]
                else:
                    pixels[i : i + 4] = [r, g, b, 1.0]
        img.pixels.foreach_set(pixels)
        out = LAYERS_DIR / f"{name}.png"
        img.filepath_raw = str(out)
        img.file_format = "PNG"
        img.save()


def _build_armature() -> bpy.types.Object:
    """Create a 6-bone armature in edit mode, return the Object."""
    arm_data = bpy.data.armatures.new("simple_doll.armature")
    arm_obj = bpy.data.objects.new("simple_doll.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj

    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = arm_data.edit_bones
    name_to_bone = {}
    for name, head_xz, tail_xz, parent in BONES:
        bone = edit_bones.new(name)
        bone.head = (head_xz[0], 0.0, head_xz[1])
        bone.tail = (tail_xz[0], 0.0, tail_xz[1])
        if parent and parent in name_to_bone:
            bone.parent = name_to_bone[parent]
        name_to_bone[name] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_planes(armature_obj: bpy.types.Object) -> dict[str, bpy.types.Object]:
    """Create one quad per sprite, parented to the armature, with material + UV."""
    out: dict[str, bpy.types.Object] = {}
    for name, w_px, h_px, _color, parent_bone in SPRITES:
        # Quad sized so width / height in Blender units match pixels / pixels_per_unit.
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

        # UV layer covers the full image (1 sprite = 1 PNG path).
        uv = mesh.uv_layers.new(name="UVMap")
        uv.data[0].uv = (0.0, 0.0)
        uv.data[1].uv = (1.0, 0.0)
        uv.data[2].uv = (1.0, 1.0)
        uv.data[3].uv = (0.0, 1.0)

        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = armature_obj
        obj.parent_type = "BONE"
        obj.parent_bone = parent_bone

        mat = _build_image_material(name)
        mesh.materials.append(mat)

        # Tag as polygon (default — explicit for clarity).
        if hasattr(obj, "proscenio"):
            obj.proscenio.sprite_type = "polygon"

        out[name] = obj
    return out


def _build_image_material(sprite_name: str) -> bpy.types.Material:
    """Material with a TEX_IMAGE node pointing at the sprite's source PNG."""
    mat = bpy.data.materials.new(name=f"{sprite_name}.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    img_path = LAYERS_DIR / f"{sprite_name}.png"
    tex.image = bpy.data.images.load(str(img_path), check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _wire_weights(
    sprite_objs: dict[str, bpy.types.Object], armature_obj: bpy.types.Object
) -> None:
    """Attach each sprite to its parent bone with weight 1.0.

    Arms additionally get 0.3 spillover to ``spine`` so the writer's
    multi-bone-weight path (SPEC 003) is exercised.
    """
    for name, _w, _h, _c, parent_bone in SPRITES:
        obj = sprite_objs[name]
        # Add an Armature modifier so vertex groups influence deformation.
        mod = obj.modifiers.new(name="Armature", type="ARMATURE")
        mod.object = armature_obj
        # Primary weight
        vg = obj.vertex_groups.new(name=parent_bone)
        vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
        # Spillover for arms
        if name in {"arm.L", "arm.R"}:
            spill = obj.vertex_groups.new(name="spine")
            spill.add(list(range(len(obj.data.vertices))), 0.3, "REPLACE")


def _build_actions(armature_obj: bpy.types.Object) -> None:
    """Two simple actions: idle (4-frame loop) and wave (8-frame arm.R)."""
    armature_obj.animation_data_create()
    _build_idle_action(armature_obj)
    _build_wave_action(armature_obj)


def _build_idle_action(armature_obj: bpy.types.Object) -> None:
    action = bpy.data.actions.new(name="idle")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 4
    bpy.ops.object.mode_set(mode="POSE")
    spine = armature_obj.pose.bones.get("spine")
    if spine is None:
        bpy.ops.object.mode_set(mode="OBJECT")
        return
    # Tiny idle bob on spine.
    for frame, dy in ((1, 0.0), (2, 0.02), (3, 0.0), (4, -0.02)):
        bpy.context.scene.frame_set(frame)
        spine.location = (0.0, 0.0, dy)
        spine.keyframe_insert(data_path="location", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")


def _build_wave_action(armature_obj: bpy.types.Object) -> None:
    import math

    action = bpy.data.actions.new(name="wave")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 8
    bpy.ops.object.mode_set(mode="POSE")
    arm_r = armature_obj.pose.bones.get("arm.R")
    if arm_r is None:
        bpy.ops.object.mode_set(mode="OBJECT")
        return
    arm_r.rotation_mode = "XYZ"
    for frame, deg in ((1, 0.0), (3, -45.0), (5, -90.0), (7, -45.0), (8, 0.0)):
        bpy.context.scene.frame_set(frame)
        arm_r.rotation_euler = (0.0, math.radians(deg), 0.0)
        arm_r.keyframe_insert(data_path="rotation_euler", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[simple_doll] FAILED: {exc}", file=sys.stderr)
        raise
