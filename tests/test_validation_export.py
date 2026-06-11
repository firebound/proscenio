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

from core.validation.active_slot import (  # noqa: E402
    _check_slot_default,
    _has_bone_transform_keys,
)
from core.validation.export import (  # noqa: E402
    _validate_atlas_files,
    _validate_element_against_armature,
    _validate_slots,
    validate_export,
)
from core.validation.issue import Issue  # noqa: E402


def _slot_empty() -> SimpleNamespace:
    return SimpleNamespace(type="EMPTY", proscenio=SimpleNamespace(is_slot=True))


def _cp_carrier(**cp: str) -> SimpleNamespace:
    # Unhydrated object: no PropertyGroup, value only on the raw CP dict.
    return SimpleNamespace(proscenio=None, get=lambda key, default=None: cp.get(key, default))


def _has(issues: list[Issue], severity: str, substr: str) -> bool:
    return any(i.severity == severity and substr in i.message for i in issues)


def _armature(*bone_names: str) -> SimpleNamespace:
    return SimpleNamespace(
        type="ARMATURE",
        data=SimpleNamespace(bones=[SimpleNamespace(name=n) for n in bone_names]),
    )


def _named_armature(name: str, *bone_names: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
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


def test_validate_export_resolves_bones_from_the_picked_armature() -> None:
    # Two armatures; the mesh rides a bone that exists only on the picked one.
    base = _named_armature("Base", "base")
    spine = _named_armature("Spine", "spine")
    mesh = _mesh("torso", parent_bone="spine", groups=[])
    scene = SimpleNamespace(
        objects=[base, spine, mesh],
        proscenio=SimpleNamespace(active_armature=spine),
    )
    assert not _has(validate_export(scene), "warning", "no parent bone")


def test_validate_export_without_a_picker_uses_the_first_armature() -> None:
    base = _named_armature("Base", "base")
    spine = _named_armature("Spine", "spine")
    mesh = _mesh("torso", parent_bone="spine", groups=[])
    scene = SimpleNamespace(
        objects=[base, spine, mesh],
        proscenio=SimpleNamespace(active_armature=None),
    )
    # First armature in scene order (Base) supplies bones; "spine" is unknown.
    assert _has(validate_export(scene), "warning", "no parent bone")


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


def test_slot_attachment_does_not_flag_a_missing_bone() -> None:
    # A slot attachment inherits its bone through the slot Empty by design.
    obj = SimpleNamespace(name="sword", parent=_slot_empty(), parent_bone="", vertex_groups=[])
    assert _validate_element_against_armature(obj, {"spine"}) == []


def test_slot_default_validates_a_raw_custom_property_edit() -> None:
    # PG absent (unhydrated); slot_default lives only on the raw CP, the way
    # the writer reads it - so the validator must see the same invalid value.
    obj = _cp_carrier(proscenio_slot_default="ghost")
    children = [SimpleNamespace(name="open"), SimpleNamespace(name="closed")]
    assert _has(_check_slot_default(obj, children, "eye"), "error", "is not a child")


def _action_with_path(data_path: str, *, layered: bool) -> SimpleNamespace:
    fcurve = SimpleNamespace(data_path=data_path)
    if not layered:
        return SimpleNamespace(fcurves=[fcurve])
    # Blender 4.4+ layered action: flat fcurves empty, curves nest in the
    # layer > strip > channelbag stack.
    channelbag = SimpleNamespace(fcurves=[fcurve])
    strip = SimpleNamespace(channelbags=[channelbag])
    return SimpleNamespace(fcurves=[], layers=[SimpleNamespace(strips=[strip])])


def _child_with_action(action: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(name="sword", animation_data=SimpleNamespace(action=action))


def test_transform_key_check_sees_a_layered_action() -> None:
    child = _child_with_action(_action_with_path("location", layered=True))
    assert _has_bone_transform_keys(child) is True


def test_transform_key_check_sees_a_legacy_action() -> None:
    child = _child_with_action(_action_with_path("rotation_euler", layered=False))
    assert _has_bone_transform_keys(child) is True


def test_transform_key_check_ignores_a_visibility_only_layered_action() -> None:
    child = _child_with_action(_action_with_path('["proscenio_slot_index"]', layered=True))
    assert _has_bone_transform_keys(child) is False


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
