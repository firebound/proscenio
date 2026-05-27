"""Splice extend strokes into the outer contour (SPEC 013 AS-AM10).

Used by Stage 2 USER_OUTER to extend the auto-walker silhouette with
artist-drawn paths. Pure module: no bpy / mathutils.

Wrap-around case (exit_outer_idx < entry_outer_idx) notes
----------------------------------------------------------
When the stroke's departure and return points map to outer verts where
exit < entry (i.e. the replacement arc wraps across the closed-loop seam),
v1 takes the FORWARD arc from entry to end-of-list plus the arc from 0 to
exit. This guarantees the outside_run is inserted at the right seam point
while the two outer arcs it replaces are the ones between entry and exit
going *forward* (the shorter direction is not computed; the artist's stroke
geometry itself already picks the intended arc). A future v2 could compute
the shorter-arc direction and always choose it.

Limitation: fully-outside strokes return None with no side effect; callers
are responsible for logging a WARNING so the artist knows the stroke had no
effect.
"""

from __future__ import annotations

from collections.abc import Sequence

Point2D = tuple[float, float]


def _point_in_polygon(point: Point2D, polygon: Sequence[Point2D]) -> bool:
    """Ray-casting point-in-polygon test."""
    if len(polygon) < 3:
        return False
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y):
            slope = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < slope:
                inside = not inside
        j = i
    return inside


def _nearest_outer_vert_index(query: Point2D, outer: Sequence[Point2D]) -> int:
    """Index of the closest outer vert (linear scan; outer is typically <256 verts)."""
    qx, qy = query
    best_idx = 0
    best_d2 = float("inf")
    for i, (vx, vy) in enumerate(outer):
        d2 = (vx - qx) ** 2 + (vy - qy) ** 2
        if d2 < best_d2:
            best_d2 = d2
            best_idx = i
    return best_idx


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

    inside_mask = [_point_in_polygon(p, outer) for p in stroke]

    if all(inside_mask):
        return None  # not an extend stroke

    if not any(inside_mask):
        return None  # fully outside - caller handles WARN

    n = len(stroke)
    departure_idx: int | None = None

    # Find first transition inside -> outside.
    for i in range(1, n):
        if inside_mask[i - 1] and not inside_mask[i]:
            departure_idx = i - 1  # last inside vert before going outside
            break

    if departure_idx is None:
        # Stroke starts outside; find first inside vert - treat the arc from
        # stroke[0] to that vert as the outside run, anchor on first_inside.
        first_inside = next((i for i, m in enumerate(inside_mask) if m), None)
        if first_inside is None or first_inside == 0:
            return None
        outside_run = list(stroke[:first_inside])
        anchor_in = stroke[first_inside]
        anchor_out = stroke[first_inside]
    else:
        # Walk forward from departure_idx+1 to find the first re-entry.
        return_idx: int | None = None
        for i in range(departure_idx + 2, n):
            if inside_mask[i]:
                return_idx = i
                break

        if return_idx is None:
            # Stroke leaves and never returns; outside run = stroke[departure_idx+1:]
            outside_run = list(stroke[departure_idx + 1 :])
            anchor_in = stroke[departure_idx]
            anchor_out = stroke[departure_idx]  # single-point splice
        else:
            outside_run = list(stroke[departure_idx + 1 : return_idx])
            anchor_in = stroke[departure_idx]
            anchor_out = stroke[return_idx]

    if not outside_run:
        return None

    entry_outer_idx = _nearest_outer_vert_index(anchor_in, outer)
    exit_outer_idx = _nearest_outer_vert_index(anchor_out, outer)

    # Build spliced outer. Take outer[0..entry_outer_idx] inclusive, then
    # insert the outside run, then continue from exit_outer_idx onward.
    # The wrap case (exit <= entry) is handled by taking outer[exit..end]
    # which naturally brings the tail before 0..entry arcs back in order.
    spliced: list[Point2D] = []

    if exit_outer_idx > entry_outer_idx:
        # Normal case: entry before exit in list order.
        # outer[0..entry] + outside_run + outer[exit..N-1]
        for i in range(entry_outer_idx + 1):
            spliced.append(outer[i])
        spliced.extend(outside_run)
        for i in range(exit_outer_idx, len(outer)):
            spliced.append(outer[i])
    elif exit_outer_idx == entry_outer_idx:
        # Stroke departs and returns at same outer vert - insert run there.
        for i in range(entry_outer_idx + 1):
            spliced.append(outer[i])
        spliced.extend(outside_run)
        for i in range(entry_outer_idx, len(outer)):
            spliced.append(outer[i])
    else:
        # Wrap-around case: exit < entry. The forward arc from entry through
        # the seam to exit is the portion being REPLACED by outside_run.
        # Keep only the complementary arc [exit..entry] + outside_run.
        for i in range(exit_outer_idx, entry_outer_idx + 1):
            spliced.append(outer[i])
        spliced.extend(outside_run)

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
