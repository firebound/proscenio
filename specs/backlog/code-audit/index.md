# Code-structure audit (apps/blender)

Structural-quality findings for `apps/blender/` (196 source files, 1283 symbols inventoried), produced by a two-phase multi-agent audit on 2026-06-28 and then **adversarially verified** against the real code. Scope is architecture and maintainability: misplaced code, god modules, single-responsibility, dependency direction, duplication, dead code, and test quality. Distinct from [code-quality.md](../code-quality.md), which tracks type-safety and lint enforcement only.

Each entry promotes into a numbered spec under `specs/` when work begins.

**Status (2026-07-02): CLOSED.** The correctness bugs + the whole quick-win cleanup theme shipped under spec 074 (PRs #180 / #181 / #182); the low-severity bug tail, the four performance rewrites, the test-quality gaps (incl. the one medium `edit-weights-modal-lifecycle`), the `psd_naming` dead-module removal, and the two decision-gated correctness bugs (O3 / O4) shipped under spec 076 (PR #183); and the last theme - the structural god-modules / SRP decomposition - shipped under spec 075 (PR #184, incl. the pure `BoneSession` / `OpenStrokePen` controllers + the no-orphan-handler sweep). Every thematic file drained and was removed; the two god-module claims left un-split (`authoring-ik-module` refuted, `build-automesh-debug-stages` already decomposed) moved to [refuted.md](refuted.md), and the `automesh-test-monolith` split (pure-organization churn) to [deferred.md](../../deferred.md). Nothing open - this whole directory is now just the method + refuted record for the audit.

## Headline

The Blender app is **structurally healthy**. After adversarial verification, every confirmed finding is **low severity** except one medium (an untested modal lifecycle). There is no critical defect, no security hole, no large dead-code mass. The findings are refinement-grade: cohesion splits, bpy-boundary tidy-ups, and duplication that wants a shared helper. Pure-core logic is well tested (mostly 85-100% coverage); the test suite exercises real code with mock discipline confined to the bpy/IO boundary.

Treat this as a slow-burn cleanup backlog, not a remediation list.

## Thematic files

- **god-modules-and-srp.md** (removed) - the oversized modules / SRP splits shipped in spec 075 (PR #184); the ten Phase-A facade splits, the photoshop-planes split, the three large splits (quick_armature / automesh_authoring / the breaking ProscenioSkinningProps nesting), and the no-orphan-handler sweep. The two claims left un-split moved to [refuted.md](refuted.md).
- [refuted.md](refuted.md) - the phase-1 findings the verification pass disproved, plus the two the 2026-07-01 implementation found already-correct at HEAD (`driver-source-bone-enum-remap`, `feet-landing-name-over-tag`). Recorded so nobody re-flags them.
- **bugs.md** (removed) - the high/medium bugs shipped in spec 074 (PRs #180 / #181), the low-severity tail + performance + the two decision-gated bugs (O3 / O4) in spec 076 (PR #183). 5 finder dimensions (idprop contract, orphan datablocks, error paths, type-safety, version-compat) never ran under the original token limit - a future correctness pass can resume `wf_9067a358-8eb`.
- **duplication.md** (removed) - 14 of 15 DRY clusters folded in spec 074 Phase 3; the last (`perimeter-length-dup`) dissolved into spec 076's `arc-length-resample-quadratic`.
- **dead-code.md** (removed) - the four safe deletes shipped in spec 074 Phase 3; the `psd_naming` module in spec 076 Phase D.
- **test-quality.md** (removed) - the one medium + the weak-assertion hardenings + the coverage adds shipped in spec 076 Phase C; the `automesh-test-monolith` split moved to [deferred.md](../../deferred.md).
- **misplaced-code.md** (removed) - all 7 pure-logic moves shipped in spec 074 Phase 3.
- **dependency-direction.md** (removed) - all 3 accessors / the i18n relocation shipped in spec 074 Phase 3.

## Severity / effort tally (confirmed + adjusted only)

- By severity: 1 medium, the rest low.
- Quick wins (SHIPPED, spec 074 Phase 3): `Rect.area` / `VertexPen.dragging` / the 2 `_bpy_compat` shims deleted, `_build_stroke_cdt_inputs` inlined. (The 5 test-assertion hardenings moved to spec 076 Phase C.)
- Large refactors (SHIPPED, spec 075 PR #184): split `automesh_authoring.py` (a pure `OpenStrokePen` click-pen controller + a `stroke_pick` hit-test), `quick_armature.py` (a pure `BoneSession` undo/redo stack + a `ViewSnapshot` collaborator), and the breaking nested-PropertyGroup split of `ProscenioSkinningProps`.

## Method and confidence

Two phases, both read-only static analysis with no code changes.

- **Phase 1 (breadth).** Ten inventory agents (one per feature slice) cataloged symbols and flagged local smells; a synthesis agent grep-verified dead code; three agents audited test quality.
- **Phase 2 (depth + verification).** One skeptic agent per phase-1 finding (50 total) re-read the real code and returned confirmed / adjusted / refuted / uncertain with concrete evidence; five agents ran token-level duplication sweeps; three agents audited the repo-root pure-pytest suites; one reconciled the 16 source files phase 1 never inventoried. ~3.35M tokens across both phases.
- **Verdicts:** 27 confirmed, 17 adjusted (real but the detail/fix was corrected), 6 refuted (see [refuted.md](refuted.md)).
- **Coverage was measured, not guessed.** `apps/blender/tests/run_coverage.py` (fixtures suite, in-Blender, rc=0) plus a repo-root `pytest --cov=apps/blender` run. Pure-core numbers are authoritative; bpy-coupled modules read as 0% under plain pytest only because their operator tests require the in-Blender harness - that is a measurement artifact, not a real gap.

## Triage marker legend

`[severity/effort]` per entry. `DECIDIR (STUDY):` marks an open design decision (resolve in a STUDY, not by guess). `[quick win]` = safe, low-effort, no behavior change.
