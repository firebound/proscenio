"""Pure tests for bind diagnoses (SPEC 013.2 bind, D11)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.bind_diagnosis import (  # noqa: E402
    BindDiagnosis,
    diagnose_bones_outside_bbox,
    diagnose_flipped_normals,
    diagnose_isolated_islands,
    diagnose_overlapping_verts,
    diagnose_scale,
)


def test_diagnose_scale_clean_returns_none():
    assert diagnose_scale((1.0, 1.0, 1.0)) is None


def test_diagnose_scale_unapplied_returns_error():
    d = diagnose_scale((2.0, 2.0, 2.0))
    assert isinstance(d, BindDiagnosis)
    assert d.kind == "scale"
    assert d.severity == "error"
    assert "Ctrl+A" in d.hint


def test_diagnose_scale_within_eps_passes():
    assert diagnose_scale((1.00005, 0.99995, 1.0)) is None


def test_diagnose_normals_all_facing_camera_returns_none():
    # Proscenio convention: -Y = facing camera (Front Ortho). Correct state.
    assert diagnose_flipped_normals([(0.0, -1.0, 0.0), (0.0, -1.0, 0.0)]) is None


def test_diagnose_normals_any_back_facing_returns_error():
    # Mixed: one good (-Y), one bad (+Y). Operator must abort.
    d = diagnose_flipped_normals([(0.0, -1.0, 0.0), (0.0, 1.0, 0.0)])
    assert d is not None
    assert d.kind == "normals"
    assert d.severity == "error"
    assert "1/2" in d.message


def test_diagnose_overlap_no_pairs_returns_none():
    assert diagnose_overlapping_verts([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]) is None


def test_diagnose_overlap_pair_within_eps_returns_warn():
    d = diagnose_overlapping_verts([(0.0, 0.0, 0.0), (1e-6, 0.0, 0.0)])
    assert d is not None
    assert d.kind == "overlap"
    assert d.severity == "warn"


def test_diagnose_islands_single_island_returns_none():
    assert diagnose_isolated_islands([[0, 1, 2]], vert_count=3) is None


def test_diagnose_islands_two_islands_returns_warn():
    d = diagnose_isolated_islands([[0, 1, 2], [3, 4, 5]], vert_count=6)
    assert d is not None
    assert d.kind == "islands"
    assert d.severity == "warn"


def test_diagnose_bone_bbox_all_inside_returns_none():
    mesh_bbox = ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
    bones = [((0.0, 0.0, 0.0), (0.5, 0.5, 0.0), "A")]
    assert diagnose_bones_outside_bbox(mesh_bbox, bones) is None


def test_diagnose_bone_bbox_any_outside_returns_warn():
    mesh_bbox = ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
    bones = [((10.0, 0.0, 0.0), (11.0, 0.0, 0.0), "far")]
    d = diagnose_bones_outside_bbox(mesh_bbox, bones)
    assert d is not None
    assert d.kind == "bone_bbox"
    assert d.severity == "warn"
