"""PropertyGroup-first / Custom-Property-fallback reader (SPEC 009 wave 9.1).

The writer's headless path (Blender ``--background``, addon not
registered) cannot rely on ``Object.proscenio`` because the
PointerProperty wiring has not happened. The post-SPEC 005 contract
is: read the PropertyGroup field first (canonical source), fall back
to the legacy Custom Property literal. Three independent
implementations of this protocol existed in ``writer.py``
(``_read_proscenio_field``, ``_is_slot_empty``, ``_read_slot_default``).
This module collapses them.

Pure Python. ``Any`` typing on the obj parameter so the writer can call
into the helper with both real ``bpy.types.Object`` instances and the
``SimpleNamespace`` mocks used by the pytest suite.
"""

from __future__ import annotations

from typing import Any


def read_field(obj: Any, *, pg_field: str, cp_key: str, default: Any) -> Any:
    """Read a Proscenio field, PropertyGroup first, Custom Property fallback.

    Returns ``default`` when neither path is available. The PG path
    wins even when the field's value equals the type default - callers
    that want "explicit override only" semantics should test the PG
    presence themselves.
    """
    props = getattr(obj, "proscenio", None)
    if props is not None:
        value = getattr(props, pg_field, None)
        if value is not None:
            return value
    if hasattr(obj, "get"):
        cp_value = obj.get(cp_key, None)
        if cp_value is not None:
            return cp_value
    return default


def read_bool_flag(obj: Any, *, pg_field: str, cp_key: str) -> bool:
    """Read a boolean flag, PG first, CP fallback. Defaults to ``False``.

    Specialised on bool because the most common shape (``is_slot``,
    ``material_isolated``, etc) is a flag predicate and casting
    consistently to ``bool`` keeps call sites tidy.

    The PG check uses a sentinel-vs-default check (not a truthiness
    check) so an explicit ``False`` on the PG correctly suppresses the
    CP fallback. The earlier truthy-only branch let a CP-True override
    a PG-False.
    """
    _missing = object()
    props = getattr(obj, "proscenio", None)
    if props is not None:
        pg_value = getattr(props, pg_field, _missing)
        if pg_value is not _missing and pg_value is not None:
            return bool(pg_value)
    if hasattr(obj, "get"):
        return bool(obj.get(cp_key, False))
    return False
