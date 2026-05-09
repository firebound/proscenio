# SPEC 000 — TODO

Closes the Phase 0 (foundation) work and primes Phase 1 (MVP). Each item is concrete, ordered roughly by dependency.

## Schema cleanup (apply Q1–Q9 decisions)

- [x] **Q2.** Remove `"cubic"` from the `interp` enum in [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json). Keep `"linear"` and `"constant"`.
- [x] **Q2.** Update [`.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md) interpolation row to match.
- [x] **Q3.** Add a one-line note in `format-spec.md`: weights accepted in v1 schema, ignored by MVP importer, full skinning in Phase 2.
- [x] **Q4.** Add a "Atlas packing" subsection to `format-spec.md` clarifying that atlases are pre-packed externally in v1.
- [x] **Q9.** Add a "Coordinate origin" line to `format-spec.md` stating the scene-root `Node2D` is `(0, 0)`.

## Documentation

- [x] Add `.ai/skills/references.md` listing prior-art repos with priority and what to read in each (extract from `STUDY.md` "Prior art" section).
- [x] Expand the "Why no GDExtension" reasoning into [`.ai/skills/architecture.md`](../../.ai/skills/architecture.md) (currently one paragraph; merge the table from `STUDY.md`).
- [x] Update `AGENTS.md` to point at `specs/` for planning specs (replacing the removed `docs/index.md` link).
- [x] Update `README.md` to point at `specs/000-initial-plan/STUDY.md` for the current plan.

## Dummy fixture (schema-first, no Blender required)

The first end-to-end test bypasses the Blender exporter entirely and hand-writes a `.proscenio` file to validate the Godot importer.

- [x] Hand-write `examples/dummy/dummy.proscenio` with: 3 bones (root, torso, head), 3 `Polygon2D` sprites as simple quads, one `idle` animation with one `bone_transform` track that rotates the head ±15°.
- [x] Add a tiny placeholder `examples/dummy/atlas.png` (commit as LFS via `.gitattributes` rule already in place).
- [x] Run `check-jsonschema --schemafile schemas/proscenio.schema.json examples/dummy/dummy.proscenio` and fix any failures.

## Godot importer — make MVP work end-to-end

Order matters. Each step must produce a visible result before moving on.

- [x] **Smoke import.** Drop `dummy.proscenio` into `apps/godot/`. Confirm the importer fires, parses, and produces a saved `.scn`. Fix any surface bugs.
- [x] **Skeleton render.** Open the imported scene in the Godot editor. Verify the `Skeleton2D` and `Bone2D` hierarchy is correct visually.
- [x] **Sprites render.** Verify each `Polygon2D` shows the right region of `atlas.png`. Y-flip and UV correctness checked by eye against the source. *Note: UVs in `.proscenio` are normalized `[0, 1]`; the Godot importer multiplies by atlas pixel size since `Polygon2D.uv` is pixel-space.*
- [x] **Implement `bone_transform` track wiring.** Currently [`animation_builder.gd`](../../apps/godot/addons/proscenio/builders/animation_builder.gd) creates empty `Animation` resources. Wire keyframes into Godot's separate position/rotation/scale tracks per `Bone2D`.
- [x] **Animation playback.** Press Play in Godot, confirm the head rotates as authored.
- [x] **Plugin-uninstall test.** Move `addons/proscenio/` out of the project. Confirm the imported scene still opens and plays. Critical no-GDExtension verification. *Verified: with the plugin disabled, a wrapper scene instancing the imported dummy still renders with the correct atlas regions and plays the idle animation. The generated `.scn` is self-contained.*

## Blender exporter — minimal path

Once the importer is proven against the hand-written fixture, write the smallest possible exporter that reproduces the same fixture from Blender data.

- [x] Build a tiny `dummy.blend` with: 3 sprite planes, an armature with 3 bones, one animation action that rotates the head bone.
- [x] Implement `apps/blender/exporters/godot/writer.py` — walks the active scene, emits `.proscenio` JSON conforming to the schema.
- [x] Add an operator `proscenio.export_godot` that opens a file picker and writes the result.
- [x] Replace the smoke-test panel button with the export button.
- [x] Round-trip test: export `dummy.blend` → `.proscenio` → import in Godot → animation plays.

## Tests

- [x] Add `apps/blender/tests/fixtures/dummy/` with the expected `.proscenio` fixture (the source `.blend` lives at `examples/dummy/dummy.blend` — single source of truth).
- [x] Replace the placeholder body of `apps/blender/tests/run_tests.py`: re-export `dummy.blend` and diff the result against `tests/fixtures/dummy/expected.proscenio` (normalized via `json.dumps(sort_keys=True)`).
- [x] Add `apps/godot/tests/test_importer.gd`: headless smoke test that exercises the builders and asserts node hierarchy, bone count and names, sprite count, animation library and length. No GUT dependency.
- [x] Wire both into `.github/workflows/ci.yml` as `test-blender` and `test-godot` jobs (Blender 5.1.1, Godot 4.6.2-stable; matrix expansion in backlog).

## Photoshop exporter

- [x] Port `coa_tools2/Photoshop/coa_export.jsx` into `apps/photoshop/proscenio_export.jsx`. Layer walk (with group recursion), per-layer PNG export, and JSON manifest matching [`.ai/skills/photoshop-jsx-dev.md`](../../.ai/skills/photoshop-jsx-dev.md). Untested against real PSD in CI — no headless Photoshop available.
- [x] Document the expected layer convention in [`apps/photoshop/README.md`](../../apps/photoshop/README.md). PSD example deferred — requires a real Photoshop session to author.

Phase 1 ends once the dummy round-trip passes and the photoshop exporter produces the per-sprite PNGs + position JSON for the same dummy.

## Cleanup before declaring Phase 1 done

- [x] Replace LICENSE placeholder body with the full GPL-3.0 text from gnu.org.
- [x] Replace the placeholder maintainer email in `apps/blender/blender_manifest.toml`.
- [x] Decide and document the canonical `Space-Wizard-Studios/firebound-proscenio` GitHub URL or update references if it differs.

## Out of scope for SPEC 000

These belong to follow-up specs, listed only so they are not lost:

- Reimport-with-merge — SPEC 001.
- Spritesheets and `Sprite2D` path — SPEC 002.
- Full skinning weights — SPEC 003.
- Slot system — SPEC 004.
- Blender authoring panel — SPEC 005.
