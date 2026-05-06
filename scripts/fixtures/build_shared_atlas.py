"""Build the shared_atlas test fixture from scratch (SPEC 007 step 2).

Run with::

    blender --background --python scripts/fixtures/build_shared_atlas.py

Idempotent: deletes the existing ``examples/shared_atlas/`` outputs and
rewrites them deterministically. Generates:

- ``atlas.png`` (256×256) — three colored shapes drawn into different
  quadrants. The fourth quadrant is transparent (so the slicing logic
  has something to ignore).
- ``shared_atlas.blend`` — three polygon meshes, each with UV bounds
  covering exactly one shape's quadrant of the shared atlas.

Tests the **sliced atlas packer** (SPEC 005.1.c.2.1): when Pack Atlas
runs over this scene, it must extract each sprite's slice (just its
shape's quadrant, not the whole atlas) into the new packed atlas. The
golden ``.proscenio`` captures the per-sprite ``texture_region`` /
UV layout so any regression in slicing surfaces in CI as a diff.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import Canvas, circle, fill, rect, save_as_png, triangle  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "examples" / "shared_atlas"
ATLAS_PATH = FIXTURE_DIR / "atlas.png"
BLEND_PATH = FIXTURE_DIR / "shared_atlas.blend"

ATLAS_W = 256
ATLAS_H = 256
QUAD = 128  # quadrant size
PIXELS_PER_UNIT = 100.0

# Background tint so the sliced areas are visually distinct from
# transparent padding the packer produces.
BACKGROUND = (0.07, 0.07, 0.07, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)
RED = (0.85, 0.20, 0.20, 1.0)
GREEN = (0.20, 0.75, 0.30, 1.0)
BLUE = (0.20, 0.40, 0.85, 1.0)

# (sprite_name, uv_min_x, uv_min_y, uv_max_x, uv_max_y, color, shape_kind)
# UVs are in [0,1] of atlas, bottom-up. Each sprite covers one quadrant
# minus a small inset to keep the slice math non-trivial.
SPRITES = (
    ("red_circle", 0.0, 0.5, 0.5, 1.0, RED, "circle"),
    ("green_triangle", 0.5, 0.5, 1.0, 1.0, GREEN, "triangle"),
    ("blue_square", 0.0, 0.0, 0.5, 0.5, BLUE, "square"),
)


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    _wipe_blend()
    _generate_atlas()
    armature_obj = _build_armature()
    for spec in SPRITES:
        _build_sprite_plane(spec, armature_obj)
    _save_blend()
    print(f"[shared_atlas] wrote {ATLAS_PATH}")
    print(f"[shared_atlas] wrote {BLEND_PATH}")


def _wipe_blend() -> None:
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


def _generate_atlas() -> None:
    canvas = Canvas.empty(ATLAS_W, ATLAS_H)
    fill(canvas, TRANSPARENT)

    # red circle in top-left quadrant
    circle(canvas, QUAD * 0.5, ATLAS_H - QUAD * 0.5, QUAD * 0.4, RED)
    # green triangle in top-right quadrant
    triangle(
        canvas,
        (QUAD + QUAD * 0.5, ATLAS_H - QUAD * 0.9),
        (QUAD + QUAD * 0.1, ATLAS_H - QUAD * 0.1),
        (QUAD + QUAD * 0.9, ATLAS_H - QUAD * 0.1),
        GREEN,
    )
    # blue square in bottom-left quadrant
    rect(canvas, int(QUAD * 0.2), int(QUAD * 0.2), int(QUAD * 0.6), int(QUAD * 0.6), BLUE)

    save_as_png(canvas, "atlas", ATLAS_PATH)


def _build_armature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("shared_atlas.armature")
    arm_obj = bpy.data.objects.new("shared_atlas.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("root")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, 0.5)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_plane(spec: tuple, armature_obj: bpy.types.Object) -> bpy.types.Object:
    name, uv_x0, uv_y0, uv_x1, uv_y1, _color, _shape = spec
    # The plane size matches the slice in world units (slice px / ppu).
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

    # UVs cover only this sprite's quadrant of the shared atlas.
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
        print(f"[shared_atlas] FAILED: {exc}", file=sys.stderr)
        raise
