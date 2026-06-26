"""Generated 2D bone-widget meshes for the custom-shape assignment.

Blender's ``pose_bone.custom_shape`` is the native mechanism (Rigify and the
Bone Widget addon both use it), but Blender ships no shape library - the mesh
must be supplied. Proscenio is a 2D pipeline, so this builds a small set of flat
wire outlines (circle, square, diamond, line, triangle, arrow) on demand, named
``WGT-proscenio-<shape>`` and deduped by name, each an Object with a fake user so
it persists in the .blend without being linked into any scene (a ``custom_shape``
only needs the Object datablock to exist, not to be in a collection).

The outlines lie in the local X-Z plane (the picture plane for a front-ortho 2D
rig) as edge-only meshes - no faces, so they read as thin control outlines. The
exact plane / fill is the deferred sub-point of spec 069 decision 7; the scale
and offset are operator-side, not baked into the mesh.
"""

from __future__ import annotations

import math

import bpy

#: Stable name prefix so the widgets are recognizable in the Blender outliner and
#: the dedupe lookup is exact.
WIDGET_PREFIX = "WGT-proscenio-"

#: The 2D shape ids the builder knows. The assign operator's enum mirrors this.
SHAPE_IDS: tuple[str, ...] = ("circle", "square", "diamond", "line", "triangle", "arrow")

_CIRCLE_SEGMENTS = 24


def _ring(
    points: list[tuple[float, float, float]],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    """A closed edge loop through ``points`` (last vert wraps to the first)."""
    edges = [(i, (i + 1) % len(points)) for i in range(len(points))]
    return points, edges


def _polyline(
    points: list[tuple[float, float, float]],
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    """An open edge chain through ``points`` (no wrap)."""
    edges = [(i, i + 1) for i in range(len(points) - 1)]
    return points, edges


def _geometry(shape: str) -> tuple[list[tuple[float, float, float]], list[tuple[int, int]]]:
    """Verts + edges for ``shape`` in the local X-Y plane (z = 0), unit-ish radius.

    The plane is deliberately X-Y: a custom shape is drawn in bone-local space,
    and for a bone lying in the world picture plane (the X-Z plane a 2D Proscenio
    rig draws into) the local Z axis points out of that plane along world Y. So a
    mesh in the local X-Y plane has its normal along local Z = world Y, which
    faces the front-ortho camera. A mesh in the local X-Z plane would instead lie
    edge-on to that camera (every outline collapsing to a line) - the bug this
    fixes. Unknown ids fall back to the circle so the assign operator always
    yields a usable widget rather than an empty mesh.
    """
    if shape == "square":
        return _ring([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)])
    if shape == "diamond":
        return _ring([(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)])
    if shape == "line":
        return _polyline([(-1, 0, 0), (1, 0, 0)])
    if shape == "triangle":
        return _ring([(0, 1, 0), (1, -1, 0), (-1, -1, 0)])
    if shape == "arrow":
        return _polyline([(-1, 0, 0), (1, 0, 0), (0.4, 0.5, 0), (1, 0, 0), (0.4, -0.5, 0)])
    # circle (and the fallback for any unknown id)
    points = [
        (
            math.cos(2 * math.pi * i / _CIRCLE_SEGMENTS),
            math.sin(2 * math.pi * i / _CIRCLE_SEGMENTS),
            0.0,
        )
        for i in range(_CIRCLE_SEGMENTS)
    ]
    return _ring(points)


def ensure_bone_widget(shape: str) -> bpy.types.Object:
    """Return the ``WGT-proscenio-<shape>`` widget Object, building it once.

    Deduped by name: a second call for the same shape returns the existing
    datablock. The Object carries a fake user so it survives a save / reload
    even while unreferenced, and is never linked into a scene collection - a
    ``custom_shape`` only needs the datablock to exist.
    """
    name = f"{WIDGET_PREFIX}{shape}"
    existing = bpy.data.objects.get(name)
    if existing is not None:
        return existing
    verts, edges = _geometry(shape)
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.use_fake_user = True
    return obj
