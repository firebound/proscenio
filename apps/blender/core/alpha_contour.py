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


def dilate(mask: BinaryMask, iterations: int) -> BinaryMask:
    """Binary dilation with a 4-connected kernel, ``iterations`` passes.

    Each pass turns every False pixel adjacent to a True pixel into
    True. Used to produce the outer contour of the annulus topology
    (outer dilate pushes the silhouette outward by N pixels). Pure
    Python loop; acceptable at the scales Proscenio targets thanks
    to the upstream downscale step.
    """
    if iterations < 0:
        raise ValueError(f"iterations must be >= 0, got {iterations}")
    if iterations == 0:
        return [row[:] for row in mask]
    width, height = _grid_dimensions(mask)
    current = mask
    for _ in range(iterations):
        previous = current
        result: BinaryMask = [row[:] for row in previous]
        for y in range(height):
            row_prev = previous[y]
            row_result = result[y]
            for x in range(width):
                if row_prev[x]:
                    continue
                for dx, dy in _NEIGHBOUR_OFFSETS_4:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and previous[ny][nx]:
                        row_result[x] = True
                        break
        current = result
    return current


def erode(mask: BinaryMask, iterations: int) -> BinaryMask:
    """Binary erosion with a 4-connected kernel, ``iterations`` passes.

    Each pass turns every True pixel adjacent to a False pixel (or
    the grid border) into False. Used to produce the inner contour
    of the annulus topology. Inverse semantics of :func:`dilate`.
    """
    if iterations < 0:
        raise ValueError(f"iterations must be >= 0, got {iterations}")
    if iterations == 0:
        return [row[:] for row in mask]
    width, height = _grid_dimensions(mask)
    current = mask
    for _ in range(iterations):
        previous = current
        result: BinaryMask = [row[:] for row in previous]
        for y in range(height):
            row_prev = previous[y]
            row_result = result[y]
            for x in range(width):
                if not row_prev[x]:
                    continue
                eroded = False
                for dx, dy in _NEIGHBOUR_OFFSETS_4:
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < width and 0 <= ny < height):
                        eroded = True
                        break
                    if not previous[ny][nx]:
                        eroded = True
                        break
                if eroded:
                    row_result[x] = False
        current = result
    return current


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


def extract_contour_pair(
    alpha: AlphaGrid,
    threshold: int,
    margin_px: int,
) -> tuple[Contour, Contour]:
    """Extract paired outer+inner contours for annulus topology (D2).

    ``margin_px`` controls the annulus thickness: the outer contour
    is the silhouette dilated by ``margin_px``, the inner is the
    silhouette eroded by ``margin_px``. Returning both contours
    is the input the annulus builder in
    ``core/automesh_geometry.py`` needs to lay down the ring of
    edge loops near the silhouette + the interior fill that COA
    Tools 2's automesh ships and that deforms cleanly under bone
    chains.

    The inner contour can be empty when the silhouette is too
    thin for the requested erosion - the caller falls back to a
    flat triangulation in that case.
    """
    if margin_px < 0:
        raise ValueError(f"margin_px must be >= 0, got {margin_px}")
    outer = extract_outer_contour(alpha, threshold, margin_px)
    inner = extract_inner_contour(alpha, threshold, margin_px)
    return (outer, inner)
