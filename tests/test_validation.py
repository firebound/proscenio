"""Unit tests for the SPEC 005 validation surface.

Runs under plain ``pytest`` — no Blender required. Mocks `bpy` objects via
:class:`SimpleNamespace` so the validation module is exercised in isolation
from the editor.

Run from the repo root:

    pytest tests/test_validation.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core import validation  # noqa: E402


def _mesh(polygon_count: int = 1) -> SimpleNamespace:
    return SimpleNamespace(polygons=[object()] * polygon_count)


def _polygon_obj(name: str = "torso", *, polygons: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="MESH",
        data=_mesh(polygons),
        proscenio=SimpleNamespace(sprite_type="polygon"),
        get=lambda key, default=None: default,
    )


def _sprite_frame_obj(
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
            sprite_type="sprite_frame",
            hframes=hframes,
            vframes=vframes,
        ),
        get=lambda key, default=None: default,
    )


# --------------------------------------------------------------------------- #
# validate_active_sprite
# --------------------------------------------------------------------------- #


def test_active_polygon_with_polygons_is_clean() -> None:
    assert validation.validate_active_sprite(_polygon_obj()) == []


def test_active_polygon_without_polygons_warns() -> None:
    issues = validation.validate_active_sprite(_polygon_obj(polygons=0))
    assert len(issues) == 1
    assert issues[0].severity == "warning"


def test_active_sprite_frame_with_valid_grid_is_clean() -> None:
    assert validation.validate_active_sprite(_sprite_frame_obj()) == []


def test_active_sprite_frame_zero_hframes_errors() -> None:
    issues = validation.validate_active_sprite(_sprite_frame_obj(hframes=0))
    severities = {i.severity for i in issues}
    assert "error" in severities


def test_active_sprite_frame_zero_vframes_errors() -> None:
    issues = validation.validate_active_sprite(_sprite_frame_obj(vframes=0))
    severities = {i.severity for i in issues}
    assert "error" in severities


def test_active_unknown_sprite_type_errors() -> None:
    obj = SimpleNamespace(
        name="weird",
        type="MESH",
        data=_mesh(1),
        proscenio=SimpleNamespace(sprite_type="banana"),
        get=lambda key, default=None: default,
    )
    issues = validation.validate_active_sprite(obj)
    assert any(i.severity == "error" and "unknown" in i.message for i in issues)


def test_active_non_mesh_object_yields_no_issues() -> None:
    assert validation.validate_active_sprite(SimpleNamespace(type="ARMATURE")) == []


# --------------------------------------------------------------------------- #
# validate_export
# --------------------------------------------------------------------------- #


def _scene(*objects: Any) -> SimpleNamespace:
    return SimpleNamespace(objects=list(objects))


def _armature(
    name: str = "rig", bone_names: tuple[str, ...] = ("root",)
) -> SimpleNamespace:
    return SimpleNamespace(
        type="ARMATURE",
        name=name,
        data=SimpleNamespace(bones=[SimpleNamespace(name=n) for n in bone_names]),
    )


def _polygon_with_groups(
    name: str = "torso",
    *,
    parent_bone: str = "",
    group_names: tuple[str, ...] = (),
) -> SimpleNamespace:
    obj = _polygon_obj(name)
    obj.parent_bone = parent_bone
    obj.vertex_groups = [SimpleNamespace(name=n) for n in group_names]
    obj.material_slots = []
    return obj


def test_export_no_armature_blocks() -> None:
    issues = validation.validate_export(_scene(_polygon_with_groups()))
    assert any(i.severity == "error" and "Armature" in i.message for i in issues)


def test_export_with_matching_vertex_group_clean() -> None:
    armature = _armature(bone_names=("root", "torso"))
    sprite = _polygon_with_groups("torso", group_names=("torso",))
    issues = validation.validate_export(_scene(armature, sprite))
    assert all(i.severity == "warning" for i in issues)


def test_export_sprite_with_orphan_vertex_groups_errors() -> None:
    armature = _armature(bone_names=("root",))
    sprite = _polygon_with_groups("torso", group_names=("nonexistent",))
    issues = validation.validate_export(_scene(armature, sprite))
    error_messages = [i.message for i in issues if i.severity == "error"]
    assert any("none resolve" in m for m in error_messages)


def test_export_sprite_with_no_groups_and_parent_bone_warns_softly() -> None:
    armature = _armature(bone_names=("root", "torso"))
    sprite = _polygon_with_groups("torso", parent_bone="torso")
    issues = validation.validate_export(_scene(armature, sprite))
    severities = {i.severity for i in issues}
    assert "error" not in severities


def test_export_sprite_unparented_warns() -> None:
    armature = _armature(bone_names=("root",))
    sprite = _polygon_with_groups("orphan")
    issues = validation.validate_export(_scene(armature, sprite))
    warnings = [i for i in issues if i.severity == "warning"]
    assert any("no parent bone" in i.message for i in warnings)
