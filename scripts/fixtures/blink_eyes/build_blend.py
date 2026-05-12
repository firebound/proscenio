"""Assemble the blink_eyes .blend (SPEC 007 step 1, Blender side).

Run with::

    blender --background --python scripts/fixtures/build_blink_eyes.py

Loads PNGs produced by ``draw_blink_eyes.py`` from disk and builds:

- 1-bone armature (`head`)
- 1 sprite_frame mesh (`eye`) referencing ``eye_spritesheet.png`` with
  ``hframes=4``, ``vframes=1``
- 1 action `blink` animating ``proscenio.frame`` 0→1→2→3→2→1→0 over
  12 frames

Run ``draw_blink_eyes.py`` first or this script aborts on missing PNGs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "blink_eyes"
SHEET_PATH = FIXTURE_DIR / "pillow_layers" / "eye_spritesheet.png"
BLEND_PATH = FIXTURE_DIR / "blink_eyes.blend"

FRAME_W = 32
FRAME_H = 32
HFRAMES = 4
VFRAMES = 1
PIXELS_PER_UNIT = 100.0


def main() -> None:
    if not SHEET_PATH.exists():
        print(
            f"[build_blink_eyes] missing {SHEET_PATH} -- run draw_blink_eyes.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    _build_sprite_frame_plane(armature_obj)
    _build_blink_action()
    _save_blend()
    _rewrite_image_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_blink_eyes] wrote {BLEND_PATH}")


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
    arm_data = bpy.data.armatures.new("blink_eyes.armature")
    arm_obj = bpy.data.objects.new("blink_eyes.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    # Bone perpendicular to the XZ picture plane, pointing TOWARD the
    # camera (Front Ortho looks along world -Y, so tail at -Y means the
    # bone points at the viewer). Spine / 2D-cutout convention --
    # bones appear as small octahedral dots from the front.
    bone = arm_data.edit_bones.new("head")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, -0.5, 0.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_frame_plane(armature_obj: bpy.types.Object) -> bpy.types.Object:
    w = FRAME_W / PIXELS_PER_UNIT
    h = FRAME_H / PIXELS_PER_UNIT
    mesh = bpy.data.meshes.new("eye")
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

    obj = bpy.data.objects.new("eye", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = armature_obj
    obj.parent_type = "BONE"
    obj.parent_bone = "head"

    mat = bpy.data.materials.new(name="eye.mat")
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


def _build_blink_action() -> None:
    sprite_obj = bpy.data.objects.get("eye")
    if sprite_obj is None:
        return
    sprite_obj.animation_data_create()
    action = bpy.data.actions.new(name="blink")
    sprite_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 12

    sequence = (
        (1, 0),
        (3, 1),
        (5, 2),
        (7, 3),
        (9, 2),
        (11, 1),
        (12, 0),
    )
    for frame, value in sequence:
        bpy.context.scene.frame_set(frame)
        if hasattr(sprite_obj, "proscenio"):
            sprite_obj.proscenio.frame = value
            sprite_obj.proscenio.keyframe_insert(data_path="frame", frame=frame)
        else:
            sprite_obj["proscenio_frame"] = value
            sprite_obj.keyframe_insert(data_path='["proscenio_frame"]', frame=frame)


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_image_to_relpath() -> None:
    """After save_as, rewrite image filepath to ``//pillow_layers/...``.

    ``bpy.path.relpath`` needs the .blend to already be on disk so its
    filepath can serve as the base; the first ``save_as`` sets that
    base, this helper rewrites + the caller saves again. Cross-machine
    safe (the previous absolute path baked the dev's local repo root
    into the .blend, breaking on any other machine).
    """
    rel = bpy.path.relpath(str(SHEET_PATH))
    for img in bpy.data.images:
        if img.filepath:
            img.filepath = rel


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_blink_eyes] FAILED: {exc}", file=sys.stderr)
        raise
