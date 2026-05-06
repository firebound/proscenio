"""Build the blink_eyes test fixture from scratch (SPEC 007).

Run with::

    blender --background --python scripts/fixtures/build_blink_eyes.py

Idempotent: deletes the existing ``examples/blink_eyes/`` outputs and
rewrites them deterministically. Generates:

- ``layers/eye_0.png`` … ``eye_3.png`` — four frames of a blink animation,
  32×32 each. Frame 0 = eye open, 3 = eye closed.
- ``eye_spritesheet.png`` — concatenated 128×32 spritesheet (4 frames
  horizontal). This is the actual texture the sprite_frame mesh
  references; the per-frame PNGs are kept around so SPEC 006's
  ``<name>_<index>`` Photoshop convention can be tested by re-packing
  them into the sheet.
- ``blink_eyes.blend`` — 1 sprite_frame mesh (``eye``) + 1-bone
  armature + 1 action animating ``eye.proscenio.frame`` 0→1→2→3→2→1→0
  over 12 frames.

The fixture exercises the ``sprite_frame`` track path: a Blender action
that drives the frame-index property and the writer emitting a
``sprite_frame`` track in the resulting ``.proscenio``.

NOT a unit-tested module — a fixture builder. Re-run whenever the
fixture spec changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "examples" / "blink_eyes"
LAYERS_DIR = FIXTURE_DIR / "layers"
SHEET_PATH = FIXTURE_DIR / "eye_spritesheet.png"
BLEND_PATH = FIXTURE_DIR / "blink_eyes.blend"

FRAME_W = 32
FRAME_H = 32
HFRAMES = 4
VFRAMES = 1
SHEET_W = FRAME_W * HFRAMES
SHEET_H = FRAME_H * VFRAMES

PIXELS_PER_UNIT = 100.0

# (frame_index, eye_open_height_ratio) — height of the open part as a
# fraction of FRAME_H. 1.0 = fully open, 0.0 = fully closed.
FRAMES = (
    (0, 1.0),
    (1, 0.6),
    (2, 0.2),
    (3, 0.0),
)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _wipe_blend()
    _generate_frame_pngs()
    _generate_spritesheet_png()
    armature_obj = _build_armature()
    sprite_obj = _build_sprite_frame_plane(armature_obj)
    _build_blink_action(sprite_obj)
    _save_blend()
    print(f"[blink_eyes] wrote {BLEND_PATH}")
    print(f"[blink_eyes] wrote {len(FRAMES)} per-frame PNG(s) under {LAYERS_DIR}")
    print(f"[blink_eyes] wrote spritesheet {SHEET_PATH}")


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


def _eye_pixels(open_ratio: float) -> list[float]:
    """Return RGBA float buffer for a single 32x32 eye frame.

    White circle on transparent background; the eye "closes" by reducing
    the visible vertical extent — mimics a blink without external assets.
    """
    pixels = [0.0] * (FRAME_W * FRAME_H * 4)
    cx, cy = FRAME_W / 2.0, FRAME_H / 2.0
    radius = FRAME_W / 2.0 - 2
    open_h = (FRAME_H * open_ratio) / 2.0
    for y in range(FRAME_H):
        for x in range(FRAME_W):
            dx = x - cx
            dy = y - cy
            inside_circle = (dx * dx + dy * dy) <= (radius * radius)
            inside_open = abs(dy) <= open_h
            if inside_circle and inside_open:
                # White iris with a darker pupil center
                pupil = (dx * dx + dy * dy) <= (radius * radius * 0.15)
                rgb = (0.1, 0.1, 0.1) if pupil else (0.95, 0.95, 0.95)
                a = 1.0
            else:
                rgb = (0.0, 0.0, 0.0)
                a = 0.0
            i = (y * FRAME_W + x) * 4
            pixels[i : i + 4] = [rgb[0], rgb[1], rgb[2], a]
    return pixels


def _generate_frame_pngs() -> None:
    for idx, open_ratio in FRAMES:
        img = bpy.data.images.new(
            name=f"eye_{idx}",
            width=FRAME_W,
            height=FRAME_H,
            alpha=True,
        )
        img.pixels.foreach_set(_eye_pixels(open_ratio))
        out = LAYERS_DIR / f"eye_{idx}.png"
        img.filepath_raw = str(out)
        img.file_format = "PNG"
        img.save()


def _generate_spritesheet_png() -> None:
    """Concatenate the per-frame PNGs into a single 128x32 strip."""
    sheet = bpy.data.images.new(
        name="eye_spritesheet", width=SHEET_W, height=SHEET_H, alpha=True
    )
    pixels = [0.0] * (SHEET_W * SHEET_H * 4)
    for idx, open_ratio in FRAMES:
        frame = _eye_pixels(open_ratio)
        x_offset = idx * FRAME_W
        for y in range(FRAME_H):
            for x in range(FRAME_W):
                src = (y * FRAME_W + x) * 4
                dst = (y * SHEET_W + x_offset + x) * 4
                pixels[dst : dst + 4] = frame[src : src + 4]
    sheet.pixels.foreach_set(pixels)
    sheet.filepath_raw = str(SHEET_PATH)
    sheet.file_format = "PNG"
    sheet.save()


def _build_armature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("blink_eyes.armature")
    arm_obj = bpy.data.objects.new("blink_eyes.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("head")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, 0.5)
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

    # Material referencing the spritesheet, not the per-frame PNGs.
    mat = bpy.data.materials.new(name="eye.mat")
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

    # Tag as sprite_frame.
    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = "sprite_frame"
        obj.proscenio.hframes = HFRAMES
        obj.proscenio.vframes = VFRAMES
        obj.proscenio.frame = 0
        obj.proscenio.centered = True
    # Mirror to legacy CPs in case the PropertyGroup is not registered yet
    # (build script runs before the addon may be enabled in headless mode).
    obj["proscenio_type"] = "sprite_frame"
    obj["proscenio_hframes"] = HFRAMES
    obj["proscenio_vframes"] = VFRAMES
    obj["proscenio_frame"] = 0
    obj["proscenio_centered"] = True

    return obj


def _build_blink_action(sprite_obj: bpy.types.Object) -> None:
    """Animate ``eye.proscenio.frame`` through 0→1→2→3→2→1→0 over 12 frames."""
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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[blink_eyes] FAILED: {exc}", file=sys.stderr)
        raise
