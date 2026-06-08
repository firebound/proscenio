"""Slot system operators.

Subpackage with:

- create.py        - PROSCENIO_OT_create_slot
- attachment.py    - PROSCENIO_OT_add_slot_attachment, PROSCENIO_OT_set_slot_default
- select.py        - PROSCENIO_OT_select_slot
- preview_shader.py - sprite_frame preview slicer setup / remove
"""

from __future__ import annotations

from . import attachment, create, preview_shader, select


def register() -> None:
    create.register()
    attachment.register()
    select.register()
    preview_shader.register()


def unregister() -> None:
    preview_shader.unregister()
    select.unregister()
    attachment.unregister()
    create.unregister()
