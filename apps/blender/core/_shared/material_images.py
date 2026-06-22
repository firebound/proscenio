"""Find the texture image(s) on a material or object - one walk, every reader.

The "iterate a material's shader nodes, keep the TEX_IMAGE images" walk was
hand-written across the addon (automesh image resolve, the writer's
per-sprite texture + atlas discovery, atlas collect / pack, the sprite
panel's size probe, export validation). Each copy derived something
slightly different off the identical node walk - the image, its name, its
pixel size, its filepath - so changing the node-finding convention meant
editing every copy in lockstep. This module owns the walk; callers keep
only their thin derivation on top.

Runtime is ``bpy``-free (the type hints sit under ``TYPE_CHECKING`` and the
bodies read through ``getattr``), so this lives in the pure ``core/_shared``
infra tier next to ``region`` / ``pg_cp_fallback``: the duck-typed,
import-without-bpy modules (``atlas_collect``, ``validation.export``) route
through it just like the bpy-bound operators and the writer, and the same
helpers serve a real ``bpy.types.Object`` and the ``SimpleNamespace`` mocks
the pure-pytest suites build.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import bpy

# Texture-node interpolation values the pixel-art toggle switches between:
# ``Closest`` is crisp nearest-neighbor (pixel art), ``Linear`` is Blender's
# bilinear default. Closed set, so it is a Literal, not a bare str.
TextureInterpolation = Literal["Closest", "Linear"]


def iter_material_image_nodes(
    material: bpy.types.Material | None,
) -> Iterator[bpy.types.ShaderNodeTexImage]:
    """Yield every TEX_IMAGE node with an image bound in one material's node tree.

    The node-level walk every image reader sits on: callers that want the
    image take ``node.image`` (see :func:`iter_material_node_images`), callers
    that mutate the node (the pixel-art interpolation toggle) keep the node.

    Empty when ``material`` is None, is not node-based, has no node tree, or
    carries no image texture node with an image bound.

    The ``use_nodes`` guard reads ``getattr(material, "use_nodes", True)``: on
    Blender 5.1 a material can hold a populated ``node_tree`` while
    ``use_nodes`` is False (the tree is inactive and must be skipped), so the
    guard is meaningful; ``Material.use_nodes`` is deprecated and removed in
    Blender 6.0, where the ``getattr`` default of True keeps discovery
    working. This is the version-robust form prescribed by the
    blender-6-compatibility spec (062) - dropping the guard outright would
    regress 5.1 by reading textures off inactive node trees.
    """
    if material is None or not getattr(material, "use_nodes", True):
        return
    tree = getattr(material, "node_tree", None)
    if tree is None:
        return
    for node in getattr(tree, "nodes", ()):
        if getattr(node, "type", "") == "TEX_IMAGE" and getattr(node, "image", None) is not None:
            yield node


def iter_material_node_images(material: bpy.types.Material | None) -> Iterator[bpy.types.Image]:
    """Yield every linked TEX_IMAGE image in one material's node tree.

    Empty when ``material`` is None, is not node-based, has no node tree, or
    carries no image texture node with an image bound.
    """
    for node in iter_material_image_nodes(material):
        image = node.image
        if image is not None:  # always true (the node walk filters), narrows for mypy
            yield image


def iter_material_images(obj: bpy.types.Object) -> Iterator[bpy.types.Image]:
    """Yield every TEX_IMAGE image across the object's material slots, in slot order."""
    for material in getattr(getattr(obj, "data", None), "materials", None) or []:
        yield from iter_material_node_images(material)


def set_object_texture_interpolation(
    obj: bpy.types.Object | None,
    interpolation: TextureInterpolation,
) -> None:
    """Set ``interpolation`` on every image-texture node across ``obj``'s materials.

    Reuses the canonical :func:`iter_material_image_nodes` walk so the
    pixel-art toggle and every image reader stay on the same node-finding
    convention. A no-op when ``obj`` is None or carries no image-texture
    nodes. Pure / bpy-free (assigns through the node's ``interpolation``
    attribute) so the pure-pytest suite exercises it with mocks.
    """
    for material in getattr(getattr(obj, "data", None), "materials", None) or []:
        for node in iter_material_image_nodes(material):
            node.interpolation = interpolation


def first_material_image(obj: bpy.types.Object | None) -> bpy.types.Image | None:
    """Return the object's texture image: active material first, then the other slots.

    The active material wins because it is what the user sees in the shader
    editor and the natural "this sprite's texture" on a multi-material mesh;
    the remaining slots are the fallback. Returns None when ``obj`` is None
    or nothing is bound, so callers no longer guard the None object case
    themselves.
    """
    data = getattr(obj, "data", None)
    if data is None:
        return None
    active = getattr(obj, "active_material", None)
    image = next(iter_material_node_images(active), None)
    if image is not None:
        return image
    for material in getattr(data, "materials", None) or []:
        if material is active:
            continue
        image = next(iter_material_node_images(material), None)
        if image is not None:
            return image
    return None
