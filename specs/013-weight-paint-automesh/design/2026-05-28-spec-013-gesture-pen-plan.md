# SPEC 013 - Toggle-pen gesture model - Implementation Plan (Phase 2)

> **For agentic workers:** implement task-by-task. Each task = failing test -> implement -> run -> commit (where headless-testable; the gesture/event work is largely manual-smoke, flagged per task).

Date: 2026-05-28
Branch: `feat/automesh-authoring-ux-polish` (bundle, continues Phase 1)
Design: [`2026-05-28-spec-013-mesh-modes-and-gestures-design.md`](2026-05-28-spec-013-mesh-modes-and-gestures-design.md) (AS-AM16)
Predecessor: Phase 1 plan [`2026-05-28-spec-013-mesh-modes-and-gestures-plan.md`](2026-05-28-spec-013-mesh-modes-and-gestures-plan.md) (AS-AM14/15/17 - shipped).
Scope: **Phase 2 only** (AS-AM16). ~450 LOC. The riskiest piece: it rewrites the Stage 2 + Stage 4 input model and the modal event routing.

**Goal:** Replace the hold-modifier pen with a toggle-modal pen so the keyboard is free for axis-lock (X/Z) and subdivision count (scroll/digit), and a straight fold/cut line no longer collapses to a single long edge.

**Tech stack:** Python 3.11, Blender 5.1 (bpy + bmesh + gpu + blf + mathutils), pytest, ruff, mypy strict.

**Locked decisions (user, 2026-05-28):**
- Full toggle pen (design AS-AM16), replacing the current hold-modifier entry.
- Subdivisions apply to **pen straight segments only** (free-draw stays resampled by `interior_spacing`).

---

## Decisions table

| # | Decision | Choice |
|---|----------|--------|
| D1 | Pen entry | Tap Shift -> DRAW(fold) [Stage 4] / DRAW(extend) [Stage 2]; tap Ctrl -> DRAW(cut). No holding. Tapping the active modifier again exits to NEUTRAL when the line is empty; ignored once verts exist. |
| D2 | In DRAW | LMB click = append pen vert (axis-lock aware); LMB drag = free-draw stroke (chaikin + resample, commit on release, stay in DRAW); RMB or Enter = finish line; Esc = discard line; tap modifier = exit-if-empty. |
| D3 | NEUTRAL plain LMB | Stage 4: click = standalone `point` (unchanged). Stage 2: no-op (unchanged). Alt+click = delete (unchanged, both stages). |
| D4 | Axis lock | `X` toggles horizontal lock, `Z` toggles vertical lock, mutually exclusive (pressing one clears the other). Locks the NEXT pen vert relative to the last placed vert (Blender front-ortho: X = world-X horizontal, Z = world-Z vertical). Cleared on finish/cancel. |
| D5 | Subdivision count | `WHEELUPMOUSE` +1, `WHEELDOWNMOUSE` -1 (floor 0); digit `ZERO..NINE` sets exact 0-9. Per-edge count for the whole line. Lives in `self._pen_subdivisions`, shown in the tooltip. Reset to 0 on finish/cancel. |
| D6 | Subdivision application | **Bake at finish**: `subdivide_polyline(pts, n)` expands the pen polyline before it is appended to `user_strokes`. No `Stroke.subdivisions` schema field, no CDT-path change, no double-subdivision risk on reload. (Deviates from the design's "round-trip the count" - baking fully satisfies the user need; the count is transient draw state. Flagged: revisit only if re-editing a stroke's density is ever required.) |
| D7 | Event routing | Stage handlers get FIRST crack at every event so DRAW mode can intercept Enter/RMB (finish) + Esc (discard line) before modal nav. In NEUTRAL the handler returns None for Enter/Esc/Backspace so modal nav (advance/cancel/retreat) runs as today. |
| D8 | Scope | Applies to BOTH Stage 2 (outer: extend/cut) and Stage 4 (interior: fold/cut). Shared pen state machine; per-stage kind vocabulary + commit target (`_user_outer_strokes` vs `_user_strokes`). |

---

## State machine (per stage)

```text
NEUTRAL
  tap Shift  -> DRAW(extend|fold)      tap Ctrl -> DRAW(cut)
  Alt+LMB    -> delete stroke at cursor
  LMB click  -> Stage 4: standalone point; Stage 2: no-op
  Enter      -> advance stage          Esc -> cancel modal     Backspace -> retreat
DRAW(kind)
  LMB click            -> append pen vert (apply axis lock vs last vert)
  LMB drag             -> free-draw stroke (chaikin+resample), commit on release, STAY in DRAW
  X / Z                -> toggle horizontal / vertical axis lock (mutually exclusive)
  wheel / digit 0-9    -> set subdivision count (live tooltip)
  RMB / Enter          -> finish: bake subdivisions, append (kind) -> NEUTRAL
  Esc                  -> discard in-progress line -> NEUTRAL (does NOT cancel modal)
  tap active modifier  -> exit to NEUTRAL if no verts; else ignored
```

## Event routing rewrite (D7) - the riskiest change

`modal()` today handles ESC / RET / BACKSPACE BEFORE the stage dispatch. Reorder so the stage handler runs first and can consume those keys when a pen line is in progress:

```python
def modal(self, context, event):
    try:
        if self._stage == AuthoringStage.USER_OUTER:
            handled = self._handle_user_outer_event(context, event)
            if handled is not None:
                return handled
        if self._stage == AuthoringStage.USER_STEINERS:
            handled = self._handle_user_steiners_event(context, event)
            if handled is not None:
                return handled
        # Modal nav - only when the stage handler did not consume the event.
        if event.type == "ESC":
            return self._finish(context, cancel=True)
        if event.type in {"RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            return self._advance(context)
        if event.type == "BACK_SPACE" and event.value == "PRESS":
            return self._retreat(context)
        if event.type == "TIMER" and getattr(event, "timer", None) is self._timer:
            ... (mode-dirty + recompute, unchanged)
    except Exception:
        ...
    return {"PASS_THROUGH"}
```

The handler returns a set (consume) ONLY when pen-active for Enter/RMB/Esc; otherwise returns None so modal nav runs. **Risk:** a NEUTRAL Enter must still advance - verify the handler returns None for Enter when not pen-active. Land this behind the smoke checklist; there is no clean headless test for modal event order.

---

## File map (Phase 2)

**Modified:**
- `apps/blender/core/automesh/stroke_geometry.py` - `subdivide_polyline` pure helper
- `tests/automesh/test_stroke_geometry.py` - subdivide_polyline tests
- `apps/blender/operators/automesh_authoring.py` - toggle-pen state machine (Stage 2 + 4), event-routing reorder, X/Z lock, wheel/digit subdiv, tooltip + chord updates
- `apps/blender/core/bpy_helpers/automesh/authoring_overlay.py` - live-preview extensions (axis guide line + baked-subdivision vert preview)
- `specs/013-weight-paint-automesh/TODO.md` - mark AS-AM16 shipped

No schema change (D6: bake at finish), so `authoring_stages.py` / `authoring_pipeline.py` / `bridge.py` are untouched.

---

## Task 1: `subdivide_polyline` pure helper (AS-AM16)

**Files:** `core/automesh/stroke_geometry.py`, `tests/automesh/test_stroke_geometry.py`

- [ ] **Step 1: Failing tests**

```python
from core.automesh.stroke_geometry import subdivide_polyline  # noqa: E402


def test_subdivide_zero_returns_input():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    assert subdivide_polyline(pts, 0) == pts


def test_subdivide_one_inserts_midpoint_per_edge():
    out = subdivide_polyline([(0.0, 0.0), (1.0, 0.0)], 1)
    assert out == [(0.0, 0.0), (0.5, 0.0), (1.0, 0.0)]


def test_subdivide_two_inserts_two_evenly_spaced_per_edge():
    out = subdivide_polyline([(0.0, 0.0), (3.0, 0.0)], 2)
    assert [round(p[0], 3) for p in out] == [0.0, 1.0, 2.0, 3.0]


def test_subdivide_multi_edge_preserves_original_verts():
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    out = subdivide_polyline(pts, 1)
    assert out[0] == (0.0, 0.0) and out[2] == (1.0, 0.0) and out[-1] == (1.0, 1.0)
    assert len(out) == 5  # 2 edges, +1 mid each


def test_subdivide_single_point_or_empty_unchanged():
    assert subdivide_polyline([(2.0, 2.0)], 3) == [(2.0, 2.0)]
    assert subdivide_polyline([], 3) == []


def test_subdivide_negative_count_treated_as_zero():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    assert subdivide_polyline(pts, -2) == pts
```

- [ ] **Step 2: Implement**

```python
def subdivide_polyline(points: Sequence[Point2D], n: int) -> list[Point2D]:
    """Insert ``n`` evenly-spaced verts into every edge of an open polyline.

    n<=0 or polylines of length <2 return the input unchanged. Original
    verts are preserved; only interior points are added per edge, so a
    straight pen line stops collapsing to one long CDT edge (AS-AM16).
    """
    if n <= 0 or len(points) < 2:
        return list(points)
    out: list[Point2D] = [points[0]]
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        for i in range(1, n + 1):
            t = i / (n + 1)
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
        out.append((bx, by))
    return out
```

- [ ] **Step 3: Run + commit** `pytest tests/automesh/test_stroke_geometry.py -v` (existing + 6 new green); ruff + mypy.

---

## Task 2: pen state + NEUTRAL toggle entry/exit (Stage 4 first)

**Files:** `automesh_authoring.py`

- [ ] Add pen draw-mode state: `self._draw_mode_active: bool`, `self._draw_kind: str` ("fold"/"cut"/"extend"), `self._pen_subdivisions: int`, `self._axis_lock: str` (""/"x"/"z"). Reuse existing `_pen_active`/`_pen_points`/`_pen_kind` for the polyline buffer.
- [ ] NEUTRAL: tap Shift (`LEFT_SHIFT`/`RIGHT_SHIFT` PRESS) -> enter DRAW(fold), tap Ctrl -> DRAW(cut). Set `_draw_mode_active`, reset subdiv + axis. Tap active modifier with empty line -> exit NEUTRAL.
- [ ] Remove the hold-modifier entry in `_lmb_press` (the `event.shift/ctrl` branch that set `_press_modifier` + free-draw preview). Plain LMB in NEUTRAL stays = standalone point (Stage 4).
- [ ] Statusbar chord + tooltip reflect NEUTRAL vs DRAW.

**MANUAL SMOKE:** tap Shift enters fold-draw (statusbar shows DRAW); tap again (empty) exits.

---

## Task 3: DRAW-mode events + event-routing reorder (D7)

**Files:** `automesh_authoring.py`

- [ ] Reorder `modal()` per the routing block above (stage handler first, then modal nav).
- [ ] In `_handle_user_steiners_event`, when `_draw_mode_active`:
  - LMB PRESS click (no drag) -> `_pen_add_point` (axis-lock applied in Task 4).
  - LMB drag -> free-draw (existing `_commit_drag_stroke` on release), stay in DRAW.
  - `RET`/`NUMPAD_ENTER` or `RIGHTMOUSE` PRESS -> `_finish_pen_line` (bake subdiv, append) -> NEUTRAL. Consume.
  - `ESC` -> discard line -> NEUTRAL. Consume (do NOT cancel modal).
  - tap active modifier -> exit-if-empty.
- [ ] In NEUTRAL the handler returns None for Enter/Esc/Backspace so modal nav runs (verify advance/cancel/retreat still work).
- [ ] `_finish_pen_line`: `pts = subdivide_polyline(self._pen_points, self._pen_subdivisions)`; append `{"kind": draw_kind_to_stroke_kind, "points": pts}`; reset pen + subdiv + axis; persist + redraw.

**MANUAL SMOKE:** in DRAW, click 3 verts, Enter finishes (line committed); Esc on a fresh line discards without cancelling modal; NEUTRAL Enter still advances stage.

---

## Task 4: X/Z axis lock (D4)

**Files:** `automesh_authoring.py`

- [ ] `X`/`Z` PRESS in DRAW toggle `self._axis_lock` ("x"=horizontal/world-X, "z"=vertical/world-Z), mutually exclusive.
- [ ] `_pen_add_point` applies the lock: when `_axis_lock` set and `_pen_points` non-empty, snap the new vert to share the locked axis with the last vert (lock "x" -> new.z = last.z; lock "z" -> new.x = last.x). (Confirm axis->coord mapping in smoke; world XZ, front-ortho.)
- [ ] Axis lock cleared on finish/cancel.

**MANUAL SMOKE:** press X, click -> segment is perfectly horizontal; Z -> vertical; toggling X then Z switches.

---

## Task 5: scroll/digit subdivision count (D5)

**Files:** `automesh_authoring.py`

- [ ] `WHEELUPMOUSE` +1, `WHEELDOWNMOUSE` -1 (floor 0) in DRAW; digit `ZERO..NINE` PRESS sets exact 0-9.
- [ ] Tooltip in DRAW shows `... | subdiv N` and axis-lock state.
- [ ] Count baked at finish (Task 3). Reset to 0 on finish/cancel.

**MANUAL SMOKE:** scroll bumps the subdiv count in the tooltip; a straight 2-click line with subdiv=2 commits 4 verts (2 inserted).

---

## Task 6: live-preview extensions (overlay)

**Files:** `authoring_overlay.py`, `automesh_authoring.py`

- [ ] Extend `_draw_live_preview` (or its state dict) to render: (a) the axis-lock guide line from the last vert to the cursor (snapped to the locked axis), and (b) the baked subdivision verts that WILL be inserted, so the artist sees final density while drawing.
- [ ] Operator feeds `axis_lock` + `subdivisions` + `cursor` into the live-preview state dict.

**MANUAL SMOKE:** while drawing, the rubber-band shows the axis guide + ghost subdivision dots.

---

## Task 7: apply the pen to Stage 2 (outer)

**Files:** `automesh_authoring.py`

- [ ] Mirror the DRAW machine in `_handle_user_outer_event`: tap Shift -> DRAW(extend), tap Ctrl -> DRAW(cut); same click/drag/X-Z/scroll/finish/cancel; commit to `_user_outer_strokes`.
- [ ] Remove the Stage 2 hold-drag entry added in Phase 1 (`_outer_stroke_press` modifier branch) in favor of the toggle machine. Alt+click delete unchanged.
- [ ] Factor the shared pen logic so Stage 2 + Stage 4 use one implementation (kind + commit-target differ).

**MANUAL SMOKE:** Stage 2 toggle pen draws an extend/cut line with axis lock + subdivisions; cut overlay red.

---

## Task 8: docs

**Files:** `specs/013-weight-paint-automesh/TODO.md`

- [ ] Mark AS-AM16 items `[x]`; add a MANUAL_TESTING block for the gesture smokes above. Commit.

---

## Final verification

```bash
pytest tests/ -q                                          # pure (incl subdivide_polyline)
blender --background --python apps/blender/tests/run_operator_tests.py   # operator regress
ruff check apps/blender tests && (cd apps/blender && mypy --config-file pyproject.toml)
```

Then hand back for the gesture smoke (most of Phase 2 is interaction, not headless-testable).

## Risks

- **Event-routing reorder (Task 3)** is the highest-risk change - a NEUTRAL Enter/Esc must still drive modal nav. No clean headless test; relies on smoke. Land Task 3 in isolation and smoke before stacking Tasks 4-7.
- **bpy event type strings** (`WHEELUPMOUSE`, digit `ONE`..`NINE`, `RIGHTMOUSE`) must match Blender 5.1 enums - verify against the running build, not from memory.
- **RMB conflict:** RMB currently passes through (viewport context menu / nav). Consuming it to finish a line only in DRAW is fine; in NEUTRAL it must still pass through.
