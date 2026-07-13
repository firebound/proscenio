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
from core.validation.checks.atlas_files import (  # noqa: E402
    validate_atlas_files as _validate_atlas_files,
)
from core.validation.checks.bone_follow import (  # noqa: E402
    validate_bone_follow as _validate_bone_follow,
)
from core.validation.checks.bone_orientation import (  # noqa: E402
    validate_bone_orientation as _validate_bone_orientation,
)
from core.validation.checks.driver_rotation import (  # noqa: E402
    validate_driver_rotation_modes as _validate_driver_rotation_modes,
)
from core.validation.checks.element_armature import (  # noqa: E402
    validate_element_against_armature as _validate_element_against_armature,
)
from core.validation.checks.ik_bake import (  # noqa: E402
    validate_ik_bake as _validate_ik_bake,
)
from core.validation.checks.mesh_flatness import (  # noqa: E402
    validate_mesh_flatness as _validate_mesh_flatness,
)
from core.validation.checks.slots import (  # noqa: E402
    validate_slots as _validate_slots,
)
from core.validation.checks.sprite_frame_uvs import (  # noqa: E402
    validate_sprite_frame_uvs as _validate_sprite_frame_uvs,
)
from core.validation.export import validate_export  # noqa: E402
from core.validation.issue import Issue  # noqa: E402

# spec 037: the writer reads each per-Object field from its ``proscenio_*``
# Custom Property (idprop) via ``obj.get``. ``_Obj`` is a bpy-Object stand-in
# whose ``.get`` derives the idprop value from a ``proscenio=`` namespace, so
# the test data stays readable while exercising the real idprop read path.
_FIELD_TO_CP = {"element_type": "proscenio_type"}


def _cp_key(field: str) -> str:
    return _FIELD_TO_CP.get(field, f"proscenio_{field}")


class _Obj(SimpleNamespace):
    """A fake bpy Object: attribute access plus idprop-style ``.get``."""

    def get(self, key, default=None):  # noqa: ANN001, ANN201
        pg = getattr(self, "proscenio", None)
        if pg is None:
            return default
        for field, value in vars(pg).items():
            if _cp_key(field) == key:
                return value
        return default


def _slot_empty() -> SimpleNamespace:
    return _Obj(type="EMPTY", proscenio=SimpleNamespace(is_slot=True))


def _cp_carrier(**cp: str) -> SimpleNamespace:
    # Unhydrated object: no PropertyGroup, value only on the raw CP dict.
    return SimpleNamespace(
        proscenio=None, get=lambda key, default=None: cp.get(key, default)
    )


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


def _sprite_uvs(
    name: str,
    uvs: list[tuple[float, float]],
    *,
    hframes: int = 2,
    vframes: int = 1,
    region_mode: str = "auto",
    element_type: str = "sprite",
) -> SimpleNamespace:
    loops = [SimpleNamespace(uv=(u, v)) for u, v in uvs]
    return _Obj(
        name=name,
        type="MESH",
        proscenio=SimpleNamespace(
            element_type=element_type,
            hframes=hframes,
            vframes=vframes,
            region_mode=region_mode,
        ),
        data=SimpleNamespace(
            uv_layers=SimpleNamespace(active=SimpleNamespace(data=loops))
        ),
    )


_FULL_SHEET = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
_SHRUNK = [(0.1, 0.1), (0.4, 0.1), (0.4, 0.4), (0.1, 0.4)]


def test_sheet_sliced_sprite_warns_on_shrunk_uvs() -> None:
    obj = _sprite_uvs("blink", _SHRUNK)
    assert _has(_validate_sprite_frame_uvs(obj), "warning", "not the full 0-1 sheet")


def test_full_sheet_sprite_has_no_warning() -> None:
    obj = _sprite_uvs("blink", _FULL_SHEET)
    assert _validate_sprite_frame_uvs(obj) == []


def test_manual_region_sprite_is_skipped() -> None:
    obj = _sprite_uvs("blink", _SHRUNK, region_mode="manual")
    assert _validate_sprite_frame_uvs(obj) == []


def test_single_frame_sprite_is_skipped() -> None:
    obj = _sprite_uvs("blink", _SHRUNK, hframes=1, vframes=1)
    assert _validate_sprite_frame_uvs(obj) == []


def test_mesh_element_is_skipped() -> None:
    obj = _sprite_uvs("torso", _SHRUNK, element_type="mesh")
    assert _validate_sprite_frame_uvs(obj) == []


def test_element_without_bone_or_groups_warns() -> None:
    obj = SimpleNamespace(name="torso", parent_bone="", vertex_groups=[])
    assert _has(
        _validate_element_against_armature(obj, {"spine"}), "warning", "no parent bone"
    )


def test_element_with_unresolved_vertex_groups_errors() -> None:
    obj = SimpleNamespace(
        name="torso", parent_bone="", vertex_groups=[SimpleNamespace(name="ghost")]
    )
    assert _has(
        _validate_element_against_armature(obj, {"spine"}),
        "error",
        "none resolve to bones",
    )


def test_element_with_matching_vertex_group_is_clean() -> None:
    obj = SimpleNamespace(
        name="torso", parent_bone="", vertex_groups=[SimpleNamespace(name="spine")]
    )
    assert _validate_element_against_armature(obj, {"spine"}) == []


def test_slot_attachment_does_not_flag_a_missing_bone() -> None:
    # A slot attachment inherits its bone through the slot Empty by design.
    obj = SimpleNamespace(
        name="sword", parent=_slot_empty(), parent_bone="", vertex_groups=[]
    )
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
    # A slot swap is authored as attachment ``hide_render`` visibility keys
    # (spec 079); those are not bone transforms, so the check must skip them.
    child = _child_with_action(_action_with_path('["hide_render"]', layered=True))
    assert _has_bone_transform_keys(child) is False


def test_duplicate_slot_name_errors() -> None:
    def slot(name: str) -> SimpleNamespace:
        return _Obj(
            name=name,
            type="EMPTY",
            parent_type="OBJECT",
            proscenio=SimpleNamespace(is_slot=True, slot_default=""),
            children=[SimpleNamespace(name=f"{name}.mesh", type="MESH")],
        )

    assert _has(
        _validate_slots([slot("brow"), slot("brow")]), "error", "duplicate slot name"
    )


def _vec3(x: float, y: float, z: float) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, z=z)


def _rest_bone(
    name: str, head: tuple[float, float, float], tail: tuple[float, float, float]
):
    return SimpleNamespace(name=name, head_local=_vec3(*head), tail_local=_vec3(*tail))


def _armature_with_rest_bones(*bones: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(type="ARMATURE", data=SimpleNamespace(bones=list(bones)))


def _mesh_obj_with_verts(
    name: str, coords: list[tuple[float, float, float]]
) -> SimpleNamespace:
    verts = [SimpleNamespace(co=_vec3(*c)) for c in coords]
    return SimpleNamespace(name=name, data=SimpleNamespace(vertices=verts))


def test_bone_tilted_out_of_the_xz_plane_warns() -> None:
    # Head->tail runs diagonally into the screen (Y), which the XZ projection
    # cannot represent.
    arm = _armature_with_rest_bones(
        _rest_bone("tilt", (0.0, 0.0, 0.0), (1.0, 1.0, 0.0))
    )
    assert _has(_validate_bone_orientation(arm), "warning", "XZ plane")


def test_bone_in_the_xz_plane_is_clean() -> None:
    arm = _armature_with_rest_bones(
        _rest_bone("flat", (0.0, 0.0, 0.0), (1.0, 0.0, 1.0))
    )
    assert _validate_bone_orientation(arm) == []


def test_bone_orientation_skips_a_zero_length_bone() -> None:
    arm = _armature_with_rest_bones(
        _rest_bone("point", (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
    )
    assert _validate_bone_orientation(arm) == []


def test_mesh_with_depth_warns() -> None:
    # One vertex lifted off the picture plane along the dropped depth axis.
    obj = _mesh_obj_with_verts(
        "box", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 1.0)]
    )
    assert _has(_validate_mesh_flatness(obj), "warning", "not flat")


def test_flat_mesh_is_clean() -> None:
    obj = _mesh_obj_with_verts(
        "quad", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
    )
    assert _validate_mesh_flatness(obj) == []


def test_flat_mesh_authored_in_xz_is_clean() -> None:
    # A quad authored directly in world XZ has Y as its flat axis; a fixed
    # Z-is-depth test would false-warn it. Frame-independent flatness clears it.
    obj = _mesh_obj_with_verts(
        "panel", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)]
    )
    assert _validate_mesh_flatness(obj) == []


def test_full_pass_surfaces_a_tilted_bone_as_a_warning() -> None:
    arm = _armature_with_rest_bones(
        _rest_bone("spine", (0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    )
    scene = SimpleNamespace(
        objects=[arm], proscenio=SimpleNamespace(active_armature=arm)
    )
    assert _has(validate_export(scene), "warning", "XZ plane")


def test_atlas_missing_file_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "bpy", None)
    node = SimpleNamespace(
        type="TEX_IMAGE", image=SimpleNamespace(filepath="missing_atlas_zzz.png")
    )
    material = SimpleNamespace(use_nodes=True, node_tree=SimpleNamespace(nodes=[node]))
    obj = SimpleNamespace(
        name="torso", material_slots=[SimpleNamespace(material=material)]
    )
    assert _has(_validate_atlas_files([obj]), "warning", "not found on disk")


# --- IK bake gate -------------------------------------------------------------


def _ik_constraint(
    subtarget: str,
    target: object,
    *,
    chain_count: int = 2,
    influence: float = 1.0,
    mute: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        type="IK",
        subtarget=subtarget,
        target=target,
        chain_count=chain_count,
        influence=influence,
        mute=mute,
    )


def _ik_pose_bone(
    name: str, *, parent: object = None, constraints: tuple = ()
) -> SimpleNamespace:
    return SimpleNamespace(name=name, parent=parent, constraints=list(constraints))


def _ik_armature(pose_bones: list, *keyed_paths: str) -> SimpleNamespace:
    action = SimpleNamespace(
        fcurves=[SimpleNamespace(data_path=p) for p in keyed_paths]
    )
    return SimpleNamespace(
        type="ARMATURE",
        pose=SimpleNamespace(bones=list(pose_bones)),
        animation_data=SimpleNamespace(action=action),
        data=SimpleNamespace(
            bones=[SimpleNamespace(name=pb.name) for pb in pose_bones]
        ),
    )


def test_ik_chain_with_animated_target_but_unkeyed_bones_errors() -> None:
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature([thigh, shin], 'pose.bones["foot_ik"].location')
    shin.constraints = [_ik_constraint("foot_ik", target=arm, chain_count=2)]
    issues = _validate_ik_bake(arm)
    assert _has(issues, "error", "Bake IK")
    assert any(i.obj_name == "shin" for i in issues), "error should name the chain tip"


def test_ik_chain_baked_to_keyframes_passes() -> None:
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature(
        [thigh, shin],
        'pose.bones["foot_ik"].location',
        'pose.bones["shin"].rotation_quaternion',
    )
    shin.constraints = [_ik_constraint("foot_ik", target=arm, chain_count=2)]
    assert _validate_ik_bake(arm) == []


# --- bone-follow health (spec 080 D7/D8): double-drive + stale inverse ---


def _identity4() -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _follow_armature(bone: str = "arm") -> SimpleNamespace:
    return SimpleNamespace(
        name="rig",
        matrix_world=_identity4(),
        data=SimpleNamespace(bones=[SimpleNamespace(name=bone, matrix_local=_identity4())]),
    )


def _follower(
    *,
    inverse: list[list[float]] | None = None,
    subtarget: str = "arm",
    armature: SimpleNamespace | None = None,
    parent_bone: str = "",
) -> SimpleNamespace:
    armature = armature if armature is not None else _follow_armature()
    con = SimpleNamespace(
        name="Proscenio Slot Follow",
        type="CHILD_OF",
        subtarget=subtarget,
        target=armature,
        inverse_matrix=inverse if inverse is not None else _identity4(),
    )
    return SimpleNamespace(
        name="hand.slot",
        constraints=[con],
        parent_type="BONE" if parent_bone else "OBJECT",
        parent_bone=parent_bone,
    )


def test_bone_follow_healthy_binding_passes() -> None:
    # Identity rest x identity inverse: the stored inverse still cancels.
    assert _validate_bone_follow([_follower()]) == []


def test_bone_follow_double_drive_warns() -> None:
    issues = _validate_bone_follow([_follower(parent_bone="arm")])
    assert _has(issues, "warning", "double-driven")


def test_bone_follow_stale_inverse_warns() -> None:
    # The stored inverse carries a translation the current rest does not
    # cancel: the rig's rest changed since the bind.
    stale = _identity4()
    stale[0][3] = 5.0
    issues = _validate_bone_follow([_follower(inverse=stale)])
    assert _has(issues, "warning", "stale follow")


def test_bone_follow_missing_bone_warns() -> None:
    issues = _validate_bone_follow([_follower(subtarget="ghost")])
    assert _has(issues, "warning", "no longer exists")


def test_bone_follow_ignores_unbound_objects() -> None:
    plain = SimpleNamespace(name="torso", constraints=[], parent_type="OBJECT", parent_bone="")
    assert _validate_bone_follow([plain]) == []


def test_ik_gate_ignores_a_muted_constraint() -> None:
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature([thigh, shin], 'pose.bones["foot_ik"].location')
    shin.constraints = [_ik_constraint("foot_ik", target=arm, chain_count=2, mute=True)]
    assert _validate_ik_bake(arm) == []


def test_ik_gate_ignores_a_zero_influence_constraint() -> None:
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature([thigh, shin], 'pose.bones["foot_ik"].location')
    shin.constraints = [
        _ik_constraint("foot_ik", target=arm, chain_count=2, influence=0.0)
    ]
    assert _validate_ik_bake(arm) == []


def test_ik_gate_skips_a_targetless_constraint() -> None:
    # A targetless IK has nothing animating it; nothing to bake, no false error.
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature([thigh, shin])
    shin.constraints = [_ik_constraint("", target=None, chain_count=2)]
    assert _validate_ik_bake(arm) == []


def test_ik_gate_clean_when_no_action() -> None:
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    shin.constraints = [_ik_constraint("foot_ik", target=None, chain_count=2)]
    arm = SimpleNamespace(
        type="ARMATURE",
        pose=SimpleNamespace(bones=[thigh, shin]),
        animation_data=None,
    )
    assert _validate_ik_bake(arm) == []


def test_ik_chain_count_zero_walks_to_the_root() -> None:
    # chain_count 0 = whole parent chain; the unkeyed root must still be caught.
    root = _ik_pose_bone("root")
    thigh = _ik_pose_bone("thigh", parent=root)
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature([root, thigh, shin], 'pose.bones["foot_ik"].location')
    shin.constraints = [_ik_constraint("foot_ik", target=arm, chain_count=0)]
    assert _has(_validate_ik_bake(arm), "error", "Bake IK")


def test_full_pass_flags_an_unbaked_ik_chain() -> None:
    thigh = _ik_pose_bone("thigh")
    shin = _ik_pose_bone("shin", parent=thigh)
    arm = _ik_armature([thigh, shin], 'pose.bones["foot_ik"].location')
    shin.constraints = [_ik_constraint("foot_ik", target=arm, chain_count=2)]
    scene = SimpleNamespace(
        objects=[arm], proscenio=SimpleNamespace(active_armature=arm)
    )
    assert _has(validate_export(scene), "error", "Bake IK")


# --- driven-bone rotation mode ------------------------------------------------


def _rot_armature(name: str, **bone_modes: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="ARMATURE",
        pose=SimpleNamespace(
            bones=[
                SimpleNamespace(name=n, rotation_mode=m) for n, m in bone_modes.items()
            ]
        ),
    )


def _driven_sprite(
    name: str,
    *,
    armature: SimpleNamespace,
    bone_target: str,
    transform_type: str = "ROT_Y",
    data_path: str = '["proscenio_region_x"]',
) -> SimpleNamespace:
    target = SimpleNamespace(
        id=armature, bone_target=bone_target, transform_type=transform_type
    )
    driver = SimpleNamespace(variables=[SimpleNamespace(targets=[target])])
    fcurve = SimpleNamespace(data_path=data_path, driver=driver)
    return SimpleNamespace(
        name=name,
        type="MESH",
        animation_data=SimpleNamespace(drivers=[fcurve]),
    )


def test_driver_rotation_mode_warns_on_a_quaternion_driven_bone() -> None:
    arm = _rot_armature("Rig", arm_bone="QUATERNION")
    sprite = _driven_sprite("flap", armature=arm, bone_target="arm_bone")
    assert _has(_validate_driver_rotation_modes([sprite]), "warning", "not XYZ Euler")


def test_driver_rotation_mode_clean_on_an_xyz_driven_bone() -> None:
    arm = _rot_armature("Rig", arm_bone="XYZ")
    sprite = _driven_sprite("flap", armature=arm, bone_target="arm_bone")
    assert _validate_driver_rotation_modes([sprite]) == []


def test_driver_rotation_mode_ignores_a_non_rotation_channel() -> None:
    # A location-driven sprite does not read rotation, so the bone's mode is moot.
    arm = _rot_armature("Rig", arm_bone="QUATERNION")
    sprite = _driven_sprite(
        "flap", armature=arm, bone_target="arm_bone", transform_type="LOC_X"
    )
    assert _validate_driver_rotation_modes([sprite]) == []


def test_driver_rotation_mode_ignores_a_non_proscenio_driver() -> None:
    # A driver on some other property is none of this validator's business.
    arm = _rot_armature("Rig", arm_bone="QUATERNION")
    sprite = _driven_sprite(
        "flap", armature=arm, bone_target="arm_bone", data_path="location"
    )
    assert _validate_driver_rotation_modes([sprite]) == []


def test_full_pass_surfaces_a_quaternion_driven_bone_as_a_warning() -> None:
    arm = _rot_armature("Rig", arm_bone="QUATERNION")
    sprite = _driven_sprite("flap", armature=arm, bone_target="arm_bone")
    scene = SimpleNamespace(
        objects=[arm, sprite], proscenio=SimpleNamespace(active_armature=arm)
    )
    assert _has(validate_export(scene), "warning", "not XYZ Euler")
