"""Splice extend strokes into the outer contour (the weight-paint-automesh).

Used by Stage 2 EDIT_OUTLINE to extend the auto-walker silhouette with
artist-drawn paths. Pure module: no bpy / mathutils.

Wrap-around case (``exit_outer_idx < entry_outer_idx``): when the
replacement arc wraps across the closed-loop seam, the splice takes the
FORWARD arc from entry to end-of-list plus the arc from 0 to exit. The
shorter direction is not computed; the artist's stroke geometry picks the
intended arc.

Fully-outside strokes return None with no side effect; callers log a
WARNING so the artist knows the stroke had no effect.
"""

from __future__ import annotations

from collections.abc import Sequence

from .._shared.geometry_2d import Point2D
from .._shared.nearest import nearest_index
from .density import point_in_polygon


def _nearest_outer_vert_index(query: Point2D, outer: Sequence[Point2D]) -> int:
    """Index of the closest outer vert (linear scan; outer is typically <256 verts)."""
    return nearest_index(query, outer)


def _extract_outside_run(
    stroke: list[Point2D],
    inside_mask: list[bool],
) -> tuple[list[Point2D], Point2D, Point2D] | None:
    """Return ``(outside_run, anchor_in, anchor_out)`` for an extend stroke.

    ``outside_run`` is the contiguous outside portion of the stroke;
    ``anchor_in`` / ``anchor_out`` are the inside samples that bracket it
    (equal when the stroke only crosses the boundary once). Returns
    ``None`` when no non-empty outside run exists.
    """
    n = len(stroke)
    departure_idx: int | None = None
    # First transition inside -> outside marks the last inside vert.
    for i in range(1, n):
        if inside_mask[i - 1] and not inside_mask[i]:
            departure_idx = i - 1
            break

    if departure_idx is None:
        # Stroke starts outside; treat the arc up to the first inside vert
        # as the outside run, anchored on that single re-entry sample.
        first_inside = next((i for i, m in enumerate(inside_mask) if m), None)
        if first_inside is None or first_inside == 0:
            return None
        anchor = stroke[first_inside]
        return list(stroke[:first_inside]), anchor, anchor

    # Walk forward from departure to find the first re-entry.
    return_idx: int | None = None
    for i in range(departure_idx + 2, n):
        if inside_mask[i]:
            return_idx = i
            break

    if return_idx is None:
        # Stroke leaves and never returns - single-point splice anchor.
        anchor = stroke[departure_idx]
        outside_run = list(stroke[departure_idx + 1 :])
        return (outside_run, anchor, anchor) if outside_run else None

    outside_run = list(stroke[departure_idx + 1 : return_idx])
    if not outside_run:
        return None
    return outside_run, stroke[departure_idx], stroke[return_idx]


def _splice_outside_run(
    outer: list[Point2D],
    outside_run: list[Point2D],
    entry_outer_idx: int,
    exit_outer_idx: int,
) -> list[Point2D]:
    """Insert ``outside_run`` into ``outer`` between the entry/exit verts.

    Take ``outer[0..entry]`` inclusive, then the run, then continue from
    ``exit`` onward. The wrap case (``exit < entry``) keeps only the
    complementary arc ``[exit..entry]`` plus the run; same-vert reinserts
    at the shared index.
    """
    spliced: list[Point2D] = []
    if exit_outer_idx > entry_outer_idx:
        spliced.extend(outer[: entry_outer_idx + 1])
        spliced.extend(outside_run)
        spliced.extend(outer[exit_outer_idx:])
    elif exit_outer_idx == entry_outer_idx:
        spliced.extend(outer[: entry_outer_idx + 1])
        spliced.extend(outside_run)
        spliced.extend(outer[entry_outer_idx:])
    else:
        spliced.extend(outer[exit_outer_idx : entry_outer_idx + 1])
        spliced.extend(outside_run)
    return spliced


def splice_extend_stroke(
    outer: list[Point2D],
    stroke: list[Point2D],
) -> list[Point2D] | None:
    """Splice an extend stroke's outside portion into the closed outer polyline.

    Returns the new outer polyline with the outside portion of the stroke
    inserted between the closest outer verts to the stroke's last-inside
    and first-re-entry samples. Returns None when:
    - Stroke is entirely inside the silhouette (not an extend - caller should
      drop or route to cut path)
    - Stroke is entirely outside silhouette (no entry/exit; caller logs WARN)
    - Stroke has < 2 samples or outer has < 3 verts

    The returned polyline preserves the original outer ordering and inserts
    the outside_run in walker direction (no reversal).

    Wrap-around: when exit_outer_idx < entry_outer_idx the outside_run is
    inserted at entry_outer_idx, then outer continues from exit_outer_idx to
    the end, then from 0 to entry_outer_idx (forward wrap). This correctly
    handles strokes that cross the polyline seam without computing shorter-arc
    direction (v1 limitation documented in module docstring).
    """
    if len(stroke) < 2 or len(outer) < 3:
        return None

    inside_mask = [point_in_polygon(p, outer) for p in stroke]

    if all(inside_mask):
        return None  # not an extend stroke

    if not any(inside_mask):
        return None  # fully outside - caller handles WARN

    run = _extract_outside_run(stroke, inside_mask)
    if run is None:
        return None
    outside_run, anchor_in, anchor_out = run

    entry_outer_idx = _nearest_outer_vert_index(anchor_in, outer)
    exit_outer_idx = _nearest_outer_vert_index(anchor_out, outer)
    spliced = _splice_outside_run(outer, outside_run, entry_outer_idx, exit_outer_idx)
    return spliced if len(spliced) >= 3 else None


def splice_extend_strokes(
    outer: list[Point2D],
    extend_strokes: list[list[Point2D]],
) -> list[Point2D]:
    """Apply splice for each stroke sequentially.

    Each splice's output becomes the input outer for the next stroke so
    multiple extend strokes compose. Strokes that return None (fully inside
    or fully outside) are skipped without mutating the running outer.
    """
    current = list(outer)
    for stroke in extend_strokes:
        result = splice_extend_stroke(current, stroke)
        if result is not None:
            current = result
    return current
