"""Strip Rigify metarig leftovers from a Blender armature.

Run with::

    blender --background <path>.blend --python scripts/maintenance/strip_rigify_meta.py

Removes Rigify-specific custom properties + widget orphans + Rigify
bone collections + the ``metarig*`` data-block name that the metarig
template adds. Targets armatures where the rig was authored from a
Rigify metarig but ``Generate Rig`` was never run -- so the metarig
sample data still hangs around even though Proscenio's writer ignores
it.

Idempotent. Saves the .blend in place when changes happen; no-op +
exit 0 when the file is already clean.

Lookup: walks every ``ARMATURE`` object and operates on each one's
data block. Override via ``PROSCENIO_RIG_OBJ`` env var to scope to a
single object name.
"""

from __future__ import annotations

import os
import sys

import bpy

OBJECT_FILTER = os.environ.get("PROSCENIO_RIG_OBJ", "")


def main() -> None:
    targets = _collect_target_armatures()
    if not targets:
        scope = f"object {OBJECT_FILTER!r}" if OBJECT_FILTER else "any"
        print(f"[strip_rigify_meta] no armature matched ({scope}) -- skipping", file=sys.stderr)
        sys.exit(0)

    changes = 0
    for arm_obj in targets:
        arm_data = arm_obj.data
        changes += _strip_data_props(arm_data)
        changes += _strip_bone_props(arm_data)
        changes += _rename_metarig_data(arm_obj, arm_data)
    changes += _strip_widget_orphans()
    changes += _strip_rigify_bone_collections_all(targets)
    changes += _strip_armature_object_props(targets)

    if changes == 0:
        print("[strip_rigify_meta] already clean -- no changes")
        return

    bpy.ops.wm.save_mainfile()
    print(f"[strip_rigify_meta] cleaned + saved ({changes} mutation(s))")


def _collect_target_armatures() -> list[bpy.types.Object]:
    out: list[bpy.types.Object] = []
    for obj in bpy.data.objects:
        if obj.type != "ARMATURE":
            continue
        if OBJECT_FILTER and obj.name != OBJECT_FILTER:
            continue
        out.append(obj)
    return out


def _rename_metarig_data(arm_obj: bpy.types.Object, arm_data: bpy.types.Armature) -> int:
    """Match the data block name to the object name when it still says ``metarig*``."""
    if not arm_data.name.lower().startswith("metarig"):
        return 0
    new_name = arm_obj.name
    if new_name in bpy.data.armatures and bpy.data.armatures[new_name] is not arm_data:
        return 0  # collision -- leave alone
    old = arm_data.name
    arm_data.name = new_name
    print(f"[strip_rigify_meta] renamed armature data {old!r} -> {new_name!r}")
    return 1


def _strip_data_props(arm_data: bpy.types.Armature) -> int:
    keys = [k for k in arm_data.keys() if k.startswith("rigify")]
    for k in keys:
        del arm_data[k]
    if keys:
        print(f"[strip_rigify_meta] removed {len(keys)} armature-data prop(s): {keys}")
    return len(keys)


def _strip_bone_props(arm_data: bpy.types.Armature) -> int:
    total = 0
    for bone in arm_data.bones:
        keys = [k for k in bone.keys() if k.startswith("rigify")]
        for k in keys:
            del bone[k]
        total += len(keys)
    if total:
        print(f"[strip_rigify_meta] removed {total} per-bone rigify prop(s)")
    return total


def _strip_widget_orphans() -> int:
    widgets = [obj for obj in bpy.data.objects if obj.name.startswith("WGT-")]
    for obj in widgets:
        bpy.data.objects.remove(obj, do_unlink=True)
    if widgets:
        print(f"[strip_rigify_meta] removed {len(widgets)} WGT-* widget object(s)")
    return len(widgets)


def _strip_rigify_bone_collections_all(targets: list[bpy.types.Object]) -> int:
    total = 0
    for arm_obj in targets:
        arm_data = arm_obj.data
        collections = getattr(arm_data, "collections_all", None) or getattr(
            arm_data, "collections", None
        )
        if collections is None:
            continue
        rigify = [c for c in collections if "rigify" in c.name.lower()]
        for coll in rigify:
            collections.remove(coll)
        if rigify:
            names = [c.name for c in rigify]
            print(
                f"[strip_rigify_meta] removed {len(rigify)} bone collection(s) "
                f"on {arm_obj.name!r}: {names}"
            )
        total += len(rigify)
    return total


def _strip_armature_object_props(targets: list[bpy.types.Object]) -> int:
    total = 0
    for obj in targets:
        keys = [k for k in obj.keys() if k.startswith("rigify") or k == "rig_id"]
        for k in keys:
            del obj[k]
        total += len(keys)
    if total:
        print(f"[strip_rigify_meta] removed {total} armature-object prop(s)")
    return total


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[strip_rigify_meta] FAILED: {exc}", file=sys.stderr)
        raise
