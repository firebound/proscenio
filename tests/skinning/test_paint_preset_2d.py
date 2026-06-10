"""Pure tests for the 2D paint preset."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.paint_preset_2d import (  # noqa: E402
    PRESET_2D,
    PaintPresetSnapshot,
    apply_2d_preset,
)


def _current() -> PaintPresetSnapshot:
    return PaintPresetSnapshot(
        use_front_faces=True,
        use_normal=True,
        use_accumulate=False,
        use_pressure_size=False,
        use_pressure_strength=False,
        use_x_mirror=False,
        brush_radius=50,
        brush_strength=1.0,
    )


def test_apply_2d_preset_returns_prior_snapshot():
    prior = _current()
    returned = apply_2d_preset(prior, mirror_x=False)
    assert returned == prior


def test_apply_2d_preset_overrides_mirror_x():
    prior = _current()
    apply_2d_preset(prior, mirror_x=True)
    from core.skinning.paint_preset_2d import build_target_preset

    target = build_target_preset(mirror_x=True)
    assert target.use_x_mirror is True
    assert target.use_front_faces is False


def test_preset_2d_locks_front_faces_off():
    # Front Faces ON breaks strokes on thin planes; must stay False in the preset.
    assert PRESET_2D.use_front_faces is False


def test_apply_2d_preset_does_not_mutate_input():
    prior = _current()
    original_radius = prior.brush_radius
    apply_2d_preset(prior, mirror_x=False)
    assert prior.brush_radius == original_radius
