"""Promote doll brow meshes to slots (SPEC 004 Wave 4.4 close-out).

Run with::

    blender --background examples/doll/doll.blend \\
        --python scripts/fixtures/doll/promote_brows_to_slots.py

The script reads the canonical baseline ``examples/doll/doll.blend``
(meshes + clean armature, no slots) and writes the promoted result to
``examples/doll/doll_slots.blend``. The baseline blend stays untouched
so the photoshop render-layers roundtrip keeps a single source of
truth -- the slot fixture is a derived artefact.

Idempotent. The output blend, after the script runs, contains:

- ``brow.L`` and ``brow.R`` as the "down" attachment meshes (their
  pre-promotion state -- vertex group named after the bone, weighted
  via that group).
- ``brow.L.up`` and ``brow.R.up`` as sibling alternates -- duplicates
  of the down meshes shifted +Z by 0.05u (raised brow position).
- A slot Empty per side (``brow.L.swap`` / ``brow.R.swap``) parents
  both attachments. ``parent_type='OBJECT'`` to ``doll.rig`` (mirrors
  the doll's vertex-group weighting pattern). ``is_slot=True``,
  ``slot_default=brow.<side>`` (down).
- A ``brow_raise`` action on each slot Empty keyframing
  ``proscenio_slot_index`` 0 -> 1 -> 0 over 30 frames (down -> up ->
  down). Writer expands these into ``slot_attachment`` tracks at
  export.

Re-running overwrites ``doll_slots.blend`` deterministically (no
duplicate ``.up`` meshes, no piled-up actions).
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = REPO_ROOT / "examples" / "doll" / "doll.blend"
OUTPUT_PATH = REPO_ROOT / "examples" / "doll" / "doll_slots.blend"

BROW_SIDES = ("L", "R")
RAISE_OFFSET_Z = 0.05


def main() -> None:
    for side in BROW_SIDES:
        _promote_one_side(side)
    _rebuild_brow_raise_action()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    print(f"[promote_brows_to_slots] wrote {OUTPUT_PATH}")


def _promote_one_side(side: str) -> None:
    down_name = f"brow.{side}"
    up_name = f"brow.{side}.up"
    slot_name = f"brow.{side}.swap"

    down = bpy.data.objects.get(down_name)
    if down is None:
        print(
            f"[promote_brows_to_slots] no '{down_name}' -- skipping side",
            file=sys.stderr,
        )
        return

    up = bpy.data.objects.get(up_name) or _duplicate_as_raised(down, up_name)
    slot = bpy.data.objects.get(slot_name) or _create_slot_empty(slot_name, down)

    for attachment in (down, up):
        if attachment.parent is not slot:
            world = attachment.matrix_world.copy()
            attachment.parent = slot
            attachment.parent_type = "OBJECT"
            attachment.matrix_parent_inverse = slot.matrix_world.inverted()
            attachment.matrix_world = world


def _duplicate_as_raised(source: bpy.types.Object, new_name: str) -> bpy.types.Object:
    """Copy ``source`` into a new Object named ``new_name``, offset +Z."""
    copy = source.copy()
    copy.data = source.data.copy()
    copy.name = new_name
    copy.data.name = new_name
    bpy.context.scene.collection.objects.link(copy)
    copy.location = source.location + Vector((0.0, 0.0, RAISE_OFFSET_Z))
    return copy


def _create_slot_empty(slot_name: str, seed_down: bpy.types.Object) -> bpy.types.Object:
    """Create a slot Empty parented to the doll armature, anchored at the down mesh."""
    armature = bpy.data.objects.get("doll.rig")
    empty = bpy.data.objects.new(slot_name, None)
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = 0.05
    bpy.context.scene.collection.objects.link(empty)
    if armature is not None:
        empty.parent = armature
        empty.parent_type = "OBJECT"
    empty.location = seed_down.matrix_world.to_translation()

    if hasattr(empty, "proscenio"):
        empty.proscenio.is_slot = True
        empty.proscenio.slot_default = seed_down.name
    # Custom Property fallback so headless writer (no addon registered)
    # still detects the slot. Mirrors the slot_cycle build pattern.
    empty["proscenio_is_slot"] = True
    empty["proscenio_slot_default"] = seed_down.name
    return empty


def _rebuild_brow_raise_action() -> None:
    """Author a ``brow_raise`` action keyframing slot index 0 -> 1 -> 0 on each slot."""
    for side in BROW_SIDES:
        slot = bpy.data.objects.get(f"brow.{side}.swap")
        if slot is None:
            continue
        slot.animation_data_create()
        # Idempotent rebuild: drop the action currently bound to THIS slot
        # before creating the fresh one. Looking up by name was wrong
        # (string was f"{slot.name}{action_name}" -> "brow.L.swapbrow_raise"
        # which never existed) so re-runs piled up "brow_raise.001",
        # "brow_raise.002", ... instead of overwriting in place.
        existing = slot.animation_data.action
        if existing is not None:
            slot.animation_data.action = None
            bpy.data.actions.remove(existing)
        action = bpy.data.actions.new(name="brow_raise")
        slot.animation_data.action = action
        bpy.context.scene.frame_start = 1
        bpy.context.scene.frame_end = 30
        for frame, idx in ((1, 0), (15, 1), (30, 0)):
            bpy.context.scene.frame_set(frame)
            slot["proscenio_slot_index"] = idx
            slot.keyframe_insert(data_path='["proscenio_slot_index"]', frame=frame)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[promote_brows_to_slots] FAILED: {exc}", file=sys.stderr)
        raise
