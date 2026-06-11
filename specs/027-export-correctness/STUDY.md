# Spec 027: Export correctness

Guarantee the exported `.proscenio` is never silently wrong - fix the writer and validator output-integrity defects.

## Scope

- **Writer respects the armature picker** - export the armature the user selected in the Skeleton panel, not always the first one in the scene.
- **Multi-polygon meshes export whole** - stop truncating a mesh to its first polygon (or hard-warn and refuse) so multi-island sprites are not silently corrupted.
- **Drop the false "no parent bone" alarm** - the validator stops flagging slot attachments, ending warning noise on every slot scene.
- **Validator reads Custom-Property edits** - validate the slot default value even when it was edited directly, not only through the panel.
- **Re-confirm the slot transform-key check** - retest the validator catch that a prior GUI failure contradicted.

## Study

### Surface notes

- Armature selection has two hardcoded `armatures[0]` homes, not one. `find_armature` ([`scene_discovery.py:14-19`](../../apps/blender/exporters/godot/writer/scene_discovery.py)) returns the first ARMATURE in scene order and never reads the picker (`active_armature`, [`scene_props.py:473-486`](../../apps/blender/properties/scene_props.py)), and `validate_export` derives `available_bones` from `armatures[0]` too ([`export.py:26-31`](../../apps/blender/core/validation/export.py)). Fixing only the writer would leave validate and export disagreeing in multi-armature scenes, so one shared picker-first resolver must feed both, guarded for the headless path (`scene.proscenio` unregistered under `--background`) and for a stale pointer (picker object deleted or no longer an ARMATURE in this scene). The Skeleton panel copy that should name the effective armature stays with the rigging-and-posing spec (`skeleton-armature-picker`, tagged as pairing with this fix).
- Multi-polygon truncation is worse than the backlog entry's "mask cutouts, complex topology" framing. `build_element` emits `polygon_at(mesh, 0)` only ([`sprites.py:93-96`](../../apps/blender/exporters/godot/writer/sprites.py)). PSD import stamps single-quad meshes ([`planes.py:250-258`](../../apps/blender/importers/photoshop/planes.py)), so the plain import path survives - but automesh output is a triangulated bmesh by construction ([`cdt.py:121`](../../apps/blender/core/bpy_helpers/automesh/cdt.py); even `SIMPLE` interior mode triangulates), so every automesh-densified mesh exports as its first triangle, silently. The scope's "hard-warn and refuse" fallback is therefore not viable - it would make the flagship deform flow un-exportable - and the backlog's "one element per polygon" option is ruled out by the same fact (a dense mesh would explode into hundreds of Polygon2D nodes with name collisions and per-island weight slicing).
- The real multi-polygon fix is not writer-only. `MeshElement` carries a single polygon ring plus per-vertex `uv` ([`proscenio.py:72-112`](../../packages/models/src/proscenio_models/proscenio.py)), and the Godot builder assigns one outline ([`mesh_builder.gd:59-62`](../../apps/godot/addons/proscenio/builders/mesh_builder.gd)); Godot's `Polygon2D.polygons` index-array support is unused on both sides. The fix adds an additive-optional `polygons` index-array field to the schema, makes the writer emit all vertices, per-face index arrays, and whole-mesh weights, and has the builder assign `Polygon2D.polygons` when present. Compatibility is additive in both directions: an old importer ignores the new field and still renders the outline, and single-face meshes keep emitting the field-less shape so the goldens do not churn. [AGENTS.md](../../AGENTS.md) rule 1 asks a `format_version` bump for cross-component shape changes - with the format-migration-path enabler still open in the schema-expressiveness spec, ship this additive at version 1 with a schema changelog note instead of bumping and stranding old importers.
- The false "no parent bone" alarm is a missing guard, not a redesign. `_validate_element_against_armature` walks every MESH with no slot-attachment skip ([`export.py:61-78`](../../apps/blender/core/validation/export.py)) while slot attachments inherit their bone through the slot Empty by design; `is_slot_empty` is already imported in that module, so the fix is skipping the parent-bone warning for meshes whose `parent` is a slot Empty. Pure duck-typed module with an existing unit suite ([`test_validation_export.py`](../../tests/test_validation_export.py)).
- The Custom-Property gap is down to one read. Element fields already route through `read_field` ([`_shared.py:21,33`](../../apps/blender/core/validation/_shared.py)), but `_check_slot_default` still reads the PG attribute directly ([`active_slot.py:40-41`](../../apps/blender/core/validation/active_slot.py)) while the writer-side slot emission reads via `read_field` - so a `proscenio_slot_default` edited in the Custom Properties UI exports unvalidated. One-line reroute, plus the help hint the backlog entry asks for (direct CP edits do not refresh the panel; panels are the expected workflow).
- The transform-key [retest] has a likely root cause rather than an unexplained GUI failure. `_has_bone_transform_keys` reads `action.fcurves` directly ([`active_slot.py:99-112`](../../apps/blender/core/validation/active_slot.py)), while the writer guards the Blender 4.4+ layered-action shape via `action_fcurves` ([`animations.py:36-47`](../../apps/blender/exporters/godot/writer/animations.py) - empty `fcurves` falls back to layers > strips > channelbags). A keyframe inserted in the 5.1.1 GUI lands in a layered action, the legacy `fcurves` view comes back empty, and the check stays silent - exactly the logged symptom, while the SimpleNamespace unit mocks (which populate `fcurves`) keep passing. Lift `action_fcurves` into a shared duck-typed home, route the validator through it, then the GUI retest confirms.

### Assessment

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Writer respects the armature picker | 5 | 1 | 1 | 1 | now | silent wrong-rig export, pure-unit fixable |
| Multi-polygon meshes export whole | 5 | 3 | 3 | 1 | now | every automesh mesh truncates to one face today |
| Drop the false "no parent bone" alarm | 4 | 1 | 1 | 1 | now | two-line skip ends per-slot-scene warning noise |
| Validator reads Custom-Property edits | 3 | 1 | 1 | 2 | now | one PG-only read left to route through `read_field` |
| Re-confirm the slot transform-key check | 4 | 3 | 1 | 1 | now | likely layered-action read gap - fix, then retest |

### Verdict summary

5 now, 0 defer, 0 gate, 0 drop.

All five are output-integrity defects in shipped surfaces - none adds an interactive surface, and four of five are pure-unit fixable in the existing harnesses. Sequence the three small chunks first (picker resolution shared by writer and validator; the slot-validator truth fixes; both land with unit tests only), then the multi-polygon chunk last as the one cross-app PR (schema + writer + Godot builder), since it is the largest diff and the only one touching the wire shape. The single GUI confirmation (transform-key warning fires on 5.1.1 layered actions) rides the already-planned verification session instead of demanding its own.
