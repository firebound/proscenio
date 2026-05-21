"""bpy-bound skinning helpers (SPEC 013.2)."""

from .automesh_hook import maybe_post_regen_reproject, maybe_pre_regen_snapshot
from .bind_apply import apply_bind
from .diagnose_collect import collect_diagnoses_for_object
from .sidecar_io import apply_sidecar, per_vert_uv_anchors, snapshot_sidecar

__all__ = [
    "apply_bind",
    "apply_sidecar",
    "collect_diagnoses_for_object",
    "maybe_post_regen_reproject",
    "maybe_pre_regen_snapshot",
    "per_vert_uv_anchors",
    "snapshot_sidecar",
]
