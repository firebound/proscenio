# Code-structure audit (apps/blender)

Structural-quality findings for `apps/blender/` (196 source files, 1283 symbols inventoried), produced by a two-phase multi-agent audit on 2026-06-28 and then **adversarially verified** against the real code. Scope is architecture and maintainability: misplaced code, god modules, single-responsibility, dependency direction, duplication, dead code, and test quality. Distinct from [code-quality.md](../code-quality.md), which tracks type-safety and lint enforcement only.

Each entry promotes into a numbered spec under `specs/` when work begins. Nothing here is a fix already applied.

## Headline

The Blender app is **structurally healthy**. After adversarial verification, every confirmed finding is **low severity** except one medium (an untested modal lifecycle). There is no critical defect, no security hole, no large dead-code mass. The findings are refinement-grade: cohesion splits, bpy-boundary tidy-ups, and duplication that wants a shared helper. Pure-core logic is well tested (mostly 85-100% coverage); the test suite exercises real code with mock discipline confined to the bpy/IO boundary.

Treat this as a slow-burn cleanup backlog, not a remediation list.

## Thematic files

- [misplaced-code.md](misplaced-code.md) - pure logic trapped in bpy-bound modules (and the reverse). 7 confirmed/adjusted.
- [god-modules-and-srp.md](god-modules-and-srp.md) - oversized modules/functions and single-responsibility splits. 18 confirmed/adjusted.
- [dependency-direction.md](dependency-direction.md) - UI/panels reaching into operator internals; one core/ layering break. 3 confirmed.
- [duplication.md](duplication.md) - DRY clusters. 2 from phase 1 + **13 new** found by token-level body comparison. 1 high, several medium.
- [dead-code.md](dead-code.md) - grep-verified unused symbols + wire-or-remove decisions. 6 confirmed (2 trivial deletes, rest are decisions).
- [test-quality.md](test-quality.md) - test organization, weak/fake tests, measured coverage, and the suite's documented strengths.
- [refuted.md](refuted.md) - **6 phase-1 findings the verification pass disproved.** Recorded so nobody re-flags them.
- [bugs.md](bugs.md) - **correctness findings (40 candidates) - PENDING VERIFICATION.** Phase-3 deep pass (bug hunt + domain invariants + resource lifecycle + perf). The session token limit was hit before the verifier stage ran, so NONE are confirmed yet; treat as leads. Resume `wf_9067a358-8eb` to finish. 5 finder dimensions (idprop contract, orphan datablocks, error paths, type-safety, version-compat) did not run.

## Severity / effort tally (confirmed + adjusted only)

- By severity: 1 medium, the rest low.
- Quick wins (trivial effort, safe): delete `Rect.area`, delete `VertexPen.dragging`, delete 2 unused `_bpy_compat` shims, inline `_build_stroke_cdt_inputs`, the 5 small test-assertion hardenings.
- Large refactors (defer until touched for another reason): split `automesh_authoring.py` (~1556 lines), `quick_armature.py` (~865 lines), nested-PropertyGroup split of `ProscenioSkinningProps` (breaking, ~47 call sites).

## Method and confidence

Two phases, both read-only static analysis with no code changes.

- **Phase 1 (breadth).** Ten inventory agents (one per feature slice) cataloged symbols and flagged local smells; a synthesis agent grep-verified dead code; three agents audited test quality.
- **Phase 2 (depth + verification).** One skeptic agent per phase-1 finding (50 total) re-read the real code and returned confirmed / adjusted / refuted / uncertain with concrete evidence; five agents ran token-level duplication sweeps; three agents audited the repo-root pure-pytest suites; one reconciled the 16 source files phase 1 never inventoried. ~3.35M tokens across both phases.
- **Verdicts:** 27 confirmed, 17 adjusted (real but the detail/fix was corrected), 6 refuted (see [refuted.md](refuted.md)).
- **Coverage was measured, not guessed.** `apps/blender/tests/run_coverage.py` (fixtures suite, in-Blender, rc=0) plus a repo-root `pytest --cov=apps/blender` run. Pure-core numbers are authoritative; bpy-coupled modules read as 0% under plain pytest only because their operator tests require the in-Blender harness - that is a measurement artifact, not a real gap. See [test-quality.md](test-quality.md).

## Triage marker legend

`[severity/effort]` per entry. `DECIDIR (STUDY):` marks an open design decision (resolve in a STUDY, not by guess). `[quick win]` = safe, low-effort, no behavior change.
