"""Assemble the shared_atlas .blend (SPEC 007 step 2, Blender side).

Run with::

    blender --background --python scripts/fixtures/build_shared_atlas.py

Loads ``examples/generated/shared_atlas/atlas.png`` produced by
``draw_shared_atlas.py`` and builds 3 polygon meshes whose UV bounds
each cover one quadrant of the shared atlas. The bottom-right quadrant
stays unused.

Run ``draw_shared_atlas.py`` first or this script aborts on missing
PNG.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "shared_atlas"
ATLAS_PATH = FIXTURE_DIR / "atlas.png"
BLEND_PATH = FIXTURE_DIR / "shared_atlas.blend"

ATLAS_W = 256
ATLAS_H = 256
PIXELS_PER_UNIT = 100.0

# (sprite_name, uv_min_x, uv_min_y, uv_max_x, uv_max_y)
# UVs are Blender-style (bottom-up): v=0 at bottom, v=1 at top.
# The PNG was drawn top-down; Blender flips on load so v=[0.5, 1.0]
# corresponds to the PNG's top half, matching where each shape was drawn.
SPRITES = (
    # Red circle drawn at top-left of the PNG → top-left UV quadrant.
    ("red_circle", 0.0, 0.5, 0.5, 1.0),
    # Green triangle drawn at top-right of the PNG → top-right UV quadrant.
    ("green_triangle", 0.5, 0.5, 1.0, 1.0),
    # Blue square drawn at bottom-left of the PNG → bottom-left UV quadrant.
    ("blue_square", 0.0, 0.0, 0.5, 0.5),
)


def main() -> None:
    if not ATLAS_PATH.exists():
        print(
            f"[build_shared_atlas] missing {ATLAS_PATH} — run draw_shared_atlas.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    for spec in SPRITES:
        _build_sprite_plane(spec, armature_obj)
    _save_blend()
    print(f"[build_shared_atlas] wrote {BLEND_PATH}")


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
    arm_data = bpy.data.armatures.new("shared_atlas.armature")
    arm_obj = bpy.data.objects.new("shared_atlas.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    # Bone tail along -Y (toward Front Ortho camera at +Y looking -Y).
    # Matches the Spine / 2D-cutout convention used by every other
    # procedural fixture; pre-fix this bone pointed +Z which made the
    # writer emit a -90deg-rotated bone in Godot, collapsing each
    # polygon to a degenerate line on import.
    bone = arm_data.edit_bones.new("root")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, -0.5, 0.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_plane(
    spec: tuple[str, float, float, float, float], armature_obj: bpy.types.Object
) -> bpy.types.Object:
    name, uv_x0, uv_y0, uv_x1, uv_y1 = spec
    slice_w_px = (uv_x1 - uv_x0) * ATLAS_W
    slice_h_px = (uv_y1 - uv_y0) * ATLAS_H
    w = slice_w_px / PIXELS_PER_UNIT
    h = slice_h_px / PIXELS_PER_UNIT

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
    uv.data[0].uv = (uv_x0, uv_y0)
    uv.data[1].uv = (uv_x1, uv_y0)
    uv.data[2].uv = (uv_x1, uv_y1)
    uv.data[3].uv = (uv_x0, uv_y1)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = armature_obj
    obj.parent_type = "BONE"
    obj.parent_bone = "root"

    mat = bpy.data.materials.new(name=f"{name}.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ATLAS_PATH), check_existing=True)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)

    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = "polygon"
    obj["proscenio_type"] = "polygon"
    return obj


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_shared_atlas] FAILED: {exc}", file=sys.stderr)
        raise
