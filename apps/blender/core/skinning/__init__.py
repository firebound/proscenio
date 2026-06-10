"""Pure-Python skinning algorithms (the weight-paint productivity follow-up).

Public surface: weight computation, mode dispatcher, diagnoses,
sidecar schema. Zero bpy import - testable without Blender.
"""

from .._shared.geometry_2d import Point2D
from .bind_diagnosis import (
    BindDiagnosis,
    DiagnosisKind,
    Severity,
    diagnose_bones_outside_bbox,
    diagnose_flipped_normals,
    diagnose_isolated_islands,
    diagnose_overlapping_verts,
    diagnose_scale,
)
from .planar_proximity import (
    BoneSegmentNamed2D,
    compute_proximity_weights,
)
from .sidecar_schema import (
    SIDECAR_VERSION,
    WeightSidecar,
    build_minimal_stub,
    compute_topology_hash,
    from_json,
    to_json,
)
from .skinning_modes import BindMode, bind_weights_for_mode

__all__ = [
    "SIDECAR_VERSION",
    "BindDiagnosis",
    "BindMode",
    "BoneSegmentNamed2D",
    "DiagnosisKind",
    "Point2D",
    "Severity",
    "WeightSidecar",
    "bind_weights_for_mode",
    "build_minimal_stub",
    "compute_proximity_weights",
    "compute_topology_hash",
    "diagnose_bones_outside_bbox",
    "diagnose_flipped_normals",
    "diagnose_isolated_islands",
    "diagnose_overlapping_verts",
    "diagnose_scale",
    "from_json",
    "to_json",
]
