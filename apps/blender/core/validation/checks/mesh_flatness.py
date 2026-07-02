"""Mesh-flatness check: warn for non-planar meshes the exporter would flatten."""

from __future__ import annotations

from .._shared import name_of
from ..issue import Issue

_FLATNESS_TOLERANCE = 0.1  # mesh depth as a fraction of its in-plane size


def validate_mesh_flatness(obj: object) -> list[Issue]:
    """Warn for meshes that are not planar - 3D geometry the exporter flattens.

    Frame-independent: a cutout sits in one plane, so its thinnest extent is
    near zero whatever plane it lies in. Comparing the smallest axis spread to
    the largest catches a genuinely 3D mesh without assuming which axis is the
    depth (the writer drops world Y, but a quad may be authored in local XY or
    XZ, so a fixed-axis test would false-warn one of them).
    """
    mesh = getattr(obj, "data", None)
    coords = [v.co for v in getattr(mesh, "vertices", ()) if getattr(v, "co", None) is not None]
    if len(coords) < 2:
        return []
    spreads = sorted(
        max(float(getattr(c, axis)) for c in coords) - min(float(getattr(c, axis)) for c in coords)
        for axis in ("x", "y", "z")
    )
    extent, thickness = spreads[2], spreads[0]
    if extent < 1e-6:
        return []  # degenerate (point) mesh, nothing to flatten
    if thickness > _FLATNESS_TOLERANCE * extent:
        return [
            Issue(
                "warning",
                "element is not flat - it has thickness on every axis, so the "
                "exporter's flatten-to-plane will lose geometry",
                name_of(obj),
            )
        ]
    return []
