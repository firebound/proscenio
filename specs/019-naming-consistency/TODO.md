# Naming consistency: the Element vocabulary - TODO

See [STUDY.md](STUDY.md) for the evaluation and decisions D1-D10 (umbrella `Element`; two kinds `mesh` -> `Polygon2D` and `sprite` -> `Sprite2D`; full wire rename, both schemas land at `format_version: 1`, no bump).

Producer-to-consumer phasing: the shape change crosses all components at once, so Phase 0 (models + codegen + fixtures) merges first and the apps adopt against the regenerated bindings. Each later phase is one PR proven by that component's gate. The guard rails are static: ruff / mypy / tsc / gdlint flag every undefined name a rename leaves behind, so only the Active Element panel draw needs a Blender smoke test.

## Status - scope-complete pending #100

The wire rename shipped across all layers (models `MeshElement` / `SpriteElement` / `elements[]`, the `element_type` enum, the Godot bindings + builders, the Photoshop tag parser, the writer emitting `elements[]`) and is proven by the Godot importer smoke (50 assertions). #100 finishes the rest: the fixture builders + the stale `sprites[]` comments; the `core/sprite_frame/` package renamed to `core/spritesheet/` (the glossary term - the modules do spritesheet UV cell-slicing, not general sprite ops); and the full internal element-vocab sweep (the writer dispatcher `build_sprite` -> `build_element`, the sprite emitter -> `build_sprite`, the atlas `_apply_sprite_frame` -> `_apply_sprite`, plus help text + docstrings). Kept by design (D6 preserves the `frame` concept): the frame-preview operator idnames, the `sprite_frame` animation-track references, and the persisted `Proscenio.SpriteFrameSlicer` datablock. The only leftover is the validator package's internal `report.sprites` / `SpritePayload` naming, which was never a 019 target (the validator sits outside the Phase 1-4 scope) and stays as a standalone backlog item. Nothing in-scope open; delete this spec once #100 merges.

## Decision lock-in

- [x] D1 - umbrella term `Element` (`sprites[]` -> `elements[]`, "Active Sprite" -> "Active Element", `sprite_type` -> `element_type`).
- [x] D2 - two kinds named for their Godot node: `mesh` -> `Polygon2D`, `sprite` -> `Sprite2D`.
- [x] D3 - full wire rename (the JSON shape changes, not just UI labels).
- [x] D4 - collapse PSD `polygon` + `mesh` into one `mesh` kind; `[mesh]`/`[poly]`/`[polygon]` all map to it.
- [x] D5 - `[sprite]` on a single layer = 1-frame sprite; `frames` relaxes to `min_length=1`.
- [x] D6 - no-rename guard: `Polygon2D`/`Sprite2D` (engine), the geometry field `polygon`, and `hframes`/`vframes`/`frame`/`centered`/`texture_region` keep their names.
- [x] D7 - no migration code; shapes change in place, fixtures regenerate from source.
- [x] D8 - producer-first phasing; the Phase 0 PR is the cross-cutting shape change.
- [x] D9 - glossary is the canonical term home.
- [x] D10 - freeze-at-launch versioning; both schemas at `format_version: 1`.

## Phase 0 - models + codegen + fixtures + the versioning decision

- [x] Revise the [`../decisions.md`](../decisions.md) "Schemas are the contract" entry to scope bump-plus-migration to post-launch (D10). (Done at planning time.)
- [ ] `packages/models/src/proscenio_models/proscenio.py`: `PolygonSprite` -> `MeshElement` (`type: Literal["polygon"]` -> `Literal["mesh"]`); `SpriteFrameSprite` -> `SpriteElement` (`type: Literal["sprite_frame"]` -> `Literal["sprite"]`); `_sprite_discriminator` -> `_element_discriminator` (tags `{mesh, sprite}`, default `"mesh"`); `Sprite` alias -> `Element`; `ProscenioDocument.sprites` -> `elements`. Keep `format_version: Literal[1]`. Keep the geometry field `polygon: list[Vec2]` on `MeshElement` (D6). Rewrite the docstrings that say "Sprite is a discriminated union" / "polygon variant".
- [ ] `packages/models/src/proscenio_models/psd_manifest.py`: `PolygonLayer` -> `MeshLayer` (`kind: Literal["polygon", "mesh"]` -> `Literal["mesh"]`); `SpriteFrameLayer` -> `SpriteLayer` (`kind: "sprite_frame"` -> `"sprite"`, `frames` `min_length=2` -> `1`); `_layer_discriminator` tags `{mesh, sprite}`; `format_version: Literal[2]` -> `Literal[1]` (collapse). Rewrite the module docstring (drop the `enum: ["polygon", "mesh"]` / `kind: "mesh"` variant prose).
- [ ] Re-run `proscenio_codegen` to regenerate every binding: TS at `apps/photoshop/src/schema_bindings/` (`proscenio.ts`, `psd_manifest.ts`), GDScript at `apps/godot/addons/proscenio/schema_bindings/` (rename `proscenio_polygon_sprite.gd` -> `proscenio_mesh_element.gd`, `proscenio_sprite_frame_sprite.gd` -> `proscenio_sprite_element.gd`, `proscenio_polygon_layer.gd` -> `proscenio_mesh_layer.gd`, `proscenio_sprite_frame_layer.gd` -> `proscenio_sprite_layer.gd`, `proscenio_sprite.gd` -> `proscenio_element.gd`, regen `proscenio_document.gd` + `proscenio_layer.gd`), JSON Schema at `packages/models/schemas/`, docs Markdown at `docs/content/api/schemas/`. The committed-match tests under `tests/codegen/` document the exact invocation.
- [ ] Update the committed-match codegen tests under `tests/codegen/` to the new artifact names + content.
- [ ] Regenerate every fixture + golden from source: `apps/godot/tests/fixtures/*.proscenio` (dummy, effect, skinned_dummy, slots_demo), `examples/generated/**`, the Blender writer goldens, the Photoshop manifest fixtures (`apps/photoshop/uxp-plugin-tests/`).
- [ ] Gate: `uv run pytest tests/codegen/`, the model unit tests, schema validation over all regenerated fixtures.

## Phase 1 - Blender

- [ ] `properties/object_props.py`: `SPRITE_TYPE_ITEMS` -> `ELEMENT_TYPE_ITEMS` (items `("mesh","Mesh","Deformable cutout - Polygon2D vertices + UV (default)",0)`, `("sprite","Sprite","Rigid quad - Sprite2D, optional hframes x vframes grid",1)`); `sprite_type` field -> `element_type` (default `"mesh"`); rewrite the `hframes`/`vframes`/`frame` descriptions ("sprite_frame only" -> "sprite only").
- [ ] Rename panels: `panels/active_sprite.py` -> `active_element.py` ("Active Sprite" -> "Active Element" in `bl_label`; `bl_idname` `PROSCENIO_PT_active_sprite` -> `_active_element`); `panels/_draw_polygon.py` -> `_draw_mesh.py`; `panels/_draw_sprite_frame.py` -> `_draw_sprite.py`. Update `panels/__init__.py` registration + every `bl_parent_id` / draw-dispatch reference.
- [ ] Rename `core/sprite_frame/` -> `core/sprite/` and `core/bpy_helpers/sprite_frame/` -> `core/bpy_helpers/sprite/` via `git mv`; update imports (`sprite_frame_math`, `sprite_frame_shader`). Run the repo-root `uv run pytest tests/` AFTER the move (Q2 - the move breaks import paths the root suite picks up).
- [ ] Rename `core/validation/active_sprite.py` -> `active_element.py`; update `core/validation/__init__.py` + `export.py` references.
- [ ] `exporters/godot/writer/sprites.py`: emit `type: "mesh"` / `"sprite"` and the `elements[]` array (was `"polygon"`/`"sprite_frame"`/`sprites[]`); `scene_discovery.py` + `writer/__init__.py` + `slots.py` `sprites` references. Optionally `git mv sprites.py elements.py`.
- [ ] `importers/photoshop/planes.py` + `__init__.py`: read manifest `kind` `"mesh"`/`"sprite"`; drop the `polygon`-vs-`mesh` branch (D4 collapse) and the `proscenio_psd_kind` hint stamp.
- [ ] Sweep the remaining literal call sites (grep `sprite_frame`, `"polygon"`, `sprites`, `Active Sprite`): `core/help_topics.py`, `core/_shared/feature_status.py`, `core/_shared/hydrate.py`, `core/mirror.py`, `core/psd/psd_manifest.py`, `core/psd/psd_naming.py`, `operators/atlas_pack/apply.py`, `operators/slot/preview_shader.py`, `panels/_draw_region.py`, `panels/_draw_driver_shortcut.py`, `panels/active_slot.py`, `panels/outliner.py`.
- [ ] Gate: the full Blender gate set - `uvx ruff check apps/blender/`, `uvx ruff format --check`, `uv run --with mypy mypy --config-file apps/blender/pyproject.toml`, `uv run pytest tests/` (repo root), the Blender fixture suite (7/7) + operator suite, the whole-addon import sweep.
- [ ] Smoke (local Blender): the **Active Element** panel renders for both a `mesh` and a `sprite` object; the type enum shows "Mesh" / "Sprite".

## Phase 2 - Photoshop

- [ ] `src/lib/tag-parser.ts`: drop `PolygonKind`; `TagBag.kind` -> `"mesh" | "sprite"`. In `consumeToken`: `case "mesh": case "poly": case "polygon": tags.kind = "mesh"`; `case "sprite": tags.kind = "sprite"` (single layer, the inversion fix); `case "spritesheet": tags.kind = "sprite"` (group, N frames). Rewrite the header comment that says `[spritesheet]` becomes `kind: "sprite_frame"`.
- [ ] `src/lib/planner.ts`: `EntryRef.kind` + the `"sprite_frame"` -> `"sprite"` literals; a `[sprite]` single layer plans a 1-frame sprite (no `_frameSources`), a `[spritesheet]` group keeps the multi-frame path.
- [ ] `src/lib/manifest.ts` + `tag-writer.ts`: `"sprite_frame"` -> `"sprite"` literals + types; `api/manifest-writer.ts` emits `format_version: 1` (collapsed).
- [ ] Sweep remaining call sites (grep `sprite_frame`): `src/hooks/useFilenameTemplate.ts`, `src/panels/sections/ExportSection.tsx`, `src/panels/sections/tags/Row.tsx`.
- [ ] Gate: `tsc --noEmit`, ESLint, `vitest` (the `tag-parser`, `exporter`, and `manifest-validator` suites carry the proof - update their fixtures for the `[sprite]` flip + 1-frame sprite).

## Phase 3 - Godot

- [ ] `importer.gd`: `document.sprites` -> `document.elements`; update the `PolygonBuilder`/`SpriteFrameBuilder` preloads + calls.
- [ ] Rename builders: `builders/polygon_builder.gd` -> `mesh_builder.gd` (`PolygonBuilder` -> `MeshBuilder`, discriminator filter `"polygon"` -> `"mesh"`); `builders/sprite_frame_builder.gd` -> `sprite_builder.gd` (`SpriteFrameBuilder` -> `SpriteBuilder`, filter `"sprite_frame"` -> `"sprite"`).
- [ ] Sweep `sprites` / `sprite_frame` references in `builders/animation_builder.gd`, `node_name_util.gd`, `slot_builder.gd`, `sprite_attach_util.gd`. `SUPPORTED_FORMAT_VERSION` stays `1`.
- [ ] `tests/test_importer.gd`: update the `document.elements` reads + the 13 `sprites` references; runs against the Phase 0 regenerated fixtures.
- [ ] Gate: `gdformat --check`, `gdlint`, `test_importer.gd`.

## Phase 4 - docs + skills + glossary

- [ ] `.ai/skills/glossary.md` (D9): rewrite the `Sprite` row into `Element` (the umbrella); add `mesh` (-> `Polygon2D`), `sprite` (-> `Sprite2D`), and `spritesheet` (= a `sprite` with frames > 1) rows from the STUDY target-vocabulary table.
- [ ] `.ai/skills/format-spec.md`: the `sprites[]` array + the `type` discriminator section (the heaviest doc - `sprite_frame` x11).
- [ ] Sweep the rest: `.ai/skills/architecture.md`, `blender-dev.md`, `godot-dev.md`, `photoshop-uxp-dev.md`, `references.md`, `testing.md`; `.ai/conventions/code.md` + `docs.md`; `README.md`; `examples/**/README.md`.
- [ ] Gate: spell-check + link check. Leave the `tests/*.md` feedback logs (UI_FEEDBACK / BUGS_FOUND / MANUAL_TESTING) untouched - historical records.

## Out of scope

No panel layout / information-architecture change (the next UI/UX spec). No `Storage split by field intent` work. No behavior change beyond the `[sprite]` inversion fix and the 1-frame sprite it enables. The `tests/*.md` logs are not renamed.
