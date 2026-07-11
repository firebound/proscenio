"""Unit tests for the slot system slot validation rules.

Pure pytest, no Blender. The slot flags read from their ``proscenio_*``
Custom Properties (idprops) via ``.get`` (spec 037); ``_Empty`` is a fake
bpy Object exposing both attribute access and that idprop ``.get``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.validation import slot_parent_bone, validate_active_slot  # noqa: E402


class _Empty(SimpleNamespace):
    """Fake bpy Object: attribute access plus idprop-style ``.get``."""

    def __init__(self, idprops: dict[str, Any] | None = None, **attrs: Any) -> None:
        super().__init__(**attrs)
        object.__setattr__(self, "_idprops", dict(idprops or {}))

    def get(self, key: str, default: Any = None) -> Any:
        return self._idprops.get(key, default)


def _slot_idprops(
    *, is_slot: bool = True, slot_default: str = "", slot_bone: str = ""
) -> dict[str, Any]:
    return {
        "proscenio_is_slot": is_slot,
        "proscenio_slot_default": slot_default,
        "proscenio_slot_bone": slot_bone,
    }


def _empty(
    name: str,
    *,
    children: list[Any] | None = None,
    parent_bone: str = "",
    parent_type: str = "OBJECT",
    props: dict[str, Any] | None = None,
) -> _Empty:
    return _Empty(
        props if props is not None else _slot_idprops(),
        name=name,
        type="EMPTY",
        children=tuple(children or ()),
        parent_bone=parent_bone,
        parent_type=parent_type,
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


def _keyframe(frame: float, value: float) -> SimpleNamespace:
    return SimpleNamespace(co=SimpleNamespace(x=frame, y=value))


def _vis_mesh(
    name: str,
    *,
    action_name: str,
    hide_render_keys: list[tuple[float, float]],
) -> SimpleNamespace:
    """A slot attachment carrying a ``hide_render`` fcurve (0.0 shown / 1.0 hidden).

    Models the visibility swap the writer reads: each key is ``(frame, value)``.
    The keys live on an action named ``action_name`` so the overlap check groups
    attachments by the animation they are keyed in.
    """
    hide_render = SimpleNamespace(
        data_path="hide_render",
        keyframe_points=tuple(_keyframe(f, v) for f, v in hide_render_keys),
    )
    action = SimpleNamespace(name=action_name, fcurves=(hide_render,))
    return SimpleNamespace(
        name=name,
        type="MESH",
        parent_bone="",
        parent_type="OBJECT",
        animation_data=SimpleNamespace(action=action),
    )


def test_non_empty_object_returns_no_issues() -> None:
    mesh = _mesh("torso")
    assert validate_active_slot(mesh) == []


def test_empty_not_flagged_as_slot_returns_no_issues() -> None:
    empty = _empty("loose_anchor", props=_slot_idprops(is_slot=False))
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
        props=_slot_idprops(slot_default="open"),
    )
    assert validate_active_slot(empty) == []


def test_slot_default_pointing_at_missing_child_errors() -> None:
    empty = _empty(
        "eye.swap",
        children=[_mesh("open"), _mesh("closed")],
        props=_slot_idprops(slot_default="dead"),
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
    the divergent-bone warning - only mismatched bone parents do."""
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
    """An animated proscenio frame fcurve is fine - the warning only fires
    on location/rotation/scale paths."""
    empty = _empty(
        "eye.swap",
        children=[
            _mesh("cycling", fcurves=[_fcurve('["proscenio_frame"]')]),
            _mesh("static"),
        ],
    )
    issues = [i for i in validate_active_slot(empty) if "bone-transform" in i.message]
    assert issues == []


def test_slot_with_no_bone_skips_bone_mismatch_check() -> None:
    """When the slot Empty has no bone parent, attachments are free to
    parent however the user wants - no divergent-bone warning."""
    empty = _empty(
        "free.swap",
        children=[
            _mesh("a", parent_bone="bone.X", parent_type="BONE"),
            _mesh("b", parent_bone="bone.Y", parent_type="BONE"),
        ],
    )
    assert validate_active_slot(empty) == []


def test_two_attachments_visible_at_same_frame_warn() -> None:
    # Both attachments keyed shown (hide_render 0.0) at frame 5 in the same
    # animation: the writer would drop one, so the validator flags the overlap.
    empty = _empty(
        "hand.swap",
        children=[
            _vis_mesh("club", action_name="attack", hide_render_keys=[(5.0, 0.0)]),
            _vis_mesh("torch", action_name="attack", hide_render_keys=[(5.0, 0.0)]),
        ],
    )
    issues = validate_active_slot(empty)
    overlaps = [i for i in issues if "are all" in i.message]
    assert len(overlaps) == 1
    assert overlaps[0].severity == "warning"
    assert "club" in overlaps[0].message and "torch" in overlaps[0].message
    assert "frame 5" in overlaps[0].message


def test_exclusive_swap_does_not_warn() -> None:
    # club shown then hidden, torch hidden then shown - never two at once.
    empty = _empty(
        "hand.swap",
        children=[
            _vis_mesh("club", action_name="attack", hide_render_keys=[(1.0, 0.0), (5.0, 1.0)]),
            _vis_mesh("torch", action_name="attack", hide_render_keys=[(1.0, 1.0), (5.0, 0.0)]),
        ],
    )
    overlaps = [i for i in validate_active_slot(empty) if "are all" in i.message]
    assert overlaps == []


def test_overlap_across_different_animations_does_not_warn() -> None:
    # Each attachment is shown at frame 5 but in a DIFFERENT animation, so they
    # never coexist on the same clip - no overlap warning.
    empty = _empty(
        "hand.swap",
        children=[
            _vis_mesh("club", action_name="attack_club", hide_render_keys=[(5.0, 0.0)]),
            _vis_mesh("torch", action_name="attack_torch", hide_render_keys=[(5.0, 0.0)]),
        ],
    )
    overlaps = [i for i in validate_active_slot(empty) if "are all" in i.message]
    assert overlaps == []


def test_slot_parent_bone_reads_a_bone_parent() -> None:
    empty = _empty("forearm.swap", parent_bone="forearm.L", parent_type="BONE")
    assert slot_parent_bone(empty) == "forearm.L"


def test_slot_parent_bone_empty_when_object_parented() -> None:
    # parent_bone is a stale leftover; parent_type OBJECT means it is not a
    # bone parent, so the shared predicate reports the slot as unparented.
    empty = _empty("loose.swap", parent_bone="forearm.L", parent_type="OBJECT")
    assert slot_parent_bone(empty) == ""


def test_slot_parent_bone_empty_when_unparented() -> None:
    empty = _empty("free.swap")
    assert slot_parent_bone(empty) == ""


def test_slot_parent_bone_reads_slot_bone_field_when_object_parented() -> None:
    # The new convention: object-parented Empty + slot_bone field set. The
    # resolver must report the field's bone, not "(unparented)".
    empty = _empty(
        "face.slot", parent_type="OBJECT", props=_slot_idprops(slot_bone="head")
    )
    assert slot_parent_bone(empty) == "head"


def test_slot_parent_bone_prefers_slot_bone_over_parent_bone() -> None:
    # slot_bone wins over a leftover bone parent, matching the writer's order.
    empty = _empty(
        "face.slot",
        parent_bone="jaw",
        parent_type="BONE",
        props=_slot_idprops(slot_bone="head"),
    )
    assert slot_parent_bone(empty) == "head"


def test_slot_parent_bone_falls_back_to_bone_parent_when_no_field() -> None:
    empty = _empty("forearm.swap", parent_bone="forearm.L", parent_type="BONE")
    assert slot_parent_bone(empty) == "forearm.L"


def test_bound_slot_with_field_emits_no_unparented_error() -> None:
    # The whole point: a slot_bone-bound slot with a child is fully valid.
    empty = _empty(
        "face.slot",
        parent_type="OBJECT",
        children=[_mesh("face_neutral")],
        props=_slot_idprops(slot_bone="head"),
    )
    assert validate_active_slot(empty) == []
