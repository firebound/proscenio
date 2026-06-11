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
