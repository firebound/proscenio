"""Shared list-view helpers: filter/sort flag computation + row cap.

Bpy-free. The UIList mixin (``panels/_list.py``) and the Outliner / Slots
``filter_items`` feed duck-typed rows plus name / visibility / sort callables
and get back the ``(flt_flags, flt_neworder)`` pair ``UIList.filter_items`` must
return, so the search + sort logic is one tested function across Bones, Actions,
Outliner and Slots. ``source_index_for_name`` (the identity->index resolver the
highlight-follow relies on) stays in :mod:`outliner_view`, its original home.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison


def _default_name(row: object) -> str:
    return str(getattr(row, "name", ""))


def _always_visible(_row: object) -> bool:
    return True


def compute_list_filter(
    rows: Sequence[object],
    *,
    bitflag: int,
    name_filter: str = "",
    name_of: Callable[[object], str] = _default_name,
    visible: Callable[[object], bool] = _always_visible,
    sort_key: Callable[[object], SupportsRichComparison] | None = None,
) -> tuple[list[int], list[int]]:
    """Return the ``(flt_flags, flt_neworder)`` a ``UIList.filter_items`` yields.

    A row gets the show bit (``bitflag``) when ``visible(row)`` is true and,
    with a non-empty ``name_filter``, the lowercased filter is a substring of
    ``name_of(row)`` lowercased. With ``sort_key`` left ``None`` the rows keep
    their source (collection) order - the right default for hierarchy-ordered
    lists like the bones - and ``flt_neworder`` is the empty list Blender reads
    as "no reorder". Pass a ``sort_key`` to reorder: ``flt_neworder[i]`` is then
    the post-sort position of source row ``i`` (``template_list`` maps the active
    source index through it), over a stable index sort so ties keep source order.
    """
    needle = name_filter.lower()
    n = len(rows)
    flt_flags = [0] * n
    for i, row in enumerate(rows):
        if not visible(row):
            continue
        if needle and needle not in name_of(row).lower():
            continue
        flt_flags[i] = bitflag
    if sort_key is None:
        return flt_flags, []
    order = sorted(range(n), key=lambda i: sort_key(rows[i]))
    flt_neworder = [0] * n
    for new_i, orig_i in enumerate(order):
        flt_neworder[orig_i] = new_i
    return flt_flags, flt_neworder


def clamped_rows(count: int, *, minimum: int, maximum: int) -> int:
    """Row count for ``template_list``: ``count`` clamped to ``[minimum, maximum]``.

    The shared row cap so a long list stops growing the panel unbounded while a
    short one still shows a few empty rows as drop targets.
    """
    return min(max(count, minimum), maximum)
