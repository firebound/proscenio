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

## Wave 6.0.5 — roundtrip tooling

Branch: `feat/spec-006.0.5-roundtrip-tooling`. Bootstraps real test PSDs from the existing Blender fixtures so the SPEC 006 importer (Wave 6.3) has cross-checked input data without hand-authoring PSDs.

- [x] `scripts/fixtures/doll/export_psd_manifest.py` — bpy: opens `doll.blend`, walks every mesh, projects world XZ bbox to a top-left PSD canvas at `PIXELS_PER_UNIT=100`, emits `examples/doll/photoshop_import/doll.psd_manifest.json` matching schema v1 (kind=polygon for every mesh; sprite_frame deferred until the doll grows hframed eyes). Layer paths point at `../render_layers/<name>.png`.
- [x] `examples/doll/photoshop_import/doll.psd_manifest.json` — generated, schema-valid, references `../render_layers/<name>.png`.
- [x] `photoshop-exporter/proscenio_import.jsx` — JSX: file-picker on a manifest, builds a fresh PSD doc at `manifest.size`, stamps each layer at its declared `position`. Layers added in z_order **descending** so z=0 lands on top of the Photoshop layer stack. Sprite_frame layers become a `LayerSet` with frame children named by index (D9 primary mechanism mirrored on the import side). Output PSD: `examples/doll/photoshop_import/doll.psd`.
- [x] Manual smoke test in Photoshop: 22 layers placed correctly, JSX exporter round-trips identical positions / sizes (within 2 px from Workbench AA edge bleed). Round-trip output lands at `examples/doll/photoshop_export/` (gitignored) when `proscenio_export.jsx` runs on the imported PSD.

## Wave 6.3 — importer core

Branch: `feat/spec-006.1-importer`. **Shipped:**

- [x] `blender-addon/importers/photoshop/__init__.py` — orchestrator: read manifest (6.0), iterate layers, dispatch by `kind`. Returns `ImportResult`. Optional `placement` enum (`landed` / `centered`) and `root_bone_name` parameter.
- [x] `blender-addon/importers/photoshop/planes.py` — quad mesh stamper, coord conversion (D6), material builder (Principled BSDF + ShaderNodeTexImage). Uses `parent_type='OBJECT'` (avoids the bone-direction rotation flip that would put meshes in world XY instead of XZ). Re-import via `proscenio_import_origin = "psd:<layer_name>"` tag (D5).
- [x] `blender-addon/core/psd_spritesheet.py` — bpy + numpy util: pad N frames to bbox max (D10), concatenate horizontally, write `_spritesheets/<name>.png`. Pillow avoided to keep the addon free of dev-only deps.
- [x] `blender-addon/importers/photoshop/armature.py` — stub armature: single root-level bone (default name `root`, configurable). Every mesh parented to the armature object.

## Wave 6.4 — operator + panel

Bundled with 6.3 (PR #18). **Shipped:**

- [x] `blender-addon/operators/import_photoshop.py` — `PROSCENIO_OT_import_photoshop` operator. File picker for the manifest JSON via `ImportHelper`. `placement: EnumProperty` (`landed` / `centered`) and `root_bone_name: StringProperty` surfaced in the redo panel.
- [x] Panel button "Import Photoshop Manifest" in the main Proscenio sidebar.
- [x] Operator registered in `blender-addon/operators/__init__.py`; panel button in `blender-addon/panels/__init__.py`.

## Wave 6.5 — fixture `simple_psd/`

Branch: `feat/spec-006.5-simple-psd-fixture`. Mirrors the SPEC 007 fixture layout.

- [ ] `examples/simple_psd/` — a small hand-authored `.psd` source (or a programmatically generated one if PSD authoring is too friction). Contains a polygon layer + a sprite_frame group of 4 frames.
- [ ] `examples/simple_psd/photoshop_export/` — JSX exporter output (`simple_psd.json` + `images/`).
- [ ] `examples/simple_psd/simple_psd.blend` — expected post-import `.blend` at the fixture root.
- [ ] `examples/simple_psd/simple_psd.expected.proscenio` — golden at the fixture root.
- [ ] `examples/simple_psd/godot/SimplePSD.tscn` + `SimplePSD.gd` — Godot wrapper following the SPEC 001 pattern.
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
