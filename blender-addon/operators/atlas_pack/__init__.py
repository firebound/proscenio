"""Atlas pack operators package (SPEC 005.1.c.2).

Subpackage with:

- pack.py    -- PROSCENIO_OT_pack_atlas
- apply.py   -- PROSCENIO_OT_apply_packed_atlas
- unpack.py  -- PROSCENIO_OT_unpack_atlas
- _paths.py  -- shared filesystem layout + snapshot helpers
"""

from __future__ import annotations

from . import apply, pack, unpack


def register() -> None:
    pack.register()
    apply.register()
    unpack.register()


def unregister() -> None:
    unpack.unregister()
    apply.unregister()
    pack.unregister()
