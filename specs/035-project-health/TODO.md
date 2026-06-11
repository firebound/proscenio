# Spec 035: Project health and shipping - TODO

Sequenced from the verdicts in [STUDY.md](STUDY.md): six items land now (the blocking release fix first, then the cheap gates, then the fixture work), nine wait behind concrete triggers, five are pruned.

## Now

### Repackage the Photoshop release job `[blocking]`

- [ ] Replace the stale `.jsx` copy in [release.yml](../../.github/workflows/release.yml) with a UXP build: setup-node + pnpm, `pnpm install --frozen-lockfile`, `pnpm run build` in `apps/photoshop` (`dist/` is gitignored, so the job must build), then zip `dist/` as `proscenio-photoshop-<version>.zip` (`.ccx` rename optional).
- [ ] Add a `workflow_dispatch` dry-run path that runs the package steps without the gh-release upload, so the job can be exercised tagless - the `.jsx` line rotted precisely because the workflow only runs on tags.
- [ ] Dry-run all three component branches (blender, godot, photoshop) via the dispatch path and check each artifact's content listing.

### Turn the existing ESLint config into a gate

- [ ] Run `pnpm run lint` over `apps/photoshop/src`; fix or narrowly scope-justify any findings so the enabling commit lands green.
- [ ] Add the lint step to the `lint-photoshop` job in [ci.yml](../../.github/workflows/ci.yml).
- [ ] Mirror it as a pre-commit local hook (sketch in [backlog-code-quality.md](../backlog-code-quality.md)).

### mypy gate for proscenio-models and proscenio-codegen

- [ ] Add `[tool.mypy]` strict-strict blocks (validator profile, `python_version = "3.11"`) to [packages/models/pyproject.toml](../../packages/models/pyproject.toml) and [packages/codegen/pyproject.toml](../../packages/codegen/pyproject.toml); scope the pydantic discriminator functions' `Any`-by-contract payloads with coded ignores.
- [ ] Add the two mypy steps to `lint-python` in ci.yml and matching pre-commit hooks.
- [ ] Land before the schema-expressiveness wave starts churning the models (cross-spec sequencing; see [EXECUTION_MAP.md](../EXECUTION_MAP.md)).

### Saved-scene assert for the plugin-uninstall guard

- [ ] In [test_importer.gd](../../apps/godot/tests/test_importer.gd), pack the built character into a `PackedScene`, save, reload, and walk every node asserting `get_script() == null` - no addon script references baked into importer output.
- [ ] Run the assert for all four fixture documents inside the same headless pass (no new CI job).

### Fixture portability: strip absolute image paths

- [ ] Apply the blink_eyes `bpy.path.relpath` + re-save pattern to [slot_cycle/build_blend.py](../../packages/fixtures/slot_cycle/build_blend.py) and the simple_psd build path; regenerate both committed `.blend`s.
- [ ] Verify with a strings-scan of both `.blend`s for machine-absolute paths and confirm the goldens still diff clean.

### End-to-end mixed-feature fixture

- [ ] Sequence after the export-correctness blocking writer fixes (armature picker, multi-polygon) so the golden bakes once.
- [ ] Author the fixture in the categorization buckets under `examples/generated/`: skinned polygon body + sprite_frame mouth + slot with mixed attachments + packed atlas + Drive-from-Bone + one animation.
- [ ] Bake the Blender-to-Godot golden and wire it into the existing `test-blender` re-export diff and `test-godot` smoke; populate the dev project via [sync_fixtures.py](../../scripts/godot/sync_fixtures.py) (never edit the synced copies).
- [ ] Optional follow-up PR: the PSD-to-Blender leg (photoshop manifest golden) once the Blender leg is green.

## Deferred

Gate items; each lands when its trigger fires.

- **blender-multi-version-matrix** - trigger: before the first `blender-v*` tag, run the full headless suite once against 4.2 LTS; keep a CI leg only if green and stable, otherwise lower `blender_version_min` to the tested floor.
- **blender-43-legacy-actions** - folds into the 4.2 run above; the function-level fallback is already unit-tested (`tests/writer/test_animations.py:175-187`).
- **godot-editor-reimport-test** - trigger: the first import-flow regression that the builders-direct suite plus the new saved-scene assert fail to catch.
- **mypy-ignore-errors-subtrees** - trigger: sweep each exempted module on its next functional touch; the validator trio (`addon_loader`, `coverage`, `measurement`) is the pilot.
- **run-coverage-ci** - trigger: Sonar analysis moves into CI; until then the documented local pre-scan recipe in `sonar-project.properties` is the workflow.
- **flat-fixture-buckets** - trigger: piggyback the move onto the next edit of a flat fixture (locked backlog decision; the move ripples through spec TODOs, the fixtures index, wrapper paths, and the sync script).
- **origin-pivot-fixture** - trigger: ship together with the sprite-pivot-offset writer work, or on the first regression where origin handling diverges between PSD authoring styles.
- **issue-pr-templates** - trigger: the repo opens to outside contributors.
- **install-dev-script** - trigger: the next fresh-machine dev setup; author the script during that setup so it is tested by construction.

## Dropped

- **ci-matrix-expansion** - no version-specific code path or support claim on the Godot side; a multi-version leg doubles heavy CI to catch nothing (the Blender half lives in the matrix gate).
- **bpy-stubs-override-sweep** - duplicate ledger row of mypy-ignore-errors-subtrees; the stubs-adoption half already shipped in PR #80.
- **drop-bpy-coverage-exclusions** - denominator bookkeeping gated on an unscheduled comprehensive-units project; removing exclusions protects no behavior.
- **edge-polish-pure-modules** - one to six edge lines per module at 89-93%; the backlog already wrote it off as diminishing returns.
- **doll-oracle-v2** - the structural pytest pins the v2 manifest; a byte-equal capture only locks whitespace and key order, firing on intentional serialisation changes - churn, not protection.
