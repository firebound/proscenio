# Dependency and version audit - June 2026

A read-only audit of every version-bearing surface in the Proscenio monorepo: language runtimes, package managers, runtime and dev dependencies, the pre-commit toolchain, GitHub Actions, and the two pinned external applications (Blender, Godot). The goal is to map what is outdated, separate the patch/minor noise from the structural majors, and lay out an ordered path to a clean, current greenfield before the imminent 1.0 release. Every "current" value is grounded in a file in the local checkout; every "latest" value was verified against PyPI, the npm registry, endoflife.date, or the upstream release pages on 2026-06-24.

Two dependabot PRs merged on remote `main` just before this audit and are not yet in the local checkout: #158 bumped the `python-dev` group (ruff 0.15.15 -> 0.15.19, plus check-jsonschema and pytest) and #157 bumped ten GitHub Actions. The tables below report the local checkout state and annotate where remote `main` already moved ahead, so the audit is usable whether you read it before or after pulling.

## Executive summary

The project is in unusually good shape for a pre-1.0 codebase. The Python lock is near the bleeding edge (mypy 2.1.0, pytest 9.x, ruff 0.15.x, numpy 2.4.x, pre-commit 4.6.0), the pinned pydantic 2.13.4 is the exact current release with no newer version available, the docs site runs current Docusaurus 3.10.1 on React 19 and TypeScript 6, and the photoshop dev toolchain already sits on eslint 9, vite 8, vitest 4, and typescript-eslint 8. There is no rot to clean up - this is a tidy-the-edges pass, not a rescue.

What actually matters before v1 is small and mostly mechanical:

1. Align the ruff pin. `.pre-commit-config.yaml` pins ruff `v0.8.4` while the uv dev-dependency resolves to ruff 0.15.x. The two run different linters over the same `apps/blender/` tree; local pre-commit and CI can disagree. Align both to 0.15.19.
2. Land the two already-merged dependabot PRs locally (#158 dev deps, #157 Actions) and stop the bleeding that false-blocks them: add `SONAR_TOKEN` to the repo's Dependabot secrets (or relax the Sonar required check for the `dependabot[bot]` actor). Today every dependabot PR red-Xes on SonarCloud because the scan runs with "Secret source: Dependabot" and the token is absent there.
3. Bump pinned Godot 4.6.2 -> 4.6.3 in CI. It is a single in-branch patch, the engine the recent release work already references, and it removes a known-issues delta before tagging v1.
4. Decide the Node line. CI and both JS workspaces target Node 22, which dropped from Active LTS to Maintenance LTS in October 2025; Node 24 is the current Active LTS. Moving the floor to 24 is a clean-greenfield decision worth making now rather than right after a 1.0.

The riskiest coupling is pydantic, and the good news is it is already at rest. pydantic is pinned 2.13.4 across the workspace lock and the bundled Blender wheels, and 2.13.4 is the latest release - so no action is needed and none should be taken. The point to internalize is what a future bump costs: any pydantic change forces re-vendoring 13 ABI-specific wheels under `apps/blender/wheels/` (pydantic-core ships one Rust wheel per platform x Python ABI, cp311 for Blender 4.2 and cp313 for Blender 5.x), regenerating the JSON Schema and the TypeScript/GDScript bindings, and re-baking fixtures and goldens. That is a dedicated PR, never a drive-by. The same "dedicated PR" rule applies to the JS majors that are available but should be held (Babel 8, eslint 10, TypeScript 6 for photoshop, webpack-cli 7) and to any Blender/Godot engine bump that would invalidate the baked fixtures.

Counts of what is behind, across everything inventoried:

- Major behind: 8 items - pnpm (9 -> 11, two majors), photoshop `@babel/*` (7 -> 8), photoshop eslint (9 -> 10), photoshop typescript (5.9 -> 6), photoshop webpack-cli (5 -> 7), and the Node runtime line (22 Maintenance -> 24 Active LTS). The four photoshop majors are deliberately held (see coupling notes); pnpm and Node are greenfield calls.
- Minor behind: 3 items - pytest (9.0.3 -> 9.1.1), photoshop typescript-eslint (8.60 -> 8.62), photoshop vite (8.0.16 -> 8.1.0).
- Patch behind: 6 items - ruff (0.15.15 -> 0.15.19, already in #158), check-jsonschema (0.37.2 -> 0.37.3), Godot (4.6.2 -> 4.6.3), photoshop vitest and @vitest/coverage-v8 (4.1.8 -> 4.1.9), photoshop webpack (5.106.2 -> 5.107.2), docs @types/react (19.2.16 -> 19.2.17).
- Config drift (not a version gap, but a real split): ruff pinned 0.8.4 in pre-commit vs 0.15.x in uv.

The deliberately-frozen pins are correct and should stay: React 16.14.0 in photoshop (UXP runtime constraint, not an upgrade target), `blender_version_min = "4.2.0"` (the 4.2 LTS floor the cp311 wheels exist for), and the `requires-python = ">=3.11"` packaging floor (which also explains why numpy holds at 2.4.6 - see the runtimes table).

The full audit follows.

## Runtimes and package managers

| Item | Current / pinned | Latest | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| Python packaging floor | `>=3.11` (root + every package `pyproject.toml`) | 3.13.14 stable; 3.14.6 exists | n/a (floor) | Hold | The floor is a deliberate compatibility contract for uv resolution and the cp311 Blender-4.2 wheel ABI, not a runtime version. Raising it is a coupled decision (see numpy + wheels), not a free bump. |
| Python type-check target (bpy-bound) | `3.13` (`apps/blender` + `packages/validator` `tool.mypy.python_version`) | 3.13.14 | current | Hold | Correctly tracks Blender 5.x's bundled CPython 3.13; the split from the 3.11 floor is intentional and documented in both files. |
| Python in CI (standalone jobs) | `3.11` (`ci.yml` lint-gdscript, validate-schema, test-godot; `setup-python`) | 3.13.14 | minor-line | Hold, optional bump to 3.12/3.13 | These jobs only run `pip install gdtoolkit` / `check-jsonschema` and Godot fixture sync; 3.11 is fine. Bumping to 3.13 would align CI with the type-check target but is cosmetic. |
| Node (CI + workspaces) | `22` (`ci.yml`, `sonar.yml`, `release.yml`, `docs-deploy.yml`; `apps/docs` `engines.node >=22.0`) | 24.17.0 (Active LTS); 22.23.1 (Maintenance LTS) | one LTS line | Needs-care (greenfield call) | Node 22 left Active LTS in Oct 2025; Node 24 is the current Active LTS. Bumping is low-risk for this codebase (webpack/Docusaurus builds) but touches all four workflows + `engines.node` + a lockfile re-resolve. Do it as the greenfield Node+pnpm PR, not piecemeal. |
| pnpm (CI) | `9` (all four workflows pass `version: 9` to `pnpm/action-setup`) | 11.9.0 | two majors | Needs-care | Two majors behind (9 -> 10 -> 11). Lockfile format and `pnpm install` semantics changed across both. Bump CI and the `packageManager` pin together with the Node bump so one lockfile re-resolve covers both. |
| pnpm (`packageManager` pin) | `pnpm@9.0.0` (`apps/photoshop/package.json`); `apps/docs` has no `packageManager` field | 11.9.0 | two majors | Needs-care | Photoshop pins corepack to pnpm 9; docs pins nothing (relies on the CI `version: 9`). Set a single current `packageManager` on both workspaces during the Node+pnpm PR so corepack and CI agree. |
| Blender (CI pin + dev) | `5.1.1` (`ci.yml` cache key + download URL) | 5.1.1 stable; 4.5 LTS / 4.2 LTS active; 5.2 LTS due Jul 2026 | current | Hold | CI already runs the current stable Blender. 5.2 LTS is weeks away but not released; chasing it pre-v1 is not worth re-baking fixtures. Revisit after 5.2 LTS ships (see spec 062 Blender-6 compatibility track). |
| Blender minimum (`blender_manifest.toml`) | `blender_version_min = "4.2.0"` | 4.2 is current LTS floor | n/a (floor) | Hold | The 4.2 floor is why the cp311 pydantic-core wheels are vendored. Raising it would drop a supported LTS and orphan the cp311 wheels; keep it. |
| Godot (CI pin) | `4.6.2-stable` (`ci.yml` cache key + download URL) | 4.6.3-stable (2026-05-21) | patch | Update now | Single in-branch patch (two string edits + cache key). 4.6.3 is the recommended upgrade over 4.6.2 and the engine the recent release commits already reference. No fixture re-bake within a patch line. |
| Godot feature version (`project.godot`) | `4.6` (`config/features`) | 4.6.x | current | Hold | Feature string tracks the minor line, not the patch; unaffected by the 4.6.2 -> 4.6.3 bump. |

Why numpy is not in the dev-dependency table as "behind": `apps/blender/pyproject.toml` requires `numpy>=2.0` and `uv.lock` resolves 2.4.6. numpy 2.5.0 exists but declares `requires-python = ">=3.12"`, so uv correctly holds the workspace at 2.4.6 under the `>=3.11` floor. This is a direct, citable consequence of the packaging floor: numpy cannot advance past 2.4.x until the floor moves to 3.12. `uv tree --outdated` does not flag it precisely because 2.4.6 is the latest version compatible with the declared constraint.

## Python dependencies

Resolved versions are from `uv.lock`; "behind" status is corroborated by `uv tree --outdated` run against the local lock. The split between the runtime deps (what ships) and the dev group (the toolchain) is called out because only one runtime dependency exists workspace-wide.

### Runtime (ships in the product)

| Item | Current (`uv.lock`) | Latest | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| pydantic | 2.13.4 | 2.13.4 | current | Hold | The single runtime dependency of `packages/models` / `packages/codegen` (`pydantic>=2.8,<3`). Already the latest release. The bundled Blender wheels and the workspace lock agree on 2.13.4. Do not bump for its own sake - see the coupling section for what a real bump would cost. |
| pydantic-core | 2.46.4 | (tracks pydantic 2.13.4) | current | Hold | Transitive under pydantic; the 13 vendored ABI wheels in `apps/blender/wheels/` are pinned to this exact build. Moves only when pydantic moves. |
| numpy | 2.4.6 | 2.5.0 (needs py>=3.12) | held by floor | Hold | Blender-runtime dep (`numpy>=2.0`); pinned at the floor-compatible 2.4.6. See the runtimes note. |
| typing-extensions / annotated-types / typing-inspection | 4.15.0 / 0.7.0 / 0.4.2 | same | current | Hold | pydantic's pure-Python transitives; all current and all vendored as wheels at matching versions. |

### Dev group (toolchain, does not ship)

| Item | Current (`uv.lock`) | Latest | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| ruff | 0.15.15 | 0.15.19 | patch | Update now | Already bumped to 0.15.19 by the merged PR #158; pull it locally. Then align the pre-commit pin to match (see CI hygiene). |
| mypy | 2.1.0 | 2.1.0 | current | Hold | The strict-strict gate across four packages already runs the latest mypy. |
| pytest | 9.0.3 | 9.1.1 | minor | Update now | Within #158's intent (the python-dev group bump); safe minor. |
| check-jsonschema | 0.37.2 | 0.37.3 | patch | Update now | Within #158's intent; trivial patch. Also pinned independently in pre-commit (0.31.0) - see CI hygiene. |
| pytest-cov | 7.1.0 | 7.1.0 | current | Hold | Current. |
| pre-commit | 4.6.0 | 4.6.0 | current | Hold | Current. |
| pillow | 12.2.0 | 12.2.0 | current | Hold | Current. |
| fake-bpy-module-latest | 20260501 | 20260501 | current | Hold | bpy stub snapshot, pinned newer than the 4.2 LTS target by design; bump when a new Blender LTS lands (the comment in `apps/blender/pyproject.toml` says exactly this). |

### Pre-commit hook toolchain (`.pre-commit-config.yaml`)

These pins are independent of `uv.lock` - pre-commit installs each hook in its own isolated env - so they drift separately and are easy to miss.

| Hook (repo) | Pinned rev | Latest | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| ruff-pre-commit | `v0.8.4` | 0.15.19 | many minors | Update now (align) | This is the headline drift: pre-commit lints `apps/blender/` with ruff 0.8.4 while uv + CI use 0.15.x. The two ruff versions can disagree on lint and format, so a clean pre-commit run does not guarantee a clean CI run. Pin to `v0.15.19` to match the uv dev dep and CI's `uvx ruff`. |
| check-jsonschema | `0.31.0` | 0.37.3 | several minors | Update | Same drift class as ruff: the schema-validation hook lags the uv-resolved 0.37.x. Validation behavior is stable across the gap, but align it for consistency. |
| pre-commit-hooks | `v5.0.0` | (current major) | current | Hold | Current. |
| godot-gdscript-toolkit | `4.3.3` | (gdtoolkit line) | check | Hold/verify | CI installs gdtoolkit unpinned (`pip install gdtoolkit`); the hook pins 4.3.3. Low risk; verify they format identically when next touching GDScript. |
| cspell-cli | `v8.17.1` | (cspell 8.x) | minor-ish | Hold | Spelling only; no functional risk. |
| mypy / eslint / drift-marker hooks | local | n/a | n/a | n/a | Run via the local `uv` / `pnpm`, so they inherit the workspace versions and carry no independent pin. |

## JavaScript dependencies - photoshop (`apps/photoshop`)

Resolved versions from `pnpm outdated` (run against the installed `node_modules`) and the lockfile. The plugin targets the UXP runtime, which constrains React hard.

| Item | Current | Latest | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| react / react-dom | 16.14.0 | 19.2.7 | three majors | Hold (frozen) | Not an upgrade target. UXP's embedded runtime is React 16; `@types/react@^16` and `react@^16.8.6` are pinned deliberately. Bumping would break the host. Leave it; this is correct, not debt. |
| @types/react / @types/react-dom | 16.14.69 / 16.9.25 | 19.2.x | three majors | Hold (frozen) | Must match the React 16 pin above. |
| typescript | 5.9.3 (range `^5.4.0`) | 6.0.3 | one major | Needs-care | TypeScript 6 is out and the docs workspace already runs it, but a major bump can surface new strict-mode diagnostics; the photoshop tree runs the no-unsafe-* eslint family on top. Bump in a dedicated PR with the eslint/typescript-eslint majors, not alone. |
| typescript-eslint | 8.60.0 | 8.62.0 | minor | Update now | Safe minor within the v8 line. |
| eslint | 9.39.4 | 10.5.0 | one major | Needs-care | eslint 10 is a flat-config-era major; pair with the typescript-eslint major that supports it. Dedicated tooling PR. |
| @babel/core + 4 babel plugins/presets | 7.29.x | 8.0.1 | one major | Needs-care | Babel 8 is a coordinated major across `@babel/core` and every plugin/preset; the repo already carries a `pnpm.overrides` entry forcing `@babel/core ^7.29.6`. Bump the whole babel set together, verify the webpack/babel-loader build still emits the UXP bundle, then drop or update the override. Dedicated PR. |
| vite | 8.0.16 | 8.1.0 | minor | Update now | Safe minor. Note vite is dev-only here and force-pinned via `pnpm.overrides` to `^8.0.16`; bump the override too. |
| vitest + @vitest/coverage-v8 | 4.1.8 | 4.1.9 | patch | Update now | Keep the two in lockstep (they must match); trivial patch. |
| webpack | 5.106.2 | 5.107.2 | patch | Update now | Safe patch within webpack 5. |
| webpack-cli | 5.1.4 | 7.0.3 | two majors | Needs-care | Two majors behind webpack-cli; the CLI majors changed flags and config handling. Bump with the webpack/babel tooling PR and re-verify `pnpm run build`. Hold otherwise. |
| ajv | 8.20.0 | 8.20.0 | current | Hold | Runtime schema validator; current. |
| nodemon | 3.1.7 (range) -> 3.1.14 resolvable | 3.1.14 | patch | Update now | Dev watch tool; trivial. |
| clean-webpack-plugin / copy-webpack-plugin / css-loader / style-loader / babel-loader / eslint-plugin-* | various | (current-ish) | none flagged | Hold | `pnpm outdated` did not flag these; they sit at the latest within their ranges. |

## JavaScript dependencies - docs (`apps/docs`)

The docs workspace is essentially current; `pnpm outdated` reports a single patch.

| Item | Current | Latest | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| @docusaurus/* (core, faster, preset-classic, theme-mermaid, module-type-aliases, plugin-client-redirects, tsconfig, types) | 3.10.1 | 3.10.1 | current | Hold | The entire Docusaurus surface is on the latest 3.10.1. Nothing to do. |
| react / react-dom | 19.2.7 (range `^19.0.0`) | 19.2.7 | current | Hold | Docs runs current React 19 - the opposite of the photoshop pin, and correct for a Docusaurus 3 site. |
| typescript | 6.0.3 (range `~6.0.2`) | 6.0.3 | current | Hold | Docs already runs TypeScript 6 successfully, which is the live proof point that the photoshop TS 6 bump is feasible. |
| @types/react | 19.2.16 | 19.2.17 | patch | Update now | One-patch drift; trivial. |
| @easyops-cn/docusaurus-search-local | 0.55.2 | 0.55.2 | current | Hold | Current. |
| docusaurus-json-schema-plugin | 1.15.1 | 1.15.1 | current | Hold | Renders the live Schema reference; current. |
| @mdx-js/react / clsx / prism-react-renderer / remark-github-admonitions-to-directives | various | (current within range) | none flagged | Hold | Not flagged by `pnpm outdated`. |

## GitHub Actions

The local checkout still pins the pre-#157 SHAs (shown below). PR #157, merged on remote `main`, already bumps these to the latest majors. The "Latest" column reflects #157's targets; "Recommendation" is therefore "pull #157" for the bumped set, with verification notes. All action uses are SHA-pinned with a version comment, which is the correct supply-chain posture and should be preserved through the bump.

| Action | Current (local SHA / comment) | Latest (per #157) | Gap | Recommendation | Rationale |
| --- | --- | --- | --- | --- | --- |
| actions/checkout | v4.2.2 | v7 | three majors | Pull #157 | Standard checkout; v5-v7 are runner/node-version housekeeping. Verify the `lfs: true` and `fetch-depth: 0` steps still behave (used by test-blender, test-godot, sonar). |
| astral-sh/setup-uv | v3.2.4 | v8 | five majors | Pull #157 | Large major jump; verify `uv sync --all-packages` still runs and caching still keys correctly in ci.yml + sonar.yml. |
| actions/setup-node | v4.1.0 | v6 | two majors | Pull #157 | Verify the `cache: pnpm` + `cache-dependency-path` block in docs-deploy.yml still resolves under v6. |
| actions/setup-python | v5.3.0 | v6 | one major | Pull #157 | Used by three jobs at python-version 3.11; low risk. |
| actions/cache | v4.2.0 | v6 | two majors | Pull #157 | Caches the Blender and Godot downloads by explicit key; verify cache hit/restore still works post-bump (a cache miss only costs a re-download, not a failure). |
| actions/upload-pages-artifact | v3.0.1 | v5 | two majors | Pull #157 | docs-deploy only; pairs with deploy-pages below. |
| actions/deploy-pages | v4.0.5 | v5 | one major | Pull #157 | docs-deploy only. |
| softprops/action-gh-release | v2.2.1 | v3 | one major | Pull #157 | release.yml only; verify the `prerelease:` expression and `files: dist/*` still upload on a dry-run dispatch before tagging v1. |
| pnpm/action-setup | v4.1.0 | v4 (SHA bump) | none (SHA) | Pull #157 | Same major; #157 only re-pins the SHA. The pnpm-version decision lives in the `version:` input (see runtimes), not here. |
| SonarSource/sonarqube-scan-action | v8.1.0 | v8.2 | minor | Pull #157 | sonar.yml only; minor. Does not by itself fix the Dependabot-secret problem below. |

## Coupling risks - where one bump cascades

These are the bumps that are never a single-line change. They are called out so they are scheduled as dedicated PRs, not attempted opportunistically.

- pydantic -> re-vendor wheels + regenerate bindings + re-bake. A pydantic bump means: download 13 new wheels into `apps/blender/wheels/` per the `wheels/README.md` recipe (pydantic + pydantic-core x 5 platforms x 2 ABIs + 3 pure-Python transitives), update the `wheels = [...]` block in `blender_manifest.toml`, re-build the local `proscenio_models` wheel, regenerate `packages/models/schemas/*.json` and the TS/GDScript bindings via the codegen, and re-run fixture validation and the round-trip goldens. The cp311/cp313 ABI split must be preserved (cp311 for Blender 4.2 LTS, cp313 for Blender 5.x). Not actionable now (2.13.4 is current) but this is the single most expensive bump in the repo.
- Blender or Godot engine bump -> re-bake fixtures and goldens. The Blender test job re-exports every fixture and diffs against committed goldens (`run_tests.py`); the Godot job walks baked `.expected.proscenio` goldens synced by `scripts/godot/sync_fixtures.py`. A minor engine bump (e.g. Blender 5.1 -> 5.2 LTS, or a Godot 4.6 -> 4.7) can shift exported values and force a goldens re-bake. The 4.6.2 -> 4.6.3 patch recommended above stays within a patch line and does not trigger this; a minor/major would, and belongs in the spec 062 / Blender-6 compatibility track.
- Node / pnpm major -> CI + lockfile re-resolve. Moving Node to 24 and pnpm to 10/11 touches all four workflows, both `engines.node` / `packageManager` declarations, and forces a fresh `pnpm-lock.yaml` resolution in each workspace. Do them as one PR so a single lockfile re-resolve covers the change, and run the frozen-lockfile install in CI to confirm reproducibility.
- TypeScript 6 / eslint 10 / typescript-eslint / Babel 8 / webpack-cli 7 (photoshop) -> one tooling PR. These majors interact: the eslint major needs a compatible typescript-eslint, TypeScript 6 may surface new diagnostics that the strict eslint config then enforces, and Babel 8 + webpack-cli 7 must still produce a working UXP bundle through babel-loader/webpack. Bump them together, drop the now-stale `pnpm.overrides` for `@babel/core` and `vite` if the direct deps cover them, and re-verify `pnpm run build`, `typecheck`, `lint`, and `test`. The docs workspace already proving TypeScript 6 + React 19 in production de-risks the TS half.

## Path to a clean v1 greenfield

Grouped and ordered. The first group is safe to land now with normal review; the second group each needs its own PR and verification.

### Group 1 - safe now (one or two small PRs)

1. Pull the two merged dependabot PRs into the local checkout: #158 (ruff 0.15.19, pytest 9.1.1, check-jsonschema 0.37.3) and #157 (the ten Actions). This is most of the patch/minor backlog in one step.
2. Align the ruff pin: set `.pre-commit-config.yaml` ruff-pre-commit `rev` to `v0.15.19` to match the uv dev dep and CI's `uvx ruff`. While there, bump the pre-commit check-jsonschema hook `0.31.0 -> 0.37.3` to match `uv.lock`. This closes the one genuine config split in the repo.
3. Bump pinned Godot `4.6.2-stable -> 4.6.3-stable` in `ci.yml` (download URL + cache key). Patch line, no fixture re-bake.
4. Sweep the safe JS minors/patches: photoshop typescript-eslint 8.62, vite 8.1.0 (and its override), vitest + coverage-v8 4.1.9, webpack 5.107.2, nodemon 3.1.14; docs @types/react 19.2.17. All within-major, all low-risk.

### Group 2 - dedicated PRs (each verified independently)

1. Node 24 + pnpm 11 greenfield: bump all four workflows to Node 24 and a current pnpm, set a matching `packageManager` on both workspaces (and add one to `apps/docs`, which currently has none), bump `apps/docs` `engines.node` to `>=24`, re-resolve both lockfiles, and confirm `pnpm install --frozen-lockfile` plus the builds pass. Best done first in Group 2 because it underlies the photoshop tooling PR.
2. Photoshop tooling majors: TypeScript 6, eslint 10 + matching typescript-eslint, Babel 8 (all `@babel/*` together), webpack-cli 7. Verify `build` / `typecheck` / `lint` / `test`; reconcile the `pnpm.overrides`. Keep React 16 frozen.
3. Engine/pydantic moves are explicitly out of scope for v1 unless forced: pydantic is already current; Blender 5.2 LTS is not yet released. Defer both to their tracks (the wheels recipe and spec 062) and do not bundle them into the v1 cleanup.

### CI hygiene (does not block v1, but stops recurring red Xes)

1. Fix the SonarCloud-on-dependabot false-block. Every dependabot PR fails the SonarCloud check because the scan runs in the Dependabot context ("Secret source: Dependabot" in the scan log) where `SONAR_TOKEN` is absent. Either add `SONAR_TOKEN` to the repository's Dependabot secrets (Settings > Secrets and variables > Dependabot), or make the Sonar check non-required for the `dependabot[bot]` actor (a branch-protection adjustment or a `sonar.yml` guard that skips the scan when the PR author is dependabot). Without this, the routine dependency bumps that keep the greenfield clean will keep arriving pre-failed and need manual override to merge.
2. Keep the SHA-pin-with-comment posture on every Action through the #157 bump; it is the correct supply-chain hygiene and the bump preserves it.
