"""Bpy-side IO for the atlas packer (SPEC 005.1.c.2 + 005.1.c.2.1 slicing).

Splits the bpy.types.Image plumbing out of the operator so the packer
algorithm itself stays pure (and testable). This module is **not**
imported by the pytest suite — it touches ``bpy.types.Image`` and
``numpy`` (Blender bundles numpy, but pip-only test environments do not).

Responsibilities:

- :func:`collect_source_images` — walk a list of mesh objects, return one
  ``SourceImage`` per object whose first material has an image-textured
  node. Each carries a ``slice_px`` rect derived from the mesh's UV bounds
  so the packer can extract just the relevant sub-region of the source
  image (covers both 1-sprite-per-PNG and shared-atlas workflows).
- :func:`compose_atlas` — given a :class:`PackResult` and the source
  image list, assemble a new ``bpy.types.Image`` containing only the
  sliced sub-regions and save it to disk.
- :func:`write_manifest` — JSON sidecar with the per-sprite rect plus
  the slice metadata the apply operator needs to rewrite UVs / regions.
- :func:`read_manifest` — inverse, used by the apply operator.

Idempotency contract. Pack and Apply are deterministic functions of the
current Blender scene state. Running them in any order multiple times
produces the same .blend / packed atlas as long as the underlying mesh
UVs and source images are the same:

- Pack(N times in a row): same .atlas.png + .atlas.json each run. The
  on-disk PNG is overwritten in place; the existing
  ``bpy.types.Image`` for the same name is removed and re-created. Source
  pixels are snapshotted into NumPy before the removal happens, so a
  source that *is* the existing packed atlas (true on second pack after
  apply) still gets read cleanly.
- Apply(N times in a row): UVs in slot coords are stable — second apply
  rewrites them to the same numbers. Materials are linked to the shared
  ``Proscenio.PackedAtlas`` (or left isolated per object).
- Pack → Apply → Pack → Apply: the slice extracted in the second pack
  comes from the already-packed atlas (slot interior) and ends up at the
  same slot coordinates because the packer is deterministic. UVs after
  the second apply land at the same positions. **Equivalent to Pack →
  Apply once.**

What the cycle is **not** is reversible across a session boundary —
once the .blend is saved post-apply, the original UVs and the original
material → image link are gone. SPEC 005.1.c.2.2 (Unpack operator) will
add a duplicated UV layer (``UVMap.pre_pack``) snapshot so the operation
becomes fully revertible. Until then, Ctrl+Z is the only revert path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .atlas_packer import PackResult, Rect
from .uv_bounds import uv_bbox_to_pixels


@dataclass(frozen=True)
class SourceImage:
    """One source slice to be repacked.

    ``image`` is the source ``bpy.types.Image`` (often shared between
    sprites). ``width`` / ``height`` are the source image dimensions.
    ``slice_px`` ``(x, y, w, h)`` is the sub-rect of the source image
    that this sprite actually uses, derived from its mesh UV bounds.
    """

    obj_name: str
    image: Any  # bpy.types.Image — Any here so the module imports without bpy
    width: int
    height: int
    slice_px: tuple[int, int, int, int]


def collect_source_images(objects: list[Any]) -> list[SourceImage]:
    """Walk ``objects`` and gather their first image-textured material.

    Each entry carries a ``slice_px`` rect derived from the mesh's UV
    bounds — for 1-sprite-per-PNG sources this covers the whole image;
    for shared-atlas sources it picks out just the sprite's sub-region.

    Objects with no image-textured material or no UV layer are silently
    skipped — the caller's validation pass should surface that as a
    warning.
    """
    out: list[SourceImage] = []
    for obj in objects:
        image = _find_first_image(obj)
        if image is None:
            continue
        w, h = image.size
        if w <= 0 or h <= 0:
            continue
        uvs = _collect_mesh_uvs(obj)
        slice_px = uv_bbox_to_pixels(uvs, int(w), int(h))
        out.append(
            SourceImage(
                obj_name=obj.name,
                image=image,
                width=int(w),
                height=int(h),
                slice_px=slice_px,
            )
        )
    return out


def _collect_mesh_uvs(obj: Any) -> list[tuple[float, float]]:
    """Flatten the active UV layer's loop coords into ``[(u, v), ...]``.

    Defensive against partially-initialized meshes — Blender 5.x can have a
    UV layer marker whose ``.data`` collection is empty (seen after the
    apply operator on certain shared-material objects), which previously
    crashed with ``IndexError`` on the second Pack Atlas run.
    """
    mesh = obj.data
    uv_layer = getattr(mesh, "uv_layers", None)
    if uv_layer is None:
        return []
    active = uv_layer.active
    if active is None or len(active.data) == 0:
        return []
    out: list[tuple[float, float]] = []
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            if li >= len(active.data):
                continue
            u, v = active.data[li].uv
            out.append((float(u), float(v)))
    return out


def _find_first_image(obj: Any) -> Any | None:
    """Return the first image bound to any material on ``obj``."""
    mesh = obj.data
    materials = getattr(mesh, "materials", None) or []
    for mat in materials:
        if mat is None or not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                return node.image
    return None


def compose_atlas(
    sources: list[SourceImage],
    packed: PackResult,
    out_path: Path,
    padding: int = 2,
) -> Any:
    """Build a single bpy.types.Image holding every packed source and save it.

    Pixels are RGBA float32. Padding pixels are left transparent (alpha=0)
    in this iteration — edge-extend padding to combat bilinear bleeding can
    be added later without changing the operator surface.

    Idempotency note. The function tolerates the case where ``src.image``
    is the same image we are about to overwrite (true on second pack runs
    after the first apply linked every sprite to the shared packed atlas).
    Source pixel arrays are copied into NumPy upfront — **before** the
    existing atlas image is removed from ``bpy.data.images`` — so the
    mid-loop ``StructRNA of type Image has been removed`` error cannot
    happen.

    Returns the new ``bpy.types.Image``.
    """
    import bpy  # local import — module must remain importable from non-bpy contexts
    import numpy as np

    # Snapshot every source's pixels into NumPy *before* mutating bpy.data.images.
    # If `src.image` is the existing atlas-with-the-same-name we are about to
    # remove, the snapshot detaches us from the bpy reference — Blender can
    # then free the StructRNA without us crashing later in the loop.
    placed_sources: list[tuple[SourceImage, Rect, np.ndarray]] = []
    for src in sources:
        rect: Rect | None = packed.placements.get(src.obj_name)
        if rect is None:
            continue
        try:
            pixels = np.array(src.image.pixels[:], dtype=np.float32).reshape(
                src.height, src.width, 4
            )
        except (ReferenceError, AttributeError):
            # Source image was already invalidated (e.g. an earlier pack run
            # in this session removed it). Skip — the caller's validation
            # path should surface this as a warning.
            continue
        placed_sources.append((src, rect, pixels))

    name = out_path.stem
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    atlas_img = bpy.data.images.new(
        name=name,
        width=packed.atlas_w,
        height=packed.atlas_h,
        alpha=True,
    )

    canvas = np.zeros((packed.atlas_h, packed.atlas_w, 4), dtype=np.float32)

    # Coordinate systems. The packer is internally top-down (y=0 means top of
    # the atlas, the bin-packing convention); ``bpy.types.Image.pixels`` is
    # bottom-up (row 0 = bottom of the image). UV-derived ``slice_px`` is
    # bottom-up because Blender mesh UVs use bottom-left origin. We slice the
    # source in bottom-up space, then convert the slot's top-down y to a
    # bottom-up canvas row before pasting.
    for src, rect, src_pixels in placed_sources:
        sx, sy_bu, sw, sh = src.slice_px
        sliced = src_pixels[sy_bu : sy_bu + sh, sx : sx + sw]
        # Defensive clamp in case the slice rect is slightly larger than the
        # placement (rounding from the packer's padding bookkeeping).
        h = min(rect.h, sliced.shape[0])
        w = min(rect.w, sliced.shape[1])
        slot_y_bu = packed.atlas_h - rect.y - rect.h
        canvas[slot_y_bu : slot_y_bu + h, rect.x : rect.x + w] = sliced[:h, :w]

    atlas_img.pixels.foreach_set(canvas.flatten().tolist())

    atlas_img.filepath_raw = str(out_path)
    atlas_img.file_format = "PNG"
    atlas_img.save()
    return atlas_img


def write_manifest(
    packed: PackResult,
    padding: int,
    sources: list[SourceImage],
    manifest_path: Path,
) -> None:
    """Persist the pack result + source slice metadata as JSON.

    ``format_version`` 2 adds ``source_w/h`` and ``slice_x/y/w/h`` per
    placement so ``apply_packed_atlas`` can rewrite UVs (polygon) and
    ``texture_region`` (sprite_frame) correctly when the source was a
    shared atlas (slice_px ≠ full image).
    """
    by_name = {src.obj_name: src for src in sources}
    placements_payload: dict[str, Any] = {}
    for name, r in packed.placements.items():
        src = by_name.get(name)
        entry: dict[str, Any] = {"x": r.x, "y": r.y, "w": r.w, "h": r.h}
        if src is not None:
            sx, sy, sw, sh = src.slice_px
            entry.update(
                {
                    "source_w": src.width,
                    "source_h": src.height,
                    "slice_x": sx,
                    "slice_y": sy,
                    "slice_w": sw,
                    "slice_h": sh,
                }
            )
        placements_payload[name] = entry
    payload: dict[str, Any] = {
        "format_version": 2,
        "atlas_w": packed.atlas_w,
        "atlas_h": packed.atlas_h,
        "padding": padding,
        "placements": placements_payload,
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


@dataclass(frozen=True)
class Placement:
    """Manifest entry: slot rect in atlas + slice rect in source image."""

    slot: Rect
    source_w: int
    source_h: int
    slice: Rect


def read_manifest(manifest_path: Path) -> tuple[int, int, int, dict[str, Placement]]:
    """Inverse of :func:`write_manifest`. Tolerates the v1 (no slice) format.

    Returns ``(atlas_w, atlas_h, padding, placements)``. Entries from v1
    manifests get ``slice == slot`` and ``source_w/h == slot.w/h`` so the
    apply operator's slice-aware code path stays correct.
    """
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    placements: dict[str, Placement] = {}
    for name, r in payload["placements"].items():
        slot = Rect(int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]))
        slice_rect = Rect(
            int(r.get("slice_x", 0)),
            int(r.get("slice_y", 0)),
            int(r.get("slice_w", slot.w)),
            int(r.get("slice_h", slot.h)),
        )
        placements[name] = Placement(
            slot=slot,
            source_w=int(r.get("source_w", slot.w)),
            source_h=int(r.get("source_h", slot.h)),
            slice=slice_rect,
        )
    return (
        int(payload["atlas_w"]),
        int(payload["atlas_h"]),
        int(payload.get("padding", 0)),
        placements,
    )
