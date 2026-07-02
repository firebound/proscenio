"""Quad mesh reuse / rebuild for the Photoshop importer."""

from __future__ import annotations

import bpy

from ...core._shared.cp_keys import (
    PROSCENIO_IMPORT_ORIGIN,
    PROSCENIO_IMPORT_PLACEMENT,
    PROSCENIO_WEIGHT_SIDECAR,
)
from ...core.bpy_helpers._shared._bpy_compat import (
    expect_mesh,
    expect_scene,
    first_uv_layer,
    iter_blend_objects,
    uv_loop_at,
)
from ...core.bpy_helpers.skinning import reproject_stored_sidecar, snapshot_live_vgroups
from ...core.skinning.sidecar_schema import from_json, to_json


def _ensure_mesh(
    name: str,
    size: tuple[float, float],
    geometry_offset: tuple[float, float] = (0.0, 0.0),
) -> bpy.types.Object:
    """Reuse an existing mesh by ``proscenio_import_origin`` tag, else create.

    A re-import whose placement (size + geometry offset) is unchanged is an art
    retouch: the mesh is left fully intact, preserving any automesh
    densification and painted weights - only the caller's material refresh
    carries the new art. A changed placement rebuilds the quad and reprojects
    the painted weights (they live in the ``proscenio_weight_sidecar`` Custom
    Property, which survives the geometry wipe) onto the fresh quad by UV
    anchor. ``geometry_offset`` shifts the quad in local space so an object
    placed at a non-bbox-centre location still displays the texture at the
    bbox-centre world position.
    """
    obj = _find_existing(name)
    if obj is not None and _placement_unchanged(obj, size, geometry_offset):
        return obj
    rebuilt_existing = obj is not None
    if obj is not None:
        _snapshot_before_rebuild(obj)
    if obj is None:
        new_mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, new_mesh)
        expect_scene(bpy.context.scene).collection.objects.link(obj)
    _build_quad(obj, size, geometry_offset)
    obj[PROSCENIO_IMPORT_PLACEMENT] = [size[0], size[1], geometry_offset[0], geometry_offset[1]]
    if rebuilt_existing:
        reproject_stored_sidecar(obj)
    return obj


def _snapshot_before_rebuild(obj: bpy.types.Object) -> None:
    """Ensure a usable weight snapshot exists on obj before the geometry wipe.

    The stored sidecar survives the rebuild, so when it is present with entries
    nothing is needed. Otherwise - a native Auto Weights bind writes no sidecar,
    and a corrupt one is unusable - capture the live vertex-group weights now so
    the post-rebuild reproject restores them instead of dropping the mesh's only
    weights.
    """
    payload = obj.get(PROSCENIO_WEIGHT_SIDECAR)
    if payload is not None:
        try:
            if from_json(payload).entries:
                return
        except ValueError:
            # Corrupt stored sidecar - fall through to a live-weights snapshot.
            pass
    snapshot = snapshot_live_vgroups(obj)
    if snapshot is not None:
        obj[PROSCENIO_WEIGHT_SIDECAR] = to_json(snapshot)


def _build_quad(
    obj: bpy.types.Object,
    size: tuple[float, float],
    geometry_offset: tuple[float, float],
) -> None:
    """Clear the object's mesh and rebuild it as a single UV-mapped quad."""
    width, height = size
    ox, oz = geometry_offset
    mesh = expect_mesh(obj)
    mesh.clear_geometry()
    half_w = width / 2.0
    half_h = height / 2.0
    mesh.from_pydata(
        vertices=[
            (ox - half_w, 0.0, oz - half_h),
            (ox + half_w, 0.0, oz - half_h),
            (ox + half_w, 0.0, oz + half_h),
            (ox - half_w, 0.0, oz + half_h),
        ],
        edges=[],
        faces=[(0, 1, 2, 3)],
    )
    mesh.update()
    uv = first_uv_layer(mesh) or mesh.uv_layers.new(name="UVMap")
    uv_loop_at(uv, 0).uv = (0.0, 0.0)
    uv_loop_at(uv, 1).uv = (1.0, 0.0)
    uv_loop_at(uv, 2).uv = (1.0, 1.0)
    uv_loop_at(uv, 3).uv = (0.0, 1.0)


def _placement_unchanged(
    obj: bpy.types.Object,
    size: tuple[float, float],
    geometry_offset: tuple[float, float],
) -> bool:
    """True when obj's baked placement matches ``size`` + ``geometry_offset``.

    A missing or malformed stored placement reads as changed, so an object that
    predates the placement tag rebuilds once (and gains the tag).
    """
    stored = obj.get(PROSCENIO_IMPORT_PLACEMENT)
    if stored is None:
        return False
    want = (size[0], size[1], geometry_offset[0], geometry_offset[1])
    try:
        return all(abs(float(stored[i]) - want[i]) < 1e-6 for i in range(4))
    except (TypeError, IndexError, ValueError):
        return False


def _find_existing(name: str) -> bpy.types.Object | None:
    """Locate a mesh previously imported from the same PSD layer.

    Identifies via the ``proscenio_import_origin = "psd:<name>"`` custom
    property (mirrors the addon's PropertyGroup-or-fallback pattern).
    Falls back to name match so a freshly-authored mesh that already
    uses the layer's name is treated as the existing one.
    """
    target = f"psd:{name}"
    for obj in iter_blend_objects():
        if obj.type != "MESH":
            continue
        if obj.get(PROSCENIO_IMPORT_ORIGIN) == target:
            return obj
        if obj.name == name and obj.get(PROSCENIO_IMPORT_ORIGIN) is None:
            return obj
    return None
