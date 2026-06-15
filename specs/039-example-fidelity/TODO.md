# Spec 039: Example pipeline fidelity - TODO

Sequenced from the verdicts in [STUDY.md](STUDY.md): two defects that make every synced example fail to open or render blank land now; the bone-orientation convention waits on an explicit decision. Surfaced by the spec 035 mixed-feature fixture; the fixture itself is correct per the current convention, so it ships independently of this repair.

## Resolution log (jun 2026 grind)

Worked on branch `feat/spec-039-example-fidelity` with full Blender + Godot headless access (renders for visual proof).

- **DONE - bone-orientation convention (was the gate).** Final convention: bones lie **in the XZ picture plane** (tail +Z up, or +X lateral), never into depth. Cutouts are **not bone-parented** (that tilts a flat mesh out of plane and collapses it on import) - static stamps are object-parented, meshes that follow a bone are skinned, invisible driver bones spin about their own axis (read via ROT_Z). An earlier pass in this grind wrongly used +Y depth bones; the user corrected it. All eight fixtures re-authored, goldens re-baked (8/8 export diff + 102 operator tests pass), README convention rewritten. Commits `ad35585` (static stamps), `47528bc` (writer support), `b8e680f` (animated fixtures).
- **DONE - PR 1 wrapper script paths.** All `examples/generated/**/godot/<Name>.tscn` rewritten to the flat `res://examples/<name>/<Name>.gd`; sync docstring fixed; verified wrappers load in Godot headless. Commit `84fcd78`.
- **DONE - PR 2 texture import ordering.** `importer.gd` ran at import order 0 (same as textures), so the `.scn` could bake before its sibling PNGs imported -> blank textures. Raised to order 100 (after textures). Confirmed in the editor: every fixture textures correctly on a clean reimport. Commit `edae17b`.
- **DONE - skinned Polygon2D Godot render.** Root cause found with a standalone probe: a skinned `Polygon2D` added as a *child* of the `Skeleton2D` collapses (Godot double-applies the skeleton transform); it must be a **sibling**. Fixed in `mesh_builder.gd`; the writer also bakes skinned-mesh polygons in absolute (skeleton) space. mixed_feature's torso + slot_swap's arm now render and deform. Commit `be47915`, `47528bc`.
- **DONE - rest-pose geometry bake.** `build_element` baked geometry at whatever posed frame the .blend was saved on; geometry on an animated bone double-applied the pose. Now detaches the action + zeroes pose to read rest. Commit `be47915`.
- **DONE - sprite region scaling + animation-builder generalization.** `sprite_builder.gd` now scales the normalized `texture_region` by the texture size; the animation builder derives screen rotation from the bone's rest matrix (supports in-plane bones, not just +Y). Commits `939c3cf`, `47528bc`.
- **DONE - mixed_feature recreation + shared_atlas spread.** mixed_feature is a coherent figure (skinned torso + face slot + driven mouth); shared_atlas's three meshes spread along +X. Blender == Godot verified by headless render.
- **OPEN - PR 3 test-godot consumes goldens.** Not started. A `.scratch/render_proof.gd` runtime harness (loads a golden, runs the builders, renders a PNG) was used throughout this grind and can seed it.
- **Deferred polish** (not blocking, noted in [backlog-bugs-found.md](../backlog-bugs-found.md)): multi-frame sprites cannot pixel-match Blender vs Godot by design (bounds match, not pixels); a slot whose attachments should *follow* a bone needs a slot-bone property so the Empty can be object-parented (flat) yet route under the Bone2D - today slot_swap's weapon is object-parented at the hand (static) while the arm swings.

## Now

### PR 1: fix the wrapper script paths across every example

- [ ] Rewrite each `examples/generated/**/godot/<Name>.tscn` `ext_resource` script path from `res://examples/<name>/godot/<Name>.gd` to the flat `res://examples/<name>/<Name>.gd` - the convention [sync_fixtures.py](../../scripts/godot/sync_fixtures.py) `_link_wrappers` documents and the layout it actually produces (the instanced `.proscenio` path is already flat and stays). Sweep all wrappers (`slot_cycle`, `slot_swap`, `atlas_pack`, `blink_eyes`, `mouth_drive`, `shared_atlas`, `simple_psd`, `mixed_feature`).
- [ ] Verify headless: run `python scripts/godot/sync_fixtures.py`, then script a load of each `res://examples/<name>/<Name>.tscn` (a bare `godot --headless --quit` only opens the project, it never loads the wrapper scenes, so it cannot surface the missing-dependency) and confirm zero "Load failed due to missing dependencies" for the wrapper scripts.

### PR 2: make imported examples render their textures

- [ ] Diagnose the editor-import path: reproduce the blank render on a clean reimport, and determine whether [importer.gd](../../apps/godot/addons/proscenio/importer.gd) `_import` bakes the `.scn` before the sibling atlas / per-sprite PNG is imported (so `ResourceLoader.load` returns null), and whether the importer declares those images as dependencies at all.
- [ ] Fix the ordering: declare each referenced image as an import dependency so Godot imports it first and reimports the `.proscenio` when it changes (or raise `_get_import_order`, or add an explicit reimport pass). Confirm against the earlier passing `SlotSwap` validation in [manual-testing.md](../manual-testing.md) (section 2.x) to pin what regressed.
- [ ] Verify in the editor: open `atlas_pack`, `mixed_feature`, and one PSD-sourced fixture in the `apps/godot` dev project after a clean reimport; every `Polygon2D` / `Sprite2D` shows its atlas region textured, none white.

### PR 3: test-godot builds against the real baked goldens

- [ ] Drive the Godot smoke test from the Blender-baked goldens (`examples/generated/**/*.expected.proscenio`) instead of hand-authored copies: run `sync_fixtures.py` in the `test-godot` CI job to populate `apps/godot/examples/`, then have [test_importer.gd](../../apps/godot/tests/test_importer.gd) (or a sibling pass) walk the synced goldens and assert the builders produce a sane node tree (counts, kinds, weights, slots, tracks). This is the coverage that exercises the writer-to-builder path end to end.
- [ ] Audit the four hand-authored fixtures (`dummy`, `effect`, `skinned_dummy`, `slots_demo`): keep only the genuine edge cases the baked goldens do not already cover (e.g. `effect`'s sprite-appearance flags), drop or convert the rest, and retire the committed `tests/fixtures/mixed_feature.proscenio` copy in favor of its synced golden.
- [ ] Note in the PR: a headless assert still cannot catch a visually-wrong-but-structurally-consistent export (the edge-on bones are rotation 0 on both sides); this item closes the drift and the builds-against-real-output gap, not the visual-convention gap - that stays with the bone-orientation item.

## Deferred

Gate item; lands when its trigger fires.

- **bone-screen-orientation - RESOLVED (jun 2026, see Resolution log).** The grind proved the real defect was not "bones rest sideways" but the -Y tail mirroring every bone-parented cutout 180deg about Z. Decision: bone-parented cutouts author **+Y** tails (un-flipped, in-plane, camera-facing); skinned meshes keep in-plane bones. No writer change was needed - the fix is in fixture authoring + the documented convention. Original options preserved below for history.
- **bone-screen-orientation (original framing)** - trigger: an explicit choice among the three options in [STUDY.md](STUDY.md) (keep +X / screen-plane tails / normalize at export). The exported bones are correct per the current convention (they match the hand-authored `skinned_dummy` oracle), so this is a deliberate convention shift rather than a defect, and the screen-plane / normalize options pull writer work behind them (the documented +Z rigid-mesh "collapses polygons" limitation). Sequence the writer change ahead of re-baking every fixture golden so the bake happens once. Related: the [flat-fixture-buckets](../035-project-health/TODO.md) move touches the same wrapper / sync surface, so fold the two if they land together.
