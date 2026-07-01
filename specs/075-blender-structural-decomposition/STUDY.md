# Spec 075 STUDY: Blender structural decomposition (god-modules + SRP)

## Why

The 2026-06-28 structural audit ([backlog/code-audit/god-modules-and-srp.md](../backlog/code-audit/god-modules-and-srp.md)) catalogued the addon's oversized modules and single-responsibility splits. Spec 061 shipped the cheap DRY folds but **deferred the god-file extractions behind a trigger** (automesh_authoring, the planes material build). The trigger is now fired: this is the dedicated decomposition pass. The work is actively planned, not gated.

A 7-agent verification pass (2026-06-29, against HEAD) re-measured every module and re-read every cohesion claim. Specs 069/070 grew two of the targets since the audit (`quick_armature.py` 865 -> 1084, `automesh_authoring.py` 1556 -> 1642) and added `draw_mesh_vertices.py` + `vertex_pen.py` (the latter is the closed-loop-pen extraction the audit asked to "continue"). All 18 god-module/SRP items are VALID at HEAD except one: `authoring-ik-module` is REFUTED as a god-module (a single cohesive IK feature whose four operators share helpers - a size-only smell; splitting by operator would fracture the shared helpers, so it is out of scope).

Sibling spec [074-blender-code-audit-remediation](../074-blender-code-audit-remediation/STUDY.md) owns the correctness bugs, performance, dead-code, DRY folds, misplaced-pure-logic moves, dependency accessors, and test-quality from the same audit. This spec (075) owns only the module-restructuring theme.

## Scope

Behaviour-preserving module restructuring of `apps/blender/`:

- **3 large splits** - `automesh_authoring.py` (1642), `quick_armature.py` (1084), `ProscenioSkinningProps` (a flat ~351-line PropertyGroup referenced across 30 files / 67 sites).
- **~11 smaller SRP / cohesion splits** - extract collaborators or split a module by concern, each internal-only with a facade / re-export so callers are unchanged.
- **no-orphan-sweep** - the one structural correctness gap: both spec-070 authoring modals store draw-handler state per-instance, so an addon reload while a modal is live leaks the handlers with no recovery. The fix is the per-instance -> ClassVar refactor + a `_sweep_orphan_handlers` mirroring `quick_armature` - structural, so it rides here rather than 074.

Out of scope: `authoring-ik-module` (refuted), `build-automesh-debug-stages` (already decomposed into named helpers; the debug-stage early-returns cannot cleanly move - leave as-is unless touched).

## No functionality loss (the hard constraint)

Every split is behaviour-preserving and lands behind green guards - this is pure structure, zero behaviour change:

- The Godot writer splits are pinned by the **8/8 in-Blender goldens** (`run_tests.py`) plus the per-writer tests - byte-identical output is the pass bar.
- The operator splits are pinned by the in-Blender `run_operator_tests.py` suite; the public surface (`bl_idname` strings, re-exported symbols) stays stable so panels and cross-module imports do not change.
- The `ProscenioSkinningProps` nesting is the only **breaking** change (every `.skinning.<field>` access becomes `.skinning.<group>.<field>`); it is a mechanical rename verified by the full skinning operator suite + `test_properties`.

## Decisions (locked, with rationale)

| # | Decision | Rationale |
| --- | --- | --- |
| D1 | **Small-safe-first, large-last.** Phase A = the ~11 internal SRP splits (facade-safe, blast radius near zero). Phase B = `photoshop-planes-module` (medium, coordinates with 074's `place-and-tag-hidden-dep`). Phase C = the 3 large splits, one PR each. Phase D = `no-orphan-sweep`. | The cheap splits build confidence + de-risk the guards before the large module surgery; the breaking `ProscenioSkinningProps` rename comes last when the suite is well-exercised. |
| D2 | **Facade / re-export on every split** so callers and `bl_idname` references never change. Public names stay importable from their original module. | Keeps each split internal-only and the diff mechanical; the writer `__init__` / panel registration / test imports stay put. |
| D3 | **One PR per large split** (`quick_armature`, `automesh_authoring`, `skinning_props`); the Phase A small splits may be grouped a few per PR by area. | The large splits each have real blast radius + a distinct guard set; isolating them keeps review + bisect tractable. |
| D4 | **Coordinate the cross-spec file overlaps with 074.** `automesh_authoring.py` (075 large split) is also touched by 074's `automesh-snap-math-dup` (Phase 3) and the `automesh-modal-preamble` DRY fold; `photoshop-planes.py` by 074's `place-and-tag-hidden-dep` + `planes-placement-math`. Land the 074 cleanup first (smaller), then the 075 split rebases onto it. | Avoids two specs fighting the same file; the 074 cleanups are smaller and make the 075 split cleaner. |
| D5 | **Pure-logic homes per `.ai/conventions/code.md`** - bpy-bound collaborators under `core/bpy_helpers/<feature>/`, bpy-free helpers under `core/<feature>/`; single-operator files stay flat, multi-operator features become subpackages. | Matches the established module-organization convention so the result is idiomatic, not ad-hoc. |
| D6 | **Phase C (the large operator splits) lands AFTER spec 074's Phase 5 test-quality.** The `quick_armature` / `automesh_authoring` splits are only as safe as the operator-test coverage of the branches being moved - and 074 Phase 5 fills exactly the gaps the audit found (the untested modal lifecycle, the `_output` hand-off, the monolith reorg). Without that, a behaviour-preserving split could pass a thin suite while silently changing an uncovered branch. | A split is "behaviour-preserving" only to the extent tests prove it; do the coverage first, then the surgery. This is the honest guard for the highest-risk work in either spec. |

## Open items

- **O1 - attempt all three large splits, or stage them?** Recommendation: do Phase A + B + `no-orphan-sweep` for certain; tackle the 3 large splits in priority order `quick_armature` -> `automesh_authoring` -> `skinning_props` (the breaking one last), pausing for review after each. Confirm the appetite for the breaking `ProscenioSkinningProps` rename (30 files) vs leaving it as the single documented exception.

## Code anchors (verified at HEAD, re-measured)

`automesh_authoring.py` 1642 / `quick_armature.py` 1084 / `planes.py` 584 / `skeleton.py` (panels) 853 / `scene_props.py` ProscenioSkinningProps ~351 / `help_topics.py` 731 / `writer/__init__.py` 202 / `writer/sprites.py` 409 / `validation/export.py` 479 / `operators/selection.py` 506 / `operators/atlas_pack/_paths.py` 68 / `core/_shared/props_access.py` 235. Source: [god-modules-and-srp.md](../backlog/code-audit/god-modules-and-srp.md). Gates per the project: `uv run ruff check` + `ruff format --check` (+ `uvx ruff format --check`), `uv run mypy --config-file apps/blender/pyproject.toml`, repo-root `uv run pytest tests/`, in-Blender `run_operator_tests.py` + `run_tests.py` goldens (8/8).
