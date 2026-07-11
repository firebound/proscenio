"""Assemble slot_swap.blend (slot system minimal fixture).

Run with::

    blender --background --python packages/fixtures/slot_swap/build_blend.py

Loads PNGs produced by ``draw_layers.py`` and builds a minimal slot
system fixture: a pseudo-arm swinging while its weapon attachment
swaps mid-animation.

Layout:

- **Armature** ``arm_rig`` with a single bone ``arm`` perpendicular
  to the XZ picture plane (tail along +Y, into the screen away from the
  Front Ortho camera at -Y; bone-parented cutouts stay un-flipped).
- **Polygon mesh** ``arm`` parented to the bone - the visible 16x32
  arm sprite.
- **Empty** ``weapon`` parented to the bone tip; flagged
  ``proscenio.is_slot = True`` with default attachment ``club``.
- **Two attachment meshes** parented to the slot Empty:
  - ``club`` - 32x32 polygon mesh with club.png material
  - ``sword`` - 32x32 polygon mesh with sword.png material
- **One slotted action ``swing``** (Blender 4.4+), shared by the armature
  and both attachment meshes on their own slots, so the writer emits one
  merged animation with two tracks:
  - The armature slot keyframes the arm bone's local Y rotation
    -pi/6 -> +pi/6 -> 0 over 24 frames (gentle swing).
  - Each attachment mesh's slot keyframes ``hide_render`` + ``hide_viewport``
    (constant): club shown -> sword shown -> club shown over the same 24
    frames. Swap happens at the apex of the swing.

The fixture exercises:

1. Slot Empty + N attachments + slot_default round-trip through the
   writer into a ``slots[]`` entry.
2. Per-attachment visibility keyframes collapse into a ``slot_attachment``
   track (spec 079).
3. Bone rotation animation co-exists with the slot swap under a shared
   slotted action name (writer's merge logic).
4. ``apps/blender/tests/run_tests.py`` re-exports the .blend and
   the result matches the committed golden.

The shared arm + slot + attachment character is built by
``_shared/weapon_slot.py``; this script only authors the ``swing`` animation.

Image filepaths stored as ``//pillow_layers/...`` so the fixture
works cross-machine. Materials use ``Closest`` interpolation so
pixel-art edges stay crisp in Eevee Material Preview.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from slot_keying import key_show_only  # noqa: E402
from weapon_slot import (  # noqa: E402
    ARM_BONE,
    AttachmentSpec,
    build_weapon_slot_character,
    finalize_blend,
    require_layers,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "slot_swap"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
ARM_PATH = LAYERS_DIR / "arm.png"
CLUB_PATH = LAYERS_DIR / "club.png"
SWORD_PATH = LAYERS_DIR / "sword.png"
BLEND_PATH = FIXTURE_DIR / "slot_swap.blend"

LOG_PREFIX = "[build_slot_swap]"


def main() -> None:
    require_layers((ARM_PATH, CLUB_PATH, SWORD_PATH), LOG_PREFIX)
    # Stagger attachments by draw order so Eevee never disambiguates coplanar
    # quads if both end up visible. The writer negates the order into z_index
    # (club -1 -> z_index 1, sword -2 -> z_index 2).
    character = build_weapon_slot_character(
        arm_image=ARM_PATH,
        attachments=(
            AttachmentSpec("club", CLUB_PATH, is_default=True, draw_order=-1),
            AttachmentSpec("sword", SWORD_PATH, is_default=False, draw_order=-2),
        ),
    )
    club_obj = character.attachments["club"]
    sword_obj = character.attachments["sword"]
    swing_action = _build_swing_action(character.armature)
    _key_attachment_visibility(swing_action, [club_obj, sword_obj])
    finalize_blend(BLEND_PATH, LOG_PREFIX)


def _build_swing_action(armature_obj: bpy.types.Object) -> bpy.types.Action:
    """Gentle Y rotation swing on the arm bone over 24 frames.

    Returns the ``swing`` action datablock so the attachment meshes can bind
    their visibility onto their own slots of the SAME action (Blender 4.4+),
    keeping the bone motion + the swap in one animation the writer emits merged.
    """
    import math

    from mathutils import Matrix

    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="swing")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 24

    arm_pose = armature_obj.pose.bones[ARM_BONE]
    arm_pose.rotation_mode = "XYZ"
    # Swing about the camera axis (world Y) = visible 2D rotation in the front
    # view. The bone points +X (in plane), so a local-Y key would not swing it;
    # matrix_basis = rest^-1 . Ry(theta) . rest expresses the world-Y rotation in
    # bone-local space (see mouth_drive / mixed_feature).
    rest = arm_pose.bone.matrix_local
    rest_inv = rest.inverted()
    swing_keys = (
        (1, -math.pi / 6),
        (12, math.pi / 6),
        (24, -math.pi / 6),
    )
    for frame, value in swing_keys:
        bpy.context.scene.frame_set(frame)
        arm_pose.matrix_basis = rest_inv @ Matrix.Rotation(value, 4, "Y") @ rest
        arm_pose.keyframe_insert(data_path="rotation_euler", frame=frame)
    return action


def _key_attachment_visibility(
    action: bpy.types.Action,
    meshes: list[bpy.types.Object],
) -> None:
    """Show-only visibility swap: club -> sword -> club over 24 frames.

    At each swap frame every attachment mesh keys ``hide_render`` +
    ``hide_viewport`` in lockstep (chosen shown, rest hidden), constant interp,
    on its own slot of the shared ``swing`` action - the exact per-mesh state
    the ``keyframe_slot_attachment`` operator authors and the writer collapses
    back into one exclusive ``slot_attachment`` track. Sharing the armature's
    action datablock keeps the swap in the ``swing`` animation (no ``.001``
    disambiguation split).
    """
    sequence = ((1, "club"), (12, "sword"), (24, "club"))
    for frame, chosen in sequence:
        bpy.context.scene.frame_set(frame)
        for mesh in meshes:
            key_show_only(mesh, action, visible=mesh.name == chosen, frame=frame)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"{LOG_PREFIX} FAILED: {exc}", file=sys.stderr)
        raise
