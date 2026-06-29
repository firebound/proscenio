# Spec 070: Manual mesh authoring (island silhouette control + standalone Manual Draw)

Two manual-authoring capabilities that share a closed-loop vertex pen but live in different places. **Manual Draw is a concept apart from the automeshes** - the artist picks one of three mutually-exclusive ways to make a mesh element, one per element:

1. **Automesh from Alpha** - fully automatic, no control (unchanged).
2. **Automesh Interactive** - the alpha trace as the base silhouette, then **manual island control** to add / remove / knife the silhouette + the interior stages. This spec replaces the silhouette-edit tools (see Part A).
3. **Manual Draw ("Draw with vertices")** - a standalone, isolated mode: the artist builds the whole mesh by clicking vertices, zero auto. This spec adds it (see Part B).

> **Rewritten 2026-06-28 (third pass).** Earlier drafts (a) invented an image-picker/from-blank flow, then (b) made "Draw with vertices" an upgrade of the Automesh OUTER "Manual contour" tool. Both wrong. The Automesh modal and Manual Draw must NOT be coupled (the modes are exclusive - using two on one element corrupts it, and the shared-operator launch let the draw open mid-automesh and break). The current branch (`feat/070`, uncommitted) carries the wrong coupling and is reverted by this plan.

## Part A - Automesh Interactive: manual island control on the silhouette

The alpha trace stays the base. The artist refines that silhouette with manual closed-loop **islands** plus the existing corridor knife, applied additively (never replacing the trace):

- **ADD** (closed island, NEW - replaces the open-stroke `extend`): a closed loop drawn over the silhouette edge **grows** it (union). The part of the loop outside the current silhouette is added. Must overlap the silhouette (a disjoint loop is dropped + warned).
- **KNIFE** (open stroke corridor - the current `cut`, renamed): an open stroke offset into a corridor that carves a gap. Unchanged behavior, new name.
- **REMOVE** (closed island, NEW): a closed loop **excludes** its area (a hole). The loop is the hole polygon directly.
- The old OUTER-stage **"Manual contour"** tool (closed loop that REPLACED the auto trace) is removed - its replace semantics are gone; its closed-loop pen tech is reused by ADD / REMOVE and by Part B.

The interior stages (interior points / fold, the triangulation preview, APPLY) are unchanged.

## Part B - Manual Draw ("Draw with vertices"): standalone isolated mode

A new operator, separate from the Automesh modal. The artist places the silhouette vertices by clicking; with 2+ verts a live triangulation preview tracks the cursor; the result is the SIMPLE triangulation of the hand-drawn contour. No alpha, no auto, no automesh stages.

Controls: **LMB** place a vertex, **RMB** drag a placed vertex, **DEL** (Ctrl+Z synonym) delete the last, **ENTER** apply (write the mesh), **ESC** cancel. Live triangulation + cursor ghost the whole time (mirrors the SIMPLE interactive preview).

Exclusivity: Manual Draw refuses to launch while the Automesh modal runs, and vice versa (one authoring modal at a time; the modes do not mix on an element).

## Decisions

### 1. Manual Draw is a standalone operator, not a tool inside the Automesh modal - LOCKED

The three modes are mutually exclusive (one per element); coupling them lets the user run both and corrupt the element, and a shared modal operator made the draw openable mid-automesh (class-level state clash). Manual Draw is its own modal operator (`PROSCENIO_OT_draw_mesh_vertices`, name TBD) with its own overlay + status bar, reusing only the PURE helpers (`contour_ring_from_pen`, `compute_triangulation_preview`, `apply_mesh` with a manual outer, `nearest_index`, the overlay draw functions). It does NOT touch the automesh stage machine. A poll/guard blocks overlap with the Automesh modal.

### 2. Automesh silhouette edits are additive islands, not a replace - LOCKED

The OUTER "Manual contour" replace tool is removed. Silhouette editing happens on top of the auto trace via ADD (grow), REMOVE (exclude), KNIFE (corridor). Lives in the silhouette-edit stage (today `EDIT_OUTLINE`). The `extend` open-stroke tool is replaced by ADD; `cut` is renamed KNIFE; REMOVE is new.

### 3. ADD island must overlap the silhouette (grow), via rasterize-into-mask - LOCKED

ADD grows the existing silhouette by **true union**, not a grafted arc. The first cut tried the extend-splice (`apply_outer_extends`) and it was wrong: a closed loop fed as an open extend grafts the loop as a *detour* (the contour "follows the drawing" with a spike - the bug the user hit). **Shipped implementation: rasterize the ADD island polygon into the alpha mask, then re-trace** (`compute_outer_merged` -> `fill_polygon_into_mask` + `extract_outer_contour_with_islands`). An overlapping island becomes one combined foreground blob, so the trace walks a single merged boundary - a clean union at trace resolution (consistent with the auto silhouette). `_split_outer_strokes` returns ADD islands as their own list; `_build_authoring_mesh` uses the merged contour as the outer override so APPLY + the live preview agree. World-XZ -> pixel is the inverse of `pixel_contour_to_world` (+ `matrix_world`).

A disjoint island (no overlap) does not merge - the trace finds the main silhouette and the island is effectively ignored (this is how "must overlap" self-enforces).

**Guidance UX (the user's question "how to tell the artist it must touch"):**

- The auto silhouette is always drawn so the artist sees where to overlap.
- The island pen snaps its verts to the silhouette boundary when near (`VertexPen` takes the silhouette verts as snap candidates).
- The committed merged-outer preview shows the grow live. (A live red "must overlap" cursor warning is a deferred polish - the island path does not run the per-cursor warn-tooltip yet.)

### 4. REMOVE island = exact polygon hole; KNIFE = the existing corridor - LOCKED

REMOVE is a closed loop, so it is a hole polygon directly - routed into `holes_world` (the same path alpha holes + the knife corridor already use, with the centroid prune). Exact, resolution-independent, no rasterize. KNIFE keeps the current corridor offset (`perpendicular_offsets` + `lens_polygon` -> `holes_world`), only the label changes.

### 5. Keep the `outer_is_manual` pipeline plumbing - LOCKED

Part B applies the hand-drawn contour through `apply_mesh`, which needs `_build_authoring_mesh` to honor a manual outer (no alpha re-trace, no resample). That plumbing (already added on the branch) stays; it also fixes the latent gap where the old 066 manual contour never reached APPLY.

### 6. Revert the wrong coupling from the Automesh modal - LOCKED

Remove from `automesh_authoring.py`: the `start_contour` prop + launch branch, the OUTER live triangulation, RMB-drag-vertex, DEL-last, ENTER-applies, the OUTER live overlay registration, and the OUTER "Manual contour" tool itself. The closed-loop pen tech moves to the ADD/REMOVE island tools (Part A) and the standalone Manual Draw operator (Part B).

## Open items - resolved (shipped)

- Stage/labeling: ADD / KNIFE / REMOVE are the `EDIT_OUTLINE` stage tools (Tab-cycled); OUTER is auto-only. **Confirmed by the user.**
- REMOVE via exact polygon hole (not rasterize). **Confirmed.**
- Manual Draw operator = `proscenio.draw_mesh_vertices`, panel label "Draw with vertices". **Confirmed.**
- Islands are silhouette-only; the interior stage keeps point / fold (additive detail), no islands. **Confirmed by the user.**
- Deferred polish: a live per-cursor "ADD must overlap" warning (the island path does not run the warn-tooltip yet); ADD currently warns only on the console when it splices to nothing.

## Testing feedback (2026-06-28, live iteration)

- **ADD result is correct, but the live merged-contour preview misreads.** A union outline can never align exactly with the drawn loop, so the green "this is what the merge will be" line was confusing. **Fix:** drop the live merged preview; render the islands as a dimmer overlay (alpha 0.6) ON TOP of the generated silhouette, and let the real union happen only at APPLY. (`compute_outer_preview` ignores ADD islands; `_ISLAND_ADD_COLOR` / `_ISLAND_REMOVE_COLOR` dimmed.)
- **Subdivision marks vanished once an edge was confirmed.** The scroll-to-subdivide ghosts only showed on the live rubber-band, not on already-placed edges. **Fix:** `_draw_placed_subdiv_ghosts` draws the subdivision ghost dots on every placed edge of the in-progress line (all pen tools).
- **Subdivision was global, should be per-edge.** Scrolling changed the density of every edge; the expected flow is: place vert, scroll to set this edge's density, place next vert (edge baked at that count), scroll again for the next. **Fix:** per-edge counts. `subdivisions` is now the CURRENT count (next edge / rubber-band); each placement bakes it into an `edge_subdivs` list; the ring/stroke subdivides per edge (`contour_ring_from_pen_edges` / `subdivide_polyline_edges`). Applies to VertexPen (Manual Draw + islands) and the open-stroke pen (knife / fold).

## UX overhaul (2026-06-29, panel + modal parity with Quick Armature)

The Mesh Generation panel read as cluttered and the modals did not follow the Quick Armature interaction conventions. Four changes:

- **Manual Draw is its own top-level panel.** It is manual mesh AUTHORING, not generation, and shares none of the automesh trace fields - sitting it under Mesh Generation made those shared fields look like they affected it. Now `PROSCENIO_PT_manual_draw` is a sibling panel (bl_order 6); Mesh Generation keeps the automeshes + their shared fields.
- **Buttons toggle (start / Exit).** Both "Author Mesh (interactive)" and "Draw with vertices" re-invoke as an Exit while their modal runs (Quick Armature `is_running` + `_exit_requested` handshake); the button shows "Exit ...", an X icon, and depressed. The guard module gained `is_running`.
- **Collapsible cheatsheet panel mirror.** While a modal runs, a `layout.panel(default_closed=True)` "Shortcuts" section mirrors the status-bar chords (`emit_authoring_chord_layout` / `emit_manual_draw_chords`), replacing the old minimal box indicator.
- **Mid-flight editing now works.** The pen consumed every mouse event, eating the cursor so the N-panel was unreachable. Now both modals gate mouse events to the viewport canvas (`event_in_canvas` via the stored invoke WINDOW region) and PASS_THROUGH over the UI - so sliders + the Exit button stay live, and the 0.1 s param timer re-previews the change. Keyboard gestures + nav are not gated. Removed the dead OUTER "Manual contour" dispatch + method (OUTER is auto-only now).

## UX round 2 (2026-06-29, panel nav + Manual Mesh standards)

- **Stage nav from the panel.** While the Automesh Interactive modal runs, the panel shows the current step label + **Back / Next** buttons above Exit. A small `proscenio.automesh_step` operator (direction enum) sets a `_nav_request` flag the modal applies on its next event (same as ENTER / BACKSPACE), so the stages are drivable without the keyboard.
- **Renamed "Manual Draw" -> "Manual Mesh"** (panel + feature id + help topic + doc page) - the old name did not read as mesh manipulation. The button stays "Draw with vertices". `PROSCENIO_PT_manual_mesh`.
- **Manual Mesh now follows the panel standards:** WARNS instead of hiding on a sprite / non-mesh (mirroring Mesh Generation's draw), and carries the standard status badge + help button (`draw_subpanel_header`, `manual_mesh` feature id = BLENDER_ONLY, `manual_mesh` help topic). As a new top-level panel it gets its own docs page (`docs/02-tools/blender-addon/09-manual-mesh.md`) + `_DOC_PATHS` + the `PANEL_PAGES` mirror entry (spec 064 exact-mirror).

## Verdict

Spec 070 grows into two parts: **(A)** replace the Automesh Interactive silhouette-edit tools with ADD (closed island, grow), KNIFE (renamed corridor cut), REMOVE (closed island, hole), additive on the auto trace; **(B)** a standalone **Manual Draw** mode (Draw with vertices), fully isolated from the automeshes. Revert the wrong draw-into-automesh coupling on the branch; keep the `outer_is_manual` plumbing. The closed-loop vertex pen is the shared building block.

## Part C - Manual Mesh authoring upgrades (2026-06-29, LOCKED)

The standalone Manual Mesh modal shipped as "draw a closed contour, apply the SIMPLE triangulation". The user asked for four upgrades; all map onto machinery the automesh pipeline already has, so the work is wiring + a modal phase split, not new geometry. Decisions LOCKED via Q&A (all four in spec 070; dense via an own panel toggle).

The unifying change is a **two-phase modal**: phase 1 DRAW the open contour (place / drag / per-edge subdiv / axis-lock, as today); closing the loop no longer auto-applies - it enters phase 2 EDIT (move verts, insert on edges, per-edge subdiv of placed edges, interior point/fold tools, dense toggle), where ENTER applies. This phase split is what makes items 1/3/4 coherent rather than four bolt-ons.

### C1. Dense fill toggle (decision: own panel toggle)

New scene prop `manual_interior_mode` (Enum SIMPLE/DENSE, default SIMPLE) on `ProscenioSkinningProps`, shown in the Manual Mesh panel; DENSE reveals the existing `automesh_interior_spacing` (shared world-unit knob). The modal `_params` reads it instead of hardcoding `interior_mode="SIMPLE"`. Outer stays verbatim (manual, no resample) in both modes; DENSE only changes the interior fill. Preview: today `compute_triangulation_preview` returns `[]` for non-SIMPLE (automesh shows a Steiner cloud instead). For Manual Mesh the throwaway-build-edges path works for both modes, so generalize it to a `compute_mesh_preview_edges(obj, image, output, params)` that returns the resulting mesh edges for ANY interior mode (SIMPLE keeps the existing helper as a thin wrapper); the manual overlay then shows a real wireframe in DENSE too.

### C2. Re-edit / continue a drawing (decision: store the source ring CP)

New Custom Property `proscenio_manual_contour` = `{points: [[x,z]...] LOCAL, edge_subdivs: [int...]}`; interior strokes reuse the existing `proscenio_user_strokes` CP. Reconstructing the source contour from the final triangulated mesh is lossy (subdiv + fill verts), so the source ring is stored explicitly. At apply (after a successful build) the modal writes the CP; at a fresh invoke (not the Exit handshake) it reads the CP and preloads the VertexPen (`points` world-converted via `matrix_world`, `edge_subdivs`, the interior strokes, the saved interior mode) directly into the EDIT phase, so the artist continues the existing drawing; ENTER re-applies (overwrites). LOCAL XZ storage keeps it stable if the object moves. A reverted element (071) clears this CP.

### C3. Interior verts / fold (decision: interior tool mode)

In the EDIT phase a tool toggle (Tab) switches OUTER (move/insert verts on the contour) <-> INTERIOR (point + fold). INTERIOR reuses the pipeline's `output.user_strokes` (kind `point` = single Steiner on click, `fold` = polyline on drag) - the exact inputs `_build_stroke_cdt_inputs` already consumes - and the existing `_draw_user_strokes` overlay. To avoid duplicating the automesh Stage-4 gesture capture, extract the click-vs-drag interior-stroke capture into a small shared helper used by both the automesh interior stage and the manual modal (`InteriorStrokePen` alongside `VertexPen`); if extraction proves entangled, fall back to a minimal in-modal capture writing the same `Stroke` dicts. Manual modal keeps `_user_strokes: list[Stroke]`, fed to `apply_mesh` via `output.user_strokes`.

### C4. Verts on existing edges (decision: in the EDIT phase)

`VertexPen` gains an EDIT phase (entered on close, not apply): clicking on a placed edge away from any vert inserts a vert splitting that edge (the two halves inherit a sensible subdiv); scrolling while hovering a placed edge changes THAT edge's `edge_subdivs` (today scroll only targets the in-progress next edge, which no longer exists once closed). RMB-drag of an existing vert and DEL stay available. This is the same `edge_subdivs` model extended from "the next edge" to "the hovered edge".

### Part C verdict

A two-phase Manual Mesh modal (DRAW -> close -> EDIT -> apply) backed by: a `manual_interior_mode` prop + a mode-agnostic preview helper (C1), a `proscenio_manual_contour` CP with preload-into-EDIT (C2), an interior point/fold tool reusing `user_strokes` (C3), and a `VertexPen` EDIT phase for on-edge insert + per-edge subdiv (C4). Sequenced cheap-first: C1, C2, then the EDIT-phase rework carrying C4 + C3. Spec 071 (revert-to-quad) is built alongside as its own operator.

## Sources

- User direction (2026-06-29): the four Manual Mesh upgrades (continue/re-edit; dense fill base; interior verts like fold; verts on existing edges); "todos os 4 na spec 070"; dense via an own panel toggle; build 071 too.
- User direction (2026-06-28): the 3 exclusive modes; "Manual Draw is a concept apart from the automeshes"; ADD-island-replaces-extend, cut->KNIFE, REMOVE island new; ADD must overlap; "tudo junto nesta spec 70".
- Code anchors: `apps/blender/operators/automesh/automesh_authoring.py` (modal, OUTER/EDIT stages, the pen), `core/bpy_helpers/automesh/authoring_pipeline.py` (`_build_authoring_mesh`, `compute_triangulation_preview`, `compute_outer`), `core/bpy_helpers/automesh/bridge.py` (`_read_alpha_and_extract_contours`, `holes_world`, `outer_override`), `core/automesh/outer_splice.py` (the old extend), `core/automesh/cut_geometry.py` (the corridor knife), `core/skinning/authoring_stages.py` (stage tools), `panels/mesh_generation.py` (entries).
