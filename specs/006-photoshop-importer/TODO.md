# SPEC 006 — TODO

PSD → Blender importer. Closes the missing leg of the pipeline. See [STUDY.md](STUDY.md) for the full design + decision rationale.

## Decision lock-in

- [x] D1 — manifest format: v1 schema with `format_version`, `kind` discriminator, `pixels_per_unit`, `z_order`, `frames[]` for sprite_frame. Locked at `schemas/psd_manifest.schema.json`.
- [x] D2 — atlas: leave per-PNG. User runs the existing Pack Atlas operator post-import.
- [x] D3 — armature stub: auto single `root` bone, every mesh parented to it.
- [x] D4 — `<name>_<index>` sprite_frame convention (already locked in SPEC 007 D4). Importer respects via the `kind` discriminator.
- [x] D5 — re-import: idempotent by manifest name. User-modified rotation / parenting / weights survive via `proscenio.import_origin` tag.
- [x] D6 — coordinate conversion: PSD top-left → Blender XZ centre at `pixels_per_unit`; `mesh_center.y = z_order * Z_EPSILON` to avoid Z-fight.
- [x] D7 — JSX manifest only. Direct `.psd` parsing deferred (fragile cross-version, duplicates JSX work).
- [x] D8 — frame source PNGs after compose: keep individuals; spritesheet goes to `_spritesheets/<name>.png`.
- [x] D9 — sprite_frame source mechanism: primary PSD layer group with numeric children, fallback flat `<name>_<index>` naming. Both detected at JSX side.
- [x] D10 — frame size mismatch: importer pads each frame to bbox of largest, transparent fill, via Pillow.

## Wave 6.0 — manifest schema + parser (foundation)

Branch: `feat/spec-006.0-foundation`. **Shipped:**

- [x] `schemas/psd_manifest.schema.json` — JSON Schema 2020-12 for manifest v1. Discriminator on `kind` via `oneOf`, `frames[]` valid only on `sprite_frame`, `additionalProperties: false` everywhere.
- [x] `blender-addon/core/psd_manifest.py` — bpy-free parser. `load(path)` / `parse(raw)` return a `Manifest` dataclass with typed `PolygonLayer` / `SpriteFrameLayer` entries. Raises `ManifestError` on shape mismatch with field-path-aware messages.
- [x] `tests/test_psd_manifest.py` — 16 cases (valid + missing required field, unknown kind, polygon-with-frames, single-frame sprite_frame, negative z_order, malformed size, unknown frame field, layers-not-array, file-missing, malformed JSON).
- [x] CI `validate-schema` job glob (`schemas/*.schema.json` indirectly via `examples/**/*.proscenio` validation) — schema itself valid against Draft 2020-12.

## Wave 6.1 — JSX exporter v1

Bundled into the foundation PR. **Shipped:**

- [x] `photoshop-exporter/proscenio_export.jsx` rewritten to emit `format_version: 1`, `pixels_per_unit` (default 100), `kind` discriminator, `z_order` from a global counter, `frames[]` for sprite_frame groups (D9 detection at JSX side via `qualifiesAsSpriteFrameGroup` + the post-walk `aggregateFlatSpriteFrames` fallback).
- [x] Hidden-layer + `_`-prefix skip rules preserved.
- [ ] Manual smoke test in Photoshop CC 2015+ (no headless option) — pending hands-on verification.

## Wave 6.2 — naming convention parser

Bundled into the foundation PR. **Shipped:**

- [x] `blender-addon/core/psd_naming.py` — bpy-free helpers used by Wave 6.3 (importer-side sanity check) and mirrored by the JSX `matchIndexedFrame` for cross-language consistency.
  - `match_indexed_frame(name) -> IndexedName | None`
  - `is_uniform_indexed_group(child_names) -> bool`
  - `group_by_index_suffix(layer_names) -> dict[base, list[(index, name)]]`
- [x] `tests/test_psd_naming.py` — 15 cases covering pure-digit / `frame_<n>` / `<base>_<n>` matches, mixed-convention rejection, mixed-base rejection, gap rejection, non-zero-start rejection, empty/single-child rejection, fallback grouping.

## Wave 6.3 — importer core

Branch: `feat/spec-006.2-importer`.

- [ ] `blender-addon/importers/photoshop/__init__.py` — orchestrator: read manifest (6.0), iterate layers, dispatch by `kind`.
- [ ] `blender-addon/importers/photoshop/planes.py` — quad mesh stamper, coord conversion (D6), material builder (Principled BSDF + ShaderNodeTexImage).
- [ ] `blender-addon/importers/photoshop/spritesheet.py` — Pillow util: pad N frames to bbox max (D10), concatenate horizontally, write `_spritesheets/<name>.png`. Returns `(hframes, vframes, tile_size_px)`.
- [ ] `blender-addon/importers/photoshop/armature.py` — stub armature: single `root` bone, parent every mesh via `parent_type='BONE'`.
- [ ] Re-import semantics (D5): identify existing meshes by `proscenio.import_origin = "psd:<layer_name>"`, replace mesh-data + material, preserve transform / parenting / weights.

## Wave 6.4 — operator + panel

Bundled with 6.3 if cohesive.

- [ ] `blender-addon/operators/import_photoshop.py` — `PROSCENIO_OT_import_photoshop` operator. File picker for the manifest JSON. Invokes the importer.
- [ ] Panel button "Import Photoshop Manifest" in the main Proscenio sidebar.
- [ ] Operator registered in `blender-addon/operators/__init__.py`, panel button in `blender-addon/panels/__init__.py`.

## Wave 6.5 — fixture `simple_psd/`

Branch: `feat/spec-006.3-simple-psd-fixture`.

- [ ] `examples/simple_psd/` — a small hand-authored `.psd` source (or a programmatically generated one if PSD authoring is too friction). Contains a polygon layer + a sprite_frame group of 4 frames.
- [ ] `examples/simple_psd/manifest.json` — JSX exporter output, committed for repeatable testing.
- [ ] `examples/simple_psd/simple_psd.blend` — expected post-import `.blend` (run the operator, save).
- [ ] `examples/simple_psd/simple_psd.expected.proscenio` — golden via `scripts/fixtures/export_proscenio.py`.
- [ ] `examples/simple_psd/SimplePSD.tscn` + `SimplePSD.gd` — Godot wrapper following the SPEC 001 pattern.
- [ ] `blender-addon/tests/run_tests.py` auto-discovers it (no change needed).
- [ ] `examples/simple_psd/README.md`.

## Documentation

- [ ] `STATUS.md` — fixtures row gains `simple_psd` once Wave 6.5 lands.
- [ ] `README.md` — Quickstart mentions the new "Import Photoshop Manifest" operator.
- [ ] `.ai/skills/blender-addon-dev.md` — "Adding a fixture" section already covers the auto-discovery; add a note about the photoshop importer entry-point.
- [ ] `.ai/skills/photoshop-jsx-dev.md` — manifest v1 contract, sprite_frame group detection rules.

## Out of scope (deferred)

- Re-export Blender → PSD (one-way pipeline only).
- Live link Blender ↔ Photoshop (backlog).
- Direct `.psd` parsing (D7).
- Slot-system PSD-group hints (lands with SPEC 004).

## Blocked on

- Nothing. All blockers resolved by SPEC 007 lock-ins (D4 sprite_frame naming) and the existing JSX exporter scaffold.
