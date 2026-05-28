"""Brush curve presets for Edit Weights modal (SPEC 013 O4).

Four named presets that configure the active weight-paint brush curve
(brush.curve.curves[0].points). Saves artist trips to the curve editor.

Curve points are (x, y) in [0, 1] x [0, 1] where x = stroke distance
from center (0=center, 1=brush edge) and y = strength multiplier
(0=no effect, 1=full effect).
"""

from __future__ import annotations

from typing import Literal

PresetName = Literal["HARD_EDGE", "SOFT_FALLOFF", "CREASE", "SMOOTH_BLEND"]

PRESETS: dict[PresetName, list[tuple[float, float]]] = {
    # Flat full strength then sharp cliff at the edge
    "HARD_EDGE": [(0.0, 1.0), (0.95, 1.0), (1.0, 0.0)],
    # Linear falloff from center to edge
    "SOFT_FALLOFF": [(0.0, 1.0), (1.0, 0.0)],
    # Crease - strong at center, near-zero at half-radius, zero at edge
    "CREASE": [(0.0, 1.0), (0.2, 0.7), (0.5, 0.0), (1.0, 0.0)],
    # Smooth blend - mid-curve s-shape
    "SMOOTH_BLEND": [(0.0, 1.0), (0.3, 0.85), (0.7, 0.15), (1.0, 0.0)],
}


PRESET_LABELS: dict[PresetName, str] = {
    "HARD_EDGE": "Hard Edge",
    "SOFT_FALLOFF": "Soft Falloff",
    "CREASE": "Crease",
    "SMOOTH_BLEND": "Smooth Blend",
}
