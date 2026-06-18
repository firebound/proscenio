"""Panel-chrome invariants: the N-panel opens with the tools collapsed.

In-Blender (the addon must be registered so the panel classes exist). Guards
the recurring annoyance of a Proscenio panel shipping without DEFAULT_CLOSED
and opening expanded.
"""

from __future__ import annotations

import bpy

# The About footer is the one top-level panel that stays open by design - it
# carries the version line + the Open help button, meant to be always reachable.
_ALWAYS_OPEN = {"PROSCENIO_PT_main"}


def _proscenio_top_level_panels() -> list[type]:
    """Registered Proscenio Panel classes that are top-level (no bl_parent_id)."""
    panels: list[type] = []
    for cls in bpy.types.Panel.__subclasses__():
        idname = getattr(cls, "bl_idname", "")
        if not idname.startswith("PROSCENIO_PT_"):
            continue
        if getattr(cls, "bl_category", "") != "Proscenio":
            continue
        if getattr(cls, "bl_parent_id", ""):
            continue  # a subpanel collapses with its parent
        panels.append(cls)
    return panels


def test_top_level_panels_open_collapsed() -> None:
    """Every top-level Proscenio panel except the About footer carries
    DEFAULT_CLOSED, so the N-panel never opens with a tool expanded."""
    panels = _proscenio_top_level_panels()
    # Sanity: the registration actually surfaced the panels (so an empty list
    # cannot make this pass vacuously).
    assert len(panels) >= 8, f"expected the Proscenio panels to be registered, found {len(panels)}"
    offenders = [
        cls.bl_idname
        for cls in panels
        if cls.bl_idname not in _ALWAYS_OPEN
        and "DEFAULT_CLOSED" not in set(getattr(cls, "bl_options", set()))
    ]
    assert not offenders, f"top-level panels missing DEFAULT_CLOSED: {sorted(offenders)}"
