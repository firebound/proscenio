"""FCurve iteration over legacy and layered (Blender 4.4+) actions.

A legacy action exposes a flat ``fcurves`` collection. A 4.4+ layered
action leaves ``fcurves`` empty and nests its curves under
layers > strips > channelbags, so reading only ``action.fcurves`` misses
every curve authored through the 4.4+ GUI. The writer's track emission and
the export validator's transform-key check both route through here so a key
inserted in a modern Blender is seen on both sides.

Duck-typed (plain ``getattr`` / iteration, no ``bpy``) so the validation
modules stay importable without Blender and the pytest suite can drive it
with ``SimpleNamespace`` stubs.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


def action_fcurves(action: object) -> Iterator[bpy.types.FCurve]:
    """Yield every FCurve on ``action``, legacy flat or 4.4+ layered.

    ``action`` is duck-typed (``object``) so the pytest suite can drive it
    with ``SimpleNamespace`` stubs; the FCurve return type is the real shape
    callers consume at runtime.
    """
    fcurves = getattr(action, "fcurves", None)
    if fcurves:
        yield from fcurves
        return
    for layer in getattr(action, "layers", None) or []:
        for strip in getattr(layer, "strips", None) or []:
            for channelbag in getattr(strip, "channelbags", None) or []:
                yield from getattr(channelbag, "fcurves", None) or []


def object_action_fcurves(obj: object) -> Iterator[bpy.types.FCurve]:
    """Yield FCurves from ``obj``'s OWN active action, scoped to its action slot.

    Unlike :func:`action_fcurves` (which flattens *every* channelbag of an
    action), this reads only the curves that belong to ``obj``:

    - Legacy (Blender 4.2) action: a bare ``fcurves`` collection is already this
      object's own curves - a legacy action binds to exactly one datablock.
    - Slotted (Blender 4.4+) action possibly SHARED across objects (the armature
      and every attachment mesh co-locate their tracks in one action per
      animation): only the channelbag whose ``slot_handle`` matches
      ``obj.animation_data.action_slot.handle``. Flattening instead would make a
      slot writer processing one mesh read every sibling mesh's visibility curves
      too, double-counting them (spec 079 R4).

    Duck-typed (plain ``getattr``) so the pytest suite can drive it with
    ``SimpleNamespace`` stubs.
    """
    anim = getattr(obj, "animation_data", None)
    action = getattr(anim, "action", None) if anim is not None else None
    if action is None:
        return
    fcurves = getattr(action, "fcurves", None)
    if fcurves:
        yield from fcurves
        return
    slot = getattr(anim, "action_slot", None)
    slot_handle = getattr(slot, "handle", None) if slot is not None else None
    for layer in getattr(action, "layers", None) or []:
        for strip in getattr(layer, "strips", None) or []:
            for channelbag in getattr(strip, "channelbags", None) or []:
                cb_handle = getattr(channelbag, "slot_handle", None)
                if slot_handle is not None and cb_handle != slot_handle:
                    continue
                yield from getattr(channelbag, "fcurves", None) or []


def _object_slot_handle(action: object, obj_name: str | None) -> object | None:
    """The slot ``handle`` in ``action`` whose slot targets the object ``obj_name``.

    Blender auto-creates one slot per bound datablock; an Object slot is
    identified by its ``name_display`` (the object's name) and its
    ``identifier`` (``"OB"`` + the object name at bind time). Matches on either
    - verified against Blender 5.1, where both retain the bind-time name. Returns
    ``None`` when ``action`` has no slot for that object (the object was never
    keyed in this action), so an attachment absent from an animation contributes
    nothing to it.
    """
    for slot in getattr(action, "slots", None) or []:
        if getattr(slot, "target_id_type", None) != "OBJECT":
            continue
        if getattr(slot, "name_display", None) == obj_name or (
            obj_name is not None and getattr(slot, "identifier", None) == f"OB{obj_name}"
        ):
            return getattr(slot, "handle", None)
    return None


def object_fcurves_in_action(obj: object, action: object) -> Iterator[bpy.types.FCurve]:
    """Yield the fcurves belonging to ``obj`` within a GIVEN ``action``.

    Unlike :func:`object_action_fcurves` (which reads ``obj``'s OWN active
    action), this reads *any* action - ``obj`` need not be actively bound to it.
    That is what per-animation slot export needs: on Blender 4.4+ one attachment
    mesh holds a channelbag in every animation's action it was keyed in, but only
    one of those actions is the mesh's active binding, so the others are only
    reachable by scanning ``bpy.data.actions`` and matching by slot identity.

    - Slotted (Blender 4.4+) action: match the slot whose Object identity is
      ``obj`` (:func:`_object_slot_handle`) and read only that slot's channelbag,
      never the flattened view - flattening would read every sibling mesh's
      curves while processing one (spec 079 R4).
    - Legacy (Blender 4.2) flat action: a bare ``fcurves`` collection carries no
      slot identity, so it belongs to exactly one datablock - the object that
      actively binds it. Yield it only when ``obj`` is that binder, so a sibling's
      flat action never cross-reads. A 4.2 object binds one active action, so this
      is the single-animation fallback (multiple animations there need slots,
      which are 4.4+).

    Duck-typed (plain ``getattr``) so the pytest suite can drive it with
    ``SimpleNamespace`` stubs.
    """
    fcurves = getattr(action, "fcurves", None)
    if fcurves:
        anim = getattr(obj, "animation_data", None)
        active = getattr(anim, "action", None) if anim is not None else None
        if active is action:
            yield from fcurves
        return
    handle = _object_slot_handle(action, getattr(obj, "name", None))
    if handle is None:
        return
    for layer in getattr(action, "layers", None) or []:
        for strip in getattr(layer, "strips", None) or []:
            for channelbag in getattr(strip, "channelbags", None) or []:
                if getattr(channelbag, "slot_handle", None) != handle:
                    continue
                yield from getattr(channelbag, "fcurves", None) or []
