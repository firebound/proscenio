"""Shared bone-list view-model helpers: depth + hierarchy/flat sort key.

Bpy-free. Reads only duck-typed bone attributes (``name``, ``parent``), so it
stays unit-testable without booting Blender and backs the Skeleton panel's
``PROSCENIO_UL_bones`` the same way :mod:`core.outliner_view` backs the
Outliner. The two share one shape: an off-toggle key that lays the flat
``template_list`` out as the parenting tree, and an on-toggle key (the native
A-Z button) that collapses every row into one name-keyed bucket for a plain
alphabetical order.
"""

from __future__ import annotations


def bone_depth(bone: object) -> int:
    """Number of parents above ``bone`` (0 for a root bone).

    Drives the Skeleton list's indent so the flat list reads as the bone
    hierarchy. Walks ``bone.parent`` to the root; a bone with no ``parent``
    attribute reads as depth 0.
    """
    depth = 0
    parent = getattr(bone, "parent", None)
    while parent is not None:
        depth += 1
        parent = getattr(parent, "parent", None)
    return depth


def _ancestor_name_chain(bone: object) -> tuple[str, ...]:
    """Lower-cased names from the root down to ``bone`` inclusive.

    Tuple order makes a parent sort immediately before its children (a parent's
    chain is a prefix of each child's, and a prefix compares less than the
    longer tuple), and a whole subtree sort before a later sibling, so the key
    is a depth-first parenting-tree order.
    """
    chain: list[str] = []
    node: object | None = bone
    while node is not None:
        chain.append((getattr(node, "name", "") or "").lower())
        node = getattr(node, "parent", None)
    chain.reverse()
    return tuple(chain)


def bone_sort_key(bone: object, *, sort_alpha: bool) -> tuple[str, ...]:
    """Sort key for the Skeleton bone list, honoring the native A-Z toggle.

    With ``sort_alpha`` on (the UIList A-Z button) every row collapses into one
    bucket keyed by name, so the list is a plain case-insensitive alphabetical
    order and the parenting tree is dropped - the caller zeroes the depth indent
    in that mode. Off, the rows lay out as the parenting tree
    (:func:`_ancestor_name_chain`), depth-first with each parent before its
    children.
    """
    name = (getattr(bone, "name", "") or "").lower()
    if sort_alpha:
        return (name,)
    return _ancestor_name_chain(bone)
