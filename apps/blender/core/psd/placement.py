"""PSD layer placement math (pure, bpy-free).

Translates a PSD layer's pixel bbox (plus an optional ``[origin]`` pivot and a
Spine-style anchor) into a Blender world location + quad size + the geometry
offset baked into the quad vertices. The Photoshop importer's ``planes`` module
is bpy-bound (it builds the mesh + material), so this coordinate math lives here
where the pure ``tests/psd`` suite exercises it without Blender.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class LayerPlacement:
    """Output of `layer_placement`: object world location plus the quad-vertex offset to bake."""

    location: tuple[float, float, float]
    size: tuple[float, float]
    # Geometry offset baked into the quad's local-space vertices so
    # the visible texture sits where the manifest says (`position +
    # size/2` in PSD pixels) even when the object's location was
    # shifted to an explicit `origin`. Zero when no origin is set.
    geometry_offset: tuple[float, float]


def origin_for_kind(
    layer_origin: Sequence[int] | None,
    element_type: str,
    layer_name: str,
) -> Sequence[int] | None:
    """Honour ``[origin]`` for sprites only; ignore (and warn about) one on a mesh.

    A Polygon2D has no pivot - the mesh exports in world / bone space, so an
    origin only shifts the Blender object pivot and cancels at export. Treating
    it as absent keeps the import placement at the bbox centre and surfaces the
    no-op rather than silently honouring a tag that does nothing downstream. A
    sprite keeps its origin: it becomes the Sprite2D offset.
    """
    if element_type == "mesh" and layer_origin is not None:
        print(
            f"[psd_import] mesh layer {layer_name!r} carries an [origin]; ignoring it "
            "(origin is sprite-only - it cancels at mesh export)"
        )
        return None
    return layer_origin


def layer_placement(
    position_px: Sequence[int],
    size_px: Sequence[int],
    doc_size_px: Sequence[int],
    pixels_per_unit: float,
    z_order: int,
    spacing: float,
    origin_px: Sequence[int] | None,
    anchor_px: Sequence[int] | None,
) -> LayerPlacement:
    """Translate PSD pixel coords + optional origin / anchor into Blender world placement.

    The Spine-style ``anchor`` (when set) becomes the world origin
    (0, 0, 0): every layer's PSD pixel position is re-zeroed against
    it. Without an anchor the importer falls back to canvas-centered
    placement.
    """
    px_x, px_y = position_px
    px_w, px_h = size_px
    doc_w, doc_h = doc_size_px
    if anchor_px is None:
        ref_x = doc_w / 2.0
        ref_y = doc_h / 2.0
    else:
        ref_x = float(anchor_px[0])
        ref_y = float(anchor_px[1])
    bbox_cx = (px_x + px_w / 2.0 - ref_x) / pixels_per_unit
    bbox_cz = (ref_y - px_y - px_h / 2.0) / pixels_per_unit
    cy = z_order * spacing
    sx = px_w / pixels_per_unit
    sz = px_h / pixels_per_unit
    if origin_px is None:
        return LayerPlacement(
            location=(bbox_cx, cy, bbox_cz),
            size=(sx, sz),
            geometry_offset=(0.0, 0.0),
        )
    origin_x, origin_y = origin_px
    ox = (origin_x - ref_x) / pixels_per_unit
    oz = (ref_y - origin_y) / pixels_per_unit
    return LayerPlacement(
        location=(ox, cy, oz),
        size=(sx, sz),
        geometry_offset=(bbox_cx - ox, bbox_cz - oz),
    )
