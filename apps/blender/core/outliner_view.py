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

from ._shared.cp_keys import PROSCENIO_TYPE
from .slot.slot_emit import is_slot_empty

#: Object categories, in Outliner sort order.
RANK_SLOT = 0  # slot Empty (top of the list, drives a slot)
RANK_ATTACHMENT = 1  # slot attachment mesh (indented under its slot)
RANK_ELEMENT_MESH = 2  # element mesh (Proscenio mesh / sprite, bone-parented or floating)
RANK_ARMATURE = 3  # armature
#: Rank for objects irrelevant to Proscenio (cameras, lights, etc.).
#: The Outliner hides these and the viewport-follow handler ignores them.
RANK_HIDDEN = 9


def category_rank(obj: object) -> int:
    """Rank ``obj`` for the Outliner's sort-by-category pass.

    Classifies by object kind only (icon / label / sort); Proscenio
    membership (authored element, picked armature) is a separate filter -
    see :func:`is_proscenio_member`.
    """
    if is_slot_empty(obj):
        return RANK_SLOT
    if getattr(obj, "type", None) == "ARMATURE":
        return RANK_ARMATURE
    if getattr(obj, "type", None) == "MESH":
        if is_slot_empty(getattr(obj, "parent", None)):
            return RANK_ATTACHMENT
        return RANK_ELEMENT_MESH
    return RANK_HIDDEN


def is_outliner_relevant(obj: object) -> bool:
    """True when ``obj`` is a kind the Proscenio Outliner can show (not a camera / light)."""
    return category_rank(obj) != RANK_HIDDEN


def is_proscenio_member(obj: object, *, rank: int, picked_armature_name: str | None) -> bool:
    """True when ``obj`` belongs to the Proscenio rig the Outliner shows.

    Beyond the kind check in :func:`category_rank`, this is the membership
    rule that keeps unrelated scene objects out of the list:

    - A free element mesh belongs only when it carries element data (the
      ``proscenio_type`` marker that import / Incorporate stamps) - a raw
      hand-modelled mesh does not, so it stays hidden until incorporated.
    - An armature belongs only when it is the one picked in the Skeleton
      panel (``scene.proscenio.active_armature``), so a stray rig does not
      crowd the list.
    - Slot Empties and their attachments always belong (a slot, and any mesh
      parented under it, is part of the rig by construction).
    """
    if rank == RANK_ELEMENT_MESH:
        getter = getattr(obj, "get", None)
        return callable(getter) and getter(PROSCENIO_TYPE) is not None
    if rank == RANK_ARMATURE:
        return picked_armature_name is not None and (
            getattr(obj, "name", None) == picked_armature_name
        )
    return rank != RANK_HIDDEN


def outliner_depth(rank: int) -> int:
    """Indent depth for the Outliner's parenting-tree layout.

    The armature is the root (0); slots and loose element meshes sit under it
    (1); a slot's attachments sit under the slot (2).
    """
    if rank == RANK_ARMATURE:
        return 0
    if rank == RANK_ATTACHMENT:
        return 2
    return 1


def hierarchy_sort_key(obj: object, *, rank: int) -> tuple[int, str, int, str]:
    """Sort key laying the flat Outliner out as a scene-parenting tree.

    Order: the picked armature first, then each slot immediately followed by
    its own attachments (grouped by slot name), then the loose element meshes -
    armature, then slot -> its mesh/sprite, then the free meshes - rather than a
    flat by-category grouping. Names are lower-cased so the order is
    case-insensitive (matching the panel's prior sort).
    """
    name = (getattr(obj, "name", "") or "").lower()
    if rank == RANK_ARMATURE:
        return (0, "", 0, name)
    if rank == RANK_SLOT:
        return (1, name, 0, "")
    if rank == RANK_ATTACHMENT:
        parent = getattr(obj, "parent", None)
        slot_name = (getattr(parent, "name", "") or "").lower()
        return (1, slot_name, 1, name)
    return (2, "", 0, name)


def outliner_sort_key(obj: object, *, rank: int, sort_alpha: bool) -> tuple[int, str, int, str]:
    """Sort key for the Outliner, honouring the native 'sort by name' toggle.

    With ``sort_alpha`` on (the UIList A-Z button), every row collapses into one
    bucket keyed by name, so the list is a plain alphabetical order and the
    parenting tree is dropped - the native toggle reads naturally. Off, the rows
    lay out as the parenting tree (:func:`hierarchy_sort_key`). The caller drops
    the depth indent in alpha mode too (see :func:`outliner_depth`).
    """
    if sort_alpha:
        return (0, "", 0, (getattr(obj, "name", "") or "").lower())
    return hierarchy_sort_key(obj, rank=rank)


def row_visible(
    obj: object,
    *,
    in_view_layer: bool,
    rank: int,
    is_member: bool,
    is_favorite: bool,
    favorites_only: bool,
    filter_text: str,
) -> bool:
    """Whether an Outliner source row should be shown.

    A row drops out when it is not a Proscenio category (``RANK_HIDDEN``),
    when it is not a Proscenio member (a raw mesh with no element data, or an
    armature that is not the picked one - see :func:`is_proscenio_member`),
    when its object is no longer in the view layer (a deleted / undone
    datablock that lingers in ``bpy.data.objects`` - the list is sourced
    from ``bpy.data`` so these would otherwise persist as click-into-warn
    ghosts), when the favorites-only filter is on and the row is not a
    favorite, or when it fails the active name filter.
    """
    if rank == RANK_HIDDEN:
        return False
    if not is_member:
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
