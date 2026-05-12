"""Dump everything we'd need from a .blend to author the Proscenio exporter.

Run via:

    blender --background examples/dummy/dummy.blend --python scripts/inspect_blend.py

Output is written to scripts/inspect_blend.out next to this script - Blender
headless on Windows is unreliable about flushing stdout to pipes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

OUT_PATH = Path(__file__).parent / "inspect_blend.out"
_LINES: list[str] = []


def print(*args, **kwargs):  # noqa: A001 - shadow built-in deliberately
    _LINES.append(" ".join(str(a) for a in args))


def _fmt_vec(v) -> str:
    return f"({', '.join(f'{c:.4f}' for c in v)})"


def _section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def _dump_scenes() -> None:
    _section("SCENES")
    for scene in bpy.data.scenes:
        print(f"  scene: {scene.name}  fps={scene.render.fps}  frames={scene.frame_start}-{scene.frame_end}")


def _dump_objects() -> None:
    _section("OBJECTS")
    for obj in bpy.data.objects:
        print(f"  - name='{obj.name}'  type={obj.type}  parent={obj.parent.name if obj.parent else None}")
        print(f"      location={_fmt_vec(obj.location)}  rotation_euler={_fmt_vec(obj.rotation_euler)}  scale={_fmt_vec(obj.scale)}")
        if obj.parent_type == "BONE":
            print(f"      parent_bone='{obj.parent_bone}'")


def _dump_bone(bone) -> None:
    print(f"    bone: '{bone.name}'  parent={bone.parent.name if bone.parent else None}")
    print(f"      head={_fmt_vec(bone.head)}  tail={_fmt_vec(bone.tail)}  length={bone.length:.4f}")
    print(f"      head_local={_fmt_vec(bone.head_local)}  tail_local={_fmt_vec(bone.tail_local)}")
    print("      matrix_local rows:")
    for row in bone.matrix_local:
        print(f"        {_fmt_vec(row)}")


def _dump_armatures() -> None:
    _section("ARMATURES")
    for arm in bpy.data.armatures:
        print(f"  armature: '{arm.name}'  bones={len(arm.bones)}")
        for bone in arm.bones:
            _dump_bone(bone)


def _dump_mesh(mesh) -> None:
    print(f"  mesh: '{mesh.name}'  verts={len(mesh.vertices)}  polys={len(mesh.polygons)}  uv_layers={len(mesh.uv_layers)}")
    for v in mesh.vertices[:6]:
        groups = [(g.group, g.weight) for g in v.groups]
        print(f"    v[{v.index}]={_fmt_vec(v.co)}  groups={groups}")
    for uv_layer in mesh.uv_layers:
        print(f"    uv_layer: '{uv_layer.name}'  loops={len(uv_layer.data)}")
        for i, item in enumerate(uv_layer.data[:8]):
            print(f"      uv[{i}]={_fmt_vec(item.uv)}")


def _dump_meshes() -> None:
    _section("MESHES")
    for mesh in bpy.data.meshes:
        _dump_mesh(mesh)


def _dump_vertex_groups() -> None:
    _section("MESH OBJECTS - VERTEX GROUPS")
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        print(f"  obj '{obj.name}' vertex_groups: {[vg.name for vg in obj.vertex_groups]}")


def _dump_material(mat) -> None:
    print(f"  material: '{mat.name}'  use_nodes={mat.use_nodes}")
    if not mat.use_nodes:
        return
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image:
            print(f"    image: name='{node.image.name}'  filepath='{node.image.filepath}'  size={node.image.size[:]}")


def _dump_materials() -> None:
    _section("MATERIALS / TEXTURES")
    for mat in bpy.data.materials:
        _dump_material(mat)


def _dump_action(action) -> None:
    frame_range = action.frame_range
    print(f"  action: '{action.name}'  frame_range={frame_range[0]:.1f}-{frame_range[1]:.1f}  fcurves={len(action.fcurves)}")
    for fc in action.fcurves:
        print(f"    fcurve: data_path='{fc.data_path}'  array_index={fc.array_index}  keys={len(fc.keyframe_points)}")
        for kp in fc.keyframe_points[:5]:
            print(f"      kp: time={kp.co[0]:.2f}  value={kp.co[1]:.4f}  interp={kp.interpolation}")


def _dump_actions() -> None:
    _section("ACTIONS")
    for action in bpy.data.actions:
        _dump_action(action)


def main() -> None:
    _dump_scenes()
    _dump_objects()
    _dump_armatures()
    _dump_meshes()
    _dump_vertex_groups()
    _dump_materials()
    _dump_actions()


if __name__ == "__main__":
    main()
    OUT_PATH.write_text("\n".join(_LINES), encoding="utf-8")
    sys.stdout.write(f"wrote {OUT_PATH}\n")
    sys.stdout.flush()
