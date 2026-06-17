"""Shared Outliner view-model helpers: category rank + identity->index.

Bpy-free. Reads only duck-typed attributes (``type``, ``parent``,
``name``) plus :func:`is_slot_empty`, so it stays unit-testable without
booting Blender and can back both the Outliner UIList (sort + filter)
and the viewport-follow handler from one source of truth. Spec 046's
reusable list component imports the identity->index mapping from here
rather than re-deriving it.
"""

from __future__ import annotations

from collections.abc import Iterable

from .slot.slot_emit import is_slot_empty

#: Rank for objects irrelevant to Proscenio (cameras, lights, etc.).
#: The Outliner hides these and the viewport-follow handler ignores them.
RANK_HIDDEN = 9


def category_rank(obj: object) -> int:
    """Rank ``obj`` for the Outliner's sort-by-category pass.

    0 = slot Empty (top of the list, drives a slot).
    1 = slot attachment mesh (rendered indented under its slot).
    2 = element mesh (Proscenio mesh / sprite, parented to bone or floating).
    3 = armature.
    9 = irrelevant for Proscenio (cameras, lights, etc.) - hidden.
    """
    if is_slot_empty(obj):
        return 0
    if getattr(obj, "type", None) == "ARMATURE":
        return 3
    if getattr(obj, "type", None) == "MESH":
        if is_slot_empty(getattr(obj, "parent", None)):
            return 1
        return 2
    return RANK_HIDDEN


def is_outliner_relevant(obj: object) -> bool:
    """True when ``obj`` is a row the Proscenio Outliner shows."""
    return category_rank(obj) != RANK_HIDDEN


def source_index_for_name(objects: Iterable[object], target_name: str) -> int | None:
    """Index of the object named ``target_name`` in ``objects`` source order.

    ``template_list``'s active index is an index into the *source*
    collection (``bpy.data.objects``), which Blender maps to the visible
    row through ``flt_neworder`` internally - so the highlight follows the
    object wherever the category sort places it. Returns ``None`` when no
    object carries the name (a stale or freed row), letting callers skip
    the write rather than point the highlight at nothing.
    """
    for idx, candidate in enumerate(objects):
        if getattr(candidate, "name", None) == target_name:
            return idx
    return None
