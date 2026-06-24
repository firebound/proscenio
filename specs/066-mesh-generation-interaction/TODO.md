# Spec 066 TODO: Mesh generation interaction

Drives the locked [STUDY](STUDY.md). D1: contour reuses the click-pen machine, closed loop -> `output.outer`. D2 (user-confirmed): bare Tab cycles the per-stage active tool, deleting the Shift/Ctrl tap-toggle and collapsing NEUTRAL/DRAW. D3: contour lives in the existing OUTER stage; downstream stages unchanged. Reopens the gated `manual-hull-pen-tool`.

The modal is intricate and headless-testable only at the pipeline + pure-helper level (the existing suite proves this). So: pure tool-cycle logic + the contour-commits-to-outer path get headless tests; the gesture dispatch is covered by a `_Probe`-style test where reachable and otherwise by the QA Companion GUI walk.

## 1. Pure tool-cycle helpers (testable, bpy-free)

- [ ] In a bpy-free core module (new `core/automesh/authoring_tools.py` or fold into an existing `core/skinning/authoring_stages.py`), add the per-stage tool vocabulary and cycle:
  - `stage_tools(stage, interior_mode) -> tuple[str, ...]`: OUTER -> `("auto", "contour")`; EDIT_OUTLINE -> `("extend", "cut")`; EDIT_INTERIOR_POINTS -> `("point", "fold", "cut")`; other stages -> `()` (no tool interaction).
  - `next_tool(stage, current, interior_mode) -> str`: cycle within `stage_tools`, wrapping; a stage with no tools returns `current` unchanged.
  - `default_tool(stage) -> str`: the tool a stage arms on entry (OUTER -> "auto", EDIT_OUTLINE -> "extend", EDIT_INTERIOR_POINTS -> "point").
  - `tool_is_pen(tool) -> bool`: True for `extend|cut|fold|contour` (LMB = pen); False for `auto|point` (auto = passive, point = single-click drop).
- [ ] Unit-test these in `tests/test_*` (pure, no Blender) - cycle order, wrap, default, pen classification.

## 2. Chord-machine rewrite in the modal (D2)

- [ ] Add `_active_tool: str` modal state (set to `default_tool(stage)` on every stage entry / mode flip / reset).
- [ ] Add a class-level `_current_active_tool: str` mirror for the status bar (like `_current_stage`).
- [ ] In `modal()`, handle bare Tab (no ctrl/shift/alt) BEFORE the per-stage dispatch: cycle `_active_tool` via `next_tool`, re-arm the pen (`tool_is_pen` -> enter pen with that kind; else exit pen + clear live preview), repaint VIEW_3D + STATUSBAR, return `RUNNING_MODAL`. Non-bare Tab passes through (Blender's Ctrl+Tab/Shift+Tab untouched).
- [ ] Delete the tap-toggle machinery from `_handle_pen_event`: the `_mod_tap_kind` PRESS/RELEASE tracking, `_on_modifier_tap`, and `_press_modifier` tap path. The stage is always armed with `_active_tool`:
  - pen tool active -> LMB click=vert / drag=draw / close-loop, X/Z lock, 0-9/wheel subdiv, RMB/Enter finish (commit + re-arm same tool), Esc cancel (clear in-progress line, stay on tool), Ctrl+Z undo vert-or-committed.
  - "point" active (interior) -> LMB click drops a Steiner point; Ctrl+Z undoes last committed.
  - "auto" active (outer) -> LMB ignored (slider/preview only).
  - Alt+click delete stays in every tool.
- [ ] `_pen_kind` is derived from `_active_tool` (extend/cut/fold map directly; contour is a new kind). Keep `_enter_draw`/`_exit_draw` but drive them from the active tool rather than a tap.
- [ ] Verify Ctrl+Z, X/Z, digits/wheel, finish/cancel/delete all still route (they are distinct keys, untouched by the Tab change).

## 3. Contour tool (D1)

- [ ] OUTER stage gains an event handler (today it has none): when `_active_tool == "contour"`, route LMB through the shared pen (`_handle_pen_event(..., "outer_contour")` or a thin wrapper) so click=vert / drag=draw / close-loop / subdiv / X-Z lock all work.
- [ ] On contour `_pen_finish` with a closed loop (>= 3 verts): set `self._output.outer = [the loop points]` (replacing the alpha-traced contour), refresh the OUTER overlay, and report the new vert count. Persist nothing new on the object (the contour is the live outer; APPLY consumes `output.outer`). Subdivisions bake into the loop like any pen.
- [ ] `auto` tool: the existing auto-trace stays; switching back to `auto` recomputes `compute_outer` (so Tab Auto<->Contour is reversible without losing the trace).
- [ ] Snap candidates for the contour pen: the loop's own verts (close-on-first-vert), no outer/stroke union needed (there is no prior outer when authoring it fresh).

## 4. Status bar (D2)

- [ ] Rewrite `emit_authoring_chord_layout` (`operators/automesh/_status_bar.py`) to read the active tool and show the Tab cycle per stage instead of the Shift/Ctrl tap chords:
  - OUTER: `Tab: Auto | Manual contour`; when contour active add the pen chords.
  - EDIT_OUTLINE: `Tab: Extend | Cut` + pen chords.
  - EDIT_INTERIOR_POINTS: `Tab: Point | Fold | Cut` + (point: LMB=point) / (pen: pen chords).
  - Keep Ctrl+Z undo, X/Z lock, 0-9/wheel subdiv, RMB/Enter finish, Alt+click delete, and Enter next / Backspace back / Esc cancel.
- [ ] Thread the active tool into `_draw_statusbar_authoring` via the new `_current_active_tool` class var.

## 5. Tests

- [ ] Pure helpers (step 1): cycle/default/pen classification.
- [ ] Headless (in-Blender) where reachable: a contour loop committed via the pen path sets `output.outer` to the loop (call the commit helper directly with a closed loop, assert `output.outer`); the existing pipeline tests stay green (the chord change does not touch `apply_mesh`).
- [ ] Confirm `test_automesh_authoring.py` (24 tests) stays green - none exercise the tap-toggle, so the rewrite must not regress them.

## 6. Gates

- [ ] `run_operator_tests.py` (full) + `run_tests.py` goldens (8/8 - the modal authors interactively and does not touch the writer, so goldens are byte-unchanged).
- [ ] `mypy` strict + `ruff format --check` + `ruff check` on `apps/blender`.

## 7. Post-merge cleanup (ONLY after the maintainer squash-merges the PR)

- [ ] QA Companion: rewrite the Quick-Armature-style automesh walk for the Tab-cycle scheme + add a contour-authoring walk (next free `BL-...` id); the modal gesture needs a GUI pass (it is not fully headless-testable).
- [ ] Lock the calls in [`decisions.md`](../decisions.md); note the `manual-hull-pen-tool` gate was reopened and shipped (update [`gated.md`](../gated.md)).
- [ ] Prune this spec folder, index in [`_index.md`](../_index.md) with the PR number.
