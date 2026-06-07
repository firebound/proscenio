"""Pure-pytest tests for the pre-export validation rules.

The full ``validate_export`` pass is duck-typed over the scene, so
SimpleNamespace fakes drive each business rule: armature required,
element/armature wiring, duplicate slot names, and missing atlas files.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.validation.export import (  # noqa: E402
    _validate_atlas_files,
    _validate_element_against_armature,
    _validate_slots,
    validate_export,
)
from core.validation.issue import Issue  # noqa: E402


def _has(issues: list[Issue], severity: str, substr: str) -> bool:
    return any(i.severity == severity and substr in i.message for i in issues)


def _armature(*bone_names: str) -> SimpleNamespace:
    return SimpleNamespace(
        type="ARMATURE",
        data=SimpleNamespace(bones=[SimpleNamespace(name=n) for n in bone_names]),
    )


def _mesh(name: str, *, parent_bone: str, groups: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="MESH",
        data=SimpleNamespace(polygons=[object()]),
        parent_bone=parent_bone,
        vertex_groups=[SimpleNamespace(name=g) for g in groups],
    )


def test_validate_export_requires_an_armature() -> None:
    issues = validate_export(SimpleNamespace(objects=[]))
    assert _has(issues, "error", "no Armature")


def test_full_pass_flags_an_unresolved_element() -> None:
    scene = SimpleNamespace(
        objects=[_armature("spine"), _mesh("torso", parent_bone="", groups=["ghost"])],
    )
    assert _has(validate_export(scene), "error", "none resolve to bones")


def test_full_pass_on_a_clean_scene_has_no_errors() -> None:
    scene = SimpleNamespace(
        objects=[_armature("spine"), _mesh("torso", parent_bone="spine", groups=[])],
    )
    assert [i for i in validate_export(scene) if i.severity == "error"] == []


def test_element_with_parent_bone_is_clean() -> None:
    obj = SimpleNamespace(name="torso", parent_bone="spine", vertex_groups=[])
    assert _validate_element_against_armature(obj, {"spine"}) == []


def test_element_without_bone_or_groups_warns() -> None:
    obj = SimpleNamespace(name="torso", parent_bone="", vertex_groups=[])
    assert _has(_validate_element_against_armature(obj, {"spine"}), "warning", "no parent bone")


def test_element_with_unresolved_vertex_groups_errors() -> None:
    obj = SimpleNamespace(
        name="torso", parent_bone="", vertex_groups=[SimpleNamespace(name="ghost")]
    )
    assert _has(
        _validate_element_against_armature(obj, {"spine"}), "error", "none resolve to bones"
    )


def test_element_with_matching_vertex_group_is_clean() -> None:
    obj = SimpleNamespace(
        name="torso", parent_bone="", vertex_groups=[SimpleNamespace(name="spine")]
    )
    assert _validate_element_against_armature(obj, {"spine"}) == []


def test_duplicate_slot_name_errors() -> None:
    def slot(name: str) -> SimpleNamespace:
        return SimpleNamespace(
            name=name,
            type="EMPTY",
            parent_type="OBJECT",
            proscenio=SimpleNamespace(is_slot=True, slot_default=""),
            children=[SimpleNamespace(name=f"{name}.mesh", type="MESH")],
        )

    assert _has(_validate_slots([slot("brow"), slot("brow")]), "error", "duplicate slot name")


def test_atlas_missing_file_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "bpy", None)
    node = SimpleNamespace(
        type="TEX_IMAGE", image=SimpleNamespace(filepath="missing_atlas_zzz.png")
    )
    material = SimpleNamespace(use_nodes=True, node_tree=SimpleNamespace(nodes=[node]))
    obj = SimpleNamespace(name="torso", material_slots=[SimpleNamespace(material=material)])
    assert _has(_validate_atlas_files([obj]), "warning", "not found on disk")
