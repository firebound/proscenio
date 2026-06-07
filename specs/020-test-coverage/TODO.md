# Test coverage - TODO

Locked from the [study](STUDY.md). Target: **70% overall + 80% new-code** coverage, Sonar gate green.

## Decisions (locked)

| # | Decision |
| --- | --- |
| D1 | Exclude non-code-under-test from the coverage denominator (`packages/fixtures/**`, `**/__main__.py`, bpy-adjacent loaders). |
| D2 | Adopt in-Blender coverage instrumentation (spike first), so the already-tested bpy-bound code counts. |
| D3 | Target 70% overall + 80% new-code (ambitious; gate stays red until the phases land). |
| D4 | Sonar New Code Period = reference branch `main`. |
| D5 | Build a UXP host mock so `src/api/**` is unit-testable. |
| D6 | GDScript stays out of the Sonar coverage KPI (no analyzer). |

## Phase 0 - hygiene + policy (cheap, do first)

- [x] D1: `packages/fixtures/**` and `**/__main__.py` added to `sonar.coverage.exclusions` (e385f83). The `addon_loader.py` / `_types.py` calls are deferred to Phase 1 - decide there whether they are unit-testable or should be excluded.
- [x] D4: New Code Period set. REFERENCE_BRANCH is not honored for `main` on Community Edition (single-branch: `set` returns 200 but `show` keeps `PREVIOUS_VERSION`, and main-vs-main is degenerate). Applied the documented fallback on the local instance: `set?project=proscenio&branch=main&type=NUMBER_OF_DAYS&value=30` (note the `branch=main` param - a project-level set without it silently no-ops). REFERENCE_BRANCH=main stays the intent for the production SonarQube once it has multi-branch analysis.
- [ ] Re-scan: confirm `new_violations=0` (S3776 fixed in 382cf93) and the denominator drops the ~500 phantom lines.

## Phase 1 - pure-Python gaps (highest value per effort)

- [ ] Writer golden tests for `apps/blender/exporters/godot/writer/` - `animations.py` (0%, 131 lines) is the priority, then `skeleton.py` / `sprites.py` / `slots.py`. Build typed-model inputs, assert the emitted document; live under `tests/`.
- [ ] Cover the small 0% modules: `apps/blender/importers/photoshop/armature.py` (19), `packages/validator/.../addon_loader.py` (21), `_types.py` (10) - unless excluded in Phase 0.
- [ ] Top-ups: `core/validation/_shared.py` (52.8%), `core/_shared` (87%).
- Gate: `uv run --all-packages --all-groups pytest tests/ --cov=packages --cov=apps/blender --cov=scripts --cov-report=xml:coverage.xml`; pure-Python dirs >= 80%.

## Phase 2 - Photoshop host mock (D5)

- [ ] Add a vitest mock for the `photoshop` UXP module (a `vitest.setup.ts` / `__mocks__/photoshop.ts`) so `api/` imports resolve under test.
- [ ] Unit-test `src/api/**` (1.5% now, 474 uncovered): `active-document.ts`, `adapt-document.ts`, `_layer-find.ts`, document/layer reads, notifications.
- Gate: `pnpm -C apps/photoshop run test:coverage`; `src/api` >= 80%.

## Phase 3 - in-Blender coverage instrumentation (D2) [SPIKE GATES THIS]

- [ ] SPIKE: prove `coverage.py` runs inside `blender --background` - `sitecustomize.py` on the path with `COVERAGE_PROCESS_START`, or wrap the runner. Produce a `.coverage` data file from `run_operator_tests.py` + `run_tests.py`.
- [ ] Combine: `coverage combine` the in-Blender data with the pure-Python pytest run into one `coverage.xml` (keep `relative_files = true`).
- [ ] Drop bpy-bound from `sonar.coverage.exclusions`: `apps/blender/operators/**`, `panels/**`, `properties/**`, `core/bpy_helpers/**` (they are now measured).
- [ ] CI: emit + combine coverage in the `test-blender` job so the scan consumes the merged report.
- Gate: combined `coverage.xml`; bpy-bound dirs counted; overall >= 70%.

## Acceptance

- [ ] Sonar quality gate GREEN: `new_violations=0`, `new_coverage >= 80`, overall `coverage >= 70`.
- [ ] Coverage-generation commands current in the `sonar-project.properties` header.

## Risks

- Phase 3 feasibility is the ceiling-setter: if in-Blender instrumentation does not work cleanly, bpy-bound stays excluded and 70% overall may be unreachable without heavier pure-Python refactoring. Spike before committing the later tasks.
- Reference-branch new-code period may be limited on Community Edition; verify in Phase 0.
