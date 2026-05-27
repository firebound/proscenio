"""Authoring stage dataclasses (SPEC 013.2 interactive-modal, T12).

Pure dataclasses describing the modal state machine:
- AuthoringStage IntEnum: 5 stages in workflow order
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
    """5-stage modal pipeline (workflow order)."""

    OUTER = 0
    INNER_LOOPS = 1
    USER_STEINERS = 2
    STEINER_PREVIEW = 3
    APPLY = 4


class Stroke(TypedDict):
    """Stage 3 stroke or single-Steiner placement (SPEC 013 S7).

    kind="point": single Steiner from a click without drag (S6 backward compat).
    kind="stroke": resampled polyline that becomes constraint edges + verts.
    """

    kind: Literal["point", "stroke"]
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


@dataclass
class StageOutput:
    """What each stage produces; subsequent stages consume + extend.

    Mutable (not frozen) so the modal can update one field at a time
    as the user advances stages without rebuilding the whole container.
    """

    outer: list[Point2D] = field(default_factory=list)
    inner_loops: list[list[Point2D]] = field(default_factory=list)
    user_steiners: list[Point2D] = field(default_factory=list)
    user_strokes: list[Stroke] = field(default_factory=list)
    all_steiners: list[Point2D] = field(default_factory=list)
