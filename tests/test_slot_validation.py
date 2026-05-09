"""Unit tests for the SPEC 004 Wave 4.1 slot validation rules (D9 + D10).

Pure pytest, no Blender. Mocks ``bpy.types.Object`` via ``SimpleNamespace``
so the validation module is exercised without Blender's RNA layer.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.validation import validate_active_slot  # noqa: E402


def _slot_props(*, is_slot: bool = True, slot_default: str = "") -> SimpleNamespace:
    return SimpleNamespace(is_slot=is_slot, slot_default=slot_default)


def _empty(
    name: str,
    *,
    children: list[Any] | None = None,
    parent_bone: str = "",
    parent_type: str = "OBJECT",
    props: SimpleNamespace | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="EMPTY",
        children=tuple(children or ()),
        parent_bone=parent_bone,
        parent_type=parent_type,
        proscenio=props if props is not None else _slot_props(),
    )


def _mesh(
    name: str,
    *,
    parent_bone: str = "",
    parent_type: str = "OBJECT",
    fcurves: list[Any] | None = None,
) -> SimpleNamespace:
    action = SimpleNamespace(fcurves=tuple(fcurves or ())) if fcurves else None
    anim_data = SimpleNamespace(action=action) if action else None
    return SimpleNamespace(
        name=name,
        type="MESH",
        parent_bone=parent_bone,
        parent_type=parent_type,
        animation_data=anim_data,
    )


def _fcurve(data_path: str) -> SimpleNamespace:
    return SimpleNamespace(data_path=data_path)


def test_non_empty_object_returns_no_issues() -> None:
    mesh = _mesh("torso")
    assert validate_active_slot(mesh) == []


def test_empty_not_flagged_as_slot_returns_no_issues() -> None:
    empty = _empty("loose_anchor", props=_slot_props(is_slot=False))
    assert validate_active_slot(empty) == []


def test_slot_with_no_children_emits_error() -> None:
    empty = _empty("eye.swap", children=[])
    issues = validate_active_slot(empty)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "no MESH children" in issues[0].message


def test_slot_with_valid_default_passes() -> None:
    empty = _empty(
        "eye.swap",
        children=[_mesh("open"), _mesh("closed")],
        props=_slot_props(slot_default="open"),
    )
    assert validate_active_slot(empty) == []


def test_slot_default_pointing_at_missing_child_errors() -> None:
    empty = _empty(
        "eye.swap",
        children=[_mesh("open"), _mesh("closed")],
        props=_slot_props(slot_default="dead"),
    )
    issues = validate_active_slot(empty)
    assert any(i.severity == "error" and "default" in i.message for i in issues)


def test_attachments_with_divergent_parent_bone_warn() -> None:
    empty = _empty(
        "forearm.swap",
        parent_bone="forearm.L",
        parent_type="BONE",
        children=[
            _mesh("front", parent_bone="forearm.L", parent_type="BONE"),
            _mesh("back", parent_bone="forearm.R", parent_type="BONE"),  # mismatch
        ],
    )
    issues = validate_active_slot(empty)
    warnings = [i for i in issues if i.severity == "warning"]
    assert len(warnings) == 1
    assert "differs from slot bone" in warnings[0].message


def test_attachments_with_no_parent_bone_skip_bone_check() -> None:
    """Attachment with parent_type='OBJECT' (no bone parent) does not trigger
    the divergent-bone warning -- only mismatched bone parents do."""
    empty = _empty(
        "forearm.swap",
        parent_bone="forearm.L",
        parent_type="BONE",
        children=[
            _mesh("front", parent_bone="forearm.L", parent_type="BONE"),
            _mesh("back", parent_type="OBJECT"),  # OBJECT-parented child is fine
        ],
    )
    assert validate_active_slot(empty) == []


def test_slot_child_with_bone_transform_keys_warns() -> None:
    empty = _empty(
        "eye.swap",
        children=[
            _mesh("open", fcurves=[_fcurve("location"), _fcurve("rotation_euler")]),
            _mesh("closed"),
        ],
    )
    issues = validate_active_slot(empty)
    warnings = [i for i in issues if "bone-transform" in i.message]
    assert len(warnings) == 1
    assert warnings[0].obj_name == "open"


def test_slot_child_with_proscenio_only_keys_does_not_warn() -> None:
    """An animated proscenio.frame fcurve is fine -- the warning only fires
    on location/rotation/scale paths."""
    empty = _empty(
        "eye.swap",
        children=[
            _mesh("cycling", fcurves=[_fcurve("proscenio.frame")]),
            _mesh("static"),
        ],
    )
    issues = [i for i in validate_active_slot(empty) if "bone-transform" in i.message]
    assert issues == []


def test_slot_with_no_bone_skips_bone_mismatch_check() -> None:
    """When the slot Empty has no bone parent, attachments are free to
    parent however the user wants -- no divergent-bone warning."""
    empty = _empty(
        "free.swap",
        children=[
            _mesh("a", parent_bone="bone.X", parent_type="BONE"),
            _mesh("b", parent_bone="bone.Y", parent_type="BONE"),
        ],
    )
    assert validate_active_slot(empty) == []
