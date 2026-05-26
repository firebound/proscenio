"""Pure-Python automesh helpers (SPEC 013).

Domain package grouping the bpy-free pieces of the automesh
pipeline: alpha contour walking + morphology, geometric helpers
for resampling / smoothing / annulus edge pairing, and the
density-under-bones interior-point generator.

External callers (operators, bpy bridge, headless validator,
unit tests) import either via the public surface re-exported
here or via the leaf modules directly when narrower scope is
desired. The package layout stays deliberately flat - no further
sub-package nesting beyond ``contour`` / ``geometry`` / ``density``.
"""

from __future__ import annotations

from .contour import (
    HOLE_SAFETY_DILATE_CELLS,
    AlphaGrid,
    BinaryMask,
    Contour,
    ContourPoint,
    binarize,
    dilate,
    erode,
    extract_contour_pair,
    extract_contours,
    extract_holes,
    extract_inner_contour,
    extract_outer_contour,
    find_first_boundary,
    trace_contour,
)
from .density import (
    BoneSegment2D,
    Point2D,
    bounding_box,
    filter_points_too_close_to_boundary,
    interior_points_for_annulus,
    point_in_polygon,
)
from .erosion_loops import compute_inner_loops
from .geometry import (
    Contour2D,
    arc_length_resample,
    build_annulus_edge_pairs,
    edge_index_start_distance,
    find_best_inner_rotation,
    laplacian_smooth,
    perimeter_length,
    to_float_contour,
)

__all__ = [
    "HOLE_SAFETY_DILATE_CELLS",
    "AlphaGrid",
    "BinaryMask",
    "BoneSegment2D",
    "Contour",
    "Contour2D",
    "ContourPoint",
    "Point2D",
    "arc_length_resample",
    "binarize",
    "bounding_box",
    "build_annulus_edge_pairs",
    "compute_inner_loops",
    "dilate",
    "edge_index_start_distance",
    "erode",
    "extract_contour_pair",
    "extract_contours",
    "extract_holes",
    "extract_inner_contour",
    "extract_outer_contour",
    "filter_points_too_close_to_boundary",
    "find_best_inner_rotation",
    "find_first_boundary",
    "interior_points_for_annulus",
    "laplacian_smooth",
    "perimeter_length",
    "point_in_polygon",
    "to_float_contour",
    "trace_contour",
]
