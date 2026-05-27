"""Authoring stage dataclasses (SPEC 013.2 interactive-modal, T12; AS-AM3 T3).

Pure dataclasses describing the modal state machine:
- AuthoringStage IntEnum: 6 stages in workflow order (USER_OUTER added AS-AM3)
- StageParams: PG-field snapshot (frozen for equality-based dirty detect)
- StageOutput: per-stage compute output (consumed by subsequent stages)

Pure Python: stdlib only (dataclasses + enum).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal, TypedDict

Point2D = tuple[float, float]


class AuthoringStage(IntEnum):
    """6-stage modal pipeline (workflow order). Stage 2 USER_OUTER
    edits the silhouette before any interior work; Stage 4 USER_STEINERS
    edits the interior. See spec AS-AM3."""

    OUTER = 0
    USER_OUTER = 1
    INNER_LOOPS = 2
    USER_STEINERS = 3
    STEINER_PREVIEW = 4
    APPLY = 5


class Stroke(TypedDict):
    """Stage 3 stroke or single-Steiner placement (SPEC 013 S7 + AS-AM7).

    kind="point": single Steiner from a click without drag (S6 backward compat).
    kind="stroke": resampled polyline that becomes constraint edges + verts.
    kind="cut": resampled polyline; emits 2 perpendicular offset loops as
        constraint edges + post-CDT face-prune removes faces inside the lens.
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
    cut_width: float = 0.03  # Stage 3 cut stroke width in world units (T9 AS-AM8)


@dataclass
class StageOutput:
    """What each stage produces; subsequent stages consume + extend.

    Mutable (not frozen) so the modal can update one field at a time
    as the user advances stages without rebuilding the whole container.
    """

    outer: list[Point2D] = field(default_factory=list)
    user_outer_strokes: list[Stroke] = field(default_factory=list)  # Stage 2 (AS-AM3)
    inner_loops: list[list[Point2D]] = field(default_factory=list)
    user_steiners: list[Point2D] = field(default_factory=list)
    user_strokes: list[Stroke] = field(default_factory=list)
    all_steiners: list[Point2D] = field(default_factory=list)
