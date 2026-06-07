# Code-quality backlog

Cross-cutting type-safety and lint-enforcement gaps surfaced by the 2026-06-06 quality audit. Scope is narrow: the project's hard rule is strong end-to-end typing across TypeScript, JavaScript, Python, and GDScript, with no hardcoded escape hatches (`any`, blanket `# type: ignore`, unscoped `eslint-disable`, `@ts-nocheck`) and no linters bypassed in CI or pre-commit.

These entries track places where a strict gate is configured but not enforced, or where a tree is exempted from type checking entirely. Feature-shaped work lives in [`backlog.md`](backlog.md); this file is exclusively code-health and toolchain enforcement. Each entry promotes into a numbered spec under `specs/` when work begins.

## Audit baseline (what is already clean)

So the next reader does not re-audit from scratch:

- **No blanket suppressions.** Every `# type: ignore` carries a specific error code (`[import-not-found]`, `[valid-type]`, `[arg-type]`); a grep for bare `# type: ignore` returns nothing. Every `eslint-disable-next-line` is single-line with a justification. The only `@ts-nocheck` is [`apps/photoshop/src/entry.ts`](../apps/photoshop/src/entry.ts) (vendored Adobe UXP starter shim, excluded from lint, documented). The only GDScript `gdlint: ignore` is one scoped line in a test.
- **tsconfig is maximally strict.** [`apps/photoshop/tsconfig.json`](../apps/photoshop/tsconfig.json) sets `strict`, `noImplicitAny`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`, plus the unused-locals/params and `useUnknownInCatchVariables` checks.
- **mypy is strict-strict where it runs.** Both [`apps/blender/pyproject.toml`](../apps/blender/pyproject.toml) and [`packages/validator/pyproject.toml`](../packages/validator/pyproject.toml) carry `strict = true` plus the `disallow_any_explicit` / `disallow_any_decorated` / `disallow_any_unimported` trio and `warn_return_any`.
- **CI does not bypass gates.** No `continue-on-error`, `allow_failure`, or `|| true` anywhere in [`.github/workflows/`](../.github/workflows/). [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) header states `--no-verify` is a bug. The `skipping` branches in `validate-schema` are "no fixtures present", not gate bypasses.

The three entries below are the real holes.

## ESLint never runs in CI or pre-commit

**What:** [`apps/photoshop/package.json`](../apps/photoshop/package.json) defines `"lint": "eslint src"`, and [`apps/photoshop/eslint.config.mjs`](../apps/photoshop/eslint.config.mjs) stacks `strictTypeChecked` + `stylisticTypeChecked` (no-unsafe-assignment, no-misused-promises, no-explicit-any, require-await, ...). But the `lint-photoshop` CI job in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs only `pnpm run typecheck` (tsc) and `pnpm test` (vitest). There is no `eslint` step in CI, and no eslint hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml).

**Why it matters:** `tsc` catches implicit `any` and structural type errors, but the `no-unsafe-*` family - which catches `any` values flowing in from untyped library boundaries (UXP host API, dynamic imports) and propagating through typed code - is an ESLint-only rule set. With eslint unenforced, the entire `strictTypeChecked` ruleset is decorative: a regression can land an `any`-tainted value that tsc waves through. This is the single cheapest gap to close because the config already exists and passes today (assuming it is run).

**Scope sketch:** add a `Lint` step to the `lint-photoshop` job (`working-directory: apps/photoshop`, `run: pnpm run lint`) ahead of or alongside `typecheck`. Optionally mirror it as a pre-commit `local` hook (`entry: pnpm --dir apps/photoshop run lint`, `files: ^apps/photoshop/src/.*\.tsx?$`, `pass_filenames: false`) so it gates locally like ruff/mypy do. Verify the current `src/` tree passes clean first; fix or scope-justify any findings before wiring the gate so CI does not go red on the enabling commit.

**Trigger to revisit:** before relying on any `no-unsafe-*` / `no-explicit-any` guarantee in the Photoshop plugin, or the first time an `any`-tainted value reaches Godot through the manifest path and the post-mortem asks why lint did not catch it.

## packages/models and packages/codegen have no mypy gate

**What:** [`packages/models/pyproject.toml`](../packages/models/pyproject.toml) and [`packages/codegen/pyproject.toml`](../packages/codegen/pyproject.toml) carry no `[tool.mypy]` section, and the `lint-python` CI job runs mypy only against `apps/blender` and `packages/validator`. The pydantic source-of-truth package and the codegen CLI that emits the JSON Schema, TypeScript bindings, and GDScript Resources from it are never type-checked in strict mode.

**Why it matters:** `proscenio-models` is the single source of truth for every downstream binding - if its types are loose, the looseness propagates into the generated TS and GDScript that the whole pipeline depends on. The codegen emitter reasons over `typing` internals (`get_args`, `get_origin`, `Union`, `Annotated`) with several `Any`-typed helper signatures ([`godot_emit.py`](../packages/codegen/src/proscenio_codegen/godot_emit.py)); a strict gate there protects the artifact-generation logic that the committed-match tests assume is correct. These two packages are the foundation of the end-to-end typing rule yet sit outside its enforcement.

**Scope sketch:** add a `[tool.mypy]` block to each package mirroring the validator's strict-strict profile (`strict`, the `disallow_any_*` trio, `warn_return_any`, `python_version` per the package's real runtime - 3.11 floor for these, not the 3.13 Blender pin), with `files` rooted at each `src/`. Add two CI steps to `lint-python` (`mypy --config-file packages/models/pyproject.toml`, same for codegen) and matching pre-commit `local` hooks. The discriminator functions (`_layer_discriminator(payload: Any)`, `_element_discriminator(payload: Any)`) take pydantic's `Any` payload by contract; allow those as scoped `# type: ignore` or a narrowly-justified per-function relaxation rather than loosening the whole package.

**Trigger to revisit:** before the next schema/binding change that touches `proscenio-models`, or when a generated-binding drift slips past the committed-match tests because the emitter logic was itself mistyped.

## mypy `ignore_errors = true` exempts large bpy-bound subtrees

**What:** [`apps/blender/pyproject.toml`](../apps/blender/pyproject.toml) sets `ignore_errors = true` for the module globs `blender.core.bpy_helpers.*`, `blender.operators.*`, `blender.panels.*`, `blender.properties.*`; [`packages/validator/pyproject.toml`](../packages/validator/pyproject.toml) does the same for `addon_loader`, `coverage`, `measurement`. Inside those trees, type checking is fully off - `any` flows freely and mypy only parses for syntax and import-cycle errors.

**Why it matters:** this is the largest surface where the end-to-end typing rule does not hold today. It is documented tech debt, not a hidden bypass - the root cause is that no PEP 561 stubs ship for `bpy` / `mathutils` / `bmesh`, so the boundary cannot be typed without a frozen stub snapshot. But it is a real hole: an `any`-typed `dict[str, Any]` payload bag can move through these modules untracked. This entry overlaps with the existing ["bpy stubs via fake-bpy-module / bpy-stubgen"](backlog.md) item in `backlog.md`, which is the enabling dependency - that item provides the stubs; this one is the per-module override removal that follows.

**Scope sketch:** drive the overrides down module-by-module as the "bpy stub sweep" lands. Each module exits its `ignore_errors` override when its pydantic conversion + Protocol typing + bpy stub narrowing pass strict-strict. Track which modules have exited vs remain so the override globs shrink rather than ossify. The validator's three modules (`addon_loader`, `coverage`, `measurement`) are the smallest cluster and the natural first target; the strict gate there already runs against the pure no-bpy modules (`invariants`, `cli`, `report`).

**Trigger to revisit:** paired with the "bpy stubs" backlog item - when a frozen per-release stub snapshot lands, or the next Blender LTS jump forces a stub refresh, sweep the freed modules out of the override at the same time.
