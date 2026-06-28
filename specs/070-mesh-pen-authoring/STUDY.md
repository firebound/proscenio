# Spec 070: Draw mesh with vertices (manual contour)

A manual version of the SIMPLE-mode contour: instead of the alpha trace placing the silhouette automatically, the artist clicks the vertices one by one, with the same live triangulation preview the interactive auto-gen already shows. The Moho / Spine / Illustrator pen, expressed as "the simple flow, but I place the points".

Logged as `mesh-pen-authoring` in [backlog/ui-feedback.md](../backlog/ui-feedback.md).

> **This STUDY was rewritten 2026-06-28 after the first draft misread the feature.** The first draft invented an image-picker / from-blank element-creation flow and a persistence-for-re-edit field; that was wrong. The real feature is a manual point-placement contour on an ALREADY-selected element, with a live triangulation preview, run through the existing SIMPLE pipeline. The first implementation (PR #166) matches the wrong draft and is to be discarded - see the verdict.

## The flow (as specified by the user)

1. Select an element (an existing mesh element).
2. Mesh Generation > **Draw with vertices**.
3. Click = place 1 vertex.
4. Click again = +1 vertex and +1 edge (chained from the previous).
5. With 2+ vertices placed, a live preview shows the next triangle at the mouse position (dashed / lighter), the same simulation the SIMPLE interactive auto-gen draws.
6. Each click adds the next vertex + edge; the preview keeps showing how the verts will triangulate.
7. Controls: **LMB** place a vertex, **RMB** drag vertices, **DEL** delete the last placed vertex, **ENTER** confirm, **ESC** cancel.

The live triangulation preview is on the whole time, mirroring the SIMPLE interactive preview (`compute_triangulation_preview`).

## Scope

- **In:** a "Draw with vertices" entry on a selected mesh element; manual click-to-place vertices building the outer contour; a live triangulation preview during placement (not only at the preview stage); RMB to drag a placed vertex; DEL to drop the last; ENTER to commit; ESC to cancel.
- **Reuse:** the SIMPLE triangulation + its preview (`compute_triangulation_preview`), the `output.outer` -> downstream -> APPLY commit, the modal overlay + the contour click-pen that spec 066 already built.
- **Out (this spec):** DENSE authoring from manual verts; creating an element from nothing / an image picker (the element exists - this draws its mesh); a persisted re-editable authoring layer (not in the described flow).
- **Study / future (the user's "outras features"):** scroll = subdivide the last edge (the interactive modal already subdivides); click-drag = spaced / smoothed verts (Moho/Spine free-draw); other Moho / Spine pen affordances.

## Open decisions

### 1. Where it lives: upgrade the spec 066 contour tool, or a separate tool / modal?

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`PROSCENIO_OT_automesh_authoring`; the OUTER stage's "contour" tool `_handle_outer_contour_event` ~471 + `_commit_contour` ~858 already place manual verts and write `self._output.outer`; the bare-Tab tool cycle `_cycle_tool` ~534; `invoke` ~213 requires a selected MESH element with an image); `apps/blender/core/skinning/authoring_stages.py` (`stage_tools(OUTER) == ("auto", "contour")` - the manual contour is already a tool there); `apps/blender/panels/mesh_generation.py` (`_draw_automesh_interactive` ~218, the "Author Mesh (interactive)" button - the existing modal entry). Locked context: `decisions.md` "Mesh generation interaction" (spec 066: the contour reuses the click-pen in the OUTER stage; bare Tab cycles the tool).

**Question:** Spec 066 already ships a "Manual contour" tool in the OUTER stage (Tab to it, click verts, close the loop). But it has a different interaction model than the one specified here: it finishes on RMB/Enter, undoes with Ctrl+Z, free-draws on drag, and shows only the polyline (no live triangulation, no vertex dragging). Is "Draw with vertices" an upgrade of that tool, a second tool beside it, or a standalone modal?

**Options:**
- (A) Upgrade the 066 contour tool into "Draw with vertices": add the live triangulation preview, RMB-drag-vertex, DEL-last, and the ENTER-confirm model to the existing OUTER contour tool, and add a direct "Draw with vertices" button that launches the modal straight into it. One manual-contour tool, no duplication; the gesture remap (decision 4) lands on it.
- (B) A second OUTER tool ("vertices") beside "auto" and "contour" in the Tab cycle, with the new model, leaving the 066 contour tool as-is. No remap risk to 066, but two near-identical manual-contour tools confuse the cycle.
- (C) A standalone modal operator separate from the auto-gen modal, sharing only the triangulation core + overlay. Cleanest gesture model, but it re-implements the modal scaffolding (overlay, stage commit, APPLY) the auto-gen modal already owns - the most code and test burden.

**Recommendation:** **(A).** The 066 contour tool is already "place verts for the outer manually"; this spec is that tool done right (live triangulation + vertex editing + the cleaner LMB/RMB/DEL/ENTER model). Upgrading it keeps one manual path and reuses the whole modal (overlay, the `output.outer` commit, the downstream stages, APPLY). (B) leaves two manual-contour tools - exactly the saturation 066 just removed. (C) duplicates the hardest, least-testable code in the addon. **Decide whether the "Draw with vertices" button launches into the contour tool with the auto trace skipped (recommended) or whether the auto-trace still runs first and the user switches via Tab.** Size **M** for (A).

### 2. The live triangulation preview during placement

**Code anchors:** `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py` (`compute_triangulation_preview` ~477 - runs the real `build_automesh` on a throwaway copy and returns WORLD-XZ edge pairs; "callers compute this on stage-enter + param-dirty and cache it rather than every TIMER tick - one CDT per refresh"); `apps/blender/operators/automesh/automesh_authoring.py` (the PREVIEW_INTERIOR stage "Vertex preview" ~115/1192 where the triangulation preview is shown today; `self._output.triangulation_preview`); `apps/blender/core/skinning/authoring_stages.py` (`StageOutput.triangulation_preview` ~143). Locked context: the SIMPLE preview is the exact APPLY triangulation, drawn so the artist sees what they will get.

**Question:** The triangulation preview exists, but it is computed at the PREVIEW_INTERIOR stage from the finished contour, not live while the contour is being drawn. The feature wants it on continuously: as each vertex is placed (and as a vertex is dragged), re-triangulate the in-progress contour and draw it, plus a ghost of the next triangle at the cursor. How is it driven cheaply enough?

**Options:**
- (A) Recompute `compute_triangulation_preview` from the in-progress verts (set `output.outer` to the placed verts) on each placement / drag-end - one CDT per vertex, matching the existing "one CDT per refresh" cadence - and draw the ghost next-edge/triangle to the cursor per MOUSEMOVE (cheap, no CDT). Cache between placements; never CDT on the bare mouse-move.
- (B) Full re-triangulate on every MOUSEMOVE so the filled preview tracks the cursor exactly. Most faithful, but a CDT per mouse event is the cost the existing code explicitly avoids - risks lag on a large contour.
- (C) Only draw the polyline + a ghost triangle at the cursor while drawing, and the full triangulation preview only on a pause / the existing preview stage. Cheapest, but it is not the "live simulation like the auto-gen" the user asked for.

**Recommendation:** **(A).** It delivers the live filled preview the user wants while honoring the codebase's own rule (CDT per placement, not per mouse-move): the heavy preview updates when the contour actually changes (a click or a drag-release), and the lightweight cursor ghost (the next edge + the candidate triangle to the cursor) tracks the mouse every frame without a CDT. (B) reintroduces the per-tick CDT cost the preview caching was built to avoid. (C) under-delivers the simulation. **Decide the cursor ghost's fidelity: just the next edge to the cursor, or the full candidate triangle (recommended) once 2+ verts exist.** Size **M** (drive the existing preview from in-progress verts + the cursor-ghost overlay).

### 3. RMB drag to move a placed vertex

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`_draw_event` ~634 + `_draw_lmb_press` / `_draw_lmb_release` - the click-vs-drag machine; RMB currently finishes the pen at ~710 `event.type in {"RET", "NUMPAD_ENTER", "RIGHTMOUSE"}`; `_remove_outer_stroke_at_mouse` ~433 and the stroke pick `~1390` - the existing nearest-vertex-within-pixel-radius hit-test pattern to copy for grabbing a vert); `apps/blender/core/automesh/` (the pure 2D nearest-index helper the pick uses). Locked context: spec 066 "bare Tab cycles the tool; RMB/Enter finish".

**Question:** RMB must drag a placed vertex (grab the nearest one, move it, re-preview). The modal has no vertex-move gesture today, and RMB is currently bound to "finish the pen". What does the grab hit-test, and what does RMB stop doing?

**Options:**
- (A) RMB press hit-tests the nearest placed vertex within a screen-pixel radius (the same pattern the stroke-delete pick uses); if hit, RMB-drag moves it (live, re-previewing on move/release); if it hits nothing, RMB is a no-op. ENTER becomes the sole "confirm". The contour's vertices are the draggable handles.
- (B) A separate "edit verts" sub-tool (Tab) where LMB drags verts, leaving RMB free. Keeps RMB unbound but splits placing and moving across a mode switch the user did not ask for (they said RMB drags, in the same flow).
- (C) Move only the last-placed vertex with RMB (no hit-test). Trivial, but it cannot fix an earlier vertex - far short of "drag vertices".

**Recommendation:** **(A).** The user specified RMB drags vertices in the same drawing flow, so RMB grabs the nearest placed vertex and moves it, and ENTER takes over as the confirm (RMB stops finishing). It reuses the nearest-within-radius hit-test the delete pick already implements, so the grab is a known pattern. (B) forces a mode the user did not ask for; (C) is too weak. **Decide whether a vertex drag is undoable independently (DEL / Ctrl+Z) or only the placement order is.** Size **M** (the grab hit-test + the drag-move + re-preview; the gesture remap rides decision 4).

### 4. The control scheme and the gesture remap

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`_draw_event` ~634 - the pen's key/mouse handling: Ctrl+Z undo, RMB/Enter finish, X/Z lock, wheel/digit subdivisions, ESC cancel; `apps/blender/operators/automesh/_status_bar.py` - the chord cheatsheet the OUTER contour shows). Locked context: spec 066 "the fixed gestures survive as distinct keys (Ctrl+Z / X-Z lock / 0-9 / wheel / RMB-Enter / Esc / Alt+click)".

**Question:** The specified controls are LMB place, RMB drag, DEL last, ENTER confirm, ESC cancel - which reassigns RMB (was finish) and adds DEL (the 066 pen undoes with Ctrl+Z). Does the remap apply only inside "Draw with vertices", or to the 066 contour pen generally? And do the 066 extras (X/Z lock, wheel subdivisions) stay?

**Options:**
- (A) Remap within the upgraded contour tool (decision 1A): DEL = delete last vertex (keep Ctrl+Z as a synonym), ENTER = confirm, RMB = drag (no longer finish), ESC = cancel. Keep the 066 extras that compose (X/Z axis lock; wheel/digit = subdivide the last edge - decision 5 / the study item). The cheatsheet updates to the new scheme.
- (B) A global remap of the contour pen for every entry point. Simpler mental model, but it changes the 066-shipped contour behavior for existing users with no new entry.
- (C) Minimal: add DEL + RMB-drag, leave RMB also finishing on a no-hit. Ambiguous (RMB both drags and finishes) - rejected on principle.

**Recommendation:** **(A).** Scope the new scheme to the "Draw with vertices" tool so the 066 contour pen's shipped behavior is not changed out from under anyone, and keep the composable extras (axis lock; wheel = subdivide the last edge, which is the user's first listed study feature and already exists as a gesture). DEL deletes the last vertex with Ctrl+Z as a synonym; ENTER is the sole finish; RMB drags. (B) is a behavior change with no trigger; (C)'s RMB overload is ambiguous. **Decide whether to keep Ctrl+Z as a DEL synonym (recommended) or DEL-only.** Size **S** (key handling + the cheatsheet copy).

### 5. Commit + the relationship to the downstream stages

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`_commit_contour` ~858 writes `self._output.outer`; the stage machine `_advance` ~1090 / APPLY ~1138-1196 triangulates and writes the mesh; `_stages_for_mode("SIMPLE")` ~136); `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py` (`apply_mesh` - the final write). Locked context: spec 066 "the contour lives in the OUTER stage; downstream stages triangulate it unchanged".

**Question:** The flow ends at ENTER = confirm. Does ENTER commit the contour and jump straight to writing the mesh (APPLY), or commit the contour and leave the user in the existing stage flow (so they can still extend / add interior points before APPLY)?

**Options:**
- (A) ENTER commits the contour and APPLYs immediately (writes the mesh on the selected element), the shortest path matching "place verts, confirm, done". The user re-enters the modal for further edits (extend / interior) if they want them.
- (B) ENTER commits the contour and advances through the normal stages (edit outline -> interior -> apply), so the full toolset is one session. More power, but it is more than the described flow and re-introduces the multi-stage walk the user did not mention.
- (C) A preference / a modifier on ENTER chooses. Flexible, more surface.

**Recommendation:** **(A) as the default, with the stages reachable.** The specified flow is place-confirm-done, so ENTER from "Draw with vertices" should produce the mesh directly. Because it is the same modal, a user who wants the edit-outline / interior tools can still Tab / advance before pressing ENTER - so (A) is really "ENTER applies; the stages are there if you walk them", which is (A) and (B) without a hard either/or. (C) adds surface for a choice the default already covers. **Decide whether ENTER on the contour tool APPLYs directly (recommended) or always advances one stage.** Size **S** (route ENTER on the contour tool to APPLY).

## Verdict summary

"Draw with vertices" is the SIMPLE contour, placed by hand: upgrade the spec 066 OUTER contour tool (decision 1A) with a live triangulation preview driven from the in-progress verts plus a cursor ghost (2A), RMB-drag-to-move-a-vertex via the existing nearest-pick (3A), and the specified LMB/RMB/DEL/ENTER/ESC scheme scoped to this tool (4A), with ENTER applying directly while the existing stages stay reachable (5A). A "Draw with vertices" button on the Mesh Generation panel launches the modal straight into it on the selected element. It reuses `compute_triangulation_preview`, the `output.outer` commit, and the whole auto-gen modal; the new surface is the live-preview-while-drawing, the vertex drag, and the gesture remap. Open locks for the user: skip-the-trace-on-launch (1), cursor-ghost fidelity (2), drag undo granularity (3), Ctrl+Z-as-DEL-synonym (4), ENTER-applies-directly (5). Total size **M**.

**Discard the first implementation.** PR #166 / branch `feat/070-mesh-pen-authoring` built the wrong (image-picker, from-blank, persisted-re-edit) draft and must be closed; the corrected feature reuses the 066 contour tool rather than creating elements.

## Sources

- The user's specified flow (2026-06-28), captured verbatim under "The flow" above.
- Spec 066 (mesh-generation-interaction), the contour pen + SIMPLE triangulation preview this upgrades; see `_index.md` and `decisions.md` "Mesh generation interaction".
- `backlog/ui-feedback.md` - the `mesh-pen-authoring` entry.
- Code anchors above, current as of 2026-06-28 (`apps/blender/operators/automesh/automesh_authoring.py`, `core/bpy_helpers/automesh/authoring_pipeline.py`, `core/skinning/authoring_stages.py`, `panels/mesh_generation.py`).
