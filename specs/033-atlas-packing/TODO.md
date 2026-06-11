# Spec 033: Atlas packing - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): the PPU loop closes first (the spec's only w1 rows), then the Unpack rename rescue, then padding quality, pack-scope clarity, and the export-closure pair. Three items wait behind triggers, one defers onto the next packer change, three are pruned.

## Now

### PR 1: seed the exporter PPU from the imported manifest

- [x] In [import-flow.ts](../../apps/photoshop/src/api/import-flow.ts), read `pixels_per_unit` from the validated manifest and seed the persisted exporter value ([usePixelsPerUnit.ts](../../apps/photoshop/src/hooks/usePixelsPerUnit.ts)) so a re-export emits the imported PPU instead of whatever the input last held.
- [x] Vitest: import a manifest with a non-default PPU and assert the next export plan stamps the same value through [planner.ts](../../apps/photoshop/src/lib/planner.ts); the `DEFAULT_PIXELS_PER_UNIT` fallback in [manifest.ts](../../apps/photoshop/src/lib/manifest.ts) stays for fresh documents.
- [x] Note in the PR: this edits the photoshop-plugin spec's surface (different files, no conflict), and the 10x-scale waiver re-measures against this fix in the verification session.

### PR 2: sync and show the scene PPU on the Blender side

- [x] Sync the scene `Pixels per unit` property ([scene_props.py](../../apps/blender/properties/scene_props.py)) from `manifest.pixels_per_unit` during PSD import ([importers/photoshop/\_\_init\_\_.py](../../apps/blender/importers/photoshop/__init__.py)) so an import at 1000 no longer exports at the untouched default 100.
- [x] Add a PPU readout row to the **Atlas** panel ([atlas.py](../../apps/blender/panels/atlas.py)) so the value is visible outside the **Export** subpanel ([pipeline.py](../../apps/blender/panels/pipeline.py)).
- [x] Headless test: import a fixture manifest with a non-default PPU and assert the scene property synced.

### PR 3: rescue Unpack across material renames and document the limit

- [x] Stamp a marker Custom Property on the material at Apply ([apply.py](../../apps/blender/operators/atlas_pack/apply.py)) and give Unpack a rescue scan over materials when the by-name lookup misses ([unpack.py](../../apps/blender/operators/atlas_pack/unpack.py)).
- [x] Add the rename caveat to the atlas help topic ([help_topics.py](../../apps/blender/core/help_topics.py)), documenting the residual material-identity-by-name edge the marker cannot cover.
- [x] Headless test: Apply, rename the material, Unpack, assert the original material restores through the marker.
- [x] Note in the PR: the pointer-based `PropertyGroup` snapshot variant stays with the storage-split spec.

### PR 4: edge-extend the atlas padding ring

- [x] Replace the transparent padding ring with edge-extended border pixels in [atlas_compose.py](../../apps/blender/core/bpy_helpers/atlas/atlas_compose.py), per the plan already noted in the [atlas_packer.py](../../apps/blender/core/atlas/atlas_packer.py) docstring - NumPy-local, default-on, no new UI knob.
- [x] Cover the composed ring in tests (the pure packer suite lives at [test_atlas_packer.py](../../tests/test_atlas_packer.py); the compose assertion goes wherever the compose path is exercised headless), asserting ring pixels repeat the sprite border instead of staying transparent.

### PR 5: pack-scope control and pack-state clarity in the Atlas panel

- [x] Differentiate the **Atlas** panel header label ([atlas.py](../../apps/blender/panels/atlas.py)) between a discovered source image and the packed atlas.
- [x] Add an exclude-from-atlas flag ([object_props.py](../../apps/blender/properties/object_props.py)) honored by `Pack Atlas` ([pack.py](../../apps/blender/operators/atlas_pack/pack.py)) so a flagged sprite keeps its own texture - the writer already carries per-sprite textures.
- [x] Headless tests: pack with one excluded mesh, assert its material stays untouched and the atlas omits its pixels.

### PR 6: validate sprite_frame UV covers the full sheet

- [x] Add the pure UV-bounds check to [export.py](../../apps/blender/core/validation/export.py), warning when a `sprite_frame` mesh's UVs do not span the full sheet - a hand-shrunk quad garbles the `hframes`/`vframes` grid silently in Godot.
- [x] Sequence after the export-correctness validator fixes land to avoid rebasing across them (see [EXECUTION_MAP.md](../EXECUTION_MAP.md)).
- [x] Unit tests beside the existing atlas file-path checks.

### PR 7: export bundle gathers the textures

- [x] Add a bundle option to the export flow that copies every referenced texture next to the `.proscenio` - the writer already walks them in [sprites.py](../../apps/blender/exporters/godot/writer/sprites.py) - closing the manual gather every PSD-sourced export needs today (`images/` and `_spritesheets/` subfolders vs the Godot importer's siblings-only resolution).
- [x] Headless test: export a PSD-imported scene with the bundle option, assert the textures land beside the file and every manifest reference resolves.

## Deferred

Gate items wait for their trigger; the defer item rides a future PR.

- **Per-asset pixels-per-unit** - gate; trigger: the mixed-PPU case recurs on a real project after uniform-PPU normalization is rejected; cost is a per-layer schema field plus importer scaling plus per-mesh world-size emission across three tools.
- **Per-object pack/unpack state** - gate; trigger: multi-atlas pages ship (schema-expressiveness spec) or a manual session logs hybrid pack-state confusion against today's single shared atlas.
- **Atlas region helper (snap UV by name)** - gate; trigger: a manual-testing session logs UV-snap friction during atlas region authoring.
- **Shrink-to-fit / configurable start size** - defer; fold the `start_size` floor change into the next packer-touching PR so the fixture regen is shared.

## Dropped

- **Strip whitespace** - sources already arrive trimmed (UXP trim plus UV-bounds slices), no offset channel exists to compensate the geometry shift, and stripping would corrupt sprite_frame full-sheet grids.
- **Rotation** - Godot cannot consume rotated atlas regions, so rotation is a Polygon2D-only footgun bought for marginal density.
- **MaxRects multiple heuristics** - BSSF is already the strongest single heuristic; trying them all buys low single-digit density at multiplied pack time.
