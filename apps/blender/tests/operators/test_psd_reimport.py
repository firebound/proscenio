"""Headless tests for weight-preserving PSD re-import.

Runs INSIDE Blender via ``run_operator_tests.py``. Exercises ``_ensure_mesh``
directly (no manifest fixture needed): an unchanged-placement re-import is an
art retouch that keeps the mesh and its painted weights; a changed-placement
re-import rebuilds the quad but reprojects the painted weights from the
surviving ``proscenio_weight_sidecar`` Custom Property rather than wiping them.
"""

from __future__ import annotations

import bpy
import pytest


def _vert_weight(obj: bpy.types.Object, group_name: str, idx: int) -> float:
    vg = obj.vertex_groups.get(group_name)
    if vg is None:
        return 0.0
    try:
        return vg.weight(idx)
    except RuntimeError:
        return 0.0


def test_reimport_unchanged_bounds_keeps_painted_weights(automesh_fixture):
    from proscenio.importers.photoshop.planes import _ensure_mesh  # type: ignore[import-not-found]

    obj = _ensure_mesh("retouch_layer", (2.0, 3.0), (0.0, 0.0))
    vg = obj.vertex_groups.new(name="arm")
    vg.add([0], 0.7, "REPLACE")
    assert _vert_weight(obj, "arm", 0) == pytest.approx(0.7)

    # Re-import with identical bounds: art retouch, no rebuild.
    obj2 = _ensure_mesh("retouch_layer", (2.0, 3.0), (0.0, 0.0))
    assert obj2 is obj
    assert _vert_weight(obj, "arm", 0) == pytest.approx(0.7), "short-circuit rebuilt the mesh"


def test_reimport_changed_bounds_reprojects_weights_not_wiped(automesh_fixture):
    from proscenio.core.bpy_helpers.skinning import (  # type: ignore[import-not-found]
        per_vert_uv_anchors,
    )
    from proscenio.core.skinning.sidecar_schema import (  # type: ignore[import-not-found]
        SIDECAR_VERSION,
        SidecarEntry,
        WeightSidecar,
        compute_topology_hash,
        to_json,
    )
    from proscenio.importers.photoshop.planes import _ensure_mesh  # type: ignore[import-not-found]

    obj = _ensure_mesh("resize_layer", (2.0, 3.0), (0.0, 0.0))
    anchors = per_vert_uv_anchors(obj)
    assert anchors is not None
    topology_hash = compute_topology_hash(
        len(obj.data.vertices),
        [list(p.vertices) for p in obj.data.polygons],
    )
    sidecar = WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=["arm"],
        mesh_topology_hash=topology_hash,
        entries=[
            SidecarEntry(uv_anchor=a, weights={"arm": 1.0}, provenance="user_paint")
            for a in anchors
        ],
    )
    obj["proscenio_weight_sidecar"] = to_json(sidecar)

    # Re-import with changed bounds: rebuild + reproject, not wipe.
    obj2 = _ensure_mesh("resize_layer", (4.0, 5.0), (0.0, 0.0))
    assert obj2 is obj
    assert "arm" in obj.vertex_groups, "reproject did not recreate the weight group"
    reprojected = any(_vert_weight(obj, "arm", v.index) > 1e-6 for v in obj.data.vertices)
    assert reprojected, "weights were wiped, not reprojected"
    # New width 4 -> half-width 2: the quad's x extent is [-2, 2].
    xs = [v.co.x for v in obj.data.vertices]
    assert max(xs) == pytest.approx(2.0)
    assert min(xs) == pytest.approx(-2.0)


def test_reimport_changed_bounds_preserves_native_weights_without_sidecar(automesh_fixture):
    # A native Auto Weights bind writes live vertex groups but no sidecar; the
    # rebuild must snapshot those before the wipe instead of dropping them.
    from proscenio.importers.photoshop.planes import _ensure_mesh  # type: ignore[import-not-found]

    obj = _ensure_mesh("native_layer", (2.0, 3.0), (0.0, 0.0))
    vg = obj.vertex_groups.new(name="leg")
    for v in obj.data.vertices:
        vg.add([v.index], 0.5, "REPLACE")
    assert obj.get("proscenio_weight_sidecar") is None

    obj2 = _ensure_mesh("native_layer", (4.0, 5.0), (0.0, 0.0))
    assert obj2 is obj
    assert "leg" in obj.vertex_groups
    preserved = any(_vert_weight(obj, "leg", v.index) > 1e-6 for v in obj.data.vertices)
    assert preserved, "native weights dropped on resize re-import"
