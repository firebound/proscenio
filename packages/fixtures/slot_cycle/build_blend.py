"""Assemble slot_cycle.blend.

Run with::

    blender --background --python packages/fixtures/slot_cycle/build_blend.py

Builds the smallest possible slot fixture:

- 1-bone armature ``slot_cycle.armature`` (single ``root`` bone).
- 1 slot Empty ``cycle.slot`` parented to the bone, ``is_slot=True``.
- 3 polygon meshes (red / green / blue) parented to the Empty as
  attachments. Each is a 32x32 quad weight-mapped to the root bone.
- ``slot_default = "attachment_red"`` - red shows at scene load.
- One slotted action ``cycle`` (Blender 4.4+) shared by the three
  attachment meshes on their own slots, keyframing each mesh's
  ``hide_render`` + ``hide_viewport`` so exactly one shows per second
  (the writer collapses them into one ``slot_attachment`` track).

Run ``draw_layers.py`` first or the textures will be missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from blend_utils import rewrite_images_to_relpath  # noqa: E402
from slot_keying import key_show_only  # noqa: E402

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
                f"[build_slot_cycle] missing {name}.png - run draw_layers.py first",
                file=sys.stderr,
            )
            sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    slot_empty = _build_slot_empty(armature_obj)
    meshes = [_build_attachment_mesh(name, slot_empty) for name in ATTACHMENT_NAMES]
    _build_cycle_visibility(meshes)
    _save_blend()
    rewrite_images_to_relpath("[build_slot_cycle]")
    bpy.ops.wm.save_mainfile()
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
    of the screen plane. This matches the doll fixture pattern - bone
    binding via vertex groups, not via parent_type='BONE'. Slot's
    ``bone`` field falls out empty in the writer's output.
    """
    empty = bpy.data.objects.new("cycle.slot", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = armature_obj
    empty.parent_type = "OBJECT"
    # Custom Property fallback so the headless writer (CI) detects the
    # slot without the addon's PropertyGroup registered (the PG-canonical
    # / CP-fallback contract).
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
    # Object-parented under the slot Empty - NOT skinned. A slot attachment must
    # stay a child of the slot so the slot_attachment track can toggle its
    # visibility; a skinned mesh is re-parented as a sibling of the Skeleton2D
    # and leaves the slot, breaking the cycle/swap animation. The slot itself
    # follows a bone via its `bone` field, not the attachments.
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


def _build_cycle_visibility(meshes: list[bpy.types.Object]) -> None:
    """Author a ``cycle`` action keying attachment visibility once per second.

    The writer's ``build_slot_animations`` walker reads each attachment mesh's
    ``hide_render`` keyframes (scoped to its own slot of the shared action) and
    collapses them into one exclusive ``slot_attachment`` track; the Godot
    importer then expands that into N per-attachment visibility tracks. Show-only
    per frame: blue -> green -> red -> blue, so exactly one shows at a time -
    the same per-mesh state the ``keyframe_slot_attachment`` operator authors.
    """
    action = bpy.data.actions.new(name="cycle")
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    sequence = (
        (1, "attachment_blue"),
        (8, "attachment_green"),
        (16, "attachment_red"),
        (24, "attachment_blue"),
    )
    for frame, chosen in sequence:
        bpy.context.scene.frame_set(frame)
        for mesh in meshes:
            key_show_only(mesh, action, visible=mesh.name == chosen, frame=frame)


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_slot_cycle] FAILED: {exc}", file=sys.stderr)
        raise
