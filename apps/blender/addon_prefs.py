"""Addon preferences - the single debug_mode toggle.

A minimal ``AddonPreferences`` so power users can flip on the developer
surface (the Diagnostics panel + the automesh Debug Pipeline subpanel)
without those panels cluttering the sidebar for everyone else.

``bl_idname`` must equal the addon's top-level package name so
``context.preferences.addons[...]`` resolves. This module lives at the
addon root, so its ``__package__`` is exactly that name.
"""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty

# The addon root package - the key both bl_idname and the prefs lookup use.
ADDON_PACKAGE = __package__ or ""


class ProscenioAddonPreferences(bpy.types.AddonPreferences):
    """Developer-surface toggle for the Proscenio addon."""

    bl_idname = ADDON_PACKAGE

    debug_mode: BoolProperty(  # type: ignore[valid-type]
        name="Debug mode",
        description=(
            "Show the developer surface: the Diagnostics panel and the automesh "
            "Debug Pipeline subpanel. Off by default so the sidebar stays focused "
            "on the authoring workflow"
        ),
        default=False,
    )

    def draw(self, _context: bpy.types.Context) -> None:
        self.layout.prop(self, "debug_mode")


def debug_mode_enabled(context: bpy.types.Context) -> bool:
    """True when the addon is enabled through Blender and debug_mode is on.

    Returns False when the addon was mounted outside Blender's addon system
    (e.g. a headless importlib smoke) so the developer panels stay hidden
    instead of crashing the poll.
    """
    prefs = context.preferences
    if prefs is None:
        return False
    addon = prefs.addons.get(ADDON_PACKAGE)  # type: ignore[attr-defined]
    if addon is None:
        return False
    return bool(getattr(addon.preferences, "debug_mode", False))


_classes: tuple[type, ...] = (ProscenioAddonPreferences,)


def register() -> None:
    if not ADDON_PACKAGE:
        raise RuntimeError(
            "Proscenio addon preferences need the addon package name, but "
            "__package__ was empty - import the addon as a package, not a loose module."
        )
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
