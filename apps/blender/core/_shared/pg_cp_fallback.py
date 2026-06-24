"""Custom-Property (idprop) reader for the per-Object Proscenio fields.

Since spec 037 each CP-canonical field has one storage home: the
``proscenio_*`` Custom Property (idprop) on the Object. The editor edits
it through a ``get=``/``set=`` PropertyGroup proxy, but the value lives in
the idprop, which exists on the Object regardless of addon registration -
so the headless writer (Blender ``--background``, addon not registered)
reads it directly. This module is the single home for that read: the
writer's per-field reads, the slot flag reads, ``core/_shared/region``,
and ``core/validation/_shared`` all route through :func:`read_field` /
:func:`read_bool_flag` and the one :class:`CPCarrier` Protocol below.

Pure Python. The ``obj`` parameter is typed against a Protocol that
matches both ``bpy.types.Object`` instances and the ``SimpleNamespace``
mocks used by the pytest suite (both expose dict-style ``.get``).
"""

from __future__ import annotations

from typing import Protocol, TypeVar, cast, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class CPCarrier(Protocol):
    """The one Custom-Property read Protocol: dict-style ``.get(key, default)``.

    Both ``bpy.types.Object`` (CP access via dict-like ``.get``) and
    pytest's ``SimpleNamespace`` mocks with a stubbed ``get`` satisfy
    this Protocol. Objects without ``.get`` read as absent. Shared by
    :func:`read_field` and :func:`read_bool_flag` so the CP-access
    surface is declared once.
    """

    def get(self, key: str, default: object | None = None) -> object: ...


def read_field(obj: object, *, cp_key: str, default: T) -> T:
    """Read a Proscenio field from its ``cp_key`` Custom Property (idprop).

    Returns ``default`` when the idprop is absent or ``None``. The value
    lives only in the idprop (the editor proxy reads the same idprop).

    The idprop is trusted to return a value compatible with ``T``: callers
    always know the field's domain type (int hframes, str type
    discriminator, etc). An incompatible idprop value is a writer bug worth
    crashing on at the call-site rather than papering over here.
    """
    if isinstance(obj, CPCarrier):
        cp_value = obj.get(cp_key, None)
        if cp_value is not None:
            return cast(T, cp_value)
    return default


def read_bool_flag(obj: object, *, cp_key: str) -> bool:
    """Read a boolean flag from its ``cp_key`` idprop. Defaults to ``False``.

    Specialised on bool because the most common shape (``is_slot``, etc) is
    a flag predicate and casting consistently to ``bool`` keeps call sites
    tidy.
    """
    if isinstance(obj, CPCarrier):
        return bool(obj.get(cp_key, False))
    return False
