"""Headless writer test: a bone-driven sprite frame bakes into a sprite_frame track.

Runs INSIDE Blender via ``run_operator_tests.py``, which registers the addon
PropertyGroup - the Drive-from-Bone driver writes to ``proscenio.frame``, so the
bake needs a live PG to read the depsgraph-evaluated value. Opens the real
``mouth_drive`` fixture (a sprite whose frame is driven from the ``mouth_drive``
bone via ``var * 2 + 2``) and asserts the writer bakes the driven sequence,
clamped to the 4-frame grid, with constant-interpolation keys.
"""

from __future__ import annotations

from pathlib import Path

import bpy
import pytest

from .conftest import _load_addon_as_package

REPO_ROOT = Path(__file__).resolve().parents[4]
MOUTH_BLEND = REPO_ROOT / "examples" / "generated" / "mouth_drive" / "mouth_drive.blend"


@pytest.fixture
def mouth_scene() -> None:
    _load_addon_as_package()
    if not MOUTH_BLEND.exists():
        pytest.skip(f"fixture missing at {MOUTH_BLEND}")
    bpy.ops.wm.open_mainfile(filepath=str(MOUTH_BLEND))


def test_mouth_drive_bakes_a_clamped_sprite_frame_track(mouth_scene: None) -> None:
    from proscenio.exporters.godot.writer.sprite_frame_animations import (
        build_sprite_frame_animations,
    )

    scene = bpy.context.scene
    anims = build_sprite_frame_animations(scene, scene.render.fps)

    tracks = [
        track
        for anim in anims
        for track in anim.tracks
        if track.type == "sprite_frame" and track.target == "mouth"
    ]
    assert len(tracks) == 1, "expected exactly one baked sprite_frame track for 'mouth'"

    keyed = [(key.time, key.frame) for key in tracks[0].keys]
    # Driven value is `int(bone_rot_y * 2 + 2)` clamped to the 4-frame grid
    # (max index 3); a key lands only where the frame changes.
    assert keyed == [
        (0.0, 2),
        (0.041667, 1),
        (0.125, 0),
        (0.458333, 2),
        (0.5, 3),
        (0.833333, 2),
    ]
    assert all(key.interp == "constant" for key in tracks[0].keys)


def test_bake_restores_the_current_frame(mouth_scene: None) -> None:
    from proscenio.exporters.godot.writer.sprite_frame_animations import (
        build_sprite_frame_animations,
    )

    scene = bpy.context.scene
    scene.frame_set(7)
    build_sprite_frame_animations(scene, scene.render.fps)
    assert scene.frame_current == 7
