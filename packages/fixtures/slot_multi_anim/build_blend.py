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
bound to the bone via the Proscenio Slot Follow constraint) - that shared
character is built by ``_shared/weapon_slot.py``; this script only authors the
two animations. Image filepaths are stored ``//``-relative so the committed
.blend is machine-independent.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

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
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "slot_multi_anim"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
ARM_PATH = LAYERS_DIR / "arm.png"
CLUB_PATH = LAYERS_DIR / "club.png"
TORCH_PATH = LAYERS_DIR / "torch.png"
BLEND_PATH = FIXTURE_DIR / "slot_multi_anim.blend"

LOG_PREFIX = "[build_slot_multi_anim]"


def main() -> None:
    require_layers((ARM_PATH, CLUB_PATH, TORCH_PATH), LOG_PREFIX)
    character = build_weapon_slot_character(
        arm_image=ARM_PATH,
        attachments=(
            AttachmentSpec("club", CLUB_PATH, is_default=True, draw_order=-1),
            AttachmentSpec("torch", TORCH_PATH, is_default=False, draw_order=-2),
        ),
    )
    _build_animations(
        character.armature,
        character.attachments["club"],
        character.attachments["torch"],
    )
    finalize_blend(BLEND_PATH, LOG_PREFIX)


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
        key_show_only(mesh, idle, visible=False, frame=1)
        key_show_only(mesh, idle, visible=False, frame=12)

    attack = bpy.data.actions.new(name="attack")
    _key_arm_swing(armature_obj, attack)
    for mesh in (club, torch):
        key_show_only(mesh, attack, visible=mesh.name == "club", frame=1)
        key_show_only(mesh, attack, visible=mesh.name == "club", frame=12)

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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"{LOG_PREFIX} FAILED: {exc}", file=sys.stderr)
        raise
