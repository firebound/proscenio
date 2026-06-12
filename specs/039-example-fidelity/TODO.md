# Spec 039: Example pipeline fidelity - TODO

Sequenced from the verdicts in [STUDY.md](STUDY.md): two defects that make every synced example fail to open or render blank land now; the bone-orientation convention waits on an explicit decision. Surfaced by the spec 035 mixed-feature fixture; the fixture itself is correct per the current convention, so it ships independently of this repair.

## Now

### PR 1: fix the wrapper script paths across every example

- [ ] Rewrite each `examples/generated/**/godot/<Name>.tscn` `ext_resource` script path from `res://examples/<name>/godot/<Name>.gd` to the flat `res://examples/<name>/<Name>.gd` - the convention [sync_fixtures.py](../../scripts/godot/sync_fixtures.py) `_link_wrappers` documents and the layout it actually produces (the instanced `.proscenio` path is already flat and stays). Sweep all wrappers (`slot_cycle`, `slot_swap`, `atlas_pack`, `blink_eyes`, `mouth_drive`, `shared_atlas`, `simple_psd`, `mixed_feature`).
- [ ] Verify headless: run `python scripts/godot/sync_fixtures.py`, then script a load of each `res://examples/<name>/<Name>.tscn` (a bare `godot --headless --quit` only opens the project, it never loads the wrapper scenes, so it cannot surface the missing-dependency) and confirm zero "Load failed due to missing dependencies" for the wrapper scripts.

### PR 2: make imported examples render their textures

- [ ] Diagnose the editor-import path: reproduce the blank render on a clean reimport, and determine whether [importer.gd](../../apps/godot/addons/proscenio/importer.gd) `_import` bakes the `.scn` before the sibling atlas / per-sprite PNG is imported (so `ResourceLoader.load` returns null), and whether the importer declares those images as dependencies at all.
- [ ] Fix the ordering: declare each referenced image as an import dependency so Godot imports it first and reimports the `.proscenio` when it changes (or raise `_get_import_order`, or add an explicit reimport pass). Confirm against the earlier passing `SlotSwap` validation in [backlog-manual-testing.md](../backlog-manual-testing.md) (section 2.x) to pin what regressed.
- [ ] Verify in the editor: open `atlas_pack`, `mixed_feature`, and one PSD-sourced fixture in the `apps/godot` dev project after a clean reimport; every `Polygon2D` / `Sprite2D` shows its atlas region textured, none white.

### PR 3: test-godot builds against the real baked goldens

- [ ] Drive the Godot smoke test from the Blender-baked goldens (`examples/generated/**/*.expected.proscenio`) instead of hand-authored copies: run `sync_fixtures.py` in the `test-godot` CI job to populate `apps/godot/examples/`, then have [test_importer.gd](../../apps/godot/tests/test_importer.gd) (or a sibling pass) walk the synced goldens and assert the builders produce a sane node tree (counts, kinds, weights, slots, tracks). This is the coverage that exercises the writer-to-builder path end to end.
- [ ] Audit the four hand-authored fixtures (`dummy`, `effect`, `skinned_dummy`, `slots_demo`): keep only the genuine edge cases the baked goldens do not already cover (e.g. `effect`'s sprite-appearance flags), drop or convert the rest, and retire the committed `tests/fixtures/mixed_feature.proscenio` copy in favor of its synced golden.
- [ ] Note in the PR: a headless assert still cannot catch a visually-wrong-but-structurally-consistent export (the edge-on bones are rotation 0 on both sides); this item closes the drift and the builds-against-real-output gap, not the visual-convention gap - that stays with the bone-orientation item.

## Deferred

Gate item; lands when its trigger fires.

- **bone-screen-orientation** - trigger: an explicit choice among the three options in [STUDY.md](STUDY.md) (keep +X / screen-plane tails / normalize at export). The exported bones are correct per the current convention (they match the hand-authored `skinned_dummy` oracle), so this is a deliberate convention shift rather than a defect, and the screen-plane / normalize options pull writer work behind them (the documented +Z rigid-mesh "collapses polygons" limitation). Sequence the writer change ahead of re-baking every fixture golden so the bake happens once. Related: the [flat-fixture-buckets](../035-project-health/TODO.md) move touches the same wrapper / sync surface, so fold the two if they land together.
