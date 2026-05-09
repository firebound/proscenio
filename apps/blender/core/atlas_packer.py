"""Vendored 2D bin-packer for atlas generation (SPEC 005.1.c.2).

MaxRects with the Best Short Side Fit (BSSF) heuristic. Pure Python, no
external deps — chosen over `pytexturepacker` because pip-installing into
Blender's bundled Python is fragile cross-platform (paths differ Win/Mac/
Linux, permissions vary, future Blender ABI may break).

Reference: Jukka Jylänki, "A Thousand Ways to Pack the Bin", 2010.

Public API:

- :class:`Rect` — placement record, ``(x, y, w, h)`` in atlas pixels.
- :class:`PackResult` — atlas size + per-name placements.
- :func:`pack` — entry point. Takes ``[(name, w, h)]`` and packing config,
  returns a :class:`PackResult` or ``None`` if every size up to ``max_size``
  fails to fit.

Padding semantics: each placement reserves ``(w + 2*pad, h + 2*pad)`` of
atlas area; the source image goes at ``(x + pad, y + pad)``. The padded
border is left for the caller to fill (transparent in the first iteration;
edge-extend can be added later).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """Axis-aligned rectangle in atlas pixel space."""

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def area(self) -> int:
        return self.w * self.h


@dataclass(frozen=True)
class PackResult:
    """Result of a successful pack: atlas dimensions + per-name placements."""

    atlas_w: int
    atlas_h: int
    placements: dict[str, Rect]


def pack(
    items: list[tuple[str, int, int]],
    *,
    padding: int = 2,
    max_size: int = 4096,
    power_of_two: bool = False,
    start_size: int = 256,
) -> PackResult | None:
    """Pack ``items`` into the smallest atlas that fits up to ``max_size``.

    Each item is ``(name, source_w, source_h)`` — source image dimensions
    in pixels. Padding is added around each placement (``w + 2*padding``
    reserved). Sizes are tried in doubling steps starting from
    ``start_size`` until the items fit or ``max_size`` is exceeded.

    Returns ``None`` when no size up to ``max_size`` accepts every item.
    """
    if not items:
        return PackResult(0, 0, {})

    padded = [(name, w + 2 * padding, h + 2 * padding) for name, w, h in items]
    largest_dim = max(max(w, h) for _, w, h in padded)
    size = max(start_size, _next_pot(largest_dim) if power_of_two else largest_dim)

    while size <= max_size:
        result = _try_pack(padded, size, size, padding)
        if result is not None:
            return result
        size *= 2
        if power_of_two:
            size = _next_pot(size)

    return None


def _next_pot(n: int) -> int:
    """Smallest power-of-two >= n (for n >= 1)."""
    if n <= 1:
        return 1
    p = 1
    while p < n:
        p *= 2
    return p


def _try_pack(
    padded_items: list[tuple[str, int, int]],
    atlas_w: int,
    atlas_h: int,
    padding: int,
) -> PackResult | None:
    """Single attempt at the given atlas size. Returns None if any item fails."""
    free_rects: list[Rect] = [Rect(0, 0, atlas_w, atlas_h)]
    placements: dict[str, Rect] = {}

    sorted_items = sorted(padded_items, key=lambda it: max(it[1], it[2]), reverse=True)

    for name, w, h in sorted_items:
        slot = _find_best_slot(free_rects, w, h)
        if slot is None:
            return None
        placements[name] = Rect(
            slot.x + padding, slot.y + padding, w - 2 * padding, h - 2 * padding
        )
        used = Rect(slot.x, slot.y, w, h)
        free_rects = _split_free_rects(free_rects, used)
        free_rects = _prune_contained(free_rects)

    return PackResult(atlas_w, atlas_h, placements)


def _find_best_slot(free_rects: list[Rect], w: int, h: int) -> Rect | None:
    """Best Short Side Fit — pick the free rect whose shorter remaining side is smallest."""
    best: Rect | None = None
    best_short = float("inf")
    best_long = float("inf")
    for free in free_rects:
        if free.w < w or free.h < h:
            continue
        leftover_w = free.w - w
        leftover_h = free.h - h
        short = min(leftover_w, leftover_h)
        long_ = max(leftover_w, leftover_h)
        if short < best_short or (short == best_short and long_ < best_long):
            best = free
            best_short = short
            best_long = long_
    return best


def _split_free_rects(free_rects: list[Rect], used: Rect) -> list[Rect]:
    """Replace any free rect overlapping ``used`` with up to four sub-rects."""
    out: list[Rect] = []
    for free in free_rects:
        if not _overlaps(free, used):
            out.append(free)
            continue
        # Top sub-rect
        if used.y > free.y:
            out.append(Rect(free.x, free.y, free.w, used.y - free.y))
        # Bottom sub-rect
        if used.bottom < free.bottom:
            out.append(Rect(free.x, used.bottom, free.w, free.bottom - used.bottom))
        # Left sub-rect
        if used.x > free.x:
            out.append(Rect(free.x, free.y, used.x - free.x, free.h))
        # Right sub-rect
        if used.right < free.right:
            out.append(Rect(used.right, free.y, free.right - used.right, free.h))
    return out


def _overlaps(a: Rect, b: Rect) -> bool:
    return not (a.right <= b.x or b.right <= a.x or a.bottom <= b.y or b.bottom <= a.y)


def _prune_contained(rects: list[Rect]) -> list[Rect]:
    """Drop any rect fully contained inside another. Stable order."""
    kept: list[Rect] = []
    for i, r in enumerate(rects):
        contained = False
        for j, other in enumerate(rects):
            if i == j:
                continue
            if _contains(other, r):
                contained = True
                break
        if not contained:
            kept.append(r)
    return kept


def _contains(outer: Rect, inner: Rect) -> bool:
    return (
        outer.x <= inner.x
        and outer.y <= inner.y
        and outer.right >= inner.right
        and outer.bottom >= inner.bottom
    )
