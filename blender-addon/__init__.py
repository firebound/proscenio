"""Proscenio Blender addon entry point.

Registers properties, operators, and panels. Real logic lives in the
submodules. Registration order matters: properties first so operators
and panels see them at register time.
"""

from . import operators, panels, properties


def register() -> None:
    properties.register()
    operators.register()
    panels.register()


def unregister() -> None:
    panels.unregister()
    operators.unregister()
    properties.unregister()
