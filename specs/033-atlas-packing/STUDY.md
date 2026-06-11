# Spec 033: Atlas packing

Improve atlas authoring and packing, and thread pixels-per-unit through the whole pipeline.

## Scope

- **Pixels-per-unit end to end** - per-asset PPU, a readout in the atlas panel, and PPU round-tripped through Photoshop.
- **Fix Unpack restoration** breaking silently when a material was renamed.
- **Packing controls** - strip whitespace, edge padding, rotation.
- **Clarify discovered-source vs packed-atlas** label.
- **Per-object pack/unpack state** visibility.
- **Document the material-identity-by-name** limitation.
- **Atlas region helper** - snap UV by name.
- **Exclude chosen sprites** from the shared atlas pack.
- **Validate sprite_frame UV** covers the full sheet.
- **Export bundle** - gather the `.proscenio` and its textures into one folder.
- **MaxRects multiple heuristics** for denser packing.
- **Shrink-to-fit / configurable start size**.

## Study

### Surface notes

- PPU is one scene-global `FloatProperty` (`properties/scene_props.py:398`, default 100) surfaced only on the **Export** subpanel (`panels/pipeline.py:89`). The PSD importer sizes every mesh by `manifest.pixels_per_unit` (`importers/photoshop/planes.py`, `__init__.py:114`) but never syncs that value into the scene prop, so an import at PPU 1000 followed by an export at the untouched scene default 100 silently mismatches scale.
- On the Photoshop side the UXP exporter already has a PPU numeric input persisted via localStorage (`hooks/usePixelsPerUnit.ts`, `panels/sections/ExportSection.tsx`), and the planner stamps it into the manifest (`lib/planner.ts:137`, fallback `DEFAULT_PIXELS_PER_UNIT = 100` in `lib/manifest.ts:18`). The import flow receives the validated manifest but never reads `pixels_per_unit` (`api/import-flow.ts`), so a re-export after import emits whatever the input last held - the logged 10x-scale waiver. Seeding the exporter PPU at import time closes the loop without the JSX-era XMP plan.
- Per-asset PPU has no schema field: the PSD manifest carries one document-level `pixels_per_unit` (`schema_bindings/psd_manifest.ts:119`), and `.proscenio` one root field (`writer/__init__.py:138`). The per-asset variant means a per-layer schema field plus importer scaling plus per-mesh world-size emission - three tools and a schema bump.
- The packer is pure Python MaxRects-BSSF (`core/atlas/atlas_packer.py`), unit-tested at `tests/test_atlas_packer.py`. Padding reserves a ring per placement that composing leaves transparent (`atlas_packer.py:17-21`, `core/bpy_helpers/atlas/atlas_compose.py:65`); the docstring already plans "edge-extend can be added later". `start_size=256` (`atlas_packer.py:65`) is never passed by the pack operator and has no scene prop.
- `collect_source_images` packs each mesh's UV-bounds slice, not the whole source image (`core/bpy_helpers/atlas/atlas_collect.py:62`), and the UXP png-writer trims every exported PNG to visible pixels (`api/png-writer.ts:71`). So sources entering the packer are already tight for both the PSD path and shared-atlas sub-regions; a whitespace-strip pass would only act on hand-loaded untrimmed PNGs and would corrupt `sprite_frame` full-sheet slices, whose grid must survive intact.
- `Pack Atlas` packs every textured mesh unconditionally (`operators/atlas_pack/pack.py:50`); the only related control is `material_isolated` (`properties/object_props.py:157`), which still points the isolated material at the atlas image (`apply.py:238-239`). There is no opt-out flag that keeps a sprite's own texture.
- The Unpack rename bug is half-fixed: `unpack.py:95-104` now warns and summarizes partial restores, but the snapshot still stores the material by name (`apply.py:110`), so a rename between Apply and Unpack still loses the original. The pointer-based `PropertyGroup` snapshot belongs with the storage split; a marker Custom Property stamped on the material at Apply gives Unpack a rescue scan without that refactor.
- The **Atlas** panel header shows one undifferentiated image label (`panels/atlas.py:32-36`) whether it found a discovered source or the packed atlas, and the `Unpack Atlas` button keys off a scene-wide snapshot check (`atlas.py:59`). The atlas help topic (`core/help_topics.py:203-227`) has no rename caveat.
- UV authoring ships `proscenio.reproject_sprite_uv` and `proscenio.snap_region_to_uv` only (`operators/uv_authoring.py`); no snap-UV-to-atlas-region-by-name operator exists.
- The `.proscenio` references textures by bare filename and the Godot importer resolves siblings only, while PSD-import assets live in `images/` and `_spritesheets/` subfolders - every PSD-sourced export currently needs a manual gather before Godot import. The writer already knows every referenced image (`writer/sprites.py:142-154`), so a copy-into-bundle option is contained on the Blender side.
- Validation already walks atlas file paths (`core/validation/export.py:93`); a sprite_frame full-sheet UV-bounds check slots into the same pure-function pattern.

### Research notes

- TexturePacker docs (CodeAndWeb): extrude repeats a sprite's border pixels to kill transparent gaps and dark halos at edges under bilinear filtering; padding plus alpha bleed are the artifact-prevention pair.
- libGDX TexturePacker defaults: `paddingX/Y: 2`, `edgePadding: true`, `bleed: true` - edge treatment is on by default in the mainstream packers, confirming it as table stakes rather than a tuning option.
- Spine texture-packer guide: padding 2 recommended because "texture filtering averages neighboring pixels"; whitespace strip is default-on there but only works because the Spine atlas format stores trim offsets the runtime re-applies - Proscenio's Apply rewrites mesh UVs directly with no offset channel, so stripping would shift geometry.
- TexturePacker Godot plugin and the community atlas importers: Godot does not support rotated atlas regions (`AtlasTexture` / `region_rect` have no rotation), and the TexturePacker-for-Godot guidance is to disable rotation outright.
- MaxRects comparisons (Jylanki 2010 "A Thousand Ways to Pack the Bin"; published occupancy figures): BSSF is the strongest single heuristic (~94% occupancy vs ~91% for BL in one comparative set); trying all heuristics buys low single-digit density at multiplied pack time.
- Unity PPU guidance (manual + pixel-perfect docs): default 100; the stated best practice is the same PPU across all sprites, because mixed PPU renders same-size art at different world sizes - the per-asset divergence is a normalization problem, not the norm.

### Assessment

Flow value 5 = core flow; test burden 1 = pure unit, 5 = recurring manual GUI; bug surface 1 = bugfix, 5 = new modal/stateful; underuse risk 1 = universal, 5 = speculative. The PPU bullet splits into its three rows (one concept, three tools - this spec owns the cluster per the execution map) and the packing-controls bullet splits into its three controls, since their verdicts diverge.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| ppu-roundtrip | 5 | 1 | 1 | 1 | now | Import flow already holds the manifest; seeding the exporter PPU kills the 10x-scale waiver; vitest-only change. |
| ppu-visibility | 4 | 2 | 1 | 1 | now | Syncing scene PPU at PSD import kills the silent import/export mismatch; the panel readout is one label row. |
| per-asset-ppu | 3 | 4 | 4 | 4 | gate | Schema bump + three tools for a workflow the engine-side practice avoids (uniform PPU); wait for the mixed-PPU case to recur for real. |
| unpack-material-rename | 3 | 2 | 2 | 1 | now | Warn already shipped; a marker-CP rescue scan completes the bug without the PG storage refactor (that half stays with the storage split). |
| packing-controls: edge padding | 4 | 2 | 2 | 1 | now | Transparent padding ring = halo seams under bilinear; default-on in every mainstream packer; NumPy-local, no new UI knob. |
| packing-controls: strip whitespace | 1 | 3 | 3 | 4 | drop | Sources arrive pre-trimmed (UXP trim + UV-bounds slices); no offset channel to compensate; would corrupt sprite_frame grids. |
| packing-controls: rotation | 1 | 3 | 4 | 5 | drop | Godot cannot consume rotated regions; a Polygon2D-only capability is a mixed-support footgun for marginal density. |
| discovered-vs-packed-label | 3 | 2 | 1 | 1 | now | One conditional label removes a real state ambiguity in the core pack flow. |
| per-object-pack-state | 2 | 4 | 3 | 4 | gate | New stateful UI surface against today's single-shared-atlas reality; wait for multi-atlas pages or a logged hybrid confusion. |
| document-material-identity | 3 | 1 | 1 | 1 | now | Help-topic text only; documents the residual rename edge left after the marker rescue. |
| atlas-region-helper | 2 | 4 | 3 | 4 | gate | Authoring operator for a workflow with no logged friction; wait for a manual-testing report. |
| exclude-from-atlas | 4 | 2 | 2 | 2 | now | Flag plus pack filter; the writer already carries per-sprite textures; protects the shared atlas from spritesheet bloat. |
| validate-spriteframe-uv | 4 | 1 | 1 | 1 | now | Pure validation unit guarding a silent grid-garble in Godot; fits the existing atlas checks. |
| export-bundle | 4 | 2 | 2 | 2 | now | PSD-import subfolders guarantee the missing-texture failure today; the bundle option closes the last manual step of the core flow. |
| maxrects-heuristics | 1 | 2 | 2 | 5 | drop | BSSF is already the strongest single heuristic; multi-heuristic re-packs buy a few percent nobody sees at this scale. |
| shrink-start-size | 2 | 2 | 2 | 3 | defer | Waste is real only at fixture scale; fold the 256-floor change into the next packer-touching PR to share the fixture regen. |

### Verdict summary

- **Now (9):** ppu-roundtrip, ppu-visibility, unpack-material-rename (marker rescue), edge padding, discovered-vs-packed-label, document-material-identity, exclude-from-atlas, validate-spriteframe-uv, export-bundle.
- **Gate (3):** per-asset-ppu, per-object-pack-state, atlas-region-helper - triggers written in [TODO.md](TODO.md).
- **Defer (1):** shrink-start-size - piggyback on the next packer change.
- **Drop (3):** strip whitespace, rotation, maxrects-heuristics - propose pruning from the backlog.
- The PPU cluster stays now in its document-level form: the Photoshop seed plus the Blender sync are small, mostly unit-tested changes, and Godot already consumes the root field unchanged. Only the per-asset extension gates.
- Cross-spec: validate-spriteframe-uv lands in `core/validation` - rebase after the export-correctness validator fixes; the ppu-roundtrip chunk edits `apps/photoshop` (the photoshop-plugin spec's surface, different files, no conflict); the pointer-based snapshot variant of the Unpack fix defers into the storage-split spec.
