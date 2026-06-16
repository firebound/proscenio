"""Assemble mixed_feature.blend - the end-to-end feature-stack fixture.

Run with::

    blender --background --python packages/fixtures/mixed_feature/build_blend.py

Stacks every Blender-to-Godot feature into one rig so the golden catches
interactions a single-feature fixture cannot:

- **Armature** ``mixed_rig`` with five flat bones in the XZ picture plane
  (the 2D-cutout convention), chained ``root`` -> ``spine`` -> ``head`` ->
  {``mouth``, ``jaw``}: ``root`` / ``spine`` skin the body and ``spine``
  bobs it (carrying the head, face slot, mouth and jaw with it through the
  chain), ``head`` carries the face slot, ``mouth`` (+X, upright) anchors
  the mouth sprite, ``jaw`` drives the mouth frame.
- **Skinned body** ``body`` - a 2-face polygon weighted across ``root``
  (lower) and ``spine`` (upper), so the export carries per-bone weights
  and the per-face ``polygons`` index arrays.
- **sprite_frame mouth** ``mouth`` - a 4-frame Sprite2D skinned to the
  ``mouth`` bone, its cell driven from ``jaw`` rotation.
- **Drive-from-Bone** - a scripted driver on ``mouth.proscenio.frame``
  reading the ``jaw`` spin (ROT_Z for the +Z bone).
- **Slot with mixed attachments** ``face.slot`` - one mesh attachment
  (``face_neutral``) and one sprite attachment (``face_glow``), default
  ``face_neutral``.
- **Packed atlas** - every element shares one ``atlas.png`` via UV bounds
  (meshes) or a manual region (sprites), so the export emits a single
  top-level ``atlas`` plus per-element regions.
- **One animation** ``mixed_anim`` keying ``jaw`` rotation, which bakes
  into a ``bone_transform`` track plus the driven ``sprite_frame`` track.

Run ``draw_layers.py`` first or this script aborts on the missing atlas.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = (
    REPO_ROOT / "examples" / "generated" / "blender_to_godot" / "mixed_feature"
)
ATLAS_PATH = FIXTURE_DIR / "atlas.png"
BLEND_PATH = FIXTURE_DIR / "mixed_feature.blend"

PIXELS_PER_UNIT = 100.0

# Manual atlas regions for the two sprite strips, in the top-down normalized
# convention the importer expects ([x, y, w, h], y=0 at the PNG top).
MOUTH_REGION = (0.0, 0.0, 0.25, 0.25)  # top-left 32x32 = 2x2 grid of 16px frames
GLOW_REGION = (0.5, 0.0, 0.5, 0.5)  # top-right quadrant, single glow face


def main() -> None:
    if not ATLAS_PATH.exists():
        print(
            f"[build_mixed_feature] missing {ATLAS_PATH} - run draw_layers.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    _build_skinned_body(armature_obj)
    mouth_obj = _build_mouth(armature_obj)
    _install_mouth_driver(mouth_obj, armature_obj)
    _build_slot(armature_obj)
    _build_action(armature_obj)
    _save_blend()
    _rewrite_images_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_mixed_feature] wrote {BLEND_PATH}")


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


def _dual(obj: bpy.types.Object, pg_name: str, cp_key: str, value: object) -> None:
    """Write a proscenio field to both the PropertyGroup and its CP fallback.

    The headless writer reads the Custom Property when the addon's
    PropertyGroup is not registered; the PG path is what panels read in an
    interactive session. Authoring both keeps the fixture honest in both.
    """
    if hasattr(obj, "proscenio"):
        setattr(obj.proscenio, pg_name, value)
    obj[cp_key] = value


def _build_armature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("mixed_rig")
    arm_obj = bpy.data.objects.new("mixed_rig", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    # Flat bones in the XZ picture plane - never into depth (Y). root / spine /
    # head climb the screen as a +Z spine; spine animates (a vertical bob) and
    # deforms the skinned body. `mouth` is +X (lateral) so the mouth Sprite2D, a
    # child of its Bone2D, exports rotation 0 and sits upright. `jaw` is the
    # invisible driver source for the mouth frame.
    edit_bones: dict[str, bpy.types.EditBone] = {}
    for name, head, tail in (
        ("root", (0.0, 0.0, -0.4), (0.0, 0.0, -0.1)),
        ("spine", (0.0, 0.0, -0.1), (0.0, 0.0, 0.3)),
        ("head", (0.0, 0.0, 0.5), (0.0, 0.0, 0.8)),
        ("mouth", (0.0, 0.0, 0.46), (0.3, 0.0, 0.46)),
        ("jaw", (0.4, 0.0, 0.5), (0.4, 0.0, 0.8)),
    ):
        b = arm_data.edit_bones.new(name)
        b.head = head
        b.tail = tail
        edit_bones[name] = b
    # Wire the chain so the spine bob carries the head, the face slot, the mouth
    # and the jaw with it (root -> spine -> head -> {mouth, jaw}). use_connect
    # stays False, so each bone keeps its authored head/tail rather than snapping
    # to its parent's tail; only the rest hierarchy (and thus pose propagation)
    # changes.
    edit_bones["spine"].parent = edit_bones["root"]
    edit_bones["head"].parent = edit_bones["spine"]
    edit_bones["mouth"].parent = edit_bones["head"]
    edit_bones["jaw"].parent = edit_bones["head"]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _atlas_material(name: str) -> bpy.types.Material:
    """A material whose Base Color samples the shared atlas (nearest-neighbor)."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ATLAS_PATH), check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _quad_mesh(
    name: str, w: float, h: float, uvs: list[tuple[float, float]]
) -> bpy.types.Mesh:
    """A single-face quad in the XZ plane with the four corner UVs given."""
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
    for i, corner in enumerate(uvs):
        uv.data[i].uv = corner
    return mesh


def _build_skinned_body(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """A 2-face polygon skinned across ``root`` (lower) and ``spine`` (upper).

    Six vertices in a 2x3 grid; the lower face weights to ``root``, the upper
    to ``spine``, the shared middle row splits 50/50. UVs cover the atlas
    bottom-left quadrant.
    """
    mesh = bpy.data.meshes.new("body")
    mesh.from_pydata(
        vertices=[
            (-0.2, 0.0, -0.5),  # 0 bottom-left
            (0.2, 0.0, -0.5),  # 1 bottom-right
            (0.2, 0.0, 0.0),  # 2 mid-right
            (-0.2, 0.0, 0.0),  # 3 mid-left
            (0.2, 0.0, 0.5),  # 4 top-right
            (-0.2, 0.0, 0.5),  # 5 top-left
        ],
        edges=[],
        faces=[(0, 1, 2, 3), (3, 2, 4, 5)],
    )
    mesh.update()
    # UVs into the atlas bottom-left quadrant (Blender bottom-up: v in [0, 0.5]).
    vert_uv = {
        0: (0.0, 0.0),
        1: (0.5, 0.0),
        2: (0.5, 0.25),
        3: (0.0, 0.25),
        4: (0.5, 0.5),
        5: (0.0, 0.5),
    }
    uv = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv.data[loop.index].uv = vert_uv[loop.vertex_index]

    obj = bpy.data.objects.new("body", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = armature_obj
    obj.parent_type = "OBJECT"

    # `root` first so it is the resolved fallback bone (first vertex group).
    vg_root = obj.vertex_groups.new(name="root")
    vg_spine = obj.vertex_groups.new(name="spine")
    vg_root.add([0, 1], 1.0, "REPLACE")
    vg_root.add([2, 3], 0.5, "REPLACE")
    vg_spine.add([2, 3], 0.5, "REPLACE")
    vg_spine.add([4, 5], 1.0, "REPLACE")
    # Armature modifier so root/spine actually deform the body in Blender (the
    # weights alone only feed the export).
    arm_mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    arm_mod.object = armature_obj

    mesh.materials.append(_atlas_material("body.mat"))
    _dual(obj, "element_type", "proscenio_type", "mesh")
    return obj


def _build_mouth(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """A 4-frame mouth Sprite2D on the ``mouth`` bone (top-left atlas quadrant).

    Skinned 1.0 to the ``mouth`` bone (a +X child of ``head``): the Sprite2D
    becomes a child of that Bone2D in Godot - upright (the +X bone exports
    rotation 0) and carried along when the head/spine move. The frame is driven
    from ``jaw`` rotation. Local Y = -0.004 keeps it the frontmost element.
    """
    # Godot reads `texture_region` (top-left 32x32) + the frame grid. The quad
    # UV is 0..1: the Setup Preview slicer maps it into the region + active cell
    # (region-aware), and the export ignores sprite UVs.
    w = 0.16
    mesh = _quad_mesh("mouth", w, w, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    obj = bpy.data.objects.new("mouth", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (0.0, -0.004, 0.46)
    obj.parent = armature_obj
    obj.parent_type = "OBJECT"
    vg = obj.vertex_groups.new(name="mouth")
    vg.add([v.index for v in mesh.vertices], 1.0, "REPLACE")
    arm_mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    arm_mod.object = armature_obj

    mesh.materials.append(_atlas_material("mouth.mat"))
    _dual(obj, "element_type", "proscenio_type", "sprite")
    _dual(obj, "hframes", "proscenio_hframes", 2)
    _dual(obj, "vframes", "proscenio_vframes", 2)
    _dual(obj, "frame", "proscenio_frame", 0)
    _dual(obj, "centered", "proscenio_centered", True)
    _apply_manual_region(obj, MOUTH_REGION)
    return obj


def _build_slot(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """A slot Empty holding one mesh + one sprite attachment (the mixed case).

    Object-parented to the armature (not a bone) so the attachment quads keep
    their screen-plane orientation - the slot_cycle convention; the slot's
    ``bone`` field falls out empty.
    """
    empty = bpy.data.objects.new("face.slot", None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.1
    bpy.context.scene.collection.objects.link(empty)
    # The face sits at the head, just above the torso (the body spans z[-0.5,
    # 0.5]); object-parented so the attachment quads keep their screen-plane
    # orientation (the slot's `bone` field stays empty).
    empty.location = (0.0, 0.0, 0.55)
    empty.parent = armature_obj
    empty.parent_type = "OBJECT"
    _dual(empty, "is_slot", "proscenio_is_slot", True)
    _dual(empty, "slot_default", "proscenio_slot_default", "face_neutral")
    # The face follows the head bone: the importer parents the slot Node2D under
    # the head Bone2D (object-parented Empty keeps the attachment quads flat).
    _dual(empty, "slot_bone", "proscenio_slot_bone", "head")
    # Author the Blender-side follow so the face tracks the head bone in the
    # viewport (mirrors the Godot importer). Baked at rest, golden-neutral.
    con = empty.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Slot Follow"
    con.target = armature_obj
    con.subtarget = "head"
    bpy.context.view_layer.update()
    head_bone = armature_obj.pose.bones["head"]
    con.inverse_matrix = (armature_obj.matrix_world @ head_bone.matrix).inverted()

    # Mesh attachment: UVs into the atlas bottom-right quadrant. Local Y =
    # -0.002 -> z_index 2, in front of the torso (0) and behind the mouth (4).
    neutral_mesh = _quad_mesh(
        "face_neutral", 0.32, 0.32, [(0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (0.5, 0.5)]
    )
    neutral = bpy.data.objects.new("face_neutral", neutral_mesh)
    bpy.context.scene.collection.objects.link(neutral)
    neutral.location = (0.0, -0.002, 0.0)
    neutral.parent = empty
    neutral.parent_type = "OBJECT"
    neutral_mesh.materials.append(_atlas_material("face_neutral.mat"))
    _dual(neutral, "element_type", "proscenio_type", "mesh")

    # Sprite attachment (the mixed-slot test: one mesh + one sprite under one
    # slot): a single-frame glowing head, region = atlas top-right quadrant. UVs
    # map the quad onto that quadrant for the Blender preview (Godot reads
    # `texture_region`, not these UVs; sprite UVs do not enter the golden).
    glow_mesh = _quad_mesh(
        "face_glow", 0.32, 0.32, [(0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0)]
    )
    glow = bpy.data.objects.new("face_glow", glow_mesh)
    bpy.context.scene.collection.objects.link(glow)
    glow.location = (0.0, -0.002, 0.0)
    glow.parent = empty
    glow.parent_type = "OBJECT"
    glow_mesh.materials.append(_atlas_material("face_glow.mat"))
    _dual(glow, "element_type", "proscenio_type", "sprite")
    _dual(glow, "hframes", "proscenio_hframes", 1)
    _dual(glow, "vframes", "proscenio_vframes", 1)
    _dual(glow, "frame", "proscenio_frame", 0)
    _dual(glow, "centered", "proscenio_centered", True)
    _apply_manual_region(glow, GLOW_REGION)
    return empty


def _apply_manual_region(
    obj: bpy.types.Object, region: tuple[float, float, float, float]
) -> None:
    rx, ry, rw, rh = region
    _dual(obj, "region_mode", "proscenio_region_mode", "manual")
    _dual(obj, "region_x", "proscenio_region_x", rx)
    _dual(obj, "region_y", "proscenio_region_y", ry)
    _dual(obj, "region_w", "proscenio_region_w", rw)
    _dual(obj, "region_h", "proscenio_region_h", rh)


def _install_mouth_driver(
    mouth_obj: bpy.types.Object, armature_obj: bpy.types.Object
) -> None:
    """Wire the ``jaw`` spin (ROT_Z) to ``mouth.proscenio.frame``."""
    data_path = "proscenio.frame"
    if (
        mouth_obj.animation_data is not None
        and mouth_obj.animation_data.drivers.find(data_path) is not None
    ):
        mouth_obj.driver_remove(data_path)

    fcurve = mouth_obj.driver_add(data_path)
    while fcurve.keyframe_points:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0])

    driver = fcurve.driver
    driver.type = "SCRIPTED"
    # Mirrors the mouth_drive fixture: `var` is the jaw spin (ROT_Z) in radians,
    # so across the action's [-pi/2, +pi/2] sweep
    # `var * 2 + 2` ranges roughly [-1.1, 5.1]. The overshoot is intentional - the
    # writer's frame-driver bake clamps to [0, hframes*vframes-1], yielding a full
    # 0..3 cell sweep with frame 2 at the rest pose. The fixture exercises exactly
    # that clamp path, so the raw expression is the point, not a bug.
    driver.expression = "var * 2 + 2"
    var = driver.variables[0] if driver.variables else driver.variables.new()
    var.name = "var"
    var.type = "TRANSFORMS"
    target = var.targets[0]
    target.id = armature_obj
    target.bone_target = "jaw"
    target.transform_type = "ROT_Z"
    target.transform_space = "WORLD_SPACE"
    target.rotation_mode = "XYZ"

    if hasattr(mouth_obj, "proscenio"):
        mouth_obj.proscenio.driver_target = "frame"
        mouth_obj.proscenio.driver_source_armature = armature_obj
        mouth_obj.proscenio.driver_source_bone = "jaw"
        mouth_obj.proscenio.driver_source_axis = "ROT_Z"
        mouth_obj.proscenio.driver_expression = "var * 2 + 2"


def _build_action(armature_obj: bpy.types.Object) -> None:
    """Animate over 24 frames: the ``jaw`` spin (drives the mouth frame) plus a
    ``spine`` bob up and down (which carries the chest, head + face with it via
    the bone chain and deforms the skinned body).

    The export carries a ``bone_transform`` track for ``jaw`` and ``spine`` plus
    the driven ``sprite_frame`` track for ``mouth``.
    """
    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="mixed_anim")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    jaw_pose = armature_obj.pose.bones["jaw"]
    jaw_pose.rotation_mode = "XYZ"
    # The jaw is an invisible driver source. Spin it about its own axis (local Y
    # = world Z); the driver reads it via ROT_Z WORLD_SPACE. Clean single channel
    # keeps the driven frame sequence stable.
    for frame, value in ((1, 0.0), (8, -math.pi / 2), (16, math.pi / 2), (24, 0.0)):
        bpy.context.scene.frame_set(frame)
        jaw_pose.rotation_euler = (0.0, value, 0.0)
        jaw_pose.keyframe_insert(data_path="rotation_euler", frame=frame, index=1)

    # Spine bob: translate up the screen (local Y for a +Z bone is world +Z) and
    # back, so the chest/head rise and fall and the body stretches.
    spine_pose = armature_obj.pose.bones["spine"]
    for frame, dz in ((1, 0.0), (12, 0.15), (24, 0.0)):
        bpy.context.scene.frame_set(frame)
        spine_pose.location = (0.0, dz, 0.0)
        spine_pose.keyframe_insert(data_path="location", frame=frame, index=1)


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_images_to_relpath() -> None:
    """After save_as, rewrite each image filepath to a ``//``-relative path."""
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
        print(f"[build_mixed_feature] FAILED: {exc}", file=sys.stderr)
        raise
