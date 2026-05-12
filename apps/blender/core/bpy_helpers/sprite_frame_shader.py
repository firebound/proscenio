"""Sprite_frame preview shader-node group builder (SPEC 004 D13).

Bpy graph builder: assembles the ``Proscenio.SpriteFrameSlicer`` node
group + wires drivers from ``obj.proscenio.frame / hframes / vframes``
onto the matching shader inputs. Invoked from the SPEC 004 panel
operator.

The pure-Python cell math (``cell_size``, ``cell_offset_x``,
``cell_offset_y``) lives in ``core.sprite_frame_math`` - bpy-free and
exercised by pytest directly. Wave 9.10 moved it out so this module
stays focused on the bpy node tree.
"""

from __future__ import annotations

from typing import Any

SLICER_GROUP_NAME = "Proscenio.SpriteFrameSlicer"
SLICER_NODE_LABEL = "Proscenio Sprite Frame Slicer"

_SOCK_UV = "UV"
_SOCK_FRAME = "Frame"
_SOCK_HFRAMES = "H Frames"
_SOCK_VFRAMES = "V Frames"


def ensure_slicer_group(node_groups: Any) -> Any:
    """Create or fetch the reusable ``Proscenio.SpriteFrameSlicer`` node group.

    The group exposes inputs ``Frame`` / ``H Frames`` / ``V Frames`` plus
    a single ``UV`` socket, and outputs a UV vector remapped onto the
    addressed cell. Idempotent: subsequent calls return the existing
    group untouched.
    """
    group = node_groups.get(SLICER_GROUP_NAME)
    if group is not None:
        return group
    group = node_groups.new(name=SLICER_GROUP_NAME, type="ShaderNodeTree")
    _populate_slicer_group(group)
    return group


def _populate_slicer_group(group: Any) -> None:
    """Wire the slicer math: ``UV * cell_size + cell_offset``."""
    interface = group.interface
    interface.new_socket(_SOCK_UV, in_out="INPUT", socket_type="NodeSocketVector")
    interface.new_socket(_SOCK_FRAME, in_out="INPUT", socket_type="NodeSocketFloat")
    interface.new_socket(_SOCK_HFRAMES, in_out="INPUT", socket_type="NodeSocketFloat")
    interface.new_socket(_SOCK_VFRAMES, in_out="INPUT", socket_type="NodeSocketFloat")
    interface.new_socket(_SOCK_UV, in_out="OUTPUT", socket_type="NodeSocketVector")

    nodes = group.nodes
    links = group.links
    grp_in = nodes.new("NodeGroupInput")
    grp_in.location = (-700, 0)
    grp_out = nodes.new("NodeGroupOutput")
    grp_out.location = (700, 0)

    sep_uv = nodes.new("ShaderNodeSeparateXYZ")
    sep_uv.location = (-500, 200)
    links.new(grp_in.outputs["UV"], sep_uv.inputs["Vector"])

    inv_h = nodes.new("ShaderNodeMath")
    inv_h.operation = "DIVIDE"
    inv_h.location = (-500, -100)
    inv_h.inputs[0].default_value = 1.0
    links.new(grp_in.outputs[_SOCK_HFRAMES], inv_h.inputs[1])

    inv_v = nodes.new("ShaderNodeMath")
    inv_v.operation = "DIVIDE"
    inv_v.location = (-500, -260)
    inv_v.inputs[0].default_value = 1.0
    links.new(grp_in.outputs[_SOCK_VFRAMES], inv_v.inputs[1])

    col_idx = nodes.new("ShaderNodeMath")
    col_idx.operation = "MODULO"
    col_idx.location = (-300, -100)
    links.new(grp_in.outputs[_SOCK_FRAME], col_idx.inputs[0])
    links.new(grp_in.outputs[_SOCK_HFRAMES], col_idx.inputs[1])

    row_idx_div = nodes.new("ShaderNodeMath")
    row_idx_div.operation = "DIVIDE"
    row_idx_div.location = (-500, -420)
    links.new(grp_in.outputs[_SOCK_FRAME], row_idx_div.inputs[0])
    links.new(grp_in.outputs[_SOCK_HFRAMES], row_idx_div.inputs[1])
    row_idx = nodes.new("ShaderNodeMath")
    row_idx.operation = "FLOOR"
    row_idx.location = (-300, -420)
    links.new(row_idx_div.outputs[0], row_idx.inputs[0])

    off_x = nodes.new("ShaderNodeMath")
    off_x.operation = "MULTIPLY"
    off_x.location = (-100, -100)
    links.new(col_idx.outputs[0], off_x.inputs[0])
    links.new(inv_h.outputs[0], off_x.inputs[1])

    row_plus_one = nodes.new("ShaderNodeMath")
    row_plus_one.operation = "ADD"
    row_plus_one.location = (-100, -420)
    row_plus_one.inputs[1].default_value = 1.0
    links.new(row_idx.outputs[0], row_plus_one.inputs[0])
    row_scaled = nodes.new("ShaderNodeMath")
    row_scaled.operation = "MULTIPLY"
    row_scaled.location = (100, -420)
    links.new(row_plus_one.outputs[0], row_scaled.inputs[0])
    links.new(inv_v.outputs[0], row_scaled.inputs[1])
    off_y = nodes.new("ShaderNodeMath")
    off_y.operation = "SUBTRACT"
    off_y.location = (300, -420)
    off_y.inputs[0].default_value = 1.0
    links.new(row_scaled.outputs[0], off_y.inputs[1])

    sliced_x = nodes.new("ShaderNodeMath")
    sliced_x.operation = "MULTIPLY_ADD"
    sliced_x.location = (300, 200)
    links.new(sep_uv.outputs["X"], sliced_x.inputs[0])
    links.new(inv_h.outputs[0], sliced_x.inputs[1])
    links.new(off_x.outputs[0], sliced_x.inputs[2])

    sliced_y = nodes.new("ShaderNodeMath")
    sliced_y.operation = "MULTIPLY_ADD"
    sliced_y.location = (300, -100)
    links.new(sep_uv.outputs["Y"], sliced_y.inputs[0])
    links.new(inv_v.outputs[0], sliced_y.inputs[1])
    links.new(off_y.outputs[0], sliced_y.inputs[2])

    combine = nodes.new("ShaderNodeCombineXYZ")
    combine.location = (500, 0)
    links.new(sliced_x.outputs[0], combine.inputs["X"])
    links.new(sliced_y.outputs[0], combine.inputs["Y"])
    links.new(combine.outputs["Vector"], grp_out.inputs["UV"])


def apply_slicer_to_material(
    material: Any,
    *,
    obj: Any,
    node_groups: Any,
) -> bool:
    """Insert the slicer between the material's TexCoord and ImageTexture nodes.

    Wires drivers from ``obj.proscenio.frame / hframes / vframes`` onto
    the matching slicer inputs. Idempotent: re-runs detect the existing
    slicer (named ``SLICER_GROUP_NAME``) and refresh the drivers without
    duplicating nodes. Returns ``True`` on success, ``False`` when the
    material has no node tree, no Image Texture node, or no usable UV
    source.
    """
    if not _material_uses_nodes(material):
        return False
    nt = material.node_tree
    tex_node = _find_image_texture_node(nt)
    if tex_node is None:
        return False
    group = ensure_slicer_group(node_groups)
    slicer = _ensure_slicer_node_in_tree(nt, group)
    _wire_slicer_to_tex(nt, slicer, tex_node)
    _wire_slicer_drivers(material, slicer, obj)
    return True


def remove_slicer_from_material(material: Any) -> bool:
    """Remove the slicer node from this material + drop its drivers.

    Reconnects the source ``TexCoord.UV`` (or whatever vector socket fed
    the slicer's UV input) directly to the ImageTexture's vector input
    so the material renders the full atlas again. Returns ``True`` when
    a slicer was found and removed, ``False`` when there was no slicer.
    """
    if not _material_uses_nodes(material):
        return False
    nt = material.node_tree
    slicer = _find_slicer_node_in_tree(nt)
    if slicer is None:
        return False
    upstream = _slicer_upstream_uv(slicer)
    tex_node = _find_image_texture_node(nt)
    if tex_node is not None and upstream is not None:
        nt.links.new(upstream, tex_node.inputs["Vector"])
    nt.nodes.remove(slicer)
    _drop_slicer_drivers(material)
    return True


# --------------------------------------------------------------------------- #
# Bpy helpers
# --------------------------------------------------------------------------- #


def _material_uses_nodes(material: Any) -> bool:
    return (
        material is not None
        and bool(getattr(material, "use_nodes", False))
        and getattr(material, "node_tree", None) is not None
    )


def _find_image_texture_node(node_tree: Any) -> Any:
    for node in node_tree.nodes:
        if node.type == "TEX_IMAGE" and getattr(node, "image", None) is not None:
            return node
    return None


def _find_slicer_node_in_tree(node_tree: Any) -> Any:
    for node in node_tree.nodes:
        if node.type == "GROUP" and getattr(node.node_tree, "name", "") == SLICER_GROUP_NAME:
            return node
    return None


def _ensure_slicer_node_in_tree(node_tree: Any, group: Any) -> Any:
    existing = _find_slicer_node_in_tree(node_tree)
    if existing is not None:
        return existing
    slicer = node_tree.nodes.new("ShaderNodeGroup")
    slicer.node_tree = group
    slicer.label = SLICER_NODE_LABEL
    slicer.location = (-200, 100)
    return slicer


def _wire_slicer_to_tex(node_tree: Any, slicer: Any, tex_node: Any) -> None:
    """Link the slicer in front of the ImageTexture's Vector input."""
    uv_source = _resolve_uv_source(node_tree, tex_node)
    if uv_source is not None:
        node_tree.links.new(uv_source, slicer.inputs["UV"])
    node_tree.links.new(slicer.outputs["UV"], tex_node.inputs["Vector"])


def _resolve_uv_source(node_tree: Any, tex_node: Any) -> Any:
    """Find the socket currently feeding the ImageTexture's Vector input."""
    vec_input = tex_node.inputs.get("Vector")
    if vec_input is None or not vec_input.is_linked:
        # No prior UV source - create a TexCoord node and wire its UV.
        tex_coord = node_tree.nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-450, 100)
        return tex_coord.outputs["UV"]
    link = vec_input.links[0]
    return link.from_socket


def _slicer_upstream_uv(slicer: Any) -> Any:
    uv_input = slicer.inputs.get("UV")
    if uv_input is None or not uv_input.is_linked:
        return None
    return uv_input.links[0].from_socket


def _wire_slicer_drivers(material: Any, slicer: Any, obj: Any) -> None:
    """Wire `obj.proscenio.{frame,hframes,vframes}` -> slicer inputs."""
    spec = (
        (_SOCK_FRAME, "frame"),
        (_SOCK_HFRAMES, "hframes"),
        (_SOCK_VFRAMES, "vframes"),
    )
    for socket_name, prop_name in spec:
        socket = slicer.inputs.get(socket_name)
        if socket is None:
            continue
        # Drop any existing driver before re-adding so re-runs stay clean.
        socket.driver_remove("default_value")
        fcurve = socket.driver_add("default_value")
        driver = fcurve.driver
        driver.type = "AVERAGE"
        var = driver.variables.new()
        var.name = "v"
        var.type = "SINGLE_PROP"
        target = var.targets[0]
        target.id_type = "OBJECT"
        target.id = obj
        target.data_path = f"proscenio.{prop_name}"


def _drop_slicer_drivers(material: Any) -> None:
    """Best-effort: drop drivers attached to any slicer-shaped node in the material.

    Called after the slicer node itself is removed; iterates remaining
    animation_data drivers + clears any whose data_path points at a node
    socket that no longer exists.
    """
    anim = getattr(material, "animation_data", None)
    if anim is None:
        return
    drivers = list(getattr(anim, "drivers", ()))
    for fcurve in drivers:
        if "Proscenio.SpriteFrameSlicer" in str(getattr(fcurve, "data_path", "")):
            anim.drivers.remove(fcurve)
