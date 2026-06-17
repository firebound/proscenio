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


def row_visible(
    obj: object,
    *,
    in_view_layer: bool,
    rank: int,
    is_favorite: bool,
    favorites_only: bool,
    filter_text: str,
) -> bool:
    """Whether an Outliner source row should be shown.

    A row drops out when it is not a Proscenio category (``RANK_HIDDEN``),
    when its object is no longer in the view layer (a deleted / undone
    datablock that lingers in ``bpy.data.objects`` - the list is sourced
    from ``bpy.data`` so these would otherwise persist as click-into-warn
    ghosts), when the favorites-only filter is on and the row is not a
    favorite, or when it fails the active name filter.
    """
    if rank == RANK_HIDDEN:
        return False
    if not in_view_layer:
        return False
    if favorites_only and not is_favorite:
        return False
    return not (filter_text and filter_text not in getattr(obj, "name", "").lower())


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
