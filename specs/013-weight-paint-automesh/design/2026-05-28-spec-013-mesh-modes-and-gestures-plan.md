# SPEC 013 - Mesh interior modes + gesture redesign - Implementation Plan (Phase 1)

> **For agentic workers:** implement task-by-task. Each task = failing test -> implement -> run -> commit. Checkbox (`- [ ]`) tracks progress.

Date: 2026-05-28
Branch: `feat/automesh-authoring-ux-polish` (bundle onto AS-AM13 polish, user choice 2026-05-28)
Design: [`2026-05-28-spec-013-mesh-modes-and-gestures-design.md`](2026-05-28-spec-013-mesh-modes-and-gestures-design.md) (AS-AM14..AS-AM17)
Scope: **Phase 1 only** (AS-AM14, AS-AM15, AS-AM17). Phase 2 (AS-AM16 gesture pen) is a separate plan.

**Goal:** Land the SIMPLE/DENSE interior mode, mode-dependent stage list, real triangulation preview, and the Stage 2 modifier-driven remap + cut-red. ~400 LOC + tests.

**Tech stack:** Python 3.11, Blender 5.1 (bpy + bmesh + gpu + blf + mathutils), pytest, ruff, mypy strict. CDT via `mathutils.geometry.delaunay_2d_cdt`.

**Locked open-question answers (user, 2026-05-28):**
- OQ1: triangulation preview recomputes on **stage-enter + param-dirty only** (not every TIMER tick); cache the result.
- OQ2: subdivisions support **both** scroll and digit (Phase 2 - not in this plan).
- OQ3: **no** SIMPLE density floor for now.

---

## Decisions table

| # | Decision | Locked default |
|---|----------|----------------|
| D1 | `interior_mode` enum values + UI labels | `SIMPLE` ("Simple (sparse, Spine-like)"), `DENSE` ("Dense (uniform fill)"); default `SIMPLE` |
| D2 | `StageParams.interior_mode` type | `Literal["SIMPLE", "DENSE"]`, default `"DENSE"` (back-compat: existing test constructors omit it -> DENSE = current behavior) |
| D3 | `build_automesh` param default | `interior_mode: Literal["SIMPLE","DENSE"] = "DENSE"` (existing callers/fixtures unchanged) |
| D4 | SIMPLE fill skip | set `interior_points = []` BEFORE `auto_interior_count` capture; `_merge_extra_steiners` still runs (user verts survive); `extra_base = outer + inner + 0` |
| D5 | Active stage list | `active_stages: list[AuthoringStage]`; SIMPLE drops `INNER_LOOPS`; both keep `STEINER_PREVIEW` (relabeled in SIMPLE) |
| D6 | Statusbar numbering | derive `"{idx+1}/{len(active_stages)} {base_name}"`; drop hardcoded `N/M` from `_STAGE_NAMES` |
| D7 | STEINER_PREVIEW label | DENSE: "Vertex preview"; SIMPLE: "Triangulation preview" |
| D8 | Mode flip mid-modal | TIMER dirty-detect recomputes `active_stages`; if current stage was dropped (INNER_LOOPS on flip to SIMPLE), snap to previous valid stage (USER_OUTER) |
| D9 | Triangulation preview source | new pure-ish helper `compute_triangulation_preview` runs the same CDT inputs APPLY uses in SIMPLE; returns world-XZ edge list; overlay draws wireframe |
| D10 | Stage 2 dispatch | modifier-driven identical to Stage 4: Shift=extend, Ctrl=cut, Alt=delete; remove `_point_inside_outer` intent resolution at PRESS |
| D11 | Stage 2 cut color | reuse Stage 4 red cut color; delete orange `_STROKE_VERT_COLOR_CUT_REMOVE` |

---

## File map (Phase 1)

**Modified:**
- `apps/blender/properties/scene_props.py` - `automesh_interior_mode` EnumProperty
- `apps/blender/panels/skinning.py` - dropdown in `_draw_automesh_box`
- `apps/blender/core/skinning/authoring_stages.py` - `StageParams.interior_mode` field
- `apps/blender/core/bpy_helpers/automesh/bridge.py` - `interior_mode` param + SIMPLE fill skip
- `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py` - thread `interior_mode` into `build_automesh`; add `compute_triangulation_preview`
- `apps/blender/operators/automesh_authoring.py` - `_snapshot_params`; `active_stages` nav refactor; statusbar label; STEINER_PREVIEW preview wiring; Stage 2 remap
- `apps/blender/operators/automesh_authoring.py` overlay / `authoring_overlay.py` - triangulation wireframe draw; Stage 2 cut color red
- `apps/blender/tests/operators/test_automesh_authoring.py` - headless tests
- `specs/013-weight-paint-automesh/TODO.md` - re-add IN-FLIGHT section + mark Phase 1 items shipped at end

**New tests:**
- `tests/automesh/test_interior_mode.py` - pure tests (StageParams default, etc.)

---

## Task 1: `interior_mode` enum on props + StageParams + panel (AS-AM14 data layer)

**Files:** `scene_props.py`, `authoring_stages.py`, `panels/skinning.py`, `automesh_authoring.py` (`_snapshot_params`), `tests/automesh/test_interior_mode.py`

- [ ] **Step 1: Failing pure test** - `tests/automesh/test_interior_mode.py`

```python
"""Pure tests for SPEC 013 interior_mode (AS-AM14)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.skinning.authoring_stages import StageParams  # noqa: E402


def _params(**kw):
    base = dict(
        resolution=0.25, alpha_threshold=1, margin_pixels=0, contour_vertices=64,
        inner_loop_count=0, inner_loop_spacing=0.15, interior_spacing=0.1,
        bone_radius=0.5, bone_factor=2,
    )
    base.update(kw)
    return StageParams(**base)


def test_interior_mode_defaults_to_dense_for_backcompat():
    assert _params().interior_mode == "DENSE"


def test_interior_mode_accepts_simple():
    assert _params(interior_mode="SIMPLE").interior_mode == "SIMPLE"


def test_stageparams_frozen_equality_includes_interior_mode():
    assert _params(interior_mode="SIMPLE") != _params(interior_mode="DENSE")
```

Run: `pytest tests/automesh/test_interior_mode.py -v` -> expect TypeError (unexpected kwarg).

- [ ] **Step 2: Add `interior_mode` to StageParams** (`authoring_stages.py`, after `cut_margin`):

```python
    cut_margin: float = 0.04  # corridor-hole gap width in world units (T-REV5)
    interior_mode: Literal["SIMPLE", "DENSE"] = "DENSE"  # AS-AM14
```

(`Literal` already imported.) Default DENSE so the ~40 existing `StageParams(...)` test constructors keep current behavior.

- [ ] **Step 3: Add `automesh_interior_mode` EnumProperty** (`scene_props.py`, in `ProscenioSkinningProps`, right before `automesh_interior_spacing` at line 138 so the SIMPLE/DENSE choice reads above the spacing it gates):

```python
    automesh_interior_mode: EnumProperty(  # type: ignore[valid-type]
        name="Interior mode",
        description=(
            "How the mesh interior is filled. SIMPLE triangulates only the "
            "silhouette, holes, and your fold/cut/steiner verts (Spine-like "
            "sparse mesh; best for most flat 2D-skinning sprites). DENSE adds "
            "the uniform interior grid + bone-density fill (capes, hair, fine "
            "border control)."
        ),
        items=[
            (
                "SIMPLE",
                "Simple (sparse, Spine-like)",
                "Constrained Delaunay over silhouette + holes + your verts only; "
                "no automatic interior fill",
            ),
            (
                "DENSE",
                "Dense (uniform fill)",
                "Uniform interior grid + bone-density subdivision (current default)",
            ),
        ],
        default="SIMPLE",
    )
```

- [ ] **Step 4: Panel dropdown** (`panels/skinning.py` `_draw_automesh_box`, after `automesh_contour_vertices` line 78, before `automesh_interior_spacing`):

```python
        col.prop(skinning_props, "automesh_interior_mode")
        col.prop(skinning_props, "automesh_contour_vertices")
        sub_dense = col.column(align=True)
        sub_dense.active = skinning_props.automesh_interior_mode == "DENSE"
        sub_dense.prop(skinning_props, "automesh_interior_spacing")
```

Move `automesh_interior_spacing` (line 79) + the density sub-block (lines 83-87) under a `sub_dense` column whose `.active` is gated on `interior_mode == "DENSE"`, so SIMPLE greys out the DENSE-only knobs (spacing, density-under-bones, bone radius/factor). Keep them drawn (greyed, not removed) so the artist sees what DENSE would expose.

- [ ] **Step 5: Thread into `_snapshot_params`** (`automesh_authoring.py:862`):

```python
        cut_margin=float(skinning.authoring_cut_margin),
        interior_mode=str(skinning.automesh_interior_mode),
```

- [ ] **Step 6: Run + commit**

```bash
pytest tests/automesh/test_interior_mode.py -v   # 3 passed
ruff check apps/blender tests && mypy apps/blender
git add apps/blender/properties/scene_props.py apps/blender/core/skinning/authoring_stages.py \
  apps/blender/panels/skinning.py apps/blender/operators/automesh_authoring.py \
  tests/automesh/test_interior_mode.py
git commit -m "feat(spec-013): interior_mode SIMPLE/DENSE on props + StageParams (AS-AM14)"
```

---

## Task 2: SIMPLE CDT path in `build_automesh` + apply_mesh thread-through (AS-AM14 algorithm)

**Files:** `bridge.py`, `authoring_pipeline.py`, `tests/operators/test_automesh_authoring.py`

- [ ] **Step 1: Failing headless test** (`test_automesh_authoring.py`): SIMPLE yields fewer interior verts than DENSE on the same fixture.

```python
def test_apply_mesh_simple_is_sparser_than_dense(automesh_fixture):
    obj = _activate("hand")
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import apply_mesh  # type: ignore[import-not-found]
    from proscenio.core.skinning.authoring_stages import StageOutput, StageParams  # type: ignore[import-not-found]
    base = dict(
        resolution=0.25, alpha_threshold=1, margin_pixels=0, contour_vertices=64,
        inner_loop_count=0, inner_loop_spacing=0.15, interior_spacing=0.1,
        bone_radius=0.5, bone_factor=2,
    )
    dense = apply_mesh(obj, image, StageOutput(), StageParams(**base, interior_mode="DENSE"), None)
    simple = apply_mesh(obj, image, StageOutput(), StageParams(**base, interior_mode="SIMPLE"), None)
    assert simple["total_verts"] < dense["total_verts"]
    assert simple["total_faces"] >= 1  # still a valid triangulation
```

Run headless -> expect AssertionError or TypeError (no `interior_mode` kwarg yet).

- [ ] **Step 2: Add `interior_mode` param to `build_automesh`** (`bridge.py:668` signature, after `cut_hole_loops`):

```python
    cut_hole_loops: list[list[tuple[float, float]]] | None = None,
    interior_mode: Literal["SIMPLE", "DENSE"] = "DENSE",
```

(import `Literal` at top if missing.)

- [ ] **Step 3: Skip the uniform fill in SIMPLE** (`bridge.py`, around lines 767-781). After the `_compute_steiner_points(...)` call returns into `interior_points`, before `auto_interior_count = len(interior_points)`:

```python
    interior_points = _compute_steiner_points(...)  # existing
    if interior_mode == "SIMPLE":
        # AS-AM14: sparse Spine-like mesh. Drop the uniform grid + bone-density
        # fill so only the silhouette, holes, and user verts (extra_steiners)
        # seed the CDT. extra_steiners still merge below; auto_interior_count
        # becomes 0 so extra_edges remap against (outer + inner + 0).
        interior_points = []
    auto_interior_count = len(interior_points)
```

Micro-opt: gate the `_compute_steiner_points` call itself behind `if interior_mode == "DENSE"` to skip the grid compute entirely (it is the expensive step). Keep `exclude_zones` computation only when DENSE. Verify the `debug_stage == "interior_points"` branch still behaves (SIMPLE -> empty points debug is fine).

- [ ] **Step 4: Thread through apply_mesh** (`authoring_pipeline.py:383` build call): add `interior_mode=params.interior_mode,` to the kwargs.

- [ ] **Step 5: Run + commit**

```bash
blender --background --python apps/blender/tests/run_tests.py -- -k "automesh"   # incl new sparser test
blender --background --python apps/blender/tests/run_tests.py                     # 7/7 fixtures (DENSE default = no regression)
ruff check apps/blender && mypy apps/blender
git add apps/blender/core/bpy_helpers/automesh/bridge.py \
  apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py \
  apps/blender/tests/operators/test_automesh_authoring.py
git commit -m "feat(spec-013): SIMPLE interior path in build_automesh (AS-AM14)"
```

---

## Task 3: mode-dependent `active_stages` + index-based nav + statusbar N/M (AS-AM15 nav)

**Files:** `automesh_authoring.py`, `tests/operators/test_automesh_authoring.py`

This is the trickiest Phase 1 task: the modal currently navigates by raw enum arithmetic (`AuthoringStage(self._stage +/- 1)`). Refactor to an ordered list.

- [ ] **Step 1: Failing headless test** - SIMPLE skips INNER_LOOPS; advance count differs by mode.

```python
def test_active_stages_simple_drops_inner_loops():
    from proscenio.operators.automesh_authoring import _stages_for_mode  # type: ignore[import-not-found]
    from proscenio.core.skinning.authoring_stages import AuthoringStage  # type: ignore[import-not-found]
    dense = _stages_for_mode("DENSE")
    simple = _stages_for_mode("SIMPLE")
    assert AuthoringStage.INNER_LOOPS in dense and AuthoringStage.INNER_LOOPS not in simple
    assert len(dense) == 6 and len(simple) == 5
    assert dense[-1] == AuthoringStage.APPLY and simple[-1] == AuthoringStage.APPLY


def test_stage_label_numbering_tracks_active_len():
    from proscenio.operators.automesh_authoring import _stage_label  # type: ignore[import-not-found]
    from proscenio.core.skinning.authoring_stages import AuthoringStage  # type: ignore[import-not-found]
    assert _stage_label(AuthoringStage.STEINER_PREVIEW, "SIMPLE").startswith("4/5")
    assert "Triangulation preview" in _stage_label(AuthoringStage.STEINER_PREVIEW, "SIMPLE")
    assert _stage_label(AuthoringStage.STEINER_PREVIEW, "DENSE").startswith("5/6")
    assert "Vertex preview" in _stage_label(AuthoringStage.STEINER_PREVIEW, "DENSE")
```

- [ ] **Step 2: Module-level helpers** (`automesh_authoring.py`, near `_STAGE_NAMES`):

Convert `_STAGE_NAMES` to base names (drop the `N/M` prefix):

```python
_STAGE_BASE_NAMES = {
    AuthoringStage.OUTER: "Outer contour",
    AuthoringStage.USER_OUTER: "Edit silhouette",
    AuthoringStage.INNER_LOOPS: "Inner loops",
    AuthoringStage.USER_STEINERS: "Interior detail",
    AuthoringStage.STEINER_PREVIEW: "Vertex preview",     # relabeled per mode
    AuthoringStage.APPLY: "Apply",
}
_SIMPLE_STAGE_ORDER = [
    AuthoringStage.OUTER, AuthoringStage.USER_OUTER,
    AuthoringStage.USER_STEINERS, AuthoringStage.STEINER_PREVIEW, AuthoringStage.APPLY,
]
_DENSE_STAGE_ORDER = [
    AuthoringStage.OUTER, AuthoringStage.USER_OUTER, AuthoringStage.INNER_LOOPS,
    AuthoringStage.USER_STEINERS, AuthoringStage.STEINER_PREVIEW, AuthoringStage.APPLY,
]


def _stages_for_mode(mode: str) -> list[AuthoringStage]:
    return list(_SIMPLE_STAGE_ORDER if mode == "SIMPLE" else _DENSE_STAGE_ORDER)


def _stage_base_name(stage: AuthoringStage, mode: str) -> str:
    if stage == AuthoringStage.STEINER_PREVIEW and mode == "SIMPLE":
        return "Triangulation preview"
    return _STAGE_BASE_NAMES[stage]


def _stage_label(stage: AuthoringStage, mode: str) -> str:
    stages = _stages_for_mode(mode)
    idx = stages.index(stage)
    return f"{idx + 1}/{len(stages)} {_stage_base_name(stage, mode)}"
```

- [ ] **Step 3: Operator holds active list + current mode.** In the class (near `_stage` init at line 127):

```python
        self._active_stages = _stages_for_mode(skinning_mode)   # computed at invoke
        self._interior_mode = skinning_mode
```

Resolve `skinning_mode` from `_snapshot_params(context).interior_mode` (or read prop directly) at invoke.

- [ ] **Step 4: Index-based `_advance` / `_retreat`** (lines 592-682). Replace `AuthoringStage(self._stage + 1)` / `- 1` with list-index walk:

```python
def _advance(self, context):
    idx = self._active_stages.index(self._stage)
    if idx >= len(self._active_stages) - 1:   # already APPLY
        return self._finish(context)          # whatever APPLY currently triggers
    next_stage = self._active_stages[idx + 1]
    # ... existing per-stage compute branches keyed on next_stage (unchanged) ...
    self._stage = next_stage
    type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
    type(self)._current_stage = self._stage
    # ... overlay re-register ...

def _retreat(self, context):
    idx = self._active_stages.index(self._stage)
    if idx == 0:
        return {"RUNNING_MODAL"}
    self._stage = self._active_stages[idx - 1]
    # ... existing per-stage compute branches ...
    type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
    type(self)._current_stage = self._stage
```

The per-stage compute branches (`if next_stage == ...:`) keep their current bodies. INNER_LOOPS branch simply never fires in SIMPLE because it is not in `_active_stages`.

- [ ] **Step 5: Mode flip mid-modal** (D8). In the TIMER dirty-detect path (where `_recompute_current_stage` runs on param change), detect `params.interior_mode != self._interior_mode`:

```python
    if params.interior_mode != self._interior_mode:
        self._interior_mode = params.interior_mode
        self._active_stages = _stages_for_mode(self._interior_mode)
        if self._stage not in self._active_stages:   # was INNER_LOOPS, now SIMPLE
            self._stage = AuthoringStage.USER_OUTER   # snap back to last valid
        type(self)._current_stage_label = _stage_label(self._stage, self._interior_mode)
        type(self)._current_stage = self._stage
        # re-register overlay for the (possibly) new stage
```

- [ ] **Step 6: Statusbar + initial label.** Replace remaining `_STAGE_NAMES[...]` reads (lines 100, 203, 656-657, 676-677, 968) with `_stage_label(stage, mode)` / `_stage_base_name`. The `_emit_authoring_chord_layout` header (line 968) uses `_stage_base_name(stage, mode)` - it needs the mode; surface it via the class attr `_current_interior_mode` mirrored alongside `_current_stage`.

- [ ] **Step 7: Run + commit**

```bash
blender --background --python apps/blender/tests/run_tests.py -- -k "active_stages or stage_label or automesh_authoring"
ruff check apps/blender && mypy apps/blender
git add apps/blender/operators/automesh_authoring.py apps/blender/tests/operators/test_automesh_authoring.py
git commit -m "feat(spec-013): mode-dependent active_stages + index nav + N/M statusbar (AS-AM15)"
```

---

## Task 4: real triangulation preview at SIMPLE step 4 (AS-AM15 preview)

**Files:** `authoring_pipeline.py` (new `compute_triangulation_preview`), `automesh_authoring.py` (wire on stage-enter), overlay draw, `tests/operators/test_automesh_authoring.py`

OQ1: compute on stage-enter + param-dirty, cache. Do NOT recompute per TIMER tick.

- [ ] **Step 1: Failing headless test** - preview returns edges for a fixture in SIMPLE.

```python
def test_triangulation_preview_returns_edges(automesh_fixture):
    obj = _activate("hand")
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import compute_triangulation_preview  # type: ignore[import-not-found]
    from proscenio.core.skinning.authoring_stages import StageOutput, StageParams  # type: ignore[import-not-found]
    params = StageParams(resolution=0.25, alpha_threshold=1, margin_pixels=0,
                         contour_vertices=64, inner_loop_count=0, inner_loop_spacing=0.15,
                         interior_spacing=0.1, bone_radius=0.5, bone_factor=2, interior_mode="SIMPLE")
    edges = compute_triangulation_preview(obj, image, StageOutput(), params)
    assert len(edges) >= 3                 # closed silhouette -> >=3 edges
    for (a, b) in edges:
        assert len(a) == 2 and len(b) == 2  # world XZ endpoints
```

- [ ] **Step 2: Implement `compute_triangulation_preview`** (`authoring_pipeline.py`). Run the SAME CDT inputs APPLY will run in SIMPLE (outer override if any + holes + user strokes -> extras/edges), but instead of writing a bmesh, return world-XZ edge pairs. Reuse `compute_outer` + the existing strokes->cdt-inputs helper, then call `mathutils.geometry.delaunay_2d_cdt` (or the existing `build_mesh_via_delaunay` into a throwaway bmesh and read its edges). Simplest correct approach: build a throwaway `bmesh`, run the SIMPLE path with `interior_points=[]`, read `bm.edges` coords, convert to world XZ via `obj.matrix_world`, free the bmesh. Return `list[tuple[Point2D, Point2D]]`.

Cache key = the StageParams snapshot (frozen, hashable) + outer/stroke output identity.

- [ ] **Step 3: Wire into modal.** Add `self._output.triangulation_preview: list[tuple[Point2D, Point2D]]` (new StageOutput field, default `[]`). When `_advance`/`_retreat` lands on `STEINER_PREVIEW` AND `interior_mode == "SIMPLE"`, compute + store. On param-dirty while on that stage, recompute. DENSE keeps the existing dense `compute_all_steiners` preview (`all_steiners`).

- [ ] **Step 4: Overlay wireframe.** In the overlay draw for `STEINER_PREVIEW`: if SIMPLE, draw `triangulation_preview` edges as a thin wireframe (GPU `LINES`, distinct color e.g. cyan); if DENSE, keep current `all_steiners` point cloud. (Overlay code lives in `authoring_overlay.py` / the operator draw callback - follow existing AS-AM12 `_draw_live_preview` pattern.)

- [ ] **Step 5: Run + commit**

```bash
blender --background --python apps/blender/tests/run_tests.py -- -k "triangulation_preview"
ruff check apps/blender && mypy apps/blender
git add apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py \
  apps/blender/core/skinning/authoring_stages.py \
  apps/blender/operators/automesh_authoring.py \
  apps/blender/core/bpy_helpers/automesh/authoring_overlay.py \
  apps/blender/tests/operators/test_automesh_authoring.py
git commit -m "feat(spec-013): SIMPLE triangulation preview at step 4 (AS-AM15)"
```

**MANUAL SMOKE (visual):** cannot verify GPU wireframe headless. Log to TODO MANUAL_TESTING: "SIMPLE step 4 shows real triangulation wireframe matching APPLY".

---

## Task 5: Stage 2 modifier-driven remap + cut RED (AS-AM17)

**Files:** `automesh_authoring.py`, overlay color, `tests/operators/test_automesh_authoring.py`

- [ ] **Step 1: Failing headless test** - Stage 2 intent comes from modifier, not location.

```python
def test_stage2_ctrl_press_sets_cut_intent_regardless_of_location(...):
    # Press with event.ctrl=True while cursor is OUTSIDE the silhouette ->
    # intent must be "cut" (modifier wins), not "extend" (old location rule).
    # Drive the operator's Stage 2 PRESS handler with a stub event; assert
    # the committed stroke kind == "cut".
```

(Match the existing Stage 4 modifier test harness in this file.)

- [ ] **Step 2: Replace location-driven intent** (`automesh_authoring.py:280-339`). Delete the `_point_inside_outer`-based intent resolution at PRESS (lines 280-284) and the "extend portion deferred" clip branch (330-339). Dispatch on modifier identical to Stage 4 (`_press_modifier`): Shift -> "extend" (kind "stroke"), Ctrl -> "cut" (kind "cut"), Alt -> delete. Reuse the Stage 4 PRESS path (lines 453-503) - factor the shared modifier->kind mapping into one helper used by both stages.

- [ ] **Step 3: Stage 2 cut color -> red** (D11). In `_stage2_overlay_kwargs` (line 718) drop the orange `_STROKE_VERT_COLOR_CUT_REMOVE`; pass the Stage 4 red cut color. Delete the now-unused orange constant.

- [ ] **Step 4: Tooltip vocabulary** (`_compute_stage2_tooltip_text` line 778). Replace location text ("inside=cut / outside=extend") with modifier text ("Shift=Extend / Ctrl=Cut / Alt=Delete"). Update the chord layout (line 969-970) `MOUSE_LMB_DRAG "out=extend / in=cut"` -> modifier chords matching Stage 4.

- [ ] **Step 5: Remove dead code.** `_point_inside_outer` (line 379) - check Stage 4 warn path (line 394-405) still uses it; if so keep, else delete. Grep before removing.

- [ ] **Step 6: Run + commit**

```bash
blender --background --python apps/blender/tests/run_tests.py -- -k "stage2 or automesh_authoring"
ruff check apps/blender && mypy apps/blender
git add apps/blender/operators/automesh_authoring.py apps/blender/tests/operators/test_automesh_authoring.py
git commit -m "fix(spec-013): Stage 2 modifier-driven + cut RED (AS-AM17)"
```

**MANUAL SMOKE (visual):** Stage 2 cut overlay reads red (matches Stage 4); Shift/Ctrl/Alt dispatch precise regardless of cursor inside/outside.

---

## Task 6: docs - TODO re-add + mark Phase 1 shipped

**Files:** `specs/013-weight-paint-automesh/TODO.md`

- [ ] Re-add the "Mesh interior modes + gesture redesign - IN FLIGHT" section (was prematurely deleted by the crashed session), then mark Phase 1 (AS-AM14/15/17) items `[x]` with their commit hashes; leave Phase 2 (AS-AM16) `[ ]`. Add a MANUAL_TESTING block listing the two visual smokes above.
- [ ] Commit:

```bash
git add specs/013-weight-paint-automesh/TODO.md
git commit -m "docs(spec-013): mark Phase 1 mesh-modes shipped, defer Phase 2 gesture (AS-AM14-17)"
```

---

## Final verification

```bash
pytest tests/ -q                                          # pure suite green
blender --background --python apps/blender/tests/run_tests.py   # operator + 7/7 fixtures green
ruff check apps/blender tests && mypy apps/blender         # clean
```

Then hand back for manual smoke (the 2 visual items - triangulation wireframe + Stage 2 red/modifier). No push / PR until user asks (per project convention).

## Notes / risks

- **Back-compat:** `StageParams.interior_mode` and `build_automesh(interior_mode=...)` both default `DENSE`, so the ~40 existing test constructors and the non-authoring `automesh_from_sprite` operator keep current behavior. Default *UI* is SIMPLE (new sprites get the sparse mesh); the property default in the PG is SIMPLE, the dataclass/function defaults are DENSE for safety.
- **Riskiest task:** Task 3 (nav refactor) - touches every `_stage +/- 1` site + statusbar + chord header. Land it behind the headless `active_stages`/`_stage_label` tests before wiring preview (Task 4) on top.
- **Phase 2 (AS-AM16)** is intentionally out of scope here; `Stroke.subdivisions` round-trip + toggle-pen gesture is a separate plan after Phase 1 smokes clean.
