"""Slot-attachment animation emission (visibility-driven, spec 079).

Each slot Empty owns N attachment MESH children. The artist keys each
attachment mesh's ``hide_render`` (mirrored to ``hide_viewport`` for viewport
preview); this walker reads those per-mesh visibility keyframes and collapses
them per frame into one exclusive ``slot_attachment`` track - the same track
shape the Godot builder already consumes. It replaces the retired
``proscenio_slot_index`` idprop model: visibility keys preview natively in
Blender, express "none visible" for free, and carry their owner intrinsically
(each mesh is its own datablock), so there is no index to drift.
"""

from __future__ import annotations

import bpy
from proscenio_models import Animation, Key, Track

from ....core._shared.action_fcurves import object_fcurves_in_action
from ....core.bpy_helpers._shared._bpy_compat import (
    iter_actions,
    iter_keyframe_points,
    iter_objects,
)
from ....core.slot.slot_emit import is_slot_empty
from .animations import action_length

# A ``slot_attachment`` key naming a child that does not exist hides every
# attachment - the Godot builder sets ``child.visible = (child.name == attachment)``.
# The writer emits this sentinel for a frame where the artist keyed every
# attachment hidden ("none visible", e.g. idle with no weapon; spec 079 D4).
NONE_ATTACHMENT = "(none)"

# hide_render / hide_viewport are booleans; a keyframe stores 0.0 (shown) or
# 1.0 (hidden). Treat < 0.5 as visible so a mid-value never mis-collapses.
_VISIBLE_THRESHOLD = 0.5


def build_slot_animations(scene: bpy.types.Scene) -> list[Animation]:
    """Walk slot Empties for attachment-mesh visibility keyframes, per animation.

    Mirrors the bone writer's coverage: it iterates EVERY action in the file
    (:func:`iter_actions`, like ``build_animations``), and for each (action, slot
    Empty) reads each attachment mesh's ``hide_render`` visibility scoped to that
    mesh's slot WITHIN that action - so a character whose ``idle`` hides every
    weapon and whose ``attack`` shows one exports a distinct ``slot_attachment``
    timeline per animation (spec 079's core). Reading is scoped per mesh per
    action (never the flattened channelbag view), so siblings sharing a 4.4+
    slotted action never cross-read (R4). Returns one animation entry per
    (slot, animation-name) pair; :func:`merge_slot_animations_into` then folds
    each entry onto the bone animation of the same name.
    """
    fps = scene.render.fps
    actions = list(iter_actions())
    out: list[Animation] = []
    for obj in iter_objects(scene):
        if not is_slot_empty(obj):
            continue
        out.extend(_slot_animations_for_empty(obj, actions, fps))
    return out


def merge_slot_animations_into(
    existing: list[Animation],
    new_anims: list[Animation],
) -> list[Animation]:
    """Merge slot animations into the existing list by animation name.

    Same-name animations get their ``tracks[]`` extended + the longer
    length wins. Different names land as new top-level entries. Lets a
    bone-transform animation and a slot-attachment animation share the same
    Animation in Godot when both were authored under the same name (on
    Blender 4.4+ they co-locate in one slotted action datablock; on 4.2 they
    are same-named separate actions).

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


def _slot_animations_for_empty(
    empty_obj: bpy.types.Object,
    actions: list[bpy.types.Action],
    fps: int,
) -> list[Animation]:
    """Build every slot_attachment animation carried by one slot Empty.

    Emits one animation per action in which any of the Empty's attachment meshes
    carries a visibility keyframe. For each action the attachments' visibility is
    read scoped to that action (their per-mesh slot on a 4.4+ slotted action, or
    a mesh's own dedicated 4.2 action) and collapsed into one exclusive
    ``slot_attachment`` track named after the action.
    """
    attachments = [child for child in empty_obj.children if child.type == "MESH"]
    if not attachments:
        return []
    order = [child.name for child in attachments]
    out: list[Animation] = []
    for action in actions:
        mesh_vis: dict[str, list[tuple[float, bool]]] = {}
        for mesh in attachments:
            vis_keys = _read_visibility_keys_in_action(mesh, action)
            if vis_keys:
                mesh_vis[mesh.name] = vis_keys
        if not mesh_vis:
            continue
        track = _build_slot_attachment_track(empty_obj.name, order, mesh_vis, fps)
        if track is None:
            continue
        out.append(
            Animation(
                name=action.name,
                length=action_length(action, fps),
                loop=True,
                tracks=[track],
            )
        )
    return out


def _read_visibility_keys_in_action(
    mesh: bpy.types.Object,
    action: bpy.types.Action,
) -> list[tuple[float, bool]]:
    """Sorted ``(frame, visible)`` from ``mesh``'s ``hide_render`` fcurve in ``action``.

    Reads only the curves scoped to ``mesh`` within ``action`` (its slot's
    channelbag on a 4.4+ slotted action, or ``action`` itself when ``mesh``
    actively binds a legacy 4.2 flat action), never the flattened action view -
    so a mesh sharing a slotted action with its siblings reads only its own curve
    (spec 079 R4). Empty when ``mesh`` has no visibility keyed in ``action``.
    ``visible`` is ``True`` when the keyed ``hide_render`` value is shown (< 0.5).
    """
    keys: list[tuple[float, bool]] = []
    for fcurve in object_fcurves_in_action(mesh, action):
        if getattr(fcurve, "data_path", None) != "hide_render":
            continue
        for kp in iter_keyframe_points(fcurve):
            frame = float(kp.co.x)
            visible = float(kp.co.y) < _VISIBLE_THRESHOLD
            keys.append((frame, visible))
    keys.sort(key=lambda pair: pair[0])
    return keys


def _build_slot_attachment_track(
    target: str,
    order: list[str],
    mesh_vis: dict[str, list[tuple[float, bool]]],
    fps: int,
) -> Track | None:
    """Collapse per-mesh visibility into one exclusive ``slot_attachment`` track.

    The event frames are the union of every attachment's keyframe frames. At
    each, the visible attachments (evaluated with constant hold) collapse to a
    single key (spec 079 R2): 0 visible emits :data:`NONE_ATTACHMENT`; 1 visible
    emits that attachment; 2+ visible emits the first in child order.
    """
    event_frames = sorted({frame for keys in mesh_vis.values() for frame, _ in keys})
    if not event_frames:
        return None
    out_keys: list[Key] = []
    for frame in event_frames:
        visible = [
            name for name in order if name in mesh_vis and _visible_at(mesh_vis[name], frame)
        ]
        attachment = visible[0] if visible else NONE_ATTACHMENT
        t = max(0.0, (frame - 1.0) / float(fps))
        out_keys.append(Key(time=round(t, 6), interp="constant", attachment=attachment))
    return Track(type="slot_attachment", target=target, keys=out_keys)


def _visible_at(keys: list[tuple[float, bool]], frame: float) -> bool:
    """Constant-hold visibility at ``frame`` (the last key at or before it).

    Before the first key, holds the first key's value - matching how a CONSTANT
    fcurve reads outside its range.
    """
    visible = keys[0][1]
    for key_frame, key_visible in keys:
        if key_frame <= frame:
            visible = key_visible
        else:
            break
    return visible
