"""Slot system operators (SPEC 004).

Subpackage with:

- create.py        - PROSCENIO_OT_create_slot
- attachment.py    - PROSCENIO_OT_add_slot_attachment, PROSCENIO_OT_set_slot_default
- preview_shader.py - sprite_frame preview slicer setup / remove
"""

from __future__ import annotations

from . import attachment, create, preview_shader


def register() -> None:
    create.register()
    attachment.register()
    preview_shader.register()


def unregister() -> None:
    preview_shader.unregister()
    attachment.unregister()
    create.unregister()
