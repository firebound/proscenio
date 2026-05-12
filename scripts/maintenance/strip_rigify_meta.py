"""Strip Rigify metarig leftovers from a Blender armature.

Run with::

    blender --background <path>.blend --python scripts/maintenance/strip_rigify_meta.py

Removes Rigify-specific custom properties + widget orphans + the
``metarig*`` data-block name that the metarig template adds, plus the
addon-registered ``rigify_type`` / ``rigify_parameters`` on pose bones.
Targets armatures where the rig was authored from a Rigify metarig
but ``Generate Rig`` was never run - so the metarig sample data still
hangs around even though Proscenio's writer ignores it.

Idempotent. Saves the .blend in place when changes happen; no-op +
exit 0 when the file is already clean.

Lookup: walks every ``ARMATURE`` object and operates on each one's
data block. Override via ``PROSCENIO_RIG_OBJ`` env var to scope to a
single object name.

Optional flags (env vars, ``"1"`` enables):

- ``PROSCENIO_STRIP_BONE_COLLECTIONS`` - remove every bone collection
  from the targeted armatures (Rigify Human Meta-Rig leaves 20
  visual-only collections like Face / Torso / Arm.L (IK)). Default off
  - destructive when the user keeps the rig in active authoring.
- ``PROSCENIO_STRIP_DRIVERS`` - delete every driver whose data path
  starts with ``proscenio.`` from every Object. Default off. Useful
  to clear smoke-test residues without re-saving the .blend by hand.
- ``PROSCENIO_STRIP_AUTOKEYED_ACTIONS`` - unlink + remove actions
  whose name matches Blender's autokey pattern (``<Object>Action``)
  and that have a single user. Authored actions (``blink``, ``walk``,
  ``idle``) keep their non-autokey names and are untouched. Default
  off. Useful when the user rotated a bone during testing with
  Auto-Keying enabled.
"""

from __future__ import annotations

import os
import sys
from typing import Any

import bpy

OBJECT_FILTER = os.environ.get("PROSCENIO_RIG_OBJ", "")
STRIP_BONE_COLLECTIONS = os.environ.get("PROSCENIO_STRIP_BONE_COLLECTIONS", "") == "1"
STRIP_DRIVERS = os.environ.get("PROSCENIO_STRIP_DRIVERS", "") == "1"
STRIP_AUTOKEYED_ACTIONS = os.environ.get("PROSCENIO_STRIP_AUTOKEYED_ACTIONS", "") == "1"


def main() -> None:
    targets = _collect_target_armatures()
    if not targets:
        scope = f"object {OBJECT_FILTER!r}" if OBJECT_FILTER else "any"
        print(f"[strip_rigify_meta] no armature matched ({scope}) - skipping", file=sys.stderr)
        sys.exit(0)

    changes = 0
    for arm_obj in targets:
        arm_data = arm_obj.data
        changes += _strip_data_props(arm_data)
        changes += _strip_bone_props(arm_data)
        changes += _rename_metarig_data(arm_obj, arm_data)
        changes += _strip_pose_bone_rigify(arm_obj)
    changes += _strip_widget_orphans()
    changes += _strip_rigify_bone_collections_all(targets)
    changes += _strip_armature_object_props(targets)
    if STRIP_BONE_COLLECTIONS:
        changes += _strip_all_bone_collections(targets)
    if STRIP_DRIVERS:
        changes += _strip_proscenio_drivers()
    if STRIP_AUTOKEYED_ACTIONS:
        changes += _strip_autokeyed_actions()

    if changes == 0:
        print("[strip_rigify_meta] already clean - no changes")
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
        return 0  # collision - leave alone
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
        collections = _writable_bone_collections(arm_obj.data)
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


def _writable_bone_collections(arm_data: bpy.types.Armature) -> Any:
    """Return the writable top-level bone collections.

    Blender 4+ splits the bone-collection API into two views:
    ``armature.collections`` (top-level, writable) and
    ``armature.collections_all`` (flattened recursive view, **read-only**).
    Older Blender exposes only ``collections``. Picking the writable one
    explicitly avoids ``AttributeError: ... remove not found`` on 4+.
    """
    return getattr(arm_data, "collections", None)


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


def _strip_pose_bone_rigify(arm_obj: bpy.types.Object) -> int:
    """Clear addon-registered ``rigify_type`` + ``rigify_parameters`` on pose bones.

    Rigify registers these as native StringProperty / PointerProperty on
    ``bpy.types.PoseBone``; they are not visible via ``bone.keys()``. With
    the addon enabled, ``property_unset`` resets each one to its default,
    flushing the metarig sample data. Without the addon, the attributes
    do not exist and the function silently skips.
    """
    pose = getattr(arm_obj, "pose", None)
    if pose is None:
        return 0
    total = 0
    cleared_names: list[str] = []
    for pose_bone in pose.bones:
        # Only ``rigify_type`` carries meaningful state - non-empty means
        # the user assigned a Rigify module to this bone. ``rigify_parameters``
        # is a PointerProperty group that always exists when the addon is
        # loaded, so checking its existence is not a meaningful signal;
        # reset alongside ``rigify_type`` for completeness without counting.
        if not (hasattr(pose_bone, "rigify_type") and getattr(pose_bone, "rigify_type", "")):
            continue
        pose_bone.property_unset("rigify_type")
        if hasattr(pose_bone, "rigify_parameters"):
            pose_bone.property_unset("rigify_parameters")
        total += 1
        cleared_names.append(pose_bone.name)
    if total:
        sample = ", ".join(cleared_names[:5])
        suffix = "..." if len(cleared_names) > 5 else ""
        print(
            f"[strip_rigify_meta] cleared rigify_type/parameters on {total} pose bone(s): "
            f"[{sample}{suffix}]"
        )
    return total


def _strip_all_bone_collections(targets: list[bpy.types.Object]) -> int:
    total = 0
    for arm_obj in targets:
        collections = _writable_bone_collections(arm_obj.data)
        if collections is None or len(collections) == 0:
            continue
        names = [c.name for c in collections]
        # collections.remove() mutates the iterator; drain via index.
        while len(collections) > 0:
            collections.remove(collections[0])
        total += len(names)
        print(
            f"[strip_rigify_meta] removed {len(names)} bone collection(s) on "
            f"{arm_obj.name!r} (PROSCENIO_STRIP_BONE_COLLECTIONS=1): {names}"
        )
    return total


def _strip_autokeyed_actions() -> int:
    """Unlink + remove actions matching Blender's auto-keyed naming pattern.

    Blender's Auto-Keying creates an action named ``<ObjectName>Action`` the
    first time a property is keyed on a freshly-animated object. Authored
    actions deliberately drop the ``Action`` suffix (``blink``, ``walk``,
    ``idle``), so the heuristic safely targets only the autokey residue.
    Skips actions referenced by NLA strips or shared between multiple
    objects (use_count > 1) - those are deliberate.
    """
    total = 0
    removed_names: list[str] = []
    for obj in bpy.data.objects:
        anim_data = obj.animation_data
        if anim_data is None or anim_data.action is None:
            continue
        action = anim_data.action
        expected_autokey_name = f"{obj.name}Action"
        if action.name != expected_autokey_name:
            continue
        if action.use_fake_user or action.users > 1:
            continue
        anim_data.action = None
        try:
            bpy.data.actions.remove(action, do_unlink=True)
        except RuntimeError:
            continue
        removed_names.append(expected_autokey_name)
        total += 1
    if removed_names:
        print(
            f"[strip_rigify_meta] removed {total} auto-keyed action(s) "
            f"(PROSCENIO_STRIP_AUTOKEYED_ACTIONS=1): {removed_names}"
        )
    return total


def _strip_proscenio_drivers() -> int:
    """Delete every driver whose data path starts with ``proscenio.``.

    Used to clear smoke-test residues. Walks every Object with
    ``animation_data.drivers``, filters by data_path prefix, calls
    ``obj.driver_remove`` to drop the driver itself, and unsets the
    target property + ``region_mode`` to defaults so the writer emits
    the same texture_region as before the test driver wired up.
    """
    total = 0
    for obj in bpy.data.objects:
        if obj.animation_data is None:
            continue
        # Capture paths BEFORE removal - the FCurve handle goes stale and
        # ``d.data_path`` returns "" once driver_remove unlinks it.
        paths = [
            d.data_path
            for d in obj.animation_data.drivers
            if d.data_path.startswith("proscenio.")
        ]
        for path in paths:
            obj.driver_remove(path)
        if paths:
            _reset_driven_props(obj, paths)
            print(f"[strip_rigify_meta] removed {len(paths)} driver(s) on {obj.name!r}: {paths}")
        total += len(paths)
    return total


def _reset_driven_props(obj: bpy.types.Object, removed_paths: list[str]) -> None:
    """Unset PG fields targeted by removed drivers + the dependent ``region_mode``.

    A driver on ``proscenio.region_x`` makes the panel author flip
    ``region_mode`` to ``manual`` to surface the field. Removing only
    the driver leaves the mesh in manual mode with the last cached
    driver value, so the .proscenio export differs from the pre-test
    golden. Reset every driven field + ``region_mode`` to defaults.
    """
    props = getattr(obj, "proscenio", None)
    if props is None:
        return
    touched_region = False
    for path in removed_paths:
        field = path[len("proscenio.") :]
        if hasattr(props, field):
            props.property_unset(field)
            if field.startswith("region_"):
                touched_region = True
    if touched_region and hasattr(props, "region_mode"):
        props.property_unset("region_mode")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[strip_rigify_meta] FAILED: {exc}", file=sys.stderr)
        raise
