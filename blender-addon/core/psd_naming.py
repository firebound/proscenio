"""PSD layer naming convention helpers (SPEC 006 Wave 6.2).

Pure Python — no bpy, no Pillow. The JSX exporter (Wave 6.1) uses the
same rules in JavaScript when classifying layer groups; this module
provides the Python mirror so the importer can sanity-check that a
sprite_frame manifest entry's children actually look like indexed
frames before composing the spritesheet.

Locked conventions (SPEC 006 D9):

- Indexed frame layer names match one of:
    - ``\\d+``           (e.g. ``0``, ``1``, ``12``)
    - ``frame_<n>``     (e.g. ``frame_0``, ``frame-1``)
    - ``<group>_<n>``   (e.g. ``eye_0``, ``eye-1``)

- A layer group qualifies as a sprite_frame source iff every child
  matches one of the patterns above with the **same** convention,
  the indices are 0-based, contiguous, and start at 0.

- Fallback (SPEC 007 D4): top-level layers ``eye_0``, ``eye_1`` … get
  grouped by stripping the ``_<index>`` suffix.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

_PURE_DIGIT_RE = re.compile(r"^(\d+)$")
_FRAME_PREFIX_RE = re.compile(r"^frame[_-](\d+)$", re.IGNORECASE)
_GROUP_PREFIX_RE = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9]*)[_-](?P<idx>\d+)$")


Convention = Literal["digit", "frame_prefix", "group_prefix"]


@dataclass(frozen=True)
class IndexedName:
    """Result of matching a layer name against a frame convention."""

    base: str  # implied group name; "" when the pattern is just digits or frame_N
    index: int
    convention: Convention


def match_indexed_frame(name: str) -> IndexedName | None:
    """Match ``name`` against any of the locked frame conventions.

    Returns the parsed :class:`IndexedName` or ``None`` if no convention
    matches. The ``base`` field carries the implied group name when the
    naming carries one (``eye_0`` → base ``eye``); for pure-digit and
    ``frame_<n>`` matches it is the empty string — context (the parent
    PSD group name) supplies the group identity in those cases.
    """
    pure = _PURE_DIGIT_RE.match(name)
    if pure is not None:
        return IndexedName(base="", index=int(pure.group(1)), convention="digit")
    framed = _FRAME_PREFIX_RE.match(name)
    if framed is not None:
        return IndexedName(
            base="", index=int(framed.group(1)), convention="frame_prefix"
        )
    grouped = _GROUP_PREFIX_RE.match(name)
    if grouped is not None:
        return IndexedName(
            base=grouped.group("name"),
            index=int(grouped.group("idx")),
            convention="group_prefix",
        )
    return None


def is_uniform_indexed_group(child_names: list[str]) -> bool:
    """Return True iff ``child_names`` are a clean indexed frame set.

    Rules (all must hold):

    - At least 2 children.
    - Every child name matches a frame convention.
    - All children use the **same** convention (no mixing pure-digit
      with ``frame_<n>``).
    - When the convention carries a base, all children share the base.
    - Indices are 0-based, contiguous, with no duplicates.
    """
    if len(child_names) < 2:
        return False
    matches: list[IndexedName] = []
    for name in child_names:
        m = match_indexed_frame(name)
        if m is None:
            return False
        matches.append(m)
    conventions = {m.convention for m in matches}
    if len(conventions) != 1:
        return False
    bases = {m.base for m in matches}
    if len(bases) != 1:
        return False
    indices = sorted(m.index for m in matches)
    if indices[0] != 0:
        return False
    return all(indices[i] == i for i in range(len(indices)))


def group_by_index_suffix(layer_names: list[str]) -> dict[str, list[tuple[int, str]]]:
    """Aggregate flat ``<base>_<index>`` layers (SPEC 007 D4 fallback).

    Walks ``layer_names`` and groups every entry that matches the
    ``<base>_<index>`` convention by base. Layers that do not match
    are returned under the synthetic key ``""`` so callers can decide
    how to handle the leftovers.

    Result: ``{ base: [(index, original_name), ...sorted by index] }``.
    """
    out: dict[str, list[tuple[int, str]]] = {}
    for name in layer_names:
        match = _GROUP_PREFIX_RE.match(name)
        if match is None:
            out.setdefault("", []).append((-1, name))
            continue
        base = match.group("name")
        idx = int(match.group("idx"))
        out.setdefault(base, []).append((idx, name))
    for entries in out.values():
        entries.sort(key=lambda pair: pair[0])
    return out
