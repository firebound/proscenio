# Spec 070 TODO: Draw mesh with vertices (manual contour)

Drives the rewritten [STUDY](STUDY.md). The feature is the SIMPLE contour placed by hand on a selected element, with the live triangulation preview the auto-gen already shows. Recommendations are (A) across the board; **confirm / lock with the user before implementing** (the first draft misread the feature, so this plan waits on a go).

Reuses the spec 066 OUTER contour tool + `compute_triangulation_preview` + the modal/overlay/APPLY. New surface: live-preview-while-drawing, RMB vertex drag, the LMB/RMB/DEL/ENTER scheme, the panel entry.

## 0. Discard the wrong first cut (before anything)

- [ ] Close PR #166 and delete branch `feat/070-mesh-pen-authoring` (the image-picker / from-blank / persisted-re-edit build). Start the corrected work on a fresh branch.
- [ ] Drop the wrong pieces: `operators/automesh/pen_mesh_new.py`, the `proscenio_authored_outer_contour` CP + its read/write helpers + `resolve_launch_mode` + the from-blank invoke branches + the from-blank panel button. (Keep nothing from the wrong draft unless decision 1 actually needs it.)

## 1. Live triangulation preview while drawing (decision 2)

- [ ] Drive `compute_triangulation_preview` from the in-progress contour: while the OUTER contour tool is active, set `output.outer` to the placed verts and recompute the preview on each placement / vertex drag-end (one CDT per change, never per MOUSEMOVE - the existing caching rule).
- [ ] Cursor ghost: per MOUSEMOVE, draw the next edge from the last vert to the cursor plus the candidate triangle (once 2+ verts exist), dashed / lighter - no CDT.
- [ ] Headless test where reachable: a contour of N placed verts yields a non-empty `triangulation_preview` (the pure preview path already tests; assert the in-progress drive).

## 2. RMB drag a placed vertex (decision 3)

- [ ] RMB press hit-tests the nearest placed vertex within a screen-pixel radius (reuse the stroke-delete nearest-pick pattern); a hit starts a drag, a miss is a no-op.
- [ ] RMB drag moves the grabbed vertex live and re-previews on move / release.
- [ ] RMB no longer finishes the pen (see decision 4); ENTER is the finish.
- [ ] Pure test: the nearest-vertex pick returns the right index within radius and None outside.

## 3. Control scheme + gesture remap, scoped to this tool (decision 4)

- [ ] In the upgraded contour tool: **DEL** deletes the last placed vertex (keep Ctrl+Z as a synonym), **ENTER** confirms, **RMB** drags, **ESC** cancels. Keep the composable extras (X/Z axis lock; wheel / digits = subdivide the last edge).
- [ ] Update `operators/automesh/_status_bar.py` OUTER-contour chords to the new scheme.
- [ ] Do NOT change the 066 contour pen's behavior outside this tool.

## 4. Entry + launch (decisions 1, 5)

- [ ] `panels/mesh_generation.py`: a **Draw with vertices** button (shown for a selected mesh element, beside Author Mesh) that launches the modal straight into the OUTER contour tool with the auto-trace skipped (empty outer, contour armed).
- [ ] The modal's invoke gains a "start in contour, no trace" launch path (a class flag set by the button, read-and-cleared in invoke) - the ONE small invoke change the corrected design keeps from the first cut.
- [ ] ENTER on the contour tool APPLYs directly (writes the mesh on the selected element); the existing stages stay reachable by Tab / advance for users who want extend / interior first.

## 5. Study / future (the user's "outras features" - not this PR unless trivial)

- [ ] Scroll = subdivide the last edge (the modal already subdivides; scope it to the last edge during drawing).
- [ ] Click-drag = spaced / smoothed verts (Moho/Spine free-draw with smoothing).
- [ ] Survey other Moho / Spine pen affordances for a follow-on.

## 6. Tests + gates

- [ ] Pure tests (preview drive, nearest-vertex pick) in repo-root `tests/`; in-Blender where the modal is needed.
- [ ] `run_operator_tests.py` + `run_tests.py` goldens (8/8 - manual authoring does not touch the writer fixtures).
- [ ] ruff (0.8.4) + mypy (`--config-file apps/blender/pyproject.toml`, from repo root) + repo-root `uv run pytest tests/`.

## 7. Post-merge cleanup (ONLY after the maintainer squash-merges)

- [ ] QA Companion: a "Draw with vertices" walk (place verts -> live preview -> RMB drag -> DEL -> ENTER), next free `BL-MESH-...` id.
- [ ] Lock the calls in [`decisions.md`](../decisions.md); remove the `mesh-pen-authoring` item from [`backlog/ui-feedback.md`](../backlog/ui-feedback.md).
- [ ] Prune this spec folder, index in [`_index.md`](../_index.md) with the PR number (070 planned -> pruned).
