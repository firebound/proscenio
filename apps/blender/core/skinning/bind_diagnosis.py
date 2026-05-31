"""Pre-flight diagnoses for the bind operator (the weight-paint productivity follow-up, D11).

Five structured checks that catch the most common bind failure
modes before the user wastes time on a bad bind. Errors abort
the operator; warnings continue with INFO reports.

Pure Python: every check receives primitive data (tuples, lists)
extracted by the bpy-bound caller. Zero bpy import here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

DiagnosisKind = Literal["scale", "normals", "overlap", "islands", "bone_bbox"]
Severity = Literal["error", "warn"]

Vec3 = tuple[float, float, float]
BBox = tuple[Vec3, Vec3]
"""(min_xyz, max_xyz) - axis-aligned bounding box."""
BoneSegment3D = tuple[Vec3, Vec3, str]
"""((head_xyz, tail_xyz, bone_name)) - 3D world-space bone segment."""

_SCALE_EPS = 1e-4
_OVERLAP_EPS = 1e-5
_NORMAL_FLIP_EPS = 0.0
"""Y component >= 0 counts as flipped on the picture plane.

Proscenio convention: sprites face the camera in Blender's Front Ortho
view (numpad 1, camera at -Y looking toward +Y). A sprite "facing the
camera" therefore has its face normal in the -Y direction (Y < 0).
Verified against ``automesh_from_sprite`` output: 100% of generated
faces land at Y == -1.0 post-CDT + recalc_face_normals."""


@dataclass(frozen=True)
class BindDiagnosis:
    """One pre-flight finding."""

    kind: DiagnosisKind
    severity: Severity
    message: str
    hint: str


def diagnose_scale(scale_xyz: Vec3) -> BindDiagnosis | None:
    """Error when any axis deviates from 1.0 by more than ``_SCALE_EPS``."""
    if all(abs(component - 1.0) <= _SCALE_EPS for component in scale_xyz):
        return None
    return BindDiagnosis(
        kind="scale",
        severity="error",
        message=f"mesh has unapplied scale {scale_xyz}",
        hint="press Ctrl+A then Scale to apply",
    )


def diagnose_flipped_normals(face_normals: list[Vec3]) -> BindDiagnosis | None:
    """Error when any face normal points away from the camera (Y >= 0).

    Proscenio sprites face the camera in Front Ortho = normal in -Y.
    Anything at Y >= 0 is back-facing, which on a 2D picture plane
    means the sprite is invisible to the user. See ``_NORMAL_FLIP_EPS``.
    """
    flipped = sum(1 for n in face_normals if n[1] >= _NORMAL_FLIP_EPS)
    if flipped == 0:
        return None
    return BindDiagnosis(
        kind="normals",
        severity="error",
        message=f"{flipped}/{len(face_normals)} face normals point away from camera",
        hint="select all + Mesh -> Normals -> Recalculate Outside (or Flip)",
    )


def diagnose_overlapping_verts(
    vert_positions: list[Vec3], eps: float = _OVERLAP_EPS
) -> BindDiagnosis | None:
    """Warn when any pair of verts sits within ``eps`` of each other.

    O(n^2) brute force - the bpy caller swaps in a KD-tree for
    large meshes before calling.
    """
    count = len(vert_positions)
    pairs = 0
    for i in range(count):
        ax, ay, az = vert_positions[i]
        for j in range(i + 1, count):
            bx, by, bz = vert_positions[j]
            if math.hypot(ax - bx, ay - by, az - bz) <= eps:
                pairs += 1
    if pairs == 0:
        return None
    return BindDiagnosis(
        kind="overlap",
        severity="warn",
        message=f"{pairs} overlapping vertex pair(s) within {eps}",
        hint="consider Mesh -> Clean Up -> Merge by Distance",
    )


def diagnose_isolated_islands(
    face_indices: list[list[int]], vert_count: int
) -> BindDiagnosis | None:
    """Warn when the mesh has more than one connected component.

    Union-find over vert indices: every face merges its members
    into one set. Component count = remaining distinct roots
    among verts that appear in any face.
    """
    parent = list(range(vert_count))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    used: set[int] = set()
    for face in face_indices:
        used.update(face)
        for i in range(1, len(face)):
            union(face[0], face[i])

    roots = {find(v) for v in used}
    if len(roots) <= 1:
        return None
    return BindDiagnosis(
        kind="islands",
        severity="warn",
        message=f"{len(roots)} isolated islands detected",
        hint="each island will be bound independently",
    )


def diagnose_bones_outside_bbox(
    mesh_bbox: BBox, bone_segments_world: list[BoneSegment3D]
) -> BindDiagnosis | None:
    """Warn when any bone's head or tail lies outside the mesh bbox."""
    (min_x, min_y, min_z), (max_x, max_y, max_z) = mesh_bbox
    outside = 0
    for head, tail, _name in bone_segments_world:
        for px, py, pz in (head, tail):
            if not (min_x <= px <= max_x and min_y <= py <= max_y and min_z <= pz <= max_z):
                outside += 1
                break
    if outside == 0:
        return None
    return BindDiagnosis(
        kind="bone_bbox",
        severity="warn",
        message=f"{outside}/{len(bone_segments_world)} bones outside mesh bbox",
        hint=(
            "those bones contribute zero weight - move armature into the mesh "
            "or shrink max_distance"
        ),
    )
