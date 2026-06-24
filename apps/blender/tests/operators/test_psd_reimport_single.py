"""Headless tests for the per-Element (single-entry) PSD re-import (spec 067).

Runs INSIDE Blender via ``run_operator_tests.py``. Exercises
``importers.photoshop.reimport_element`` and the manifest-path stamp: a single
Element re-imports from one manifest entry honouring the spec 055 contract
(same-bounds keeps weights, changed-bounds reprojects), every sibling Element
is untouched, the whole-figure feet-anchor is skipped, and an unresolvable
layer is a warn-and-no-op.
"""

from __future__ import annotations

import json

import bpy
import pytest


def _png(tmp_path, name):
    png = tmp_path / f"{name}.png"
    img = bpy.data.images.new(f"{name}_probe", 4, 4)
    img.filepath_raw = str(png)
    img.file_format = "PNG"
    img.save()
    return png


def _two_layer_manifest(tmp_path, head_size=(20, 20), torso_size=(20, 20)):
    _png(tmp_path, "head")
    _png(tmp_path, "torso")
    manifest = {
        "format_version": 1,
        "doc": "two_layer.psd",
        "size": [128, 128],
        "pixels_per_unit": 100.0,
        "layers": [
            {
                "kind": "mesh",
                "name": "head",
                "path": "head.png",
                "position": [10, 10],
                "size": list(head_size),
                "z_order": 0,
            },
            {
                "kind": "mesh",
                "name": "torso",
                "path": "torso.png",
                "position": [10, 40],
                "size": list(torso_size),
                "z_order": 1,
            },
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _by_origin(meshes, layer_name):
    target = f"psd:{layer_name}"
    for obj in meshes:
        if obj.get("proscenio_import_origin") == target:
            return obj
    raise AssertionError(f"no mesh stamped from layer {layer_name!r}")


def _vert_weight(obj, group_name, idx):
    vg = obj.vertex_groups.get(group_name)
    if vg is None:
        return 0.0
    try:
        return vg.weight(idx)
    except RuntimeError:
        return 0.0


def test_import_stamps_manifest_source_path(automesh_fixture, tmp_path):
    # Every imported object remembers the absolute source manifest path so a
    # per-Element reimport resolves it without a picker.
    from proscenio.importers.photoshop import import_manifest  # type: ignore[import-not-found]

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    manifest_path = _two_layer_manifest(tmp_path)
    result = import_manifest(manifest_path)
    assert result.meshes
    for obj in result.meshes:
        assert obj.get("proscenio_import_manifest") == str(manifest_path)


def test_reimport_element_touches_only_target(automesh_fixture, tmp_path):
    # Re-importing one Element must not disturb a sibling's mesh / weights.
    from proscenio.importers.photoshop import (  # type: ignore[import-not-found]
        import_manifest,
        reimport_element,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    manifest_path = _two_layer_manifest(tmp_path)
    result = import_manifest(manifest_path)
    head = _by_origin(result.meshes, "head")
    torso = _by_origin(result.meshes, "torso")

    vg = torso.vertex_groups.new(name="arm")
    vg.add([0], 0.6, "REPLACE")
    torso_data = torso.data
    torso_vert_count = len(torso_data.vertices)

    out = reimport_element(head, manifest_path)
    assert out.status == "restamped"
    assert out.obj is head
    # Sibling untouched: same mesh datablock, same vert count, same weight.
    assert torso.data is torso_data
    assert len(torso.data.vertices) == torso_vert_count
    assert _vert_weight(torso, "arm", 0) == pytest.approx(0.6)


def test_reimport_element_same_bounds_keeps_weights(automesh_fixture, tmp_path):
    from proscenio.importers.photoshop import (  # type: ignore[import-not-found]
        import_manifest,
        reimport_element,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    manifest_path = _two_layer_manifest(tmp_path)
    result = import_manifest(manifest_path)
    head = _by_origin(result.meshes, "head")
    vg = head.vertex_groups.new(name="neck")
    vg.add([0], 0.8, "REPLACE")
    head_data = head.data

    out = reimport_element(head, manifest_path)
    assert out.status == "restamped"
    assert head.data is head_data, "same-bounds reimport rebuilt the mesh"
    assert _vert_weight(head, "neck", 0) == pytest.approx(0.8)


def test_reimport_element_changed_bounds_reprojects(automesh_fixture, tmp_path):
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
    from proscenio.importers.photoshop import (  # type: ignore[import-not-found]
        import_manifest,
        reimport_element,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    manifest_path = _two_layer_manifest(tmp_path)
    result = import_manifest(manifest_path)
    head = _by_origin(result.meshes, "head")

    anchors = per_vert_uv_anchors(head)
    assert anchors is not None
    topology_hash = compute_topology_hash(
        len(head.data.vertices),
        [list(p.vertices) for p in head.data.polygons],
    )
    sidecar = WeightSidecar(
        version=SIDECAR_VERSION,
        vertex_group_names=["neck"],
        mesh_topology_hash=topology_hash,
        entries=[
            SidecarEntry(uv_anchor=a, weights={"neck": 1.0}, provenance="user_paint")
            for a in anchors
        ],
    )
    head["proscenio_weight_sidecar"] = to_json(sidecar)

    # Grow the head layer's bounds in the manifest, then reimport just it.
    bigger = _two_layer_manifest(tmp_path, head_size=(40, 50))
    out = reimport_element(head, bigger)
    assert out.status == "restamped"
    assert "neck" in head.vertex_groups, "reproject did not recreate the weight group"
    reprojected = any(_vert_weight(head, "neck", v.index) > 1e-6 for v in head.data.vertices)
    assert reprojected, "weights were wiped, not reprojected"


def test_reimport_element_missing_layer_is_noop(automesh_fixture, tmp_path):
    # A layer renamed / removed in the PSD leaves the Element intact.
    from proscenio.importers.photoshop import (  # type: ignore[import-not-found]
        import_manifest,
        reimport_element,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    manifest_path = _two_layer_manifest(tmp_path)
    result = import_manifest(manifest_path)
    head = _by_origin(result.meshes, "head")
    head_data = head.data
    vg = head.vertex_groups.new(name="neck")
    vg.add([0], 0.9, "REPLACE")

    # A manifest where the head layer is gone (renamed in the PSD).
    _png(tmp_path, "cranium")
    renamed = {
        "format_version": 1,
        "doc": "two_layer.psd",
        "size": [128, 128],
        "pixels_per_unit": 100.0,
        "layers": [
            {
                "kind": "mesh",
                "name": "cranium",
                "path": "cranium.png",
                "position": [10, 10],
                "size": [20, 20],
                "z_order": 0,
            }
        ],
    }
    renamed_path = tmp_path / "renamed.json"
    renamed_path.write_text(json.dumps(renamed), encoding="utf-8")

    out = reimport_element(head, renamed_path)
    assert out.status == "missing"
    assert out.warning is not None
    assert head.data is head_data, "no-op reimport mutated the Element mesh"
    assert _vert_weight(head, "neck", 0) == pytest.approx(0.9)


def test_reimport_element_does_not_re_anchor_siblings(automesh_fixture, tmp_path):
    # The single-Element path skips the whole-figure feet anchor: a sibling's Z
    # must not move when only the other Element is reimported.
    from proscenio.importers.photoshop import (  # type: ignore[import-not-found]
        import_manifest,
        reimport_element,
    )

    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    manifest_path = _two_layer_manifest(tmp_path)
    result = import_manifest(manifest_path)
    head = _by_origin(result.meshes, "head")
    torso = _by_origin(result.meshes, "torso")
    torso_z = torso.location.z

    # Reimport the head with grown bounds (would change the figure's lowest
    # point, hence re-anchor every mesh, if the single path anchored).
    bigger = _two_layer_manifest(tmp_path, head_size=(20, 80))
    reimport_element(head, bigger)
    assert torso.location.z == pytest.approx(torso_z), "single reimport re-anchored a sibling"
