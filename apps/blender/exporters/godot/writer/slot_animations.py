"""Slot-attachment animation emission."""

from __future__ import annotations

import bpy
from proscenio_models import Animation, Key, Track

from ....core._bpy_compat import iter_keyframe_points, iter_objects
from ....core.cp_keys import PROSCENIO_SLOT_INDEX
from .animations import action_fcurves
from .slots import is_slot_empty


def build_slot_animations(scene: bpy.types.Scene) -> list[Animation]:
    """Walk slot Empties for actions keyframing ``proscenio_slot_index``.

    Each fcurve key maps an integer index to one of the slot's
    ``attachments[]``, expanded into a ``slot_attachment`` track
    targeting the slot's name. Constant interpolation - hard-cut.
    Returns one animation entry per (slot, action) pair; the merge
    helper consolidates entries that share an action name.
    """
    fps = scene.render.fps
    out: list[Animation] = []
    for obj in iter_objects(scene):
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
        frame_start = float(action.frame_range[0])
        frame_end = float(action.frame_range[1])
        length = max(0.001, (frame_end - frame_start) / float(fps))
        out.append(
            Animation(
                name=action.name,
                length=round(length, 6),
                loop=True,
                tracks=[track],
            )
        )
    return out


def merge_slot_animations_into(
    existing: list[Animation],
    new_anims: list[Animation],
) -> list[Animation]:
    """Merge slot animations into the existing list by action name.

    Same-name animations get their ``tracks[]`` extended + the longer
    length wins. Different names land as new top-level entries. Lets a
    bone-transform action and a slot-attachment action share the same
    Animation in Godot when the user authored both under the same
    action name.

    Returns a new list with merged Animations (existing animations may
    have their ``tracks`` and ``length`` fields mutated to absorb the
    new entries).
    """
    out = list(existing)
    by_name: dict[str, Animation] = {anim.name: anim for anim in out}
    for anim in new_anims:
        existing_anim = by_name.get(anim.name)
        if existing_anim is None:
            out.append(anim)
            by_name[anim.name] = anim
            continue
        existing_anim.tracks.extend(anim.tracks)
        existing_anim.length = max(existing_anim.length, anim.length)
    return out


def _build_slot_attachment_track(
    empty_obj: bpy.types.Object,
    action: bpy.types.Action,
    fps: int,
) -> Track | None:
    """Project ``proscenio_slot_index`` fcurve keys to a slot_attachment track."""
    attachments = tuple(c.name for c in empty_obj.children if c.type == "MESH")
    if not attachments:
        return None
    keys: list[Key] = []
    target_path = f'["{PROSCENIO_SLOT_INDEX}"]'
    for fcurve in action_fcurves(action):
        if fcurve.data_path != target_path:
            continue
        for kp in iter_keyframe_points(fcurve):
            frame = float(kp.co.x)
            t = max(0.0, (frame - 1) / float(fps))
            idx = int(kp.co.y)
            if 0 <= idx < len(attachments):
                keys.append(
                    Key(
                        time=round(t, 6),
                        interp="constant",
                        attachment=attachments[idx],
                    )
                )
    if not keys:
        return None
    keys.sort(key=lambda k: k.time)
    return Track(type="slot_attachment", target=empty_obj.name, keys=keys)
