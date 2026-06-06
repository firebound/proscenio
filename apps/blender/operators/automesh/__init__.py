"""Automesh operators.

Subpackage with:

- automesh           - PNG sprite -> annulus mesh
- automesh_authoring - PROSCENIO_OT_automesh_authoring modal
"""

from __future__ import annotations

from . import automesh, automesh_authoring


def register() -> None:
    automesh.register()
    automesh_authoring.register()


def unregister() -> None:
    automesh_authoring.unregister()
    automesh.unregister()
