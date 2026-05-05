# SPEC 002 — TODO

Implements the `Sprite2D` rendering path alongside the existing `Polygon2D` path. See [STUDY.md](STUDY.md) for the design rationale and Option A discriminator decision.

## Decision lock-in

- [x] Confirm Option A (explicit `type` discriminator) and additive schema change (no `format_version` bump) before starting implementation.
- [x] Confirm builder split (D2 — `polygon_builder.gd` + `sprite_frame_builder.gd` + dispatcher in `importer.gd`).
- [x] Confirm authoring contract: Blender Object Custom Properties (`proscenio_type`, `proscenio_hframes`, `proscenio_vframes`, `proscenio_frame`, `proscenio_centered`).
- [x] Worked example fixture named `effect` — single bone, single sprite, 4-frame loop.

## Schema and format docs

- [ ] Add `oneOf` `[PolygonSprite, SpriteFrameSprite]` in [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json). `PolygonSprite.type` is optional with default `"polygon"`; `SpriteFrameSprite.type` is required `const "sprite_frame"`.
- [ ] Verify all existing `.proscenio` fixtures still validate (additive change, must remain green).
- [ ] Update [`.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md): document the discriminator, the `SpriteFrameSprite` shape, and an example mixing both kinds in one document.
- [ ] Update [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json) inline `description` strings on the new fields so the JSON Schema doubles as inline documentation.

## Blender writer

- [ ] In [`blender-addon/exporters/godot/writer.py`](../../blender-addon/exporters/godot/writer.py), branch `_build_sprite` on `obj.get("proscenio_type", "polygon")`:
  - `"polygon"` → emit current shape (no changes to existing fixtures' output).
  - `"sprite_frame"` → emit `{ type, name, bone, hframes, vframes, frame, centered }` from custom properties.
- [ ] Add a `Literal["polygon", "sprite_frame"]` alias and a `SpriteFrameDict` `TypedDict` to mirror the schema additions.
- [ ] Surface a `RuntimeError` when a sprite has `proscenio_type = "sprite_frame"` but no `proscenio_hframes` — fail at export with a clear message rather than producing an invalid `.proscenio`.
- [ ] Run the schema validator over the exporter's output (the existing in-process check in `run_tests.py` covers this once a `sprite_frame` fixture exists).

## Godot importer

- [ ] Refactor `importer.gd._import` to dispatch sprite construction by `sprite_data.type`. Recommended split: keep `polygon_builder.gd` focused on `Polygon2D`, add a sibling `sprite_frame_builder.gd`.
- [ ] Implement `sprite_frame_builder.gd` (`extends RefCounted`, `@tool`):
  - Instances `Sprite2D`.
  - Sets `texture`, `hframes`, `vframes`, `frame`, `centered`, `offset`.
  - Honors `region` via `region_enabled = true` + `region_rect` if present.
  - Returns the configured `Sprite2D` to the dispatcher.
- [ ] Treat the absence of `type` as `"polygon"` (do not error on legacy fixtures).
- [ ] Implement the `sprite_frame` track case in [`animation_builder.gd`](../../godot-plugin/addons/proscenio/builders/animation_builder.gd): a Godot `Animation` value track at `<sprite>:frame` with `INTERPOLATION_NEAREST`.
- [ ] Push a clear `push_error` when `track.target` references a sprite that does not exist or is the wrong kind for the track type.
- [ ] Run the existing `test_importer.gd` to confirm the legacy `Polygon2D` path is untouched. The test should still report `PASS: 10 assertions` for the existing fixture.

## Worked example

- [ ] Add a new fixture under `examples/effect/`:
  - `effect.proscenio` hand-written with one bone, one `sprite_frame` sprite, and a 0.4 s frame-by-frame animation cycling `frame: 0..3`.
  - `atlas.png` — 4-frame horizontal strip (e.g. 64 × 16 px, 16 × 16 per frame).
  - `README.md` matching the structure of `examples/dummy/README.md` — three-roles table adapted for the spritesheet path.
- [ ] Add the matching wrapper assets (`Effect.tscn` + `Effect.gd`) to demonstrate that the wrapper-scene pattern (SPEC 001) works identically for `sprite_frame` sprites.

## Tests

- [ ] Extend [`godot-plugin/tests/test_importer.gd`](../../godot-plugin/tests/test_importer.gd) (or add a sibling test file) to load the new fixture, assert the `Sprite2D` is constructed with the right `hframes`/`vframes`/`frame`, assert the animation library has a track on `:frame`, and confirm the idempotent rebuild equality still holds.
- [ ] Add a Blender-side fixture mirroring the worked example (`effect.blend` + `blender-addon/tests/fixtures/effect/expected.proscenio`) so `run_tests.py` has a second case beyond the existing `dummy/` one. The test runner should diff both fixtures.
- [ ] Add a regression assertion for legacy `.proscenio` (no `type` field) — must still build a `Polygon2D` exactly as before.
- [ ] Update CI matrix-aware comments in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) only if a workflow change is needed; the existing `test-blender` and `test-godot` jobs should pick up the new fixture without edit.

## Documentation

- [ ] Add a "Choosing the rendering path" subsection to [`.ai/skills/godot-plugin-dev.md`](../../.ai/skills/godot-plugin-dev.md): when to pick `Polygon2D`, when to pick `Sprite2D`, what each unlocks downstream (skinning weights for the former, frame animation for the latter).
- [ ] Update [`README.md`](../../README.md) iteration loop if the spritesheet path changes anything user-visible (the wrapper-scene pattern stays identical).
- [ ] Update [`STATUS.md`](../../STATUS.md) when SPEC 002 closes, moving it from "só prevista" to "shipped" and linking the worked example.

## Defer (potential SPEC 002.1 if demand emerges)

- `region_rect` authoring polish — Blender UI panel that lets the user pick a sub-rectangle visually instead of typing four custom-property numbers.
- `frame_coords` (`Vector2i`) as an alternative addressing for `frame`. Today the schema accepts only the row-major `int`.
- Animation events / method tracks — sound and particle cues on frame transitions are a natural complement but do not gate SPEC 002.
- Authoring UX panel — replace raw Custom Properties with a dedicated Blender sidebar panel exposing a dropdown for `proscenio_type` and integer fields for the frame metadata.
