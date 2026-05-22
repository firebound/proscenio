"""2D-safe weight paint preset (SPEC 013.2 paint, T2).

Edit Weights modal applies this preset on invoke + restores the prior
state on exit. Frozen dataclass = single-call swap; symmetric apply +
restore avoids drift.

Pure Python: stdlib only (dataclasses).
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class PaintPresetSnapshot:
    """8 brush toggles tied to weight-paint UX."""

    use_front_faces: bool
    use_normal: bool
    use_accumulate: bool
    use_pressure_size: bool
    use_pressure_strength: bool
    use_x_mirror: bool
    brush_radius: int
    brush_strength: float


PRESET_2D = PaintPresetSnapshot(
    use_front_faces=False,
    use_normal=False,
    use_accumulate=True,
    use_pressure_size=True,
    use_pressure_strength=True,
    use_x_mirror=False,
    brush_radius=24,
    brush_strength=0.5,
)


def build_target_preset(*, mirror_x: bool) -> PaintPresetSnapshot:
    """PRESET_2D with use_x_mirror overridden from the picker rig flag."""
    return replace(PRESET_2D, use_x_mirror=mirror_x)


def apply_2d_preset(current: PaintPresetSnapshot, *, mirror_x: bool) -> PaintPresetSnapshot:
    """Return the prior snapshot so caller can restore it later.

    The bpy bridge layer (paint_preset_bind) writes ``build_target_preset(mirror_x)``
    onto ``tool_settings.weight_paint``; this pure helper just returns
    the prior values verbatim so the restore path has them at hand.
    """
    return current
