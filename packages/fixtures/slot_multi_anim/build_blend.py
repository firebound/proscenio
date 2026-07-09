"""Assemble slot_multi_anim.blend (per-animation slot swaps, spec 079 core).

Run with::

    blender --background --python packages/fixtures/slot_multi_anim/build_blend.py

Builds a slot system fixture that carries a DIFFERENT attachment-visibility
timeline per animation - the case single-active-action reading could not
express. One slot Empty owns two attachments (``club``, ``torch``) and the
blend holds TWO animations authored on the Blender 4.4+ slotted-action model:

- ``idle``   - both attachments hidden -> the writer collapses to "(none)".
- ``attack`` - ``club`` shown, ``torch`` hidden, plus a gentle arm swing so the
  animation also carries a ``bone_transform`` track (proving the slot track
  merges onto the bone animation of the same name).

Each mesh's visibility co-locates with the animation it belongs to: on 4.4+ the
attachment binds ``animation_data.action`` to that animation's action datablock
on its own slot, so ``club`` holds a channelbag in BOTH ``idle`` and ``attack``
even though only one is its active binding. The writer scans every action and
matches each mesh's slot by identity, so it recovers both timelines.

Layout mirrors ``slot_swap`` (one lateral ``arm`` bone in the XZ picture plane,
the arm mesh skinned to it, the slot Empty object-parented at the bone tip and
bound to the bone via the Proscenio Slot Follow constraint). Image filepaths are
stored ``//``-relative so the committed .blend is machine-independent.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from blend_utils import rewrite_images_to_relpath  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "slot_multi_anim"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
ARM_PATH = LAYERS_DIR / "arm.png"
CLUB_PATH = LAYERS_DIR / "club.png"
TORCH_PATH = LAYERS_DIR / "torch.png"
BLEND_PATH = FIXTURE_DIR / "slot_multi_anim.blend"

PIXELS_PER_UNIT = 100.0

ARM_W_PX = 32
ARM_H_PX = 8
WEAPON_W_PX = 32
WEAPON_H_PX = 32

ARM_BONE = "arm"
SLOT_NAME = "weapon"


def main() -> None:
    for path in (ARM_PATH, CLUB_PATH, TORCH_PATH):
        if not path.exists():
            print(
                f"[build_slot_multi_anim] missing {path} - run draw_layers.py first",
                file=sys.stderr,
            )
            sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    _build_arm_mesh(armature_obj)
    slot_empty = _build_slot_empty(armature_obj)
    club_obj = _build_attachment(
        "club", CLUB_PATH, slot_empty, is_default=True, draw_order=-1
    )
    torch_obj = _build_attachment(
        "torch", TORCH_PATH, slot_empty, is_default=False, draw_order=-2
    )
    _build_animations(armature_obj, club_obj, torch_obj)
    _save_blend()
    rewrite_images_to_relpath("[build_slot_multi_anim]")
    bpy.ops.wm.save_mainfile()
    print(f"[build_slot_multi_anim] wrote {BLEND_PATH}")


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
    """Single lateral arm bone, in the XZ picture plane (+X, never into depth)."""
    arm_data = bpy.data.armatures.new("arm_rig")
    arm_obj = bpy.data.objects.new("arm_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new(ARM_BONE)
    bone.head = (0.0, 0.0, 0.0)
    bone.tail = (0.32, 0.0, 0.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _quad_mesh(name: str, w_px: int, h_px: int) -> bpy.types.Mesh:
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
    uv = mesh.uv_layers.new(name="UVMap")
    uv.data[0].uv = (0.0, 0.0)
    uv.data[1].uv = (1.0, 0.0)
    uv.data[2].uv = (1.0, 1.0)
    uv.data[3].uv = (0.0, 1.0)
    return mesh


def _build_material(name: str, image_path: Path) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(image_path), check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _stamp_polygon_props(obj: bpy.types.Object) -> None:
    obj["proscenio_type"] = "mesh"
    obj["proscenio_centered"] = True


def _build_arm_mesh(armature_obj: bpy.types.Object) -> bpy.types.Object:
    mesh = _quad_mesh("arm", ARM_W_PX, ARM_H_PX)
    obj = bpy.data.objects.new("arm", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (0.16, 0.0, 0.0)
    obj.parent = armature_obj
    obj.parent_type = "OBJECT"
    vg = obj.vertex_groups.new(name=ARM_BONE)
    vg.add([v.index for v in mesh.vertices], 1.0, "REPLACE")
    arm_mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    arm_mod.object = armature_obj
    mat = _build_material("arm.mat", ARM_PATH)
    mesh.materials.append(mat)
    _stamp_polygon_props(obj)
    return obj


def _build_slot_empty(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """Empty at the hand, flagged as a slot that follows the arm bone."""
    empty = bpy.data.objects.new(SLOT_NAME, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = armature_obj
    empty.parent_type = "OBJECT"
    empty.location = (0.32, 0.0, 0.0)
    empty["proscenio_is_slot"] = True
    empty["proscenio_slot_default"] = "club"
    empty["proscenio_slot_bone"] = ARM_BONE
    con = empty.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Slot Follow"
    con.target = armature_obj
    con.subtarget = ARM_BONE
    bpy.context.view_layer.update()
    pose_bone = armature_obj.pose.bones[ARM_BONE]
    con.inverse_matrix = (armature_obj.matrix_world @ pose_bone.matrix).inverted()
    return empty


def _build_attachment(
    name: str,
    image_path: Path,
    slot_empty: bpy.types.Object,
    *,
    is_default: bool,
    draw_order: int,
) -> bpy.types.Object:
    """Polygon mesh attachment parented to the slot Empty."""
    mesh = _quad_mesh(name, WEAPON_W_PX, WEAPON_H_PX)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = slot_empty
    obj.parent_type = "OBJECT"
    obj.location = (0.0, draw_order * 0.001, 0.0)
    obj["proscenio_y_draw_order"] = draw_order
    mat = _build_material(f"{name}.mat", image_path)
    mesh.materials.append(mat)
    _stamp_polygon_props(obj)
    if not is_default:
        obj.hide_viewport = True
        obj.hide_render = True
    return obj


def _build_animations(
    armature_obj: bpy.types.Object,
    club: bpy.types.Object,
    torch: bpy.types.Object,
) -> None:
    """Author the two animations - ``idle`` (none) and ``attack`` (club + swing).

    ``idle`` keys both attachments hidden (no bone motion); ``attack`` keys the
    club shown, the torch hidden, and a gentle arm swing. On Blender 4.4+ every
    datablock keyed under an animation binds that animation's action on its own
    slot, so ``club`` / ``torch`` each hold a channelbag in BOTH actions even
    though their active binding ends on ``attack``.
    """
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 12

    idle = bpy.data.actions.new(name="idle")
    for mesh in (club, torch):
        _key_show_only(mesh, idle, visible=False, frame=1)
        _key_show_only(mesh, idle, visible=False, frame=12)

    attack = bpy.data.actions.new(name="attack")
    _key_arm_swing(armature_obj, attack)
    for mesh in (club, torch):
        _key_show_only(mesh, attack, visible=mesh.name == "club", frame=1)
        _key_show_only(mesh, attack, visible=mesh.name == "club", frame=12)

    # Each attachment ends actively bound to `attack`, so `idle` has no active
    # user and Blender would purge it as orphan data on save (losing the whole
    # idle timeline). A fake user keeps every animation datablock alive - the
    # writer scans them all by slot identity, not by active binding. `attack`
    # gets one too so both animations round-trip identically through save/reopen.
    for action in (idle, attack):
        action.use_fake_user = True


def _key_arm_swing(armature_obj: bpy.types.Object, action: bpy.types.Action) -> None:
    """Gentle world-Y rotation of the arm bone over frames 1..12 on ``action``."""
    armature_obj.animation_data_create()
    armature_obj.animation_data.action = action
    arm_pose = armature_obj.pose.bones[ARM_BONE]
    arm_pose.rotation_mode = "XYZ"
    rest = arm_pose.bone.matrix_local
    rest_inv = rest.inverted()
    for frame, value in ((1, -math.pi / 12), (12, math.pi / 12)):
        bpy.context.scene.frame_set(frame)
        arm_pose.matrix_basis = rest_inv @ Matrix.Rotation(value, 4, "Y") @ rest
        arm_pose.keyframe_insert(data_path="rotation_euler", frame=frame)


def _key_show_only(
    mesh: bpy.types.Object,
    action: bpy.types.Action,
    *,
    visible: bool,
    frame: int,
) -> None:
    """Bind ``mesh`` to ``action`` and hard-cut-key its visibility at ``frame``."""
    mesh.animation_data_create()
    if mesh.animation_data.action is not action:
        mesh.animation_data.action = action
    mesh.hide_viewport = not visible
    mesh.hide_render = not visible
    mesh.keyframe_insert(data_path="hide_viewport", frame=frame)
    mesh.keyframe_insert(data_path="hide_render", frame=frame)
    for fcurve in _object_fcurves_in_action(mesh, action):
        if fcurve.data_path in ("hide_render", "hide_viewport"):
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "CONSTANT"
            fcurve.update()


def _object_fcurves_in_action(
    obj: bpy.types.Object, action: bpy.types.Action
) -> list[bpy.types.FCurve]:
    """The fcurves ``obj`` owns within ``action`` (its slot channelbag on 4.4+)."""
    flat = getattr(action, "fcurves", None)
    if flat:
        return list(flat)
    anim = obj.animation_data
    slot = getattr(anim, "action_slot", None)
    handle = getattr(slot, "handle", None) if slot is not None else None
    out: list[bpy.types.FCurve] = []
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                if (
                    handle is not None
                    and getattr(channelbag, "slot_handle", None) != handle
                ):
                    continue
                out.extend(channelbag.fcurves)
    return out


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_slot_multi_anim] FAILED: {exc}", file=sys.stderr)
        raise
