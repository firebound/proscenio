# Spec 070 TODO: Manual mesh authoring (islands + standalone Manual Draw)

Drives the rewritten [STUDY](STUDY.md). Two parts on one branch: **A)** Automesh Interactive silhouette edits become additive islands (ADD / KNIFE / REMOVE); **B)** a standalone **Manual Draw** mode, isolated from the automeshes. Decisions are LOCKED from the user Q&A; the few open items (STUDY "Open items") are confirmed before / during build.

## 0. Revert the wrong coupling (first)

- [ ] In `automesh_authoring.py` remove: the `start_contour` prop + launch branch, the OUTER live-triangulation drive, RMB-drag-vertex, DEL-last, ENTER-applies, the OUTER live-overlay registration (`_stage_outer_overlay_kwargs` + the overlay OUTER branch), the `close_loop` ghost wiring, and the OUTER "Manual contour" (`contour`) tool. The Automesh modal returns to its pre-070 behavior except where Part A changes it.
- [ ] Keep the `outer_is_manual` plumbing in `authoring_stages.py` + `authoring_pipeline.py` (Part B + the latent-gap fix rely on it).
- [ ] Keep the reusable PURE pen tech (`contour_ring_from_pen`) for ADD/REMOVE + Manual Draw.

## 1. Part A - Automesh Interactive island silhouette control

- [ ] Stage tools: in the silhouette-edit stage (`EDIT_OUTLINE`) replace `("extend", "cut", "delete")` with `("add", "knife", "remove", "delete")`. OUTER stage becomes auto-only (drop the `contour` tool).
- [ ] **KNIFE** = the current `cut` corridor, renamed only (labels, icons, status bar, warn text). No behavior change.
- [ ] **REMOVE** (closed island): a closed loop -> hole polygon routed into `holes_world` (reuse the cut-hole/`delete_faces_inside_holes` path; no corridor offset). Persist + preview like the other silhouette edits.
- [x] **ADD** (closed island, replaces extend): rasterized into the alpha mask + re-traced (`compute_outer_merged` / `fill_polygon_into_mask` / `extract_outer_contour_with_islands`) so an overlapping island UNIONS into one merged contour - not a grafted detour (the extend-splice first cut produced the "follows my drawing" spike and was replaced). A disjoint island does not merge (self-enforces "must overlap").
- [ ] ADD guidance UX: silhouette always drawn (dimmed); island pen snaps to the boundary (`_pen_snap_candidates`); live warn-tooltip when the loop is fully outside; APPLY drops a non-overlapping ADD with a WARNING.
- [ ] Live preview of the edited silhouette (the existing `compute_outer_preview` equivalent) reflects ADD/REMOVE so the artist sees the result before APPLY.
- [ ] Status bar + panel modal indicator: ADD / KNIFE / REMOVE labels + chords.

## 2. Part B - Manual Draw ("Draw with vertices") standalone

- [ ] New operator `PROSCENIO_OT_draw_mesh_vertices` (name TBD) - own modal loop, own overlay registration + status bar. Reuses PURE: `contour_ring_from_pen`, `compute_triangulation_preview`, `apply_mesh` (manual outer), `nearest_index`, the overlay draw funcs. No automesh stage machine.
- [ ] Controls: LMB place / RMB drag vertex / DEL (Ctrl+Z) last / ENTER apply / ESC cancel; live triangulation (one CDT per placement / drag-release) + cursor ghost (candidate triangle) per MOUSEMOVE; X/Z axis lock + wheel/digit subdivide reused.
- [ ] Panel: a **Draw with vertices** entry (its own operator), separate from "Author Mesh (interactive)".
- [ ] Exclusivity guard: Manual Draw poll refuses while the Automesh modal runs (and the Automesh entry refuses while Manual Draw runs) - one authoring modal at a time.

## 3. Tests + gates

- [ ] Pure/operator tests: ADD island grows the silhouette (mesh bigger, area covered); REMOVE island carves a hole (boundary edges, faces dropped); KNIFE unchanged (rename only - existing cut tests retargeted); disjoint ADD dropped + warned; Manual Draw applies the hand contour (mesh = the drawn shape, like the current manual-outer test); exclusivity poll blocks overlap.
- [ ] `run_operator_tests.py` + `run_tests.py` goldens (8/8 - silhouette tooling does not touch the writer fixtures).
- [ ] ruff (0.8.4) + mypy (`--config-file apps/blender/pyproject.toml`, from repo root) + repo-root `uv run pytest tests/`.

## C. Manual Mesh authoring upgrades (2026-06-29, LOCKED) - four items

Two-phase modal: DRAW (open contour) -> close -> EDIT (move/insert/subdiv/interior/dense) -> ENTER applies. Sequenced cheap-first.

### C1. Dense fill toggle (own panel toggle)

- [ ] Scene prop `manual_interior_mode` (Enum SIMPLE/DENSE, default SIMPLE) on `ProscenioSkinningProps`.
- [ ] Manual Mesh panel: draw the toggle; DENSE reveals `automesh_interior_spacing`.
- [ ] Modal `_params` reads `manual_interior_mode` instead of hardcoding SIMPLE.
- [ ] `compute_mesh_preview_edges` (mode-agnostic throwaway-build edges); SIMPLE wrapper kept; manual overlay shows the wireframe in DENSE too.
- [ ] Tests: apply DENSE yields more interior verts than SIMPLE on the same contour; preview helper returns edges for both modes.

### C2. Re-edit / continue (store the source ring CP)

- [ ] `proscenio_manual_contour` CP read/write helpers in `cp_keys.py` (`{points LOCAL, edge_subdivs}`); interior strokes reuse `proscenio_user_strokes`.
- [ ] Apply writes the CP after a successful build; invoke (fresh, not Exit) preloads pen + strokes + mode into the EDIT phase.
- [ ] Tests: CP round-trips; a re-invoke on a manually-meshed element preloads the contour (points + subdivs); 071 revert clears the CP.

### C3. Interior verts / fold (interior tool mode)

- [ ] Extract `InteriorStrokePen` (click=point, drag=fold) shared by the automesh Stage-4 capture + the manual modal; fall back to a minimal in-modal capture if entangled.
- [ ] Manual modal EDIT phase: Tab toggles OUTER <-> INTERIOR; INTERIOR writes `Stroke` dicts to `_user_strokes`; overlay via `_draw_user_strokes`.
- [ ] `apply_mesh` fed `output.user_strokes`; status bar + cheatsheet show the interior chords.
- [ ] Tests: a manual contour + an interior fold stroke applies with the fold's extra edge present.

### C4. Verts on existing edges (EDIT phase)

- [ ] `VertexPen` EDIT phase entered on close (not apply): click on a placed edge inserts a vert splitting it (halves inherit subdiv); scroll over a hovered placed edge changes THAT edge's `edge_subdivs`; RMB-drag + DEL stay.
- [ ] Manual modal: close enters EDIT (no auto-apply); ENTER applies; ESC clears the in-progress line then exits.
- [ ] Tests: insert-on-edge grows the ring vert count at the right position; hovered-edge subdiv changes only that edge.

### C. Gates

- [ ] ruff + mypy (`--config-file apps/blender/pyproject.toml`) + repo-root `uv run pytest tests/` + `run_operator_tests.py` + `run_tests.py` goldens (8/8).
- [ ] `manual_mesh` doc page (`09-manual-mesh.md`) updated for the two-phase flow + dense + interior + edge edits.

## 4. Post-merge cleanup (ONLY after the maintainer squash-merges)

- [ ] QA Companion: an Automesh-Interactive island walk (ADD / KNIFE / REMOVE) + a Manual Draw walk; next free `BL-MESH-...` ids.
- [ ] Lock the calls in [`decisions.md`](../decisions.md); remove `mesh-pen-authoring` from [`backlog/ui-feedback.md`](../backlog/ui-feedback.md).
- [ ] Prune this spec folder, index in [`_index.md`](../_index.md) with the PR number (070 planned -> pruned).
