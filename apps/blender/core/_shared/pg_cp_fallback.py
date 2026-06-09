"""PropertyGroup-first / Custom-Property-fallback reader.

The writer's headless path (Blender ``--background``, addon not
registered) cannot rely on ``Object.proscenio`` because the
PointerProperty wiring has not happened. The post-the authoring panel contract
is: read the PropertyGroup field first (canonical source), fall back
to the legacy Custom Property literal. This module is the single home
for that contract: the writer's per-field reads, the slot flag reads,
``core/_shared/region``, ``core/validation/_shared`` and the
``hydrate`` migrator all route through :func:`read_field` /
:func:`read_bool_flag` and the one :class:`CPCarrier` Protocol below,
rather than re-deriving the PG-first / CP-fallback logic each.

The presence rule is uniform: an explicit PropertyGroup value wins even
when it equals the type default (``False`` / ``0`` / ``""``); only a
``None`` or absent PG field falls through to the Custom Property, and
only a ``None`` or absent CP falls through to ``default``.

Pure Python. The ``obj`` parameter is typed against a Protocol that
matches both ``bpy.types.Object`` instances and the ``SimpleNamespace``
mocks used by the pytest suite (both implement ``getattr`` access and
either implement ``.get`` or do not - the helper guards both paths).
"""

from __future__ import annotations

from typing import Protocol, TypeVar, cast, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class CPCarrier(Protocol):
    """The one Custom-Property read Protocol: dict-style ``.get(key, default)``.

    Both ``bpy.types.Object`` (CP access via dict-like ``.get``) and
    pytest's ``SimpleNamespace`` mocks with a stubbed ``get`` satisfy
    this Protocol. Objects without ``.get`` skip the CP fallback. Shared
    by :func:`read_field`, :func:`read_bool_flag`, and the ``hydrate``
    migrator so the CP-access surface is declared once.
    """

    def get(self, key: str, default: object | None = None) -> object: ...


def read_field(obj: object, *, pg_field: str, cp_key: str, default: T) -> T:
    """Read a Proscenio field, PropertyGroup first, Custom Property fallback.

    Returns ``default`` when neither path is available. The PG path
    wins even when the field's value equals the type default - callers
    that want "explicit override only" semantics should test the PG
    presence themselves.

    The CP fallback is trusted to return a value compatible with ``T``:
    callers always know the field's domain type (int hframes, str type
    discriminator, etc) and the PropertyGroup-side writes are typed by
    Blender's PG schema. An incompatible CP value is a writer bug worth
    crashing on at the call-site rather than papering over here.
    """
    props = getattr(obj, "proscenio", None)
    if props is not None:
        value = getattr(props, pg_field, None)
        if value is not None:
            return cast(T, value)
    if isinstance(obj, CPCarrier):
        cp_value = obj.get(cp_key, None)
        if cp_value is not None:
            return cast(T, cp_value)
    return default


def read_bool_flag(obj: object, *, pg_field: str, cp_key: str) -> bool:
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
    if isinstance(obj, CPCarrier):
        return bool(obj.get(cp_key, False))
    return False
