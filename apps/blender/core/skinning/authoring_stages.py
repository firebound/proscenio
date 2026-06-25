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


# Per-stage interactive tools (spec 066). The modal arms exactly one tool per
# stage; bare Tab cycles within the stage's tuple. A pen tool (extend / cut /
# fold / contour) makes LMB the click-pen; "point" drops a single Steiner on a
# click; "auto" is the passive alpha-traced outer (no LMB interaction). A stage
# absent from the map has no interactive tool (INNER_LOOPS / PREVIEW_INTERIOR /
# APPLY are slider + navigation only).
_STAGE_TOOLS: dict[AuthoringStage, tuple[str, ...]] = {
    AuthoringStage.OUTER: ("auto", "contour"),
    AuthoringStage.EDIT_OUTLINE: ("extend", "cut", "delete"),
    # Interior has no "cut": the Stage 4 cut produced the same corridor hole as
    # the Stage 2 silhouette cut (both route into holes_world), so it was a
    # redundant operation - dropped. Cut the silhouette in Edit silhouette.
    AuthoringStage.EDIT_INTERIOR_POINTS: ("point", "fold", "delete"),
}
# Pen tools make LMB the click-pen. "delete" is a tool too but not a pen: its LMB
# removes the committed stroke under the cursor (replacing the old Alt+click).
_PEN_TOOLS = frozenset({"extend", "cut", "fold", "contour"})


def stage_tools(stage: AuthoringStage) -> tuple[str, ...]:
    """Ordered interactive tools for ``stage`` (empty when it has none)."""
    return _STAGE_TOOLS.get(stage, ())


def default_tool(stage: AuthoringStage) -> str:
    """The tool a stage arms on entry (its first); ``""`` when it has none."""
    tools = stage_tools(stage)
    return tools[0] if tools else ""


def next_tool(stage: AuthoringStage, current: str) -> str:
    """Cycle to the next tool of ``stage`` (wrapping).

    Returns ``current`` unchanged when the stage has no tools; resets to the
    first tool when ``current`` is not among the stage's tools (defensive: a
    stage flip can leave a stale tool until the next entry re-arms the default).
    """
    tools = stage_tools(stage)
    if not tools:
        return current
    try:
        idx = tools.index(current)
    except ValueError:
        return tools[0]
    return tools[(idx + 1) % len(tools)]


def tool_is_pen(tool: str) -> bool:
    """True when the tool makes LMB the click-pen (extend / cut / fold / contour)."""
    return tool in _PEN_TOOLS


class Stroke(TypedDict):
    """Stage 3 stroke or single-Steiner placement.

    kind="point": single Steiner from a click without drag.
    kind="stroke": resampled polyline that becomes constraint edges + verts.
    kind="cut": a perpendicular offset lens whose corridor is routed into
        ``holes_world`` so the CDT carves it as a hole (removes faces). Both the
        Stage 2 silhouette cut and the legacy Stage 4 interior cut took this same
        path - there was never a material-preserving "rip" - so spec 066 dropped
        the redundant interior cut (cut the silhouette in Edit silhouette). A
        true rip / seam (split_edges, no material removed) stays a future
        feature, not this kind.
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
