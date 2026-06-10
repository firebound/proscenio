"""Decode a JSON-encoded Custom Property into a list or dict.

The "read ``obj.get(KEY)``, ``json.loads`` a stored string (or coerce the raw
IDProperty), fall back to an empty collection on absence or corruption" idiom
was hand-written across the skinning bone-mode store, the authoring
stroke / Steiner persistence, the atlas pre-pack snapshot, and the
weight-overlay provenance read. This module owns the decode; callers keep
their own per-shape parsing (filter, point-coerce, stroke-parse) on top.

Runtime is ``bpy``-free (the type hint sits under ``TYPE_CHECKING``; the body
reads through the dict-style ``.get`` Blender exposes on Objects and the
pytest mocks stub). A returned collection is always a fresh ``list`` / ``dict``
the caller may mutate.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bpy


def read_json_list_cp(obj: bpy.types.Object, key: str) -> list[object]:
    """Decode the JSON list stored under ``key``.

    Empty list when the property is absent, is not a JSON string / array, or
    fails to parse. A stored JSON string is parsed; a raw IDProperty array is
    coerced with ``list``.
    """
    raw = obj.get(key)
    if raw is None:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else list(raw)
    except (ValueError, TypeError):
        return []
    return data if isinstance(data, list) else []


def read_json_dict_cp(obj: bpy.types.Object, key: str) -> dict[str, object]:
    """Decode the JSON dict stored under ``key``.

    Empty dict when the property is absent, is not a JSON string / mapping, or
    fails to parse. A stored JSON string is parsed; a raw IDProperty group is
    coerced with ``dict``.
    """
    raw = obj.get(key)
    if raw is None:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}
