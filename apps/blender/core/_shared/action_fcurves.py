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
