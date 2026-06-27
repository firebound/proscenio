"""Rig UI view-model: flatten a bone-collection tree into renderable rows.

Bpy-free. Reads only duck-typed collection attributes (``name``, ``children``),
so the Rig UI subpanel's nesting logic is unit-testable without booting Blender,
the same way :mod:`core.bone_view` backs the Skeleton bone list.

A branch collection (one with children) becomes a header row whose select
buttons are its direct children; each branch child then recurses into its own
header row (depth-first, pre-order), so a deep collection tree reads as a flat
sequence of grouped rows. A top-level leaf collection becomes a single
headerless row that is its own select button. The eye toggle and theme selector
of every row bind to :attr:`RigUIRow.collection_name`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class RigUIRow:
    """One drawable Rig UI row.

    ``header`` is the group-label text drawn above the row, or ``None`` for a
    headerless top-level leaf. ``collection_name`` is the collection the row's
    eye (and, on a top-level row, theme selector) act on. ``member_names`` are
    the select-button collections, left to right (a branch's direct children, or
    the leaf itself). ``is_top_level`` is true only for rows produced directly
    from a top-level collection: those carry the theme/color selector (it applies
    to the whole subtree below), while nested rows draw eye + buttons only - there
    is exactly one color control per top-level tree.
    """

    header: str | None
    collection_name: str
    member_names: tuple[str, ...]
    is_top_level: bool


def _name(collection: object) -> str:
    return (getattr(collection, "name", "") or "") if collection is not None else ""


def _children(collection: object) -> list[object]:
    return list(getattr(collection, "children", None) or [])


def rig_ui_rows(top_collections: Iterable[object] | None) -> list[RigUIRow]:
    """Flatten ``top_collections`` (the armature's top-level bone collections).

    Walks each top-level collection depth-first, pre-order: a branch emits its
    header row then recurses into the children that are themselves branches; a
    leaf emits a single headerless self-button row only when it sits at the top
    level (a leaf nested under a branch shows only as a button in that branch's
    row, never its own row). Only rows from a top-level collection are flagged
    ``is_top_level`` (they carry the theme selector); recursed rows are not.
    Top-level order is preserved.
    """
    rows: list[RigUIRow] = []

    def visit(collection: object, *, top: bool) -> None:
        children = _children(collection)
        name = _name(collection)
        if children:
            rows.append(
                RigUIRow(
                    header=name,
                    collection_name=name,
                    member_names=tuple(_name(c) for c in children),
                    is_top_level=top,
                )
            )
            for child in children:
                if _children(child):
                    visit(child, top=False)
        else:
            rows.append(
                RigUIRow(header=None, collection_name=name, member_names=(name,), is_top_level=top)
            )

    for collection in top_collections or []:
        visit(collection, top=True)
    return rows
