"""Pure-Python alpha-channel contour walker (SPEC 013 Wave 13.1).

bpy-free. Lives under ``core/`` so unit tests can exercise the
contour tracing + morphology math without booting Blender. The
bpy bridge in ``core/bpy_helpers/automesh_bmesh.py`` reads the
image pixels and feeds the binary mask into the helpers here.

No third-party dependencies. Per SPEC 013 Constraints, the addon
must not depend on OpenCV / numpy at runtime (COA Tools 2 issues
#94 / #107 prove that PyPI-fetch dependencies are the addon's
single biggest adoption blocker - corp / ISP firewalls, version
mismatch, manual cv2 copy breaking numpy ABI). Moore Neighbour
contour tracing + 8-connectivity binary morphology + Laplacian
contour smoothing are all expressible in plain Python loops at
the scales Proscenio targets (alpha grids downscaled to
<=256x256 before tracing).
"""

from __future__ import annotations

from collections.abc import Callable

AlphaGrid = list[list[int]]
BinaryMask = list[list[bool]]
ContourPoint = tuple[int, int]
Contour = list[ContourPoint]


_NEIGHBOUR_OFFSETS_8: tuple[tuple[int, int], ...] = (
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
)
"""Eight Moore neighbours indexed clockwise from East."""


_NEIGHBOUR_OFFSETS_4: tuple[tuple[int, int], ...] = (
    (1, 0),
    (0, 1),
    (-1, 0),
    (0, -1),
)
"""Four Von Neumann neighbours used by binary morphology kernels."""


HOLE_SAFETY_DILATE_CELLS: int = 1
"""Foreground dilation applied to the mask before hole detection
(SPEC 013 D2 amendment). Symmetric to the outer 1-cell safety
dilate: dilating the foreground SHRINKS each hole by 1 cell so the
mesh-side hole cutout sits INSIDE the actual alpha hole boundary,
guaranteeing the mesh never cuts an alpha pixel around the hole's
inner silhouette edge. Trades a tiny mesh-over-transparent bleed
band (~2% of hole area at downscale=0.25) for the alpha-safety
invariant the user demands. Erode-instead-of-dilate was prototyped
and rejected: even 1-cell erosion eats alpha around the hole edge."""


_MAX_CONTOUR_STEPS: int = 200_000
"""Defensive cap on Moore-Neighbour tracing - protects against
pathological inputs that would otherwise loop indefinitely. Above
the cap the trace returns whatever it has so the caller never
hangs the Blender UI thread."""


def binarize(alpha: AlphaGrid, threshold: int) -> BinaryMask:
    """Threshold an alpha grid into a binary boolean mask.

    Pixels with alpha strictly above ``threshold`` are considered
    foreground (True). Threshold defaults match COA Tools 2's
    automesh (127) so the same input PNGs produce comparable
    silhouettes.
    """
    if not alpha:
        raise ValueError("alpha grid must contain at least one row")
    if not alpha[0]:
        raise ValueError("alpha grid rows must contain at least one column")
    if not 0 <= threshold <= 255:
        raise ValueError(f"threshold must be in [0, 255], got {threshold}")
    return [[pixel > threshold for pixel in row] for row in alpha]


def _grid_dimensions(grid: BinaryMask) -> tuple[int, int]:
    """Return (width, height) of a non-empty mask; raise on empty."""
    if not grid or not grid[0]:
        raise ValueError("mask must be non-empty")
    return (len(grid[0]), len(grid))


def _has_foreground_neighbour(mask: BinaryMask, x: int, y: int, width: int, height: int) -> bool:
    """True iff any 4-neighbour of ``(x, y)`` is foreground (in-bounds)."""
    for dx, dy in _NEIGHBOUR_OFFSETS_4:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and mask[ny][nx]:
            return True
    return False


def _touches_background_or_border(
    mask: BinaryMask, x: int, y: int, width: int, height: int
) -> bool:
    """True iff any 4-neighbour of ``(x, y)`` is background OR out-of-bounds."""
    for dx, dy in _NEIGHBOUR_OFFSETS_4:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < width and 0 <= ny < height):
            return True
        if not mask[ny][nx]:
            return True
    return False


def _dilate_once(mask: BinaryMask, width: int, height: int) -> BinaryMask:
    """One dilation pass - every background cell adjacent to foreground flips on."""
    result: BinaryMask = [row[:] for row in mask]
    for y in range(height):
        row_mask = mask[y]
        row_result = result[y]
        for x in range(width):
            if not row_mask[x] and _has_foreground_neighbour(mask, x, y, width, height):
                row_result[x] = True
    return result


def _erode_once(mask: BinaryMask, width: int, height: int) -> BinaryMask:
    """One erosion pass - every foreground cell touching background / border flips off."""
    result: BinaryMask = [row[:] for row in mask]
    for y in range(height):
        row_mask = mask[y]
        row_result = result[y]
        for x in range(width):
            if row_mask[x] and _touches_background_or_border(mask, x, y, width, height):
                row_result[x] = False
    return result


_SinglePass = Callable[[BinaryMask, int, int], BinaryMask]


def _apply_morphology(mask: BinaryMask, iterations: int, single_pass: _SinglePass) -> BinaryMask:
    """Repeatedly apply ``single_pass(mask, w, h)`` for ``iterations`` rounds.

    Shared loop body for :func:`dilate` + :func:`erode`. Iterations
    must be non-negative; 0 returns a defensive copy so callers can
    mutate the result freely.
    """
    if iterations < 0:
        raise ValueError(f"iterations must be >= 0, got {iterations}")
    if iterations == 0:
        return [row[:] for row in mask]
    width, height = _grid_dimensions(mask)
    current = mask
    for _ in range(iterations):
        current = single_pass(current, width, height)
    return current


def dilate(mask: BinaryMask, iterations: int) -> BinaryMask:
    """Binary dilation with a 4-connected kernel, ``iterations`` passes.

    Each pass turns every False pixel adjacent to a True pixel into
    True. Used to produce the outer contour of the annulus topology
    (outer dilate pushes the silhouette outward by N pixels). Pure
    Python loop; acceptable at the scales Proscenio targets thanks
    to the upstream downscale step.
    """
    return _apply_morphology(mask, iterations, _dilate_once)


def erode(mask: BinaryMask, iterations: int) -> BinaryMask:
    """Binary erosion with a 4-connected kernel, ``iterations`` passes.

    Each pass turns every True pixel adjacent to a False pixel (or
    the grid border) into False. Used to produce the inner contour
    of the annulus topology. Inverse semantics of :func:`dilate`.
    """
    return _apply_morphology(mask, iterations, _erode_once)


def find_first_boundary(mask: BinaryMask) -> ContourPoint | None:
    """Scan rows top-to-bottom for the first True pixel.

    Returns the pixel coordinate of the first foreground hit, or
    ``None`` when the mask is entirely background. Used as the
    seed for Moore Neighbour tracing. Top-to-bottom raster scan
    guarantees that the seed pixel was approached from the west
    (the cell to its immediate left is False, since we would have
    found it first otherwise), which feeds the tracing algorithm's
    initial direction assumption.
    """
    width, height = _grid_dimensions(mask)
    for y in range(height):
        row = mask[y]
        for x in range(width):
            if row[x]:
                return (x, y)
    return None


def trace_contour(mask: BinaryMask, start: ContourPoint) -> Contour:
    """Moore Neighbour contour trace from a boundary seed pixel.

    Walks the foreground boundary clockwise. Uses the standard
    "rotate the search start to the right of the incoming edge"
    convention so the algorithm always finds the next boundary
    pixel without re-walking visited cells. Terminates via Jacob's
    stopping criterion (return to start with the same incoming
    direction) or via the defensive step cap.

    The seed pixel MUST be a foreground boundary cell (typically
    obtained via :func:`find_first_boundary`). Behavior is
    undefined for interior seeds.
    """
    width, height = _grid_dimensions(mask)
    sx, sy = start
    if not (0 <= sx < width and 0 <= sy < height):
        raise ValueError(f"start point {start} is outside the mask")
    if not mask[sy][sx]:
        raise ValueError(f"start point {start} is not a foreground pixel")

    contour: Contour = [start]
    cx, cy = start
    previous_direction = 4
    steps = 0

    # Simple stopping criterion: terminate on the first revisit to
    # ``start``. This is correct for the simple closed contours that
    # alpha-threshold + binary morphology produce on a sprite
    # silhouette (every silhouette is a single-loop alpha island
    # after dilate / erode by the standard automesh margin). The
    # strict Pavlidis-Jacob "revisit AND same incoming search
    # direction" criterion was prototyped against this code (PR #51
    # review feedback) but rejected: it requires careful pre-move
    # vs post-move ordering to avoid double-counting start AND it
    # only matters for figure-eight contours that the addon never
    # generates. The defensive ``_MAX_CONTOUR_STEPS`` cap below is
    # the ultimate guard against pathological inputs.
    while steps < _MAX_CONTOUR_STEPS:
        steps += 1
        search_start = (previous_direction + 2) % 8
        found = False
        for offset in range(8):
            direction = (search_start + offset) % 8
            dx, dy = _NEIGHBOUR_OFFSETS_8[direction]
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height and mask[ny][nx]:
                cx, cy = nx, ny
                previous_direction = (direction + 4) % 8
                found = True
                break

        if not found:
            break

        if (cx, cy) == start and len(contour) >= 2:
            break

        contour.append((cx, cy))

    return contour


def extract_outer_contour(
    alpha: AlphaGrid,
    threshold: int,
    dilate_px: int,
) -> Contour:
    """Threshold + dilate + trace the outer boundary of a sprite.

    Returns the clockwise-ordered contour points of the dilated
    silhouette. Empty silhouette raises ``ValueError`` because there
    is nothing to mesh - callers (the operator) should surface this
    via the pre-flight diagnosis path with an actionable hint.
    """
    mask = binarize(alpha, threshold)
    if dilate_px > 0:
        mask = dilate(mask, dilate_px)
    seed = find_first_boundary(mask)
    if seed is None:
        raise ValueError(
            "alpha grid contains no foreground pixels above the threshold; "
            "check the image alpha channel and the threshold setting"
        )
    return trace_contour(mask, seed)


def extract_inner_contour(
    alpha: AlphaGrid,
    threshold: int,
    erode_px: int,
) -> Contour:
    """Threshold + erode + trace the inner boundary of a sprite.

    Returns the clockwise-ordered contour of the eroded silhouette.
    When erosion wipes the silhouette entirely (margin too large
    for the sprite), returns an empty list so the caller can fall
    back to a single-contour topology instead of the annulus. The
    operator should report INFO when this happens.
    """
    mask = binarize(alpha, threshold)
    if erode_px > 0:
        mask = erode(mask, erode_px)
    seed = find_first_boundary(mask)
    if seed is None:
        return []
    return trace_contour(mask, seed)


def _flood_fill(
    mask: BinaryMask,
    visited: BinaryMask,
    seeds: list[ContourPoint],
) -> None:
    """Mark every ``True`` cell reachable from ``seeds`` as visited.

    Mutates ``visited`` in place. Used twice by :func:`extract_holes`:
    once to flag "outside" background reachable from the grid border,
    once to flag a freshly traced hole region so subsequent scans do
    not re-trace it.
    """
    width, height = _grid_dimensions(mask)
    stack = list(seeds)
    while stack:
        x, y = stack.pop()
        if not (0 <= x < width and 0 <= y < height):
            continue
        if visited[y][x] or not mask[y][x]:
            continue
        visited[y][x] = True
        for dx, dy in _NEIGHBOUR_OFFSETS_4:
            stack.append((x + dx, y + dy))


def extract_holes(mask: BinaryMask) -> list[Contour]:
    """Trace contours of background islands fully enclosed by foreground.

    A "hole" is a region of False cells in ``mask`` that does not
    reach the grid border. The grid border is treated as the
    boundary between sprite and image padding, so background
    reachable from the border is the surrounding empty area, not
    a hole.

    Returns one closed contour per hole, walked clockwise on the
    INVERTED mask (= counter-clockwise on the original foreground).
    CDT (``mathutils.geometry.delaunay_2d_cdt``) treats nested
    closed loops as holes via ``output_type=2``, regardless of
    orientation, so the caller can append each contour to the
    constraint edge set directly.

    Implementation: flood-fill from every border background cell
    to mark "outside" pixels, then scan the remaining background
    pixels for hole seeds and trace each connected island once
    via the standard Moore-Neighbour walker on the inverted mask.
    """
    width, height = _grid_dimensions(mask)
    inverted: BinaryMask = [[not cell for cell in row] for row in mask]
    visited: BinaryMask = [[False] * width for _ in range(height)]

    border_seeds: list[ContourPoint] = []
    for x in range(width):
        border_seeds.append((x, 0))
        border_seeds.append((x, height - 1))
    for y in range(height):
        border_seeds.append((0, y))
        border_seeds.append((width - 1, y))
    _flood_fill(inverted, visited, border_seeds)

    holes: list[Contour] = []
    for y in range(height):
        for x in range(width):
            if inverted[y][x] and not visited[y][x]:
                holes.append(trace_contour(inverted, (x, y)))
                _flood_fill(inverted, visited, [(x, y)])
    return holes


def extract_contour_pair(
    alpha: AlphaGrid,
    threshold: int,
    margin_px: int,
) -> tuple[Contour, Contour]:
    """Extract paired outer+inner contours for annulus topology (D2).

    Convenience back-compat wrapper around :func:`extract_contours`
    that drops the holes list. Existing callers (and unit tests)
    that do not need hole-aware triangulation can keep using this.

    See :func:`extract_contours` for the full signature.
    """
    outer, inner, _holes = extract_contours(alpha, threshold, margin_px)
    return (outer, inner)


def extract_contours(
    alpha: AlphaGrid,
    threshold: int,
    margin_px: int,
) -> tuple[Contour, Contour, list[Contour]]:
    """Extract outer contour + inner annulus ring + per-hole contours.

    Builds on the annulus topology of :func:`extract_contour_pair`
    by also returning every alpha hole inside the silhouette. The
    bpy bridge feeds the hole contours to CDT as additional
    constraint loops so the mesh excludes the hole interior - SPEC
    013 D2 amendment (Proscenio differentiates from Spine + COA2
    here, which both refuse to support holes).

    ``margin_px`` controls the OUTER annulus thickness exactly as
    in :func:`extract_contour_pair`. Holes are detected on the
    same dilated outer mask so a hole that the user wanted treated
    as a hole survives the 1-cell safety dilation; hairline alpha
    gaps narrower than the safety dilation are intentionally
    swallowed so they do not produce noise mesh holes.
    """
    if margin_px < 0:
        raise ValueError(f"margin_px must be >= 0, got {margin_px}")
    # Outer ALWAYS gets at least 1 cell of dilation for safety.
    # Without it, the mesh boundary sits at the LEFT edge of the
    # rightmost True cell, which is INSIDE the alpha silhouette on
    # the right side (pixel_contour_to_world places verts at cell
    # left/top corners; for cells that border background on the
    # right, this puts the vert several source pixels INSIDE the
    # alpha). 1-cell safety dilation pushes the boundary out by 1
    # cell on every side so coverage approaches 100% even at
    # margin_pixels=0 (single-contour mode).
    outer_dilate = max(1, margin_px)
    raw_mask = binarize(alpha, threshold)
    outer_mask = dilate(raw_mask, outer_dilate) if outer_dilate > 0 else raw_mask
    seed = find_first_boundary(outer_mask)
    if seed is None:
        raise ValueError(
            "alpha grid contains no foreground pixels above the threshold; "
            "check the image alpha channel and the threshold setting"
        )
    outer = trace_contour(outer_mask, seed)
    # Detect holes on a foreground DILATED by 1 cell. Dilating
    # foreground shrinks each hole by 1 cell, which places the
    # mesh-side hole boundary INSIDE the alpha hole - guaranteeing
    # the mesh never cuts alpha at the hole's inner silhouette
    # (user invariant: never cut alpha). The flip side is a small
    # bleed band of mesh covering ~1 cell of transparent pixels at
    # the hole edge; this is the symmetric analogue of the outer
    # safety margin.
    hole_mask = dilate(raw_mask, HOLE_SAFETY_DILATE_CELLS)
    holes = extract_holes(hole_mask)
    if margin_px == 0:
        return (outer, [], holes)
    inner = extract_inner_contour(alpha, threshold, margin_px)
    return (outer, inner, holes)
