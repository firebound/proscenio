# Spec 035: Project health and shipping

Strengthen the toolchain that guards every other area, and fix the release packaging.

## Scope

- **Repackage the Photoshop release job** for the UXP dist (the stale `.jsx` copy would fail a tag).
- **Blender headless multi-version matrix** (4.2 LTS + latest).
- **Godot/Blender CI matrix expansion**.
- **Test the Blender 4.3 legacy-actions path**.
- **Full Godot editor-reimport test** with a plugin-disabled assertion.
- **Plugin-uninstall warning / CI guard**.
- **Run ESLint** in CI and pre-commit.
- **A mypy gate** for `packages/models` and `packages/codegen`.
- **Drop the mypy ignore_errors exemptions** on the bpy-bound subtrees.
- **Finish adopting the bpy stubs** - drop the remaining overrides.
- **Wire run_coverage into CI**.
- **Drop the bpy-bound coverage exclusions** once units are comprehensive.
- **Edge-polish the pure modules** sitting at 89-93%.
- **An end-to-end mixed-feature fixture** (atlas + sprite_frame + slots + drive).
- **Migrate the flat fixtures** into the psd_to_blender / blender_to_godot buckets.
- **Audit simple_psd / slot_cycle** for absolute image paths baked into the `.blend`.
- **A dedicated origin/pivot fixture**.
- **Re-run the doll roundtrip oracle** against schema v2.
- **Issue and PR templates**.
- **An install-dev script** to automate the dev junctions.

## Study

### Surface notes

CI shape ([ci.yml](../../.github/workflows/ci.yml)): six parallel jobs. Four are light (ruff + two mypy configs + repo pytest; tsc + vitest; gdformat + gdlint; check-jsonschema over fixtures). `test-blender` is the wall-time long pole: a cached Blender 5.1.1 download, a wheels bootstrap, then three headless test passes (golden re-export diff, automesh validation, operator tests). `test-godot` pins 4.6.2 and needs a headless editor pass just to prime the `class_name` cache before its smoke script. Any matrix expansion multiplies the two heavy jobs, not the four cheap ones.

- **Version pins vs claims.** CI runs Blender 5.1.1 only while [blender_manifest.toml](../../apps/blender/blender_manifest.toml) ships `blender_version_min = "4.2.0"`: the 4.2+ support claim is untested in CI. Godot pins 4.6.2 and the plugin has no version-specific code paths, so there is no fallback branch a Godot matrix would protect.
- **The legacy-actions exposure is narrower than the backlog row says.** [tests/writer/test_animations.py](../../tests/writer/test_animations.py) lines 175-187 already unit-test both `action_fcurves` branches (legacy `fcurves`, layered `channelbags`) against stub objects. What is genuinely untested is a real 4.2/4.3 runtime end to end, not the function logic.
- **Release ([release.yml](../../.github/workflows/release.yml)).** One job switching on tag prefix. The photoshop branch still `cp`s `apps/photoshop/proscenio_export.jsx`, which no longer exists, so a `photoshop-v*` tag fails today. Two facts the backlog sketch misses: `apps/photoshop/dist/` is gitignored, so the fix needs Node + pnpm + `pnpm run build` steps before any zip; and the workflow only ever runs on tags, which is exactly how the `.jsx` line rotted unnoticed - a `workflow_dispatch` dry-run path closes that rot class.
- **Type gates.** [apps/blender/pyproject.toml](../../apps/blender/pyproject.toml) and the validator run mypy strict-strict, but `ignore_errors = true` blankets four bpy-bound globs (`operators`, `panels`, `properties`, `core/bpy_helpers`) plus the validator trio (`addon_loader`, `coverage`, `measurement`). [packages/models/pyproject.toml](../../packages/models/pyproject.toml) and [packages/codegen/pyproject.toml](../../packages/codegen/pyproject.toml) carry no `[tool.mypy]` at all and no CI step - the pydantic source of truth and the emitter that generates every downstream binding are the only Python packages with zero type gate.
- **Lint gap.** `apps/photoshop` defines `"lint": "eslint src"` with a strictTypeChecked + stylisticTypeChecked [eslint.config.mjs](../../apps/photoshop/eslint.config.mjs), but the `lint-photoshop` job runs only tsc + vitest and pre-commit has no eslint hook. The `no-unsafe-*` family (the `any`-flow guard at the untyped UXP host boundary) is enforced nowhere.
- **Coverage.** [sonar-project.properties](../../sonar-project.properties) documents a local-only two-interpreter recipe; no Sonar analysis runs in CI, so wiring `run_coverage.py` into `test-blender` today would lengthen the longest job to produce a report with no consumer. The bpy-bound exclusions are a documented honest-denominator policy (the headless suites measure those dirs at 23-29%).
- **Fixtures.** Builders in `packages/fixtures/` emit committed outputs under `examples/generated/` (`.blend` + `.expected.proscenio` + godot wrappers), linked into `apps/godot/` by [sync_fixtures.py](../../scripts/godot/sync_fixtures.py) - edits to the synced copies do not persist. The `psd_to_blender` / `blender_to_godot` buckets hold only `tag_smoke`; eight fixtures stay flat. [slot_cycle/build_blend.py](../../packages/fixtures/slot_cycle/build_blend.py) loads its layer PNGs with no `bpy.path.relpath` rewrite before save (lines 146-149), the same portability defect blink_eyes already had and fixed.
- **Godot tests.** [test_importer.gd](../../apps/godot/tests/test_importer.gd) exercises the builders in-memory under an addon-disabled project but never packs, saves, and reloads a `.scn` - the shipped-scene invariant (no addon script references baked into importer output) has no automated assert.

### Assessment

Scores are 1-5. Flow value: size x likelihood of the regression class the gate protects (5 = export correctness or the release mechanics themselves). Test burden: cost to build plus recurring CI/maintenance cost (1 = one-line config, 5 = a heavy CI job needing babysitting). Bug surface: workflow complexity the item itself adds. Underuse risk: 5 = the gate realistically never fires.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| release-photoshop-stale | 5 | 2 | 1 | 1 | now | A `photoshop-v*` tag fails deterministically today; this is shipping correctness itself, fixed in ~20 workflow lines. |
| blender-multi-version-matrix | 4 | 4 | 1 | 3 | gate | The 4.2+ claim is real exposure, but a permanent second Blender leg doubles the heaviest job and goldens may diverge across versions; one green 4.2 run gates the first tag instead. |
| ci-matrix-expansion | 2 | 4 | 1 | 5 | drop | No version-specific code path or support claim on the Godot side; a multi-version Godot leg is the textbook matrix job that catches nothing. The Blender half is owned by the matrix gate above. |
| blender-43-legacy-actions | 3 | 1 | 1 | 2 | gate | Both `action_fcurves` branches are already unit-tested (`test_animations.py:175-187`); the remaining exposure is a real 4.2 runtime, which folds into the matrix gate's one-off run. |
| godot-editor-reimport-test | 3 | 4 | 2 | 3 | gate | Headless editor-import harnesses are flaky to babysit; the highest-value half (the saved-scene assert) ships separately via plugin-uninstall-warning at a fraction of the cost. |
| plugin-uninstall-warning | 4 | 2 | 1 | 2 | now | Pack-save-reload the built character and assert zero script refs: protects the scenes-ship-without-the-addon invariant every consumer depends on, as an append to the existing harness. |
| eslint-not-in-ci | 3 | 1 | 1 | 2 | now | The strictTypeChecked config exists and is decorative; one CI step plus one pre-commit hook turns the `no-unsafe-*` family on at the untyped UXP boundary. |
| models-codegen-no-mypy | 4 | 2 | 1 | 2 | now | The schema source of truth and the binding emitter are the only ungated Python; mistypes there propagate into every generated artifact, and heavy schema churn is queued next. |
| mypy-ignore-errors-subtrees | 3 | 5 | 1 | 3 | gate | The full sweep is weeks of stub-fighting across ~6900 bpy-bound lines; sweep module-by-module on touch, validator trio first, so the cost rides existing work. |
| bpy-stubs-override-sweep | 3 | 5 | 1 | 3 | drop | Duplicate ledger row: the stubs-adoption half shipped (PR #80) and the remaining work is literally the ignore_errors sweep row above. |
| run-coverage-ci | 2 | 4 | 1 | 5 | gate | Instrumented in-Blender reruns lengthen the longest job to produce a report no CI consumer reads; the local recipe stands until Sonar itself moves into CI. |
| drop-bpy-coverage-exclusions | 1 | 3 | 1 | 5 | drop | Denominator bookkeeping contingent on comprehensive bpy-bound units, a project nobody scheduled; removing exclusions catches nothing by itself. |
| edge-polish-pure-modules | 1 | 2 | 1 | 5 | drop | One to six uncovered edge lines per module at 89-93%; the backlog itself wrote it off as diminishing returns. |
| mixed-feature-fixture | 5 | 3 | 2 | 1 | now | The only gate that exercises feature stacking (atlas + sprite_frame + slots + drive), the exact class single-feature goldens cannot catch, and the safety net for the queued schema wave. |
| flat-fixture-buckets | 1 | 3 | 2 | 5 | gate | Pure reorganization whose move ripples through spec TODOs, the fixtures index, wrapper paths, and the sync script; locked decision: piggyback on the next edit of a flat fixture. |
| simple-psd-slot-cycle-abs-paths | 3 | 1 | 1 | 1 | now | Real portability defect with a known one-file fix pattern (blink_eyes precedent); absolute paths in committed `.blend`s make goldens machine-dependent. |
| origin-pivot-fixture | 3 | 2 | 1 | 4 | gate | Origin paths are triple-covered today (doll oracle, tag_smoke, pytest); the fixture earns its keep when the sprite-pivot-offset writer work lands and needs a regression net. |
| doll-oracle-v2 | 2 | 2 | 1 | 5 | drop | Structural invariants are already pytest-pinned; a byte-equal SHA only locks whitespace and key order, firing on intentional serialisation changes - churn, not protection. |
| issue-pr-templates | 1 | 1 | 1 | 5 | gate | Zero protection for a solo repo; trivially added when an outside contributor actually appears. |
| install-dev-script | 1 | 2 | 1 | 4 | gate | Convenience, not a gate, and a twice-a-year script rots silently; write it during the next fresh-machine setup so it is tested by construction. |

### Verdict summary

Counts: **6 now, 9 gate, 5 drop, 0 defer** - every non-now item either carries a concrete trigger or gets pruned.

Cheapest 20% that buys ~80% of the protection: the release-job repackage (the one item that fails deterministically), the ESLint CI step (config already written), the models/codegen mypy gate (two small pyproject blocks plus two CI lines guarding the source of truth), the abs-path fixture fix (one builder edit plus re-save), and the saved-scene script-ref assert (a ~30-line append to `test_importer.gd`). All five are one-PR-or-less, near-zero recurring cost, and each guards a distinct real regression class: shipping mechanics, `any`-flow at the UXP boundary, schema/binding generation, fixture portability, and the shipped-scene contract.

The one heavier now-item is the mixed-feature fixture: the single highest-flow-value gate in the spec (feature interaction through the whole pipeline), landed before the schema-expressiveness wave churns the writer and sequenced after the export-correctness blocking fixes so the golden bakes once.

Pruned: the two coverage-polish rows (metric bookkeeping with no behavior protection), the Godot multi-version matrix (no protected class), the byte-equal oracle re-capture (the structural pytest is the right oracle), and the duplicate stubs-sweep ledger row.
