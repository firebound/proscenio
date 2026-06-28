"""Automesh operators.

Subpackage with:

- automesh           - PNG sprite -> annulus mesh
- automesh_authoring - PROSCENIO_OT_automesh_authoring modal
- pen_mesh_new       - PROSCENIO_OT_pen_mesh_new (from-blank pen element + launch)
"""

from __future__ import annotations

from . import automesh, automesh_authoring, pen_mesh_new


def register() -> None:
    automesh.register()
    automesh_authoring.register()
    pen_mesh_new.register()


def unregister() -> None:
    pen_mesh_new.unregister()
    automesh_authoring.unregister()
    automesh.unregister()
