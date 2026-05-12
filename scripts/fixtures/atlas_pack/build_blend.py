"""Assemble the atlas_pack .blend (SPEC 007 / SPEC 005.1.c workbench).

Run with::

    blender --background --python scripts/fixtures/atlas_pack/build_blend.py

Loads 9 PNGs produced by ``draw_layers.py`` from disk and builds:

- 1-bone armature (``root``).
- 9 sprite quad meshes (``sprite_1`` .. ``sprite_9``), each parented to
  ``root`` bone, arranged in a 3x3 grid.
- 9 materials (one per sprite), each with its own Image Texture node
  pointing at the matching ``pillow_layers/sprite_N.png``. Each mesh's
  UVs span 0..1 across its own texture.
- No actions. The fixture exists to exercise the Atlas Pack / Apply /
  Unpack flow, not animation.

Run ``draw_layers.py`` first or this script aborts on missing PNGs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "atlas_pack"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
BLEND_PATH = FIXTURE_DIR / "atlas_pack.blend"

FRAME_W = 32
FRAME_H = 32
PIXELS_PER_UNIT = 100.0
GRID_COLS = 3
GRID_ROWS = 3
SPRITE_COUNT = GRID_COLS * GRID_ROWS
GRID_SPACING = 0.40  # world units between sprite centers


def main() -> None:
    missing = [
        LAYERS_DIR / f"sprite_{i + 1}.png"
        for i in range(SPRITE_COUNT)
        if not (LAYERS_DIR / f"sprite_{i + 1}.png").exists()
    ]
    if missing:
        names = ", ".join(str(p.name) for p in missing)
        print(
            f"[build_atlas_pack] missing PNG(s): {names} - run draw_layers.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    for idx in range(SPRITE_COUNT):
        _build_sprite_quad(idx, armature_obj)
    _save_blend()
    _rewrite_image_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_atlas_pack] wrote {BLEND_PATH}")


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
    arm_data = bpy.data.armatures.new("atlas_pack.armature")
    arm_obj = bpy.data.objects.new("atlas_pack.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("root")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, -0.5, 0.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_quad(idx: int, armature_obj: bpy.types.Object) -> bpy.types.Object:
    """Build sprite_<idx+1>: own mesh + UVs + material + Image Texture."""
    sprite_id = idx + 1
    name = f"sprite_{sprite_id}"
    png_path = LAYERS_DIR / f"{name}.png"

    col = idx % GRID_COLS
    row = idx // GRID_COLS
    # Center the grid around world origin. cx is inverted (col=0 -> +X
    # world) so sprite_1..9 read left-to-right on screen in Blender's
    # Front Orthographic view (where world +X maps to screen LEFT,
    # matching the UV flip in _build_sprite_quad).
    cx = ((GRID_COLS - 1) / 2.0 - col) * GRID_SPACING
    cz = ((GRID_ROWS - 1) / 2.0 - row) * GRID_SPACING

    w = FRAME_W / PIXELS_PER_UNIT
    h = FRAME_H / PIXELS_PER_UNIT
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
    # UVs flipped on U so the PIL image appears unmirrored in Blender's
    # Front Orthographic view (world +X maps to screen LEFT in this
    # convention; without the flip, the texture renders mirrored, which
    # is invisible on symmetric sprites like blink_eyes but obvious on
    # asymmetric content like the atlas_pack digits).
    uv.data[0].uv = (1.0, 0.0)
    uv.data[1].uv = (0.0, 0.0)
    uv.data[2].uv = (0.0, 1.0)
    uv.data[3].uv = (1.0, 1.0)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (cx, 0.0, cz)
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
    tex.image = bpy.data.images.load(str(png_path), check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)

    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = "polygon"
        obj.proscenio.centered = True
    obj["proscenio_type"] = "polygon"
    obj["proscenio_centered"] = True
    return obj


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_image_to_relpath() -> None:
    """After save_as, rewrite every image filepath to ``//pillow_layers/...``.

    Without this the absolute path of the dev's working copy bakes into
    the .blend and the fixture breaks on any other machine.
    """
    for img in bpy.data.images:
        if not img.filepath:
            continue
        try:
            img.filepath = bpy.path.relpath(img.filepath)
        except ValueError:
            # Different drive on Windows - leave the absolute path.
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_atlas_pack] FAILED: {exc}", file=sys.stderr)
        raise
