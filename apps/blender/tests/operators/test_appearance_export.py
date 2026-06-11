"""Headless writer test: appearance + pivot offset derive from native Blender state.

Runs INSIDE Blender via ``run_operator_tests.py``. Builds real mesh objects (no
.blend fixture) and drives the writer so the bpy matrix / mesh-bounds path - the
pivot-offset projection pure pytest cannot exercise - is covered. The bpy-free
derivations (modulate / z_index / flips) are unit-tested in ``tests/writer``;
here they ride along on a real object to prove the wiring.
"""

from __future__ import annotations

import bmesh
import bpy
import pytest

from .conftest import _load_addon_as_package


@pytest.fixture
def addon() -> None:
    """Mount the addon and start from an empty file.

    Skips when the bundled ``proscenio_models`` predates the appearance fields
    - Blender installs the wheel into an isolated site-packages, so a stale
    cached install would fail the emit rather than exercise it. Rebuild via
    ``uv build packages/models --wheel --out-dir apps/blender/wheels``.
    """
    _load_addon_as_package()
    from proscenio_models import SpriteElement

    if "modulate" not in SpriteElement.model_fields:
        pytest.skip("bundled proscenio_models predates the appearance fields")
    bpy.ops.wm.read_homefile(use_empty=True)


def _new_quad(name: str, corners: list[tuple[float, float, float]]) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new(co) for co in corners]
    bm.faces.new(verts)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_sprite_emits_appearance_and_offset(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_sprite

    # Centred quad so the pivot offset stays zero while the appearance fields
    # exercise their own derivations.
    obj = _new_quad(
        "hat",
        [(-0.5, 0.0, -0.5), (0.5, 0.0, -0.5), (0.5, 0.0, 0.5), (-0.5, 0.0, 0.5)],
    )
    obj.color = (1.0, 0.5, 0.25, 1.0)
    obj.location.y = 0.002  # z_order 2, two steps behind the front plane
    obj.scale.x = -1.0  # mirrored horizontally

    sprite = build_sprite(obj, ppu=100.0)
    assert sprite.type == "sprite"
    assert sprite.modulate == [1.0, 0.5, 0.25, 1.0]
    assert sprite.z_index == -2
    assert sprite.flip_h is True
    assert sprite.flip_v is None
    assert sprite.offset == [0.0, 0.0]  # centred geometry -> no pivot shift


def test_sprite_offset_tracks_an_off_centre_pivot(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_sprite

    # Quad spanning X[0,1] Z[0,1] with the origin at the corner: the visible
    # centre sits at local (0.5, 0, 0.5), which maps to Godot (50, -50).
    obj = _new_quad(
        "off_pivot",
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)],
    )

    sprite = build_sprite(obj, ppu=100.0)
    assert sprite.offset == [50.0, -50.0]


def test_mesh_emits_modulate_and_z_index(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_element

    obj = _new_quad(
        "panel",
        [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)],
    )
    obj.color = (0.2, 0.4, 0.6, 1.0)
    obj.location.y = 0.001  # z_order 1, one step back

    element = build_element(obj, {}, ppu=100.0)
    assert element.type == "mesh"
    assert element.modulate == [0.2, 0.4, 0.6, 1.0]
    assert element.z_index == -1
