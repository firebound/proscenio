"""Collect 5 pre-flight diagnoses from a bpy mesh + armature.

Extracts primitive data via bmesh / mathutils.kdtree, delegates
the actual checks to the pure ``core.skinning.bind_diagnosis``
helpers. Lives under ``core/bpy_helpers/skinning/`` per the
domain-package convention adopted in Wave 13.2 cleanup (PR #52).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bmesh
import bpy
from mathutils import Vector, kdtree

from ...skinning.bind_diagnosis import (
    BindDiagnosis,
    diagnose_bones_outside_bbox,
    diagnose_flipped_normals,
    diagnose_isolated_islands,
    diagnose_overlapping_verts,
    diagnose_scale,
)

if TYPE_CHECKING:
    from ...skinning.bind_diagnosis import BBox, BoneSegment3D, Vec3

_KDTREE_THRESHOLD = 256
"""Vert count above which the KD-tree overlap check beats O(n^2).

256 is a 16x16 grid - typical automesh downsampled-grid output already
crosses this. KD-tree is O(n log n) build + O(n log n) range query;
worth paying the constant overhead even at moderate mesh sizes."""

_KDTREE_RADIUS = 1e-5
"""Same epsilon as the pure overlap check (``_OVERLAP_EPS``)."""


def _collect_bone_segments_world(
    armature: bpy.types.Object,
) -> list[BoneSegment3D]:
    """3D world-space ((head, tail, name)) for every deform bone."""
    matrix_world = armature.matrix_world
    segments: list[BoneSegment3D] = []
    for bone in armature.data.bones:
        if not bone.use_deform:
            continue
        head = matrix_world @ bone.head_local
        tail = matrix_world @ bone.tail_local
        segments.append(((head.x, head.y, head.z), (tail.x, tail.y, tail.z), bone.name))
    return segments


def _mesh_world_bbox(obj: bpy.types.Object) -> BBox:
    """World-space AABB from obj.bound_box * matrix_world."""
    matrix_world = obj.matrix_world
    corners = [matrix_world @ Vector(corner) for corner in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def _overlap_pairs_kdtree(vert_positions: list[Vec3]) -> int:
    """KD-tree pair count for meshes above _KDTREE_THRESHOLD verts."""
    tree = kdtree.KDTree(len(vert_positions))
    for index, pos in enumerate(vert_positions):
        tree.insert(pos, index)
    tree.balance()
    seen: set[tuple[int, int]] = set()
    for index, pos in enumerate(vert_positions):
        for _co, other_index, _dist in tree.find_range(pos, _KDTREE_RADIUS):
            if other_index == index:
                continue
            key = (min(index, other_index), max(index, other_index))
            seen.add(key)
    return len(seen)


def _diagnose_overlap_with_kdtree(
    vert_positions: list[Vec3],
) -> BindDiagnosis | None:
    """Switch to KD-tree for large meshes; fall back to pure brute force."""
    if len(vert_positions) <= _KDTREE_THRESHOLD:
        return diagnose_overlapping_verts(vert_positions)
    pairs = _overlap_pairs_kdtree(vert_positions)
    if pairs == 0:
        return None
    return BindDiagnosis(
        kind="overlap",
        severity="warn",
        message=f"{pairs} overlapping vertex pair(s) within {_KDTREE_RADIUS}",
        hint="consider Mesh -> Clean Up -> Merge by Distance",
    )


def collect_diagnoses_for_object(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
) -> list[BindDiagnosis]:
    """Run all 5 pre-flight checks. Returns merged list in stable order."""
    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        face_normals = [(f.normal.x, f.normal.y, f.normal.z) for f in bm.faces]
        vert_positions = [(v.co.x, v.co.y, v.co.z) for v in bm.verts]
        face_indices = [[v.index for v in f.verts] for f in bm.faces]
    finally:
        bm.free()

    bones_world = _collect_bone_segments_world(armature)
    bbox = _mesh_world_bbox(obj)

    findings: list[BindDiagnosis] = []
    for check in (
        diagnose_scale((obj.scale[0], obj.scale[1], obj.scale[2])),
        diagnose_flipped_normals(face_normals),
        _diagnose_overlap_with_kdtree(vert_positions),
        diagnose_isolated_islands(face_indices, len(vert_positions)),
        diagnose_bones_outside_bbox(bbox, bones_world),
    ):
        if check is not None:
            findings.append(check)
    return findings
