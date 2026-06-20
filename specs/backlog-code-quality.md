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

- The no-hard-wrap prose rule, the dead and placeholder code removals, and the frozen-dataclass tuple fix -> spec 054 code-review-cleanup.
- The god-file and single-responsibility hotspots (`automesh_authoring`, the `planes` material build) and the two sprite-bone-parent DRY folds -> spec 061 blender-module-decomposition.
- The documentation and help-text coverage pass -> spec 060 documentation-coverage-pass.
- The bundled `proscenio_models` wheel staleness gate was not planned as its own spec; it rides the next schema-touching spec (037 storage-split) and now lives in [`deferred.md`](deferred.md).

New code-health and toolchain-enforcement gaps land here.
