"""Typed payload bags for the validator report.

Replaces the ``dict[str, object]`` payload bags the validator used to
ferry data between ``measurement.py`` -> ``invariants.py`` ->
``report.py`` with frozen dataclasses, so consumers can read fields by
attribute access and mypy gates the shape at every boundary.

The payloads are JSON-serialisable via ``dataclasses.asdict`` -
``report.write_json_report`` round-trips them through ``asdict`` before
dumping so the on-disk JSON shape is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LeakRecord:
    """One leak pixel: PSD-coords, world-coords, alpha + quadrant."""

    pixel_x: int
    pixel_y_storage: int
    pixel_y_visual_pil: int
    alpha: int
    world_x: float
    world_z: float
    quadrant: str


@dataclass(frozen=True)
class Quadrants:
    """Leak counts split by image quadrant (top-left / top-right / etc)."""

    TL: int = 0
    TR: int = 0
    BL: int = 0
    BR: int = 0

    def any(self) -> bool:
        return self.TL > 0 or self.TR > 0 or self.BL > 0 or self.BR > 0


@dataclass(frozen=True)
class Metrics:
    """Per-sprite measurement output.

    Field order + naming mirrors the legacy dict payload so the JSON
    report shape stays stable; only the static type changes.
    """

    verts: int
    faces: int
    triangles: int
    degenerate_triangles: int
    mean_area: float
    uv_out_of_range_loops: int
    coverage_pct: float | None
    leak_count: int
    leak_quadrants: Quadrants
    leak_records_sample: list[LeakRecord]
    hole_bleed_count: int


@dataclass(frozen=True)
class Invariants:
    """Verdict of the invariant check for one sprite."""

    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SpritePayload:
    """One sprite's full validator output - metrics + invariant verdict."""

    metrics: Metrics
    invariants: Invariants


@dataclass
class ValidationReport:
    """Top-level validator output for the whole run."""

    sprites: dict[str, SpritePayload] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
