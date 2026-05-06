"""Build the blink_eyes test fixture from scratch (SPEC 007 step 1).

Run with::

    blender --background --python scripts/fixtures/build_blink_eyes.py

Idempotent: deletes the existing ``examples/blink_eyes/`` outputs and
rewrites them deterministically. Generates:

- ``layers/eye_0.png`` … ``eye_3.png`` — four 32×32 frames (open / partial /
  nearly closed / closed). The ``<name>_<index>`` naming matches SPEC 007
  D4 so SPEC 006's PS importer can later regroup them automatically.
- ``eye_spritesheet.png`` — the 128×32 strip that the sprite_frame mesh
  actually references at runtime.
- ``blink_eyes.blend`` — 1 sprite_frame mesh + 1-bone armature + 1 action
  animating ``proscenio.frame`` 0→1→2→3→2→1→0 over 12 frames.

Tests the ``sprite_frame`` end-to-end path: writer must emit a
``sprite_frame`` track for the action; importer must consume it.

NOT a unit-tested module — a fixture builder. Re-run whenever the
fixture spec changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import Canvas, circle, save_as_png  # noqa: E402

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

WHITE = (0.95, 0.95, 0.95, 1.0)
PUPIL = (0.10, 0.10, 0.10, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)

# (frame_index, eye_open_height_ratio) — 1.0 fully open, 0.0 fully closed.
FRAMES = (
    (0, 1.0),
    (1, 0.6),
    (2, 0.2),
    (3, 0.0),
)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _wipe_blend()
    _generate_per_frame_pngs()
    _generate_spritesheet()
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


def _draw_eye_frame(canvas: Canvas, open_ratio: float) -> None:
    """Stamp a single eye frame onto ``canvas`` — white iris + dark pupil, vertically clipped by ``open_ratio``."""
    cx = canvas.width / 2.0
    cy = canvas.height / 2.0
    iris_r = canvas.width / 2.0 - 2
    pupil_r = iris_r * 0.4
    open_h = (canvas.height * open_ratio) / 2.0
    circle(canvas, cx, cy, iris_r, WHITE)
    circle(canvas, cx, cy, pupil_r, PUPIL)
    if open_h < canvas.height / 2.0:
        for y in range(canvas.height):
            if abs(y + 0.5 - cy) > open_h:
                for x in range(canvas.width):
                    canvas.set(x, y, TRANSPARENT)


def _generate_per_frame_pngs() -> None:
    for idx, open_ratio in FRAMES:
        canvas = Canvas.empty(FRAME_W, FRAME_H)
        _draw_eye_frame(canvas, open_ratio)
        save_as_png(canvas, f"eye_{idx}", LAYERS_DIR / f"eye_{idx}.png")


def _generate_spritesheet() -> None:
    canvas = Canvas.empty(SHEET_W, SHEET_H)
    for idx, open_ratio in FRAMES:
        sub = Canvas.empty(FRAME_W, FRAME_H)
        _draw_eye_frame(sub, open_ratio)
        x_offset = idx * FRAME_W
        for y in range(FRAME_H):
            for x in range(FRAME_W):
                src = (y * FRAME_W + x) * 4
                dst = (y * SHEET_W + x_offset + x) * 4
                canvas.pixels[dst : dst + 4] = sub.pixels[src : src + 4]
    save_as_png(canvas, "eye_spritesheet", SHEET_PATH)


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
