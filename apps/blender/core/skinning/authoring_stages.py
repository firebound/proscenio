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


# Per-stage interactive tools. The modal arms exactly one tool per stage; bare
# Tab cycles within the stage's tuple. Tools come in three interaction families:
# - an OPEN-stroke pen ("knife" / "fold") makes LMB the click/free-draw pen;
# - a closed-loop ISLAND tool ("add" / "remove", spec 070) uses the shared
#   VertexPen to click a closed loop;
# - a single-shot / passive tool ("point" drops a Steiner, "auto" is the
#   alpha trace, "delete" removes a committed stroke).
# A stage absent from the map has no interactive tool (INNER_LOOPS /
# PREVIEW_INTERIOR / APPLY are slider + navigation only).
_STAGE_TOOLS: dict[AuthoringStage, tuple[str, ...]] = {
    # OUTER is auto-only now: manual silhouette work is the additive ADD/REMOVE
    # islands in Edit silhouette (spec 070), and the fully-manual mesh is the
    # standalone Manual Draw mode - the old replace-the-trace "contour" is gone.
    AuthoringStage.OUTER: ("auto",),
    # Edit silhouette (spec 070): ADD island grows the trace, KNIFE (the former
    # "cut") carves a corridor, REMOVE island excludes a closed area.
    AuthoringStage.EDIT_OUTLINE: ("add", "knife", "remove", "delete"),
    # Interior stays additive detail on the auto fill (mark points, add fold
    # edges); islands do not apply here.
    AuthoringStage.EDIT_INTERIOR_POINTS: ("point", "fold", "delete"),
}
# Open-stroke pen tools: LMB is the click/free-draw pen (the old machine).
_PEN_TOOLS = frozenset({"knife", "fold"})
# Closed-loop island tools (spec 070): driven by the shared VertexPen, not the
# open-stroke pen machine.
_ISLAND_TOOLS = frozenset({"add", "remove"})


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
    """True when the tool makes LMB the open-stroke click-pen (knife / fold)."""
    return tool in _PEN_TOOLS


def tool_is_island(tool: str) -> bool:
    """True when the tool draws a closed-loop island via the shared VertexPen
    (add / remove, spec 070)."""
    return tool in _ISLAND_TOOLS


class Stroke(TypedDict):
    """A user-authored stroke or island.

    kind="point": single Steiner from a click without drag (interior).
    kind="stroke": resampled polyline that becomes constraint edges + verts
        (interior fold-line).
    kind="cut": a perpendicular offset lens whose corridor is routed into
        ``holes_world`` so the CDT carves it as a hole (the KNIFE tool, spec 070;
        formerly the Edit-silhouette "cut"). A true rip / seam (split_edges, no
        material removed) stays a future feature, not this kind.
    kind="add": a closed-loop silhouette ISLAND (spec 070) that GROWS the auto
        trace - spliced in as an outer extend (the part outside the trace is
        added; a fully-outside island is dropped + warned).
    kind="remove": a closed-loop silhouette ISLAND that EXCLUDES its area -
        routed directly into ``holes_world`` as a hole polygon (the loop is the
        hole; no corridor offset).
    """

    kind: Literal["point", "stroke", "cut", "add", "remove"]
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
    # True when ``outer`` was authored by hand (the Draw-with-vertices manual
    # contour) rather than the alpha trace. APPLY + the SIMPLE preview honor a
    # manual outer verbatim - no alpha re-trace, no arc-length resample (which
    # would redistribute the artist's exact verts); an auto outer is re-traced
    # fresh at APPLY so slider tweaks are reflected.
    outer_is_manual: bool = False
    outer_preview: list[Point2D] = field(default_factory=list)
    user_outer_strokes: list[Stroke] = field(default_factory=list)  # Stage 2
    inner_loops: list[list[Point2D]] = field(default_factory=list)
    user_steiners: list[Point2D] = field(default_factory=list)
    user_strokes: list[Stroke] = field(default_factory=list)
    all_steiners: list[Point2D] = field(default_factory=list)
    # SIMPLE-mode triangulation preview - world-XZ edge endpoint pairs from the
    # real CDT.
    triangulation_preview: list[tuple[Point2D, Point2D]] = field(default_factory=list)
