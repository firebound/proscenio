"""Panel-chrome invariants: the N-panel opens with the tools collapsed.

In-Blender (the addon must be registered so the panel classes exist). Guards
the recurring annoyance of a Proscenio panel shipping without DEFAULT_CLOSED
and opening expanded - now for subpanels too, so expanding a section does not
spill its primary subpanel open.
"""

from __future__ import annotations

import bpy

# The About footer is the one panel that stays open by design - it carries the
# version line + the Open help button, meant to be always reachable.
_ALWAYS_OPEN = {"PROSCENIO_PT_main"}


def _proscenio_panels() -> list[type]:
    """Every registered Proscenio Panel class (top-level + subpanels)."""
    panels: list[type] = []
    for cls in bpy.types.Panel.__subclasses__():
        idname = getattr(cls, "bl_idname", "")
        if not idname.startswith("PROSCENIO_PT_"):
            continue
        if getattr(cls, "bl_category", "") != "Proscenio":
            continue
        panels.append(cls)
    return panels


def test_every_panel_opens_collapsed() -> None:
    """Every Proscenio panel - top-level and subpanel - except the About footer
    carries DEFAULT_CLOSED, so nothing opens expanded (a subpanel no longer
    spills open when its parent is expanded)."""
    panels = _proscenio_panels()
    # Sanity: the registration actually surfaced the panels (so an empty list
    # cannot make this pass vacuously). The tree is well over a dozen with
    # subpanels included.
    assert len(panels) >= 12, f"expected the Proscenio panels to be registered, found {len(panels)}"
    offenders = [
        cls.bl_idname
        for cls in panels
        if cls.bl_idname not in _ALWAYS_OPEN
        and "DEFAULT_CLOSED" not in getattr(cls, "bl_options", set())
    ]
    assert not offenders, f"panels missing DEFAULT_CLOSED: {sorted(offenders)}"
