"""Apply bind weights to a bpy mesh + stamp the populated WeightSidecar.

Wipes every vertex group EXCEPT ``proscenio_base_sprite`` (D3 UV
anchor must survive), recreates one group per deform bone, then
populates per-vert weights from the chosen ``BindMode``. After
weights succeed, builds a populated ``WeightSidecar`` via
``snapshot_sidecar`` and stamps it onto
``obj["proscenio_weight_sidecar"]`` tagged ``provenance="auto_seed"``.
"""

from __future__ import annotations

import contextlib

import bpy

from ...skinning.planar_proximity import BoneSegmentNamed2D
from ...skinning.sidecar_schema import to_json
from ...skinning.skinning_modes import BindMode, bind_weights_for_mode
from ._helpers import wipe_non_base_groups
from .sidecar_io import snapshot_sidecar

_SIDECAR_KEY = "proscenio_weight_sidecar"
_ENVELOPE_RADIUS_KEY = "proscenio_envelope_radius"
_ENVELOPE_DEFAULT_RADIUS = 1.0
_ORPHAN_EPS = 1e-6
_ADAPTIVE_MAX_FACTOR = 1.5


def _bone_segments_xz(
    armature: bpy.types.Object,
) -> list[BoneSegmentNamed2D]:
    """Project deform bones to XZ world-space (matches sprite plane)."""
    matrix_world = armature.matrix_world
    segments: list[BoneSegmentNamed2D] = []
    for bone in armature.data.bones:
        if not bone.use_deform:
            continue
        head = matrix_world @ bone.head_local
        tail = matrix_world @ bone.tail_local
        segments.append(((head.x, head.z), (tail.x, tail.z), bone.name))
    return segments


def _adaptive_max_distance(armature: bpy.types.Object) -> float:
    """1.5 * max extent of the armature's deform-bone world-space bbox.

    Only deform bones count - control bones (IK targets, helpers) can sit
    far from the mesh and would inflate the extent past anything useful
    to a proximity bind.
    """
    matrix_world = armature.matrix_world
    deform_bones = [b for b in armature.data.bones if b.use_deform]
    if not deform_bones:
        return 1.0
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for bone in deform_bones:
        for point in (matrix_world @ bone.head_local, matrix_world @ bone.tail_local):
            xs.append(point.x)
            ys.append(point.y)
            zs.append(point.z)
    extent = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    return _ADAPTIVE_MAX_FACTOR * extent if extent > 0.0 else 1.0


def _collect_envelope_radii(armature: bpy.types.Object) -> dict[str, float]:
    """Read per-bone ``proscenio_envelope_radius`` Custom Property.

    Missing keys default to ``_ENVELOPE_DEFAULT_RADIUS`` (1.0).
    Edit Weights modal (Wave 13.2-paint) becomes the UI surface
    for these radii; bind alone exposes them via the manual
    Custom Property editor.
    """
    radii: dict[str, float] = {}
    for bone in armature.data.bones:
        if not bone.use_deform:
            continue
        radii[bone.name] = float(bone.get(_ENVELOPE_RADIUS_KEY, _ENVELOPE_DEFAULT_RADIUS))
    return radii


def apply_bind(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    mode: BindMode,
    *,
    falloff_power: float = 2.0,
    max_distance: float = -1.0,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, int]:
    """Bind ``obj`` to ``armature`` weights. Returns counters dict.

    Counters: ``verts_bound`` (total verts), ``orphan_verts``
    (sum-of-weights < eps), ``groups_created``, ``bones_used``,
    ``groups_wiped``. BONE_HEAT dispatches to ``_apply_bone_heat``
    which delegates to Blender's parent_set ARMATURE_AUTO; other
    modes use the planar proximity / envelope / single-nearest /
    empty algorithms.
    """
    if mode == "BONE_HEAT":
        return _apply_bone_heat(obj, armature)

    bone_segments = _bone_segments_xz(armature)
    effective_max = max_distance if max_distance >= 0.0 else _adaptive_max_distance(armature)
    effective_radii = (
        envelope_radii if envelope_radii is not None else _collect_envelope_radii(armature)
    )

    mesh = obj.data
    obj_world = obj.matrix_world
    vert_positions_xz = [((obj_world @ v.co).x, (obj_world @ v.co).z) for v in mesh.vertices]

    weights = bind_weights_for_mode(
        mode,
        vert_positions_xz,
        bone_segments,
        falloff_power=falloff_power,
        max_distance=effective_max if mode == "PROXIMITY" else None,
        envelope_radii=effective_radii,
    )
    # weights is guaranteed non-None here because BONE_HEAT is handled above
    assert weights is not None

    if _SIDECAR_KEY in obj:
        del obj[_SIDECAR_KEY]
    groups_wiped = wipe_non_base_groups(obj)
    for bone_name in weights:
        obj.vertex_groups.new(name=bone_name)
    for bone_name, per_vert_weights in weights.items():
        group = obj.vertex_groups[bone_name]
        for vert_idx, weight in enumerate(per_vert_weights):
            if weight > 0.0:
                group.add([vert_idx], weight, "REPLACE")

    orphan_verts = 0
    for vert_idx in range(len(mesh.vertices)):
        total = sum(weights[name][vert_idx] for name in weights)
        if total < _ORPHAN_EPS:
            orphan_verts += 1

    sidecar = snapshot_sidecar(obj, armature, provenance="auto_seed")
    obj[_SIDECAR_KEY] = to_json(sidecar)

    return {
        "verts_bound": len(mesh.vertices),
        "orphan_verts": orphan_verts,
        "groups_created": len(weights),
        "bones_used": len(bone_segments),
        "groups_wiped": groups_wiped,
    }


def _apply_bone_heat(obj: bpy.types.Object, armature: bpy.types.Object) -> dict[str, int]:
    """Delegate weight computation to Blender's parent_set ARMATURE_AUTO.

    Wipes any prior sidecar BEFORE the bpy.ops call (atomicity per
    fix(spec-013.2)); stamps a populated WeightSidecar via
    ``snapshot_sidecar`` (provenance="auto_seed") AFTER on success.
    Failure raises RuntimeError upward - operator surfaces a hint
    about trying PROXIMITY as fallback.
    """
    if _SIDECAR_KEY in obj:
        del obj[_SIDECAR_KEY]
    groups_wiped = wipe_non_base_groups(obj)

    deform_bone_names = [b.name for b in armature.data.bones if b.use_deform]
    prior_active = bpy.context.view_layer.objects.active
    prior_selected = list(bpy.context.selected_objects)
    try:
        for other in prior_selected:
            other.select_set(False)
        obj.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    finally:
        # Restore the full selection state, not just the active object.
        # parent_set leaves obj + armature selected; user's pre-bind
        # selection should survive an in-or-out success/failure.
        obj.select_set(False)
        armature.select_set(False)
        for prior in prior_selected:
            # ReferenceError = object was removed mid-operation; skip silently.
            with contextlib.suppress(ReferenceError):
                prior.select_set(True)
        bpy.context.view_layer.objects.active = prior_active

    sidecar = snapshot_sidecar(obj, armature, provenance="auto_seed")
    obj[_SIDECAR_KEY] = to_json(sidecar)

    orphan_verts = _count_orphans(obj, deform_bone_names)
    return {
        "verts_bound": len(obj.data.vertices),
        "orphan_verts": orphan_verts,
        "groups_created": len(deform_bone_names),
        "bones_used": len(deform_bone_names),
        "groups_wiped": groups_wiped,
    }


def _count_orphans(obj: bpy.types.Object, bone_names: list[str]) -> int:
    """Count verts whose total weight across bone groups is below eps.

    Blender's bone heat may leave verts unweighted when the bone
    geometry doesn't reach them. Surface them so the operator can
    WARN the user.
    """
    bone_groups = {
        obj.vertex_groups[name].index for name in bone_names if name in obj.vertex_groups
    }
    orphans = 0
    for vert in obj.data.vertices:
        total = sum(g.weight for g in vert.groups if g.group in bone_groups)
        if total < _ORPHAN_EPS:
            orphans += 1
    return orphans
