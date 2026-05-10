"""Assemble mouth_drive.blend (manual fixture for Drive from Bone testing).

Run with::

    blender --background --python scripts/fixtures/mouth_drive/build_blend.py

Loads PNGs produced by ``draw_layers.py`` and builds:

- 1-bone armature ``mouth_rig`` with bone ``mouth_drive`` (Z-axis vertical
  in Blender world; rotating around X tilts head -- but driver tests
  typically use Z rotation in Blender 2D plane).
- 1 sprite_frame mesh ``mouth`` referencing ``mouth_spritesheet.png`` with
  ``hframes=4``, ``vframes=1``. Plane parented to the bone.

Note: driver from bone -> ``mouth.proscenio.frame`` is **NOT installed**
here. The fixture's purpose is to give the user a ready cena to exercise
the ``Drive from Bone`` operator manually -- selecting the mouth + bone,
clicking the panel button, and validating that the driver gets created
and responds to bone rotation.

Image filepath is stored as a Blender relative path (``//pillow_layers/...``)
so the .blend works cross-machine.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "mouth_drive"
SHEET_PATH = FIXTURE_DIR / "pillow_layers" / "mouth_spritesheet.png"
BLEND_PATH = FIXTURE_DIR / "mouth_drive.blend"

FRAME_W = 32
FRAME_H = 32
HFRAMES = 4
VFRAMES = 1
PIXELS_PER_UNIT = 100.0


def main() -> None:
    if not SHEET_PATH.exists():
        print(
            f"[build_mouth_drive] missing {SHEET_PATH} -- run draw_layers.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    _build_sprite_frame_plane(armature_obj)
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
    arm_data = bpy.data.armatures.new("mouth_rig")
    arm_obj = bpy.data.objects.new("mouth_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("mouth_drive")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, 0.5)
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
    obj.parent_bone = "mouth_drive"

    mat = bpy.data.materials.new(name="mouth.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(SHEET_PATH), check_existing=True)
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


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_image_to_relpath() -> None:
    """After save_as, rewrite image filepath to ``//pillow_layers/...``.

    Blender's ``bpy.path.relpath`` needs the .blend to already be saved
    so its filepath can serve as the base. The first save_as sets that
    base; we then rewrite + save again. Mirrors what ``Make Paths
    Relative`` does in the File menu, but scoped to this image only.
    """
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
