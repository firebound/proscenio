"""Pure helpers for the Custom-Property-backed PropertyGroup proxies.

The CP-canonical per-Object fields (``element_type``, ``frame``, the
region fields, the slot flags, ...) store their value in a single home:
the ``proscenio_*`` Custom Property (idprop) the headless writer reads.
The panel still edits them through a typed ``ProscenioObjectProps``
field, but that field is a ``get=``/``set=`` proxy that reads and writes
the idprop instead of storing anything itself. There is no mirror and no
hydrate - one field, one home.

Blender's ``EnumProperty`` ``get``/``set`` callbacks work in integer
space (the item's numeric identifier), while the idprop stores the string
identifier the writer expects. These two pure functions bridge the two
representations from the same ``items`` tuple the property declares, so
the mapping cannot drift from the dropdown. Kept bpy-free so the unit
tests exercise them without a Blender session.
"""

from __future__ import annotations

from collections.abc import Sequence


def enum_value_to_index(value: str, values: Sequence[str], *, default_index: int = 0) -> int:
    """Map a stored enum identifier string to its integer index.

    ``values`` is the ordered tuple of identifier strings, taken from the
    EnumProperty ``items``. An unknown or absent value falls back to
    ``default_index`` (clamped into range) rather than raising, so a
    hand-edited or legacy idprop can never crash the dropdown ``get``.
    """
    try:
        return values.index(value)
    except ValueError:
        return _clamp_index(default_index, values)


def enum_index_to_value(index: int, values: Sequence[str], *, default_index: int = 0) -> str:
    """Map an integer enum index back to its stored identifier string.

    An out-of-range index falls back to ``values[default_index]`` so a
    dropdown ``set`` always writes a valid identifier to the idprop.
    """
    if not values:
        raise ValueError("enum values must be non-empty")
    if 0 <= index < len(values):
        return values[index]
    return values[_clamp_index(default_index, values)]


def _clamp_index(index: int, values: Sequence[str]) -> int:
    if not values:
        return 0
    return max(0, min(index, len(values) - 1))
