"""Slot-attachment animation emission (SPEC 004 D5)."""

from __future__ import annotations

from typing import Any

import bpy

from ....core.cp_keys import PROSCENIO_SLOT_INDEX  # type: ignore[import-not-found]
from .animations import action_fcurves
from .slots import is_slot_empty


def build_slot_animations(scene: bpy.types.Scene) -> list[dict[str, Any]]:
    """Walk slot Empties for actions keyframing ``proscenio_slot_index``.

    Each fcurve key maps an integer index to one of the slot's
    ``attachments[]``, expanded into a ``slot_attachment`` track
    targeting the slot's name. Constant interpolation - D5 hard-cut.
    Returns one animation entry per (slot, action) pair; the merge
    helper consolidates entries that share an action name.
    """
    fps = scene.render.fps
    out: list[dict[str, Any]] = []
    for obj in scene.objects:
        if obj.type != "EMPTY":
            continue
        if not is_slot_empty(obj):
            continue
        anim_data = getattr(obj, "animation_data", None)
        action = getattr(anim_data, "action", None) if anim_data is not None else None
        if action is None:
            continue
        track = _build_slot_attachment_track(obj, action, fps)
        if track is None:
            continue
        frame_start, frame_end = action.frame_range
        length = max(0.001, (frame_end - frame_start) / float(fps))
        out.append(
            {
                "name": action.name,
                "length": round(length, 6),
                "loop": True,
                "tracks": [track],
            }
        )
    return out


def merge_slot_animations_into(
    existing: list[dict[str, Any]],
    new_anims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge slot animations into the existing list by action name.

    Same-name animations get their ``tracks[]`` extended + the longer
    length wins. Different names land as new top-level entries. Lets a
    bone-transform action and a slot-attachment action share the same
    Animation in Godot when the user authored both under the same
    action name.
    """
    out = list(existing)
    by_name: dict[str, dict[str, Any]] = {anim["name"]: anim for anim in out}
    for anim in new_anims:
        existing_anim = by_name.get(anim["name"])
        if existing_anim is None:
            out.append(anim)
            by_name[anim["name"]] = anim
            continue
        existing_anim["tracks"].extend(anim["tracks"])
        existing_anim["length"] = max(float(existing_anim["length"]), float(anim["length"]))
    return out


def _build_slot_attachment_track(
    empty_obj: bpy.types.Object,
    action: bpy.types.Action,
    fps: int,
) -> dict[str, Any] | None:
    """Project ``proscenio_slot_index`` fcurve keys to a slot_attachment track."""
    attachments = tuple(c.name for c in empty_obj.children if c.type == "MESH")
    if not attachments:
        return None
    keys: list[dict[str, Any]] = []
    target_path = f'["{PROSCENIO_SLOT_INDEX}"]'
    for fcurve in action_fcurves(action):
        if fcurve.data_path != target_path:
            continue
        for kp in fcurve.keyframe_points:
            frame = float(kp.co.x)
            t = max(0.0, (frame - 1) / float(fps))
            idx = int(kp.co.y)
            if 0 <= idx < len(attachments):
                keys.append(
                    {
                        "time": round(t, 6),
                        "interp": "constant",
                        "attachment": attachments[idx],
                    }
                )
    if not keys:
        return None
    keys.sort(key=lambda k: k["time"])
    return {
        "type": "slot_attachment",
        "target": empty_obj.name,
        "keys": keys,
    }
