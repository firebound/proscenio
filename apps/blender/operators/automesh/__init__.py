"""Automesh operators.

Subpackage with:

- automesh             - PNG sprite -> annulus mesh
- automesh_authoring   - PROSCENIO_OT_automesh_authoring modal
- draw_mesh_vertices   - PROSCENIO_OT_draw_mesh_vertices (Manual Draw, spec 070)
"""

from __future__ import annotations

from . import automesh, automesh_authoring, draw_mesh_vertices


def register() -> None:
    automesh.register()
    automesh_authoring.register()
    draw_mesh_vertices.register()


def unregister() -> None:
    draw_mesh_vertices.unregister()
    automesh_authoring.unregister()
    automesh.unregister()
