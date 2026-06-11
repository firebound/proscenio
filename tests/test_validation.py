"""Unit tests for the authoring panel validation surface.

Runs under plain ``pytest`` - no Blender required. Mocks `bpy` objects via
:class:`SimpleNamespace` so the validation module is exercised in isolation
from the editor.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core import validation  # noqa: E402


def _mesh(polygon_count: int = 1, vert_count: int = 4) -> SimpleNamespace:
    # Default is a single quad (4 verts, 1 face) - the shape a sprite element
    # keeps; mesh-element checks only read polygons.
    return SimpleNamespace(
        vertices=[object()] * vert_count,
        polygons=[object()] * polygon_count,
    )


def _mesh_obj(name: str = "torso", *, polygons: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="MESH",
        data=_mesh(polygons),
        proscenio=SimpleNamespace(element_type="mesh"),
        get=lambda key, default=None: default,
    )


def _sprite_obj(
    name: str = "spark",
    *,
    hframes: int = 4,
    vframes: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="MESH",
        data=_mesh(1),
        proscenio=SimpleNamespace(
            element_type="sprite",
            hframes=hframes,
            vframes=vframes,
        ),
        get=lambda key, default=None: default,
    )


def test_active_mesh_with_polygons_is_clean() -> None:
    assert validation.validate_active_element(_mesh_obj()) == []


def test_active_mesh_without_polygons_warns() -> None:
    issues = validation.validate_active_element(_mesh_obj(polygons=0))
    assert len(issues) == 1
    assert issues[0].severity == "warning"


def test_active_sprite_with_valid_grid_is_clean() -> None:
    assert validation.validate_active_element(_sprite_obj()) == []


def test_active_sprite_with_a_dense_mesh_warns_it_is_not_a_quad() -> None:
    """A sprite exports as a Sprite2D from its single base quad. A mesh tool
    (automesh) that ran on the sprite replaces the quad with a dense mesh the
    writer cannot map to a sprite, so the validator warns it is no longer a
    quad and points at native bone-parenting instead."""
    obj = _sprite_obj()
    obj.data = _mesh(polygon_count=90, vert_count=60)
    issues = validation.validate_active_element(obj)
    assert any(i.severity == "warning" and "quad" in i.message for i in issues)


def test_active_sprite_zero_hframes_errors() -> None:
    issues = validation.validate_active_element(_sprite_obj(hframes=0))
    severities = {i.severity for i in issues}
    assert "error" in severities


def test_active_sprite_zero_vframes_errors() -> None:
    issues = validation.validate_active_element(_sprite_obj(vframes=0))
    severities = {i.severity for i in issues}
    assert "error" in severities


def test_active_unknown_element_type_errors() -> None:
    obj = SimpleNamespace(
        name="weird",
        type="MESH",
        data=_mesh(1),
        proscenio=SimpleNamespace(element_type="banana"),
        get=lambda key, default=None: default,
    )
    issues = validation.validate_active_element(obj)
    assert any(i.severity == "error" and "unknown" in i.message for i in issues)


def test_active_non_mesh_object_yields_no_issues() -> None:
    assert validation.validate_active_element(SimpleNamespace(type="ARMATURE")) == []
