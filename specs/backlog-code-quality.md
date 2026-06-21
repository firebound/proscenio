# Code-quality backlog

Cross-cutting type-safety and lint-enforcement gaps surfaced by the 2026-06-06 quality audit. Scope is narrow: the project's hard rule is strong end-to-end typing across TypeScript, JavaScript, Python, and GDScript, with no hardcoded escape hatches (`any`, blanket `# type: ignore`, unscoped `eslint-disable`, `@ts-nocheck`) and no linters bypassed in CI or pre-commit.

These entries track places where a strict gate is configured but not enforced, or where a tree is exempted from type checking entirely. Feature-shaped work lives in [`backlog.md`](backlog.md); this file is exclusively code-health and toolchain enforcement. Each entry promotes into a numbered spec under `specs/` when work begins.

## Audit baseline (what is already clean)

So the next reader does not re-audit from scratch:

- **No blanket suppressions.** Every `# type: ignore` carries a specific error code (`[import-not-found]`, `[valid-type]`, `[arg-type]`); a grep for bare `# type: ignore` returns nothing. Every `eslint-disable-next-line` is single-line with a justification. The only `@ts-nocheck` is [`apps/photoshop/src/entry.ts`](../apps/photoshop/src/entry.ts) (vendored Adobe UXP starter shim, excluded from lint, documented). The only GDScript `gdlint: ignore` is one scoped line in a test.
- **tsconfig is maximally strict.** [`apps/photoshop/tsconfig.json`](../apps/photoshop/tsconfig.json) sets `strict`, `noImplicitAny`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, plus the unused-locals/params and `useUnknownInCatchVariables` checks.
- **mypy is strict-strict where it runs.** [`apps/blender/pyproject.toml`](../apps/blender/pyproject.toml), [`packages/validator/pyproject.toml`](../packages/validator/pyproject.toml), and [`packages/models/pyproject.toml`](../packages/models/pyproject.toml) + [`packages/codegen/pyproject.toml`](../packages/codegen/pyproject.toml) carry `strict = true` (the models/codegen pair drops `disallow_any_explicit` under the pydantic plugin; the rest of the strict profile holds).
- **CI does not bypass gates.** No `continue-on-error`, `allow_failure`, or `|| true` anywhere in [`.github/workflows/`](../.github/workflows/). [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) header states `--no-verify` is a bug. The `skipping` branches in `validate-schema` are "no fixtures present", not gate bypasses. ESLint runs as a CI step and a pre-commit hook.

## Open items routed to specs

The 2026-06-20 backlog-drain wave routed the entries that were here into specs (see [`_index.md`](_index.md)):

- The two sprite-bone-parent DRY folds shipped in spec 061; the god-file and single-responsibility hotspots (`automesh_authoring`, the `planes` material build) stay trigger-gated under spec 061 (split when the file fights the next change).
- The bundled `proscenio_models` wheel staleness gate was not planned as its own spec; it rides the next schema-touching spec (037 storage-split) and now lives in [`deferred.md`](deferred.md).

New code-health and toolchain-enforcement gaps land here.

- **ruff version drift, pre-commit versus CI.** The [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) ruff hook is pinned to 0.8.4 while CI runs `uvx ruff` (unpinned, currently ~0.15.x); the two disagree on `assert ..., (message)` line wrapping, so a file that passes the pre-commit hook can still fail CI `ruff format --check` (hit and worked around in spec 056). Align them - pin CI to the hook version, or bump the hook to match CI.
- **High cognitive-complexity functions (S3776), accepted not refactored.** Spec 063 accepted seven at-threshold S3776 findings via `sonar.issue.ignore.multicriteria` rather than refactor load-bearing code unsupervised: the Godot export writers (`exporters/godot/writer/{__init__,sprites,sprite_frame_animations}.py`), `core/automesh/outer_splice.py`, `operators/help_dispatch.py`, `operators/skinning/edit_weights.py`, and `apps/photoshop/src/lib/layer-descriptor.ts`. Behavior is pinned by the goldens and headless suites; extract collaborators when one of these files next fights a change, then drop the matching multicriteria entry.

## Test-coverage gaps (from specs 053, 052)

Behaviors shipped with verification by inspection + type/lint + (Blender) goldens, but without a dedicated automated test, because the current harnesses cannot reach them. Listed so a future coverage pass closes them. Paths already exercised by a golden or fixture are NOT listed (they are considered covered).

- **Photoshop has no React/component test harness.** The `apps/photoshop` vitest suite runs in the node environment over pure logic (`lib/`, `api/` with mocks); there is no jsdom + React Testing Library, so component and hook behavior is unverified. Uncovered behaviors from spec 053: the import button going busy before the picker (`useImportFlow`), the Validate panel's Doc-Refresh re-running the preview, the "From selection" no-marquee inline note, the tag-draft `selectionNote` clearing on manual edit, and the cosmetic JSX. Enabler: add jsdom + `@testing-library/react` to the vitest config, then cover these.
- **Blender operator paths without a dedicated test** (spec 052): the atlas Apply malformed-manifest report-and-cancel path (needs a corrupt packed-atlas manifest fixture), the Drive-from-Bone shortcut's UI enable-state for a zero-bone armature (needs a panel-draw assertion approach), the set-active-action freed-armature `ReferenceError` guard (needs a freed-datablock simulation), and the Quick Armature invoke seeding `lock_to_front_ortho` from the panel (the modal regression runs invoke but does not assert the seed). The `zip(strict=True)` writer guard is NOT listed - the goldens exercise that writer path with valid data.
