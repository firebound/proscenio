"""Assemble slot_cycle.blend (SPEC 004 Wave 4.3).

Run with::

    blender --background --python scripts/fixtures/slot_cycle/build_blend.py

Builds the smallest possible slot fixture:

- 1-bone armature ``slot_cycle.armature`` (single ``root`` bone).
- 1 slot Empty ``cycle.slot`` parented to the bone, ``is_slot=True``.
- 3 polygon meshes (red / green / blue) parented to the Empty as
  attachments. Each is a 32x32 quad weight-mapped to the root bone.
- ``slot_default = "attachment_red"`` -- red shows at scene load.
- An action ``cycle`` keyframing each attachment per second
  (Wave 4.2 imports as one visibility track per attachment in Godot).

Run ``draw_layers.py`` first or the textures will be missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "slot_cycle"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
BLEND_PATH = FIXTURE_DIR / "slot_cycle.blend"

PIXELS_PER_UNIT = 100.0
QUAD_SIZE_PX = 32

ATTACHMENT_NAMES: tuple[str, ...] = (
    "attachment_red",
    "attachment_green",
    "attachment_blue",
)


def main() -> None:
    for name in ATTACHMENT_NAMES:
        if not (LAYERS_DIR / f"{name}.png").exists():
            print(
                f"[build_slot_cycle] missing {name}.png -- run draw_layers.py first",
                file=sys.stderr,
            )
            sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    slot_empty = _build_slot_empty(armature_obj)
    for name in ATTACHMENT_NAMES:
        _build_attachment_mesh(name, slot_empty)
    _build_cycle_action(slot_empty)
    _save_blend()
    print(f"[build_slot_cycle] wrote {BLEND_PATH}")


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
    arm_data = bpy.data.armatures.new("slot_cycle.armature")
    arm_obj = bpy.data.objects.new("slot_cycle.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("root")
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.0, 0.0, 0.5)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_slot_empty(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """Build the slot anchor Empty.

    Parented to the armature object via ``parent_type='OBJECT'`` (NOT
    ``BONE``). Bone-parenting rotates child meshes to align with the
    bone's local Y axis, which would tilt our XZ-plane attachments out
    of the screen plane. This matches the doll fixture pattern -- bone
    binding via vertex groups, not via parent_type='BONE'. Slot's
    ``bone`` field falls out empty in the writer's output.
    """
    empty = bpy.data.objects.new("cycle.slot", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = armature_obj
    empty.parent_type = "OBJECT"
    if hasattr(empty, "proscenio"):
        empty.proscenio.is_slot = True
        empty.proscenio.slot_default = ATTACHMENT_NAMES[0]
    # Also write Custom Property fallback so headless writer (CI) detects
    # the slot without relying on the addon's PropertyGroup being
    # registered. Mirrors the proscenio_<field> pattern used by sprite
    # meshes (SPEC 005 PG-canonical / CP-fallback contract).
    empty["proscenio_is_slot"] = True
    empty["proscenio_slot_default"] = ATTACHMENT_NAMES[0]
    return empty


def _build_attachment_mesh(name: str, slot_empty: bpy.types.Object) -> bpy.types.Object:
    half = (QUAD_SIZE_PX / PIXELS_PER_UNIT) / 2.0
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        vertices=[
            (-half, 0.0, -half),
            (half, 0.0, -half),
            (half, 0.0, half),
            (-half, 0.0, half),
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

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = slot_empty
    obj.parent_type = "OBJECT"

    mat = bpy.data.materials.new(name=f"{name}.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(
        str(LAYERS_DIR / f"{name}.png"),
        check_existing=True,
    )
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)
    return obj


def _build_cycle_action(slot_empty: bpy.types.Object) -> None:
    """Author a ``cycle`` action keyframing ``proscenio_slot_index``.

    The writer's ``_build_slot_animations`` walker reads this Custom
    Property fcurve and projects each int value to the matching slot
    attachment name; the Godot importer then expands the resulting
    ``slot_attachment`` track into N visibility tracks. Custom-property
    keyframing works without the addon's PropertyGroup being registered,
    so this path is robust to headless contexts (CI runs Blender with
    no addon enabled).
    """
    slot_empty.animation_data_create()
    action = bpy.data.actions.new(name="cycle")
    slot_empty.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    sequence = (
        (1, 0),
        (8, 1),
        (16, 2),
        (24, 0),
    )
    for frame, idx in sequence:
        bpy.context.scene.frame_set(frame)
        slot_empty["proscenio_slot_index"] = idx
        slot_empty.keyframe_insert(data_path='["proscenio_slot_index"]', frame=frame)


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_slot_cycle] FAILED: {exc}", file=sys.stderr)
        raise
