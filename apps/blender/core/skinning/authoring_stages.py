"""Authoring stage dataclasses.

Pure dataclasses describing the modal state machine:
- AuthoringStage IntEnum: six stages in workflow order
- StageParams: PG-field snapshot (frozen for equality-based dirty detect)
- StageOutput: per-stage compute output (consumed by subsequent stages)

Pure Python: stdlib only (dataclasses + enum).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal, TypedDict

from .._shared.geometry_2d import Point2D


class AuthoringStage(IntEnum):
    """Six-stage modal pipeline (workflow order). Stage 2 EDIT_OUTLINE
    edits the silhouette before any interior work; Stage 4 EDIT_INTERIOR_POINTS
    edits the interior."""

    OUTER = 0
    EDIT_OUTLINE = 1
    INNER_LOOPS = 2
    EDIT_INTERIOR_POINTS = 3
    PREVIEW_INTERIOR = 4
    APPLY = 5


class Stroke(TypedDict):
    """Stage 3 stroke or single-Steiner placement.

    kind="point": single Steiner from a click without drag.
    kind="stroke": resampled polyline that becomes constraint edges + verts.
    kind="cut" on user_outer_strokes (Stage 2): perpendicular offset lens +
        post-CDT face-prune removes faces inside the lens (silhouette trim).
    kind="cut" on user_strokes (Stage 4): polyline constraint + post-CDT
        bmesh.ops.split_edges rip - duplicates verts without removing material.
    """

    kind: Literal["point", "stroke", "cut"]
    points: list[tuple[float, float]]  # WORLD XZ, post-smooth + post-resample


@dataclass(frozen=True)
class StageParams:
    """Snapshot of ProscenioSkinningProps fields the modal reads.

    Frozen so re-run logic compares via equality to detect dirty state
    (slider drag mutates the PG; modal polls + recomputes when params
    differ from the cached snapshot).
    """

    resolution: float
    alpha_threshold: int
    margin_pixels: int
    contour_vertices: int
    inner_loop_count: int
    inner_loop_spacing: float
    interior_spacing: float
    bone_radius: float
    bone_factor: int
    cut_margin: float = 0.04  # corridor-hole gap width in world units
    interior_mode: Literal["SIMPLE", "DENSE"] = "DENSE"


@dataclass
class StageOutput:
    """What each stage produces; subsequent stages consume + extend.

    Mutable (not frozen) so the modal can update one field at a time
    as the user advances stages without rebuilding the whole container.
    """

    # world-XZ spliced outer (Stage 2 extend strokes applied) - the silhouette
    # APPLY will build. Mutated in-place so the overlay handler sees updates
    # without re-registration.
    outer: list[Point2D] = field(default_factory=list)
    outer_preview: list[Point2D] = field(default_factory=list)
    user_outer_strokes: list[Stroke] = field(default_factory=list)  # Stage 2
    inner_loops: list[list[Point2D]] = field(default_factory=list)
    user_steiners: list[Point2D] = field(default_factory=list)
    user_strokes: list[Stroke] = field(default_factory=list)
    all_steiners: list[Point2D] = field(default_factory=list)
    # SIMPLE-mode triangulation preview - world-XZ edge endpoint pairs from the
    # real CDT.
    triangulation_preview: list[tuple[Point2D, Point2D]] = field(default_factory=list)
