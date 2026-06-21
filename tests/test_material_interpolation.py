"""Unit tests for the pixel-art texture-interpolation walk.

The per-element ``Pixel art`` checkbox (spec 057) flips every image-texture
node on the active object's materials between ``Closest`` (crisp,
nearest-neighbor) and ``Linear`` (Blender's bilinear default). The pure
node walk + interpolation set lives in ``core._shared.material_images`` next
to the existing image walk, so it is exercised here without a Blender
session - ``SimpleNamespace`` stands in for the bpy ``Object`` / ``Material``
/ node duck types the walk reads through ``getattr`` / ``setattr``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.hydrate import OBJECT_PROPS  # noqa: E402  - sys.path setup above
from core._shared.material_images import (  # noqa: E402  - sys.path setup above
    iter_material_image_nodes,
    set_object_texture_interpolation,
)
from core.mirror import OBJECT_MIRROR_MAP  # noqa: E402  - sys.path setup above


def _tex_node(interpolation: str = "Linear") -> SimpleNamespace:
    """A TEX_IMAGE node mock with an image bound and an interpolation slot."""
    return SimpleNamespace(
        type="TEX_IMAGE",
        image=SimpleNamespace(name="tex"),
        interpolation=interpolation,
    )


def _material(*nodes: SimpleNamespace, use_nodes: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        use_nodes=use_nodes,
        node_tree=SimpleNamespace(nodes=list(nodes)),
    )


def _object(*materials: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(data=SimpleNamespace(materials=list(materials)))


def test_iter_image_nodes_yields_only_tex_image_nodes() -> None:
    tex = _tex_node()
    other = SimpleNamespace(type="EMISSION")
    nodes = list(iter_material_image_nodes(_material(other, tex)))
    assert nodes == [tex]


def test_iter_image_nodes_skips_image_node_without_image() -> None:
    bound = _tex_node()
    unbound = SimpleNamespace(type="TEX_IMAGE", image=None, interpolation="Linear")
    nodes = list(iter_material_image_nodes(_material(unbound, bound)))
    assert nodes == [bound]


def test_iter_image_nodes_skips_inactive_node_tree() -> None:
    # use_nodes=False: the tree is inactive on Blender 5.1 and must be skipped.
    nodes = list(iter_material_image_nodes(_material(_tex_node(), use_nodes=False)))
    assert nodes == []


def test_iter_image_nodes_handles_none_material() -> None:
    assert list(iter_material_image_nodes(None)) == []


def test_pixel_art_on_sets_closest_across_all_materials() -> None:
    a, b = _tex_node("Linear"), _tex_node("Linear")
    obj = _object(_material(a), _material(b))
    set_object_texture_interpolation(obj, "Closest")
    assert a.interpolation == "Closest"
    assert b.interpolation == "Closest"


def test_pixel_art_off_restores_linear() -> None:
    node = _tex_node("Closest")
    obj = _object(_material(node))
    set_object_texture_interpolation(obj, "Linear")
    assert node.interpolation == "Linear"


def test_set_interpolation_handles_object_without_materials() -> None:
    obj = SimpleNamespace(data=SimpleNamespace(materials=None))
    # No materials: a no-op, must not raise.
    set_object_texture_interpolation(obj, "Closest")


def test_set_interpolation_handles_none_object() -> None:
    set_object_texture_interpolation(None, "Closest")  # must not raise


def test_pixel_art_not_exported() -> None:
    """``pixel_art`` is authoring-only: never mirrored to a CP, never hydrated.

    The toggle changes only viewport interpolation. If it ever picked up a
    mirror/hydrate entry it would start writing a Custom Property and could
    leak into a downstream reader, so guard both maps here.
    """
    mirror_attrs = {attr for _cp, attr, _caster in OBJECT_MIRROR_MAP}
    hydrate_attrs = {attr for _cp, attr in OBJECT_PROPS}
    assert "pixel_art" not in mirror_attrs
    assert "pixel_art" not in hydrate_attrs
