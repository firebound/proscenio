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
from bpy.props import BoolProperty, EnumProperty

from .core._shared.report import set_min_level

# The addon root package - the key both bl_idname and the prefs lookup use.
ADDON_PACKAGE = __package__ or ""


def _on_log_level_update(self: ProscenioAddonPreferences, _context: bpy.types.Context) -> None:
    """Push the chosen verbosity into the shared report gate immediately."""
    set_min_level(self.log_level)


class ProscenioAddonPreferences(bpy.types.AddonPreferences):
    """Developer-surface toggle for the Proscenio addon."""

    bl_idname = ADDON_PACKAGE

    log_level: EnumProperty(  # type: ignore[valid-type]
        name="Log level",
        description=(
            "How much Proscenio operators report to the Info log. Errors only = "
            "just failures; Info = the default running commentary"
        ),
        items=[
            ("errors", "Errors only", "Only error reports surface"),
            ("info", "Info", "Info + warnings + errors (default)"),
        ],
        default="info",
        update=_on_log_level_update,
    )

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
        box = self.layout.box()
        box.label(text="Developer", icon="TOOL_SETTINGS")
        box.prop(self, "log_level")
        box.prop(self, "debug_mode")


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
    _sync_log_level_from_prefs()


def _sync_log_level_from_prefs() -> None:
    """Best-effort: push the saved log_level into the report gate at register.

    The ``update`` callback covers runtime changes; this applies a value the
    user saved in a previous session. Guarded so a headless mount (no
    ``context.preferences``) leaves the report gate at its default.
    """
    prefs = bpy.context.preferences
    if prefs is None:
        return
    addon = prefs.addons.get(ADDON_PACKAGE)  # type: ignore[attr-defined]
    if addon is not None:
        set_min_level(str(getattr(addon.preferences, "log_level", "info")))


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
