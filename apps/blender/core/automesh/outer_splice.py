"""Splice extend strokes into the outer contour (the weight-paint-automesh).

Used by Stage 2 EDIT_OUTLINE to extend the auto-walker silhouette with
artist-drawn paths. Pure module: no bpy / mathutils.

The splice anchors at the points where the stroke actually CROSSES the
contour, not at the outer vertices nearest the stroke's inside samples. The
crossing points are unambiguous, so the result does not depend on how sparse
the pen clicks are, on the contour's winding direction, or on where the
polyline seam (index 0) falls - the three traps the nearest-vertex splice fell
into (logged in specs/029).

For a two-sided extend (the stroke leaves the silhouette and re-enters) the two
crossings split the contour into two arcs. The bump replaces one of them; the
correct one is picked by area - growing the silhouette - so a stroke drawn
against the winding or across the seam can never amputate the contour.

On-boundary stroke samples count as inside (the pen snaps endpoints exactly
onto contour verts), so a snap-anchored extend is not misread as fully outside
and dropped.

Strokes that touch the silhouette only once (a half gesture: out-and-not-back,
or starting outside) splice as a spike rooted at the single crossing. Strokes
entirely inside or entirely outside return None with no side effect; callers
log a WARNING so the artist knows the stroke had no effect.
"""

from __future__ import annotations

from collections.abc import Sequence

from .._shared.geometry_2d import Point2D
from .density import point_in_polygon, point_on_contour

_INTERSECT_EPSILON = 1e-9
_PARALLEL_EPSILON = 1e-12


def _inside_or_on(point: Point2D, outer: Sequence[Point2D]) -> bool:
    """Inside the contour OR on its boundary (snap-anchored endpoints count)."""
    return point_in_polygon(point, outer) or point_on_contour(point, outer)


def _segment_intersection(
    p0: Point2D, p1: Point2D, q0: Point2D, q1: Point2D
) -> tuple[Point2D, float, float] | None:
    """Intersection of segment ``p0->p1`` with ``q0->q1``.

    Returns ``(point, t, u)`` where ``t`` is the parameter along ``p`` and
    ``u`` the parameter along ``q``, both in ``[0, 1]``. Returns None when the
    segments are parallel/collinear (handled by the boundary mask) or do not
    meet within their spans.
    """
    rx, ry = p1[0] - p0[0], p1[1] - p0[1]
    sx, sy = q1[0] - q0[0], q1[1] - q0[1]
    denom = rx * sy - ry * sx
    if abs(denom) < _PARALLEL_EPSILON:
        return None
    qpx, qpy = q0[0] - p0[0], q0[1] - p0[1]
    t = (qpx * sy - qpy * sx) / denom
    u = (qpx * ry - qpy * rx) / denom
    if not (-_INTERSECT_EPSILON <= t <= 1.0 + _INTERSECT_EPSILON):
        return None
    if not (-_INTERSECT_EPSILON <= u <= 1.0 + _INTERSECT_EPSILON):
        return None
    point = (p0[0] + t * rx, p0[1] + t * ry)
    return point, min(max(t, 0.0), 1.0), min(max(u, 0.0), 1.0)


def _seg_contour_crossing(
    seg0: Point2D, seg1: Point2D, outer: Sequence[Point2D], *, pick_far: bool
) -> tuple[Point2D, int, float] | None:
    """Where stroke segment ``seg0->seg1`` crosses the closed ``outer`` contour.

    Returns ``(crossing_point, edge_index, edge_param)`` for the crossing
    nearest ``seg0`` (``pick_far`` False) or nearest ``seg1`` (``pick_far``
    True), so an exit segment anchors at its first boundary hit and an entry
    segment at its last. ``edge_param`` orders multiple crossings that land on
    the same edge.
    """
    n = len(outer)
    best: tuple[float, Point2D, int, float] | None = None
    for edge in range(n):
        hit = _segment_intersection(seg0, seg1, outer[edge], outer[(edge + 1) % n])
        if hit is None:
            continue
        point, t, u = hit
        if best is None or (t > best[0] if pick_far else t < best[0]):
            best = (t, point, edge, u)
    if best is None:
        return None
    _, point, edge, u = best
    return point, edge, u


def _signed_area(pts: list[Point2D]) -> float:
    acc = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        acc += x0 * y1 - x1 * y0
    return acc / 2.0


def _splice_at_crossings(
    outer: list[Point2D],
    run: list[Point2D],
    exit_cross: tuple[Point2D, int, float],
    entry_cross: tuple[Point2D, int, float],
) -> list[Point2D]:
    """Replace the contour arc the bump caps, keeping the larger-area result.

    The two crossings split the contour into two arcs. Inserting the bump in
    place of one arc and the (reversed) bump in place of the other yields two
    candidate silhouettes; the larger-area one is the grow. Picking by area is
    winding- and seam-independent: a wrong-direction or seam-straddling stroke
    can only ever produce the small (capped) polygon, which loses.
    """
    point_a, edge_a, param_a = exit_cross
    point_b, edge_b, param_b = entry_cross

    # Order all nodes around the loop: original verts at edge param 0, crossings
    # at their measured edge param. Stable sort keeps a vert ahead of a crossing
    # that lands exactly on it.
    nodes: list[tuple[int, float, Point2D]] = [(i, 0.0, v) for i, v in enumerate(outer)]
    idx_a = len(nodes)
    nodes.append((edge_a, param_a, point_a))
    idx_b = len(nodes)
    nodes.append((edge_b, param_b, point_b))
    order = sorted(range(len(nodes)), key=lambda k: (nodes[k][0], nodes[k][1]))
    pos = {k: p for p, k in enumerate(order)}

    def forward_verts(src: int, dst: int) -> list[Point2D]:
        """Original-vertex points strictly between ``src`` and ``dst`` (forward)."""
        out: list[Point2D] = []
        steps = len(order)
        k = (pos[src] + 1) % steps
        while k != pos[dst]:
            out.append(nodes[order[k]][2])
            k = (k + 1) % steps
        return out

    arc_a_to_b = forward_verts(idx_a, idx_b)
    arc_b_to_a = forward_verts(idx_b, idx_a)
    candidate_keep_b_to_a = [point_a, *run, point_b, *arc_b_to_a]
    candidate_keep_a_to_b = [point_b, *reversed(run), point_a, *arc_a_to_b]
    if abs(_signed_area(candidate_keep_b_to_a)) >= abs(_signed_area(candidate_keep_a_to_b)):
        return candidate_keep_b_to_a
    return candidate_keep_a_to_b


def _splice_spike(
    outer: list[Point2D], cross: tuple[Point2D, int, float], run: list[Point2D]
) -> list[Point2D]:
    """Insert a one-sided spike at a single crossing (a half gesture).

    The stroke touched the boundary once, so there is no arc to replace; the
    outside run is grafted at the crossing edge and returns to it.
    """
    point, edge, _param = cross
    n = len(outer)
    head = [outer[i] for i in range(edge + 1)]
    tail = [outer[i] for i in range(edge + 1, n)]
    return [*head, point, *run, point, *tail]


def splice_extend_stroke(
    outer: list[Point2D],
    stroke: list[Point2D],
) -> list[Point2D] | None:
    """Splice an extend stroke's outside portion into the closed outer polyline.

    Returns the new outer polyline with the outside portion of the stroke
    grafted in at the contour crossings, or None when the stroke is not an
    extend:

    - entirely inside the silhouette (caller drops or routes to the cut path),
    - entirely outside it (no crossing; caller logs WARN),
    - fewer than 2 samples, or the outer has fewer than 3 verts.

    A two-sided stroke (out and back) replaces the capped arc by area; a
    one-sided stroke (out only, or in from outside) grafts a spike at its
    single crossing.
    """
    if len(stroke) < 2 or len(outer) < 3:
        return None

    mask = [_inside_or_on(point, outer) for point in stroke]
    if all(mask) or not any(mask):
        return None

    n = len(stroke)
    departure = next((i - 1 for i in range(1, n) if mask[i - 1] and not mask[i]), None)

    if departure is None:
        # Stroke starts outside and enters: graft the outside prefix at the
        # re-entry crossing.
        first_inside = next((i for i, inside in enumerate(mask) if inside), None)
        if first_inside is None or first_inside == 0:
            return None
        run = list(stroke[:first_inside])
        cross = _seg_contour_crossing(
            stroke[first_inside - 1], stroke[first_inside], outer, pick_far=True
        )
        if cross is None:
            return None
        spliced = _splice_spike(outer, cross, run)
        return spliced if len(spliced) >= 3 else None

    re_entry = next((i for i in range(departure + 2, n) if mask[i]), None)
    exit_cross = _seg_contour_crossing(
        stroke[departure], stroke[departure + 1], outer, pick_far=False
    )
    if exit_cross is None:
        return None

    if re_entry is None:
        # Leaves and never returns: single-crossing spike.
        run = list(stroke[departure + 1 :])
        spliced = _splice_spike(outer, exit_cross, run)
        return spliced if len(spliced) >= 3 else None

    run = list(stroke[departure + 1 : re_entry])
    entry_cross = _seg_contour_crossing(
        stroke[re_entry - 1], stroke[re_entry], outer, pick_far=True
    )
    if entry_cross is None:
        return None
    spliced = _splice_at_crossings(outer, run, exit_cross, entry_cross)
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


def apply_outer_extends(
    outer: list[Point2D],
    extend_strokes: list[list[Point2D]],
) -> list[Point2D] | None:
    """Splice all extend strokes; None when nothing changed.

    Returns the new outer when at least one stroke spliced, else None - so the
    caller can warn and skip the override. Detection is by value: every stroke
    being a no-op leaves the contour equal to the input (the splice always
    returns a fresh list, so an identity check would never fire). A degenerate
    result (< 3 verts) also returns None.
    """
    spliced = splice_extend_strokes(outer, extend_strokes)
    if len(spliced) < 3 or spliced == list(outer):
        return None
    return spliced
