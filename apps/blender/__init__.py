"""Proscenio Blender addon entry point.

Registers properties, operators, and panels. Real logic lives in the
submodules. Registration order matters: properties first so operators
and panels see them at register time.
"""

from . import addon_prefs, operators, panels, properties
from .core import i18n
from .core.bpy_helpers import preview_icons


def register() -> None:
    i18n.register()
    preview_icons.register()
    addon_prefs.register()
    properties.register()
    operators.register()
    panels.register()


def unregister() -> None:
    panels.unregister()
    operators.unregister()
    properties.unregister()
    addon_prefs.unregister()
    preview_icons.unregister()
    i18n.unregister()
