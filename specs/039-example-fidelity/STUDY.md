# Spec 039: Example pipeline fidelity

Make the synced Godot examples open and render faithfully. The mixed-feature fixture (spec 035) was the trigger: inspecting it surfaced three defects that turn out to be systemic across every example, not unique to that fixture. Each one makes the dev-project examples look broken even though the underlying `.proscenio` data is correct.

## Scope

- **Wrapper script paths** that every example `.tscn` gets wrong, so the wrapper scene fails to load.
- **Textures rendering blank** for every imported example in the Godot editor.
- **Bone orientation** in the exported skeleton reading as flattened / edge-on, raising a convention question first exposed by a skinned Blender fixture.

Surface: [sync_fixtures.py](../../scripts/godot/sync_fixtures.py), the per-fixture `godot/*.tscn` wrappers, [importer.gd](../../apps/blender/../../apps/godot/addons/proscenio/importer.gd), the Godot builders, the writer's [skeleton.py](../../apps/blender/exporters/godot/writer/skeleton.py).

## Study

### Surface notes

**1. Wrapper scripts resolve to a path the sync never writes.** [sync_fixtures.py](../../scripts/godot/sync_fixtures.py) links each `examples/<name>/godot/*.{tscn,gd}` flat into `res://examples/<name>/`, dropping the `godot/` subdir at the destination - its own `_link_wrappers` docstring states the convention is "the wrapper TSCNs reference `res://<name>/<Name>.gd` (root, not `res://<name>/godot/<Name>.gd`)". Every committed wrapper violates that: `SlotCycle.tscn`, `AtlasPack.tscn`, and the new `MixedFeature.tscn` all carry `[ext_resource ... path="res://examples/<name>/godot/<Name>.gd"]`. After the sync flattens, that path has no file, so the wrapper scene loads with a missing-dependency error (the "Load failed due to missing dependencies: MixedFeature.gd" dialog). The fix is one of two shapes: rewrite every wrapper's script `ext_resource` to the flat path (the instanced `.proscenio` `ext_resource` is already flat and correct), or change the sync to preserve `godot/`. The flat path is the documented intent, so the wrappers are what is wrong.

**2. Imported examples render every sprite blank.** Opening any synced fixture in the editor shows white `Polygon2D` / `Sprite2D` nodes with no texture (confirmed on `atlas_pack` and `mixed_feature`). The `.proscenio` data is not at fault: a headless build that mirrors `importer.gd` (load the atlas via `ResourceLoader`, pass it to the builders) applies every texture (`TEX=true` on all four elements, atlas 128x128 resolves, geometry + regions correct). The gap is at editor-import time: [importer.gd](../../apps/godot/addons/proscenio/importer.gd) `_import` bakes the `.scn` and resolves the atlas / per-sprite PNG through `ResourceLoader.load` against the sibling file. When the `.proscenio` imports before its sibling image has been imported, the load returns null and the baked scene carries no texture. The plugin is enabled in `apps/godot` (`project.godot` `editor_plugins`), so this is ordering / dependency declaration, not a disabled importer. [backlog-manual-testing.md](../backlog-manual-testing.md) (section 2.x) records this exact flow passing earlier on `SlotSwap.tscn` (F6 play, textures), so it regressed - candidates: the sync flatten landing after that validation, a Godot 4.6.x import-order change, or a latent ordering bug now manifesting on the larger example set.

**3. Bones export edge-on, so Godot rests them sideways.** The fixture build scripts author bones with the tail along world -Y (the "2D-cutout" convention the existing scripts document). [skeleton.py](../../apps/blender/exporters/godot/writer/skeleton.py) projects bone direction with `godot_world_angle_from_dir = atan2(-dir.z, dir.x)`; a tail pointing purely -Y has `dir.z == dir.x == 0`, so the angle is 0 and the bone length rides `bone.length` (the projection would otherwise collapse to zero). Godot then rests every `Bone2D` at its default +X, which reads as a sideways / flattened rig. This matches the hand-authored `skinned_dummy` fixture (all bones `rotation: 0`), so +X is the current format convention, not a writer bug. The tension is that a vertical character rig should point its spine up (Godot rotation -90, which the writer only emits from a +Z tail), and [shared_atlas](../../packages/fixtures/shared_atlas/build_blend.py) documents that a +Z tail "collapses each polygon to a line on import" for rigid (`parent_bone`) meshes. A skinned mesh parents to the skeleton rather than a bone, so it may not hit that collapse - but the rigid mouth in the mixed fixture does. This is a convention decision with a writer-limitation tradeoff, not a one-line fix.

**4. The Godot builders are tested only against hand-authored input.** [test_importer.gd](../../apps/godot/tests/test_importer.gd) loads four hand-authored `.proscenio` fixtures (`dummy`, `effect`, `skinned_dummy`, `slots_demo`) plus a committed copy of the mixed-feature golden. None of the eight Blender-baked goldens under `examples/generated/` reach the Godot builders - they are exercised only by `test-blender`'s re-export diff. So the Godot side is validated against JSON written by hand, never against real writer output, which is how the edge-on skinned-bone export went unnoticed: the hand-authored `skinned_dummy` sets bone rotations the writer never produces, so "skinning passes" while the real Blender-to-Godot skinned path was never built and looked at. The hand-authored fixtures earn a narrow keep as isolated unit inputs (no Blender in `test-godot`, pinned values, fast), but using them as the only coverage buys end-to-end confidence the suite has not earned, and the committed golden copy drifts from its source.

### Assessment

Scores 1-5. Flow value: size x likelihood of the class of breakage the work removes (5 = every example is unusable). Test burden: cost to build plus recurring cost. Bug surface: complexity the change itself adds. Underuse risk: 5 = the fix protects nothing real.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| wrapper-script-path | 4 | 1 | 1 | 1 | now | Every wrapper scene fails to load against the documented flat convention; a path rewrite (or a one-line sync change) is near-free and unblocks opening any example. |
| texture-import-ordering | 5 | 3 | 2 | 1 | now | Every imported example renders blank - the headline defect. The data is proven correct, so the work is scoped to the editor-import path (dependency declaration / import order / a reimport pass). |
| bone-screen-orientation | 3 | 3 | 2 | 3 | gate | The exported bones are correct per the current convention (they match the hand-authored skinned oracle); the change is a deliberate convention shift that tangles with the documented +Z rigid-mesh collapse, so it waits on an explicit decision (below) and likely a writer follow-up. |
| godot-tests-consume-goldens | 4 | 2 | 1 | 1 | now | Point `test-godot` at the real Blender-baked goldens so the builders run against writer output, and shrink the hand-authored set to the genuine edge cases the goldens do not cover. Closes the end-to-end gap on the Godot side and removes the golden-copy drift. |

### Verdict summary

Counts: **3 now, 1 gate, 0 drop**. The `now` items are what make examples openable, visible, and tested against real writer output; the bone-orientation item is real but is a convention decision, not a defect, and is gated on the choice below plus the writer work it implies.

### Bone-orientation decision (gate trigger)

The gate opens when one of these is chosen:

- **Keep +X (status quo).** Bones rest sideways but stay consistent with the `skinned_dummy` oracle and the rigid-mesh `parent_bone` path that ships today. No writer change. Document the convention so the next reader does not read it as a bug. Lowest risk; leaves the rig visually unintuitive.
- **Author bones in the screen plane.** Give bones a real in-plane direction (tail along +Z for an "up" spine) so Godot rests them anatomically. Requires resolving the +Z "collapses polygons" limitation in the writer for rigid meshes first, or restricting screen-plane tails to skinned bones only (mixed rigs then carry two conventions). Higher value, real writer work.
- **Normalize at export.** Leave Blender authoring as -Y tails but have the writer derive a sensible 2D rest (e.g. from the parent->child chain direction) instead of the camera-axis projection. Keeps authoring simple, moves the cost into `skeleton.py`, and needs a round-trip check against every existing golden.
