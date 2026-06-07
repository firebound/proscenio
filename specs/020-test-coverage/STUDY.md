# Test coverage strategy

> **Shipped** (PR #95, squash `5b0bed4`): Sonar gate GREEN - overall coverage 36.0% -> 88.8%, new-code 58.7% -> 90.9%, 0 smells / bugs / vulnerabilities / violations. Execution status, the as-shipped decisions, and the final exclusion policy live in [TODO.md](TODO.md). The analysis below is the original pre-work study, kept as the historical record (its "Current measured state" and "Decisions pending" reflect the starting point, not the outcome).

## Problem

The Sonar quality gate fails on `new_coverage` (58.7% < 80%), and overall coverage sits at 36.0%. The bare number is misleading: large parts of the codebase are either not code-under-test (fixture generators), tested-but-uninstrumented (bpy-bound code exercised only inside Blender), or invisible to Sonar entirely (GDScript). Before chasing a percentage we need to know which lines *should* count, which are *already tested but not measured*, and which need *new tests*. This study maps that and proposes the levers in priority order.

The code itself is already clean: 0 bugs, 0 vulnerabilities, 0 security hotspots, 3 code smells (resolved), 0.9% duplication, A/A/A ratings. Coverage is the only weak axis.

## Current measured state (last Sonar scan)

- Overall coverage 36.0%; `lines_to_cover` 7106 after exclusions (down from 13537 raw).
- Gate (ERROR): `new_coverage` 58.7% (need 80), `new_violations` 0 after the smell fixes, duplication OK.
- New Code Period = `PREVIOUS_VERSION`, but the project version never changes (always `0`), so "new code" is ill-defined and the leak metric is noisy.

Per-directory uncovered hot spots (uncovered lines / coverage):

| Lines uncovered | Coverage | Path | Category |
| --- | --- | --- | --- |
| 474 | 1.5% | `apps/photoshop/src/api/**` | UXP boundary, needs host mocking |
| 188 + 143 + 86 + 51 | 0% | `packages/fixtures/**` | fixture generators, not code-under-test |
| 131 | 0% | `apps/blender/exporters/godot/writer/animations.py` | pure-ish writer, testable now |
| 34 | 0% | `packages/codegen/src/proscenio_codegen/__main__.py` | CLI entrypoint |
| 21 + 10 | 0% | `packages/validator/src/.../addon_loader.py`, `_types.py` | small, bpy-adjacent |
| 19 | 0% | `apps/blender/importers/photoshop/armature.py` | bpy-bound importer |
| (well covered) | 96% | `apps/blender/core/automesh`, `core/atlas` | reference for "good" |

## The five coverage categories

1. **Pure-Python, normal pytest (easy).** `apps/blender/core/` bpy-free modules (they lazy-import bpy) plus `packages/` (codegen, models, validator). Already well covered in places (automesh 96%, atlas 96%). Runs via `uv run pytest tests/`. Test infra: repo-root `tests/` (~24 suites + `automesh/`, `codegen/`, `skinning/`).

2. **bpy-bound, tested only inside Blender (the big blind spot).** `apps/blender/operators/`, `panels/`, `properties/`, `core/bpy_helpers/` (59 + 35 modules). These ARE tested - `apps/blender/tests/operators/` has 10 headless operator suites run via `blender --background --python run_operator_tests.py`, plus the 7-fixture suite in `run_tests.py`. But coverage.py is not instrumented inside that Blender interpreter, so none of it lands in `coverage.xml`. Today these dirs are listed in `sonar.coverage.exclusions` precisely because the normal pytest run cannot import them - so tested code is excluded rather than measured.

3. **Photoshop TS (mixed).** `src/lib/` is well covered (tag-parser, tag-writer, manifest-validator, etc. - 152 vitest tests across ~9 suites). `src/api/` (the UXP host boundary) is ~1.5% because it imports the live `photoshop` module; testing it needs a mocked host. `src/components/`, `src/hooks/` partially covered.

4. **GDScript (invisible).** `apps/godot/` has no Sonar coverage analyzer at all. `test_importer.gd` (50 assertions) + GUT exist for correctness but cannot move the Sonar number. Out of scope for the percentage.

5. **Not code-under-test.** `packages/fixtures/**` (build_blend.py and friends) generate fixtures; `__main__.py` CLI shims. Counting these as "uncovered" depresses the denominator for no value.

## Levers (priority order)

- **Lever 0 - denominator hygiene (quick win, hours).** Add `packages/fixtures/**`, `**/__main__.py`, and the bpy-adjacent loaders to `sonar.coverage.exclusions`. Removes ~500 phantom-uncovered lines so the percentage reflects real test targets. No new tests.

- **Lever 1 - cover the .proscenio writer (high value, days).** `apps/blender/exporters/godot/writer/` (animations.py at 0%, 131 lines, plus siblings) is the Blender->Godot contract producer and is largely pure (constructs typed models from inputs). Golden-fixture writer tests under `tests/` raise coverage and harden the most important output path. Pure-Python, no Blender needed if inputs are stubbed.

- **Lever 2 - in-Blender coverage instrumentation (biggest structural unlock, days-to-weeks).** Run coverage.py *inside* the headless suites (`COVERAGE_PROCESS_START` + `coverage.process_startup()` in a sitecustomize, or wrap with `coverage run`), then `coverage combine` the in-Blender data with the pure-pytest run into one `coverage.xml`. This makes the already-tested bpy-bound code (operators, panels, bpy_helpers) count, and lets us drop those from `coverage.exclusions`. Risk: Blender's bundled interpreter + extension import path make instrumentation fiddly; needs a spike.

- **Lever 3 - Photoshop host mock (medium, days).** Provide a vitest mock for the `photoshop` UXP module so `src/api/**` (474 uncovered) can be unit-tested. `lib/` purity rule means most logic is already testable; api/ is the boundary that needs the shim.

- **Lever 4 - GDScript (accept / separate).** No Sonar path. Keep `test_importer.gd` + GUT for correctness; optionally explore gdUnit4 coverage later, but it will not feed Sonar. Decide whether GDScript is simply out of the coverage KPI.

- **Lever 5 - gate policy (config, hours).** Set New Code Period to reference branch `main` so each PR is measured on its own diff, and adopt "tests land with new code." Makes the gate meaningful + achievable per-PR instead of chasing a retroactive 80% over a noisy leak period.

## Decisions pending

| # | Question | Options | Lean |
| --- | --- | --- | --- |
| D1 | Denominator scope | (a) exclude fixtures + `__main__` + loaders; (b) leave as-is | (a) |
| D2 | In-Blender coverage instrumentation | (a) spike + adopt (unlocks ~90 bpy-bound modules); (b) keep bpy-bound excluded, measure only pure-Python + TS | needs your call - (a) is the only way the operator/panel tests count |
| D3 | Coverage target | (a) gate new_coverage 80% (Sonar default); (b) lower to a realistic floor now, ratchet up; (c) overall-coverage target instead of new-code | (b) ratchet |
| D4 | New Code Period | (a) reference branch `main`; (b) number of days; (c) leave PREVIOUS_VERSION | (a) |
| D5 | Photoshop api/ testing | (a) build a `photoshop` host mock; (b) exclude api/ as untestable boundary | (a) |
| D6 | GDScript in the KPI | (a) accept invisible (exclude from the goal); (b) invest later | (a) |

## Suggested phasing

- **Phase 0 - hygiene + policy (D1, D4, D5-config):** coverage.exclusions cleanup, New Code Period = main, lower gate floor temporarily. Cheap; makes the number honest and the gate actionable.
- **Phase 1 - pure-Python gaps (Lever 1):** writer golden tests + the small 0% modules (validator loaders, importers/photoshop). Highest value-per-effort.
- **Phase 2 - Photoshop host mock (Lever 3):** unlock `src/api/**`.
- **Phase 3 - in-Blender coverage spike (Lever 2):** the structural unlock; de-risk with a spike before committing. If it works, drop bpy-bound from exclusions and ratchet the gate up.

## Open questions

- D2 is the crux: is the effort of in-Blender coverage instrumentation worth unlocking the bpy-bound dirs, or do we accept measuring only the pure-Python + TS surface and exclude bpy-bound for good? That single choice sets the achievable ceiling.
- What overall coverage number is the actual goal (not just the gate)? 50%? 70%? It changes how far Phases 1-3 must go.
