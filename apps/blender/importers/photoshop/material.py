"""Flat unlit EEVEE material build for the Photoshop importer."""

from __future__ import annotations

import contextlib
from collections.abc import Iterable
from pathlib import Path
from typing import Literal, cast

import bpy

from ...core.bpy_helpers._shared._bpy_compat import (
    expect_mesh,
    iter_shader_nodes,
    material_by_name,
    node_input_at,
    node_input_by_name,
    node_output_by_name,
    set_material_at,
)

# EEVEE material.blend_method mapping for the photoshop tag system blend modes.
# Blender 4.2+ collapsed the alpha modes to {OPAQUE, CLIP, HASHED,
# BLEND} (the old "ADDITIVE" / "MULTIPLY" alpha modes were retired in
# favour of shader-node-based blending). Every non-opaque mode here
# routes through "BLEND"; the manifest-declared mode is stamped as a
# custom property so downstream writers (Godot) can emit the exact
# requested compositing operator.
_BLEND_METHOD_BY_MODE: dict[str, str] = {
    "normal": "BLEND",
    "multiply": "BLEND",
    "screen": "BLEND",
    "additive": "BLEND",
}


def _attach_material(
    obj: bpy.types.Object,
    image_path: Path,
    blend_mode: str | None = None,
) -> None:
    """Build (or refresh) a flat-shaded material with a TexImage node.

    ``blend_mode`` (when set) maps the photoshop tag system blend mode onto the
    EEVEE material's ``blend_method`` so the artist sees a sensible
    viewport approximation. The exact mode is preserved as a custom
    property by ``_tag_blend_mode`` for downstream writers.
    """
    mesh = expect_mesh(obj)
    image = bpy.data.images.load(str(image_path), check_existing=True)
    image.name = image_path.stem
    # Decode the PNG as sRGB explicitly: the texture must show its authored
    # color, and a stray Non-Color / AgX assignment (config- or user-set) would
    # shift it. The exporter writes plain sRGB PNGs.
    colorspace = getattr(image, "colorspace_settings", None)
    if colorspace is not None:
        # Best-effort + guarded like _apply_flat_color_management: a non-default
        # OCIO config (e.g. ACES) may not expose a literal "sRGB" colorspace, and
        # the bare assignment would raise and abort the import. Leave Blender's
        # default colorspace in that case rather than fail.
        with contextlib.suppress(TypeError, AttributeError):
            colorspace.name = "sRGB"
    mat_name = f"{obj.name}.mat"
    mat = material_by_name(mat_name) or bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nt = mat.node_tree
    if nt is None:
        raise RuntimeError(
            f"Proscenio: material {mat_name!r} has no node tree after use_nodes=True"
        )
    while nt.nodes:
        nt.nodes.remove(next(iter_shader_nodes(nt)))
    # Unlit / shadeless: cutout art is flat 2D, so show the texture exactly - an
    # Emission gated by the texture alpha, with no diffuse / specular / IOR sheen
    # and no dependence on scene lighting. With a Standard view transform (set on
    # import) this reproduces the source PNG 1:1; the old Principled BSDF washed
    # it out with a Fresnel highlight.
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    emission = nt.nodes.new(type="ShaderNodeEmission")
    transparent = nt.nodes.new(type="ShaderNodeBsdfTransparent")
    mix = nt.nodes.new(type="ShaderNodeMixShader")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    if not isinstance(tex, bpy.types.ShaderNodeTexImage):
        raise RuntimeError("Proscenio: nodes.new returned the wrong type for ShaderNodeTexImage")
    tex.image = image
    nt.links.new(node_output_by_name(tex, "Color"), node_input_by_name(emission, "Color"))
    # Mix Shader Fac = texture alpha: Transparent (input 1) where alpha is 0, the
    # Emission (input 2) where alpha is 1. The two shader inputs share the name
    # "Shader", so they are addressed by index.
    nt.links.new(node_output_by_name(tex, "Alpha"), node_input_by_name(mix, "Fac"))
    nt.links.new(node_output_by_name(transparent, "BSDF"), node_input_at(mix, 1))
    nt.links.new(node_output_by_name(emission, "Emission"), node_input_at(mix, 2))
    nt.links.new(node_output_by_name(mix, "Shader"), node_input_by_name(out, "Surface"))
    _set_material_blend_method(mat, blend_mode)
    if mesh.materials:
        set_material_at(mesh, 0, mat)
    else:
        mesh.materials.append(mat)


def _set_material_blend_method(mat: bpy.types.Material, blend_mode: str | None) -> None:
    """Map the manifest blend mode onto the EEVEE material's ``blend_method``.

    Defensive against Blender enum drift (e.g. ADDITIVE retired in 4.2):
    look the value up in the property's enum_items before assigning so a
    stale mapping does not abort the entire import.
    """
    if not hasattr(mat, "blend_method"):
        return
    method = _BLEND_METHOD_BY_MODE.get(blend_mode or "normal", "BLEND")
    prop = mat.bl_rna.properties.get("blend_method")
    enum_items = cast(Iterable[bpy.types.EnumPropertyItem], getattr(prop, "enum_items", ()))
    valid: set[str] = {item.identifier for item in enum_items} if prop is not None else set()
    mat.blend_method = cast(
        Literal["OPAQUE", "CLIP", "HASHED", "BLEND"],
        method if method in valid else "BLEND",
    )
