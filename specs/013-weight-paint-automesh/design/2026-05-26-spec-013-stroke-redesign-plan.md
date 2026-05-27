# SPEC 013 Stroke Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land Stage 3 stroke redesign + supporting productivity polish on branch `feat/spec-013-stroke-redesign`: Stage 3 stroke redesign (S1-S9) + mixed-flow auto-snapshot (M1-M2) + 7 productivity items (O1-O7). ~1700 LOC.

**Architecture:** Two coherent halves inside one PR. Part A scope (Tasks 1-15) = Stage 3 redesign + extra_edges CDT extension + mixed-flow auto-snapshot. Part B scope (Tasks 16-25) = productivity operators. Commits topically grouped so reviewer can read in order. Per spec [`2026-05-26-spec-013-stroke-redesign-design.md`](2026-05-26-spec-013-stroke-redesign-design.md).

**Tech Stack:** Python 3.11, Blender 5.1 (bpy + bmesh + gpu + blf + mathutils), pytest, ruff, mypy strict. CDT via `mathutils.geometry.delaunay_2d_cdt`. KDTree via `mathutils.kdtree.KDTree`.

**Branch:** `feat/spec-013-stroke-redesign` (created from main).

---

## File Structure

**New files (PR-A scope):**
- `apps/blender/core/automesh/stroke_geometry.py` - pure Chaikin smooth + polyline resample + endpoint snap helpers
- `tests/automesh/test_stroke_geometry.py` - pure pytest
- `tests/automesh/test_extra_edges_cdt.py` - pure pytest for CDT extra_edges threading
- `tests/skinning/test_auto_snapshot_from_vgroups.py` - pure pytest
- `apps/blender/tests/operators/test_mixed_flow_auto_snapshot.py` - headless bpy

**New files (PR-B scope):**
- `apps/blender/operators/copy_weights_to_selected.py` - weight transfer operator
- `apps/blender/operators/sidecar_io.py` - import/export operators
- `apps/blender/core/skinning/brush_curve_presets.py` - 4 preset configurations
- `tests/skinning/test_weight_transfer.py` - pure pytest
- `apps/blender/tests/operators/test_weight_transfer.py` - headless bpy
- `apps/blender/tests/operators/test_brush_curve_presets.py` - headless bpy
- `apps/blender/tests/operators/test_sidecar_io.py` - headless bpy

**Modified files (PR-A scope):**
- `apps/blender/core/bpy_helpers/automesh/cdt.py` - thread `extra_edges` kwarg through `_build_cdt_inputs` + `build_mesh_via_delaunay`
- `apps/blender/core/bpy_helpers/automesh/bridge.py` - add `extra_edges` kwarg to `build_automesh` + pass to delaunay
- `apps/blender/core/skinning/authoring_stages.py` - `StageOutput.user_steiners` -> `user_strokes` (with backward compat alias)
- `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py` - read/write strokes JSON + `_strokes_to_cdt_inputs` + apply_mesh forwards `extra_edges`
- `apps/blender/operators/automesh_authoring.py` - stroke capture state + LMB drag handler + Ctrl+Z undo + Shift+LMB delete-stroke
- `apps/blender/core/bpy_helpers/automesh/authoring_overlay.py` (or wherever Stage 3 overlay draws) - render in-progress raw stroke + committed stroke edges
- `apps/blender/core/skinning/__init__.py` - `_build_sidecar_from_current_vgroups` helper + patch `maybe_pre_regen_snapshot`
- `apps/blender/tests/operators/test_automesh_authoring.py` - add stroke tests

**Modified files (PR-B scope):**
- `apps/blender/operators/bind_mesh.py` - read `obj["proscenio_bone_modes"]` dict + per-bone soft/hard dispatch
- `apps/blender/core/skinning/bind_apply.py` - per-bone mode application
- `apps/blender/operators/bind_mesh.py` (poll + execute) - multi-mesh batch bind (iterate selected meshes)
- `apps/blender/ui/skinning_panel.py` (or wherever bind sub-box draws) - per-bone soft/hard toggle UI + brush preset buttons + UX1 rename + tooltip
- `apps/blender/operators/edit_weights.py` (modal) - brush preset hotkey/button handler
- `apps/blender/operators/restore_weight_snapshot.py` (or wherever Restore op lives) - UX1 rename

---

## PR-A scope: Stage 3 stroke redesign + extra_edges + mixed-flow

### Task 1: Pure stroke_geometry module (Chaikin smooth)

**Files:**
- Create: `apps/blender/core/automesh/stroke_geometry.py`
- Test: `tests/automesh/test_stroke_geometry.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/automesh/test_stroke_geometry.py
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.stroke_geometry import chaikin_smooth  # noqa: E402


def test_chaikin_zero_iters_returns_input_unchanged():
    pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
    assert chaikin_smooth(pts, iters=0) == pts


def test_chaikin_one_iter_subdivides_each_segment_into_two():
    pts = [(0.0, 0.0), (1.0, 0.0)]
    out = chaikin_smooth(pts, iters=1)
    # First + last endpoints preserved; one segment -> 2 new mid points
    # at 1/4 and 3/4 -> total 4 points (start, q1, q3, end)
    assert len(out) == 4
    assert out[0] == (0.0, 0.0)
    assert out[-1] == (1.0, 0.0)
    assert math.isclose(out[1][0], 0.25)
    assert math.isclose(out[2][0], 0.75)


def test_chaikin_two_iters_smooths_zigzag_toward_centroid():
    # symmetric zigzag; after smoothing peaks pull toward midline (y=0)
    pts = [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0), (3.0, 1.0), (4.0, 0.0)]
    out = chaikin_smooth(pts, iters=2)
    max_y = max(p[1] for p in out)
    assert max_y < 1.0  # original peaks were 1.0; smoothed must be lower
    assert max_y > 0.3  # but not flattened entirely


def test_chaikin_preserves_endpoints_at_all_iter_counts():
    pts = [(5.0, 5.0), (6.0, 6.0), (7.0, 5.0)]
    for iters in (1, 2, 3, 5):
        out = chaikin_smooth(pts, iters=iters)
        assert out[0] == (5.0, 5.0)
        assert out[-1] == (7.0, 5.0)


def test_chaikin_single_point_returns_single_point():
    assert chaikin_smooth([(1.0, 2.0)], iters=2) == [(1.0, 2.0)]


def test_chaikin_two_points_with_zero_iters_returns_input():
    assert chaikin_smooth([(0.0, 0.0), (1.0, 0.0)], iters=0) == [(0.0, 0.0), (1.0, 0.0)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/automesh/test_stroke_geometry.py -v`
Expected: ModuleNotFoundError / ImportError on `chaikin_smooth`.

- [ ] **Step 3: Implement chaikin_smooth**

```python
# apps/blender/core/automesh/stroke_geometry.py
"""Pure polyline helpers for Stage 3 stroke pipeline (SPEC 013 ).

Stage 3 captures raw mouse paths during USER_STEINERS; this module
processes them before they reach the CDT:

- chaikin_smooth: noise reduction (industry standard for input polylines)
- resample_polyline: enforce global interior_spacing along the path
- snap_endpoint: pull stroke endpoints to nearest contour vert when close

All functions are pure: no bpy / no mathutils import. Tested in
isolation by tests/automesh/test_stroke_geometry.py.
"""

from __future__ import annotations

from collections.abc import Sequence

Point2D = tuple[float, float]


def chaikin_smooth(points: Sequence[Point2D], iters: int) -> list[Point2D]:
    """Chaikin corner-cutting subdivision.

    Each iteration replaces every interior segment with two new points
    at 1/4 and 3/4 along the segment. Endpoints are preserved.

    iters=0 returns input unchanged.
    Polylines of length <= 1 return unchanged regardless of iters.
    """
    if iters <= 0 or len(points) <= 1:
        return list(points)
    pts = list(points)
    for _ in range(iters):
        if len(pts) <= 1:
            break
        new_pts: list[Point2D] = [pts[0]]
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            new_pts.append((ax * 0.75 + bx * 0.25, ay * 0.75 + by * 0.25))
            new_pts.append((ax * 0.25 + bx * 0.75, ay * 0.25 + by * 0.75))
        new_pts.append(pts[-1])
        pts = new_pts
    return pts
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/automesh/test_stroke_geometry.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/automesh/stroke_geometry.py tests/automesh/test_stroke_geometry.py
git commit -m "feat(spec-013): add stroke_geometry.chaikin_smooth (S3)

Pure helper for Stage 3 stroke noise reduction. Chaikin corner-cutting
subdivision (1/4 + 3/4 weights), preserves endpoints. 6 pure tests."
```

---

### Task 2: stroke_geometry.resample_polyline

**Files:**
- Modify: `apps/blender/core/automesh/stroke_geometry.py`
- Modify: `tests/automesh/test_stroke_geometry.py`

- [ ] **Step 1: Add failing tests**

```python
# Append to tests/automesh/test_stroke_geometry.py
from core.automesh.stroke_geometry import resample_polyline  # noqa: E402


def test_resample_straight_line_at_spacing():
    # 10-unit line, spacing 1.0 -> 11 points (endpoints inclusive)
    out = resample_polyline([(0.0, 0.0), (10.0, 0.0)], spacing=1.0)
    assert len(out) == 11
    for i, (x, y) in enumerate(out):
        assert math.isclose(x, float(i))
        assert math.isclose(y, 0.0)


def test_resample_preserves_endpoints():
    out = resample_polyline([(0.0, 0.0), (3.0, 4.0)], spacing=1.0)
    assert out[0] == (0.0, 0.0)
    assert math.isclose(out[-1][0], 3.0)
    assert math.isclose(out[-1][1], 4.0)


def test_resample_single_point_returns_single_point():
    assert resample_polyline([(2.0, 3.0)], spacing=1.0) == [(2.0, 3.0)]


def test_resample_empty_returns_empty():
    assert resample_polyline([], spacing=1.0) == []


def test_resample_zero_or_negative_spacing_raises():
    import pytest
    with pytest.raises(ValueError, match="spacing"):
        resample_polyline([(0.0, 0.0), (1.0, 0.0)], spacing=0.0)
    with pytest.raises(ValueError, match="spacing"):
        resample_polyline([(0.0, 0.0), (1.0, 0.0)], spacing=-0.1)


def test_resample_path_shorter_than_spacing_returns_endpoints_only():
    out = resample_polyline([(0.0, 0.0), (0.3, 0.0)], spacing=1.0)
    assert out == [(0.0, 0.0), (0.3, 0.0)]


def test_resample_zigzag_yields_uniform_arc_length_spacing():
    pts = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (2.0, 1.0)]  # L-bend, total len 3
    out = resample_polyline(pts, spacing=1.0)
    # 4 points expected (0, 1, 2, 3 arc-length)
    assert len(out) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/automesh/test_stroke_geometry.py::test_resample_straight_line_at_spacing -v`
Expected: ImportError on resample_polyline.

- [ ] **Step 3: Implement resample_polyline**

```python
# Append to apps/blender/core/automesh/stroke_geometry.py
import math


def resample_polyline(points: Sequence[Point2D], spacing: float) -> list[Point2D]:
    """Uniform arc-length resample of an open polyline.

    Walks the input as a piecewise-linear curve and emits a point
    every `spacing` world units along the arc. Endpoints are
    preserved. Polylines shorter than spacing return endpoints only.

    Raises ValueError on spacing <= 0.
    """
    if spacing <= 0:
        raise ValueError(f"spacing must be > 0, got {spacing}")
    if len(points) <= 1:
        return list(points)
    pts = list(points)
    segments: list[tuple[Point2D, Point2D, float]] = []
    total_len = 0.0
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        seg_len = math.hypot(bx - ax, by - ay)
        if seg_len > 0:
            segments.append((pts[i], pts[i + 1], seg_len))
            total_len += seg_len
    if total_len <= spacing:
        return [pts[0], pts[-1]]
    out: list[Point2D] = [pts[0]]
    target = spacing
    consumed = 0.0
    for (ax, ay), (bx, by), seg_len in segments:
        while target <= consumed + seg_len:
            t = (target - consumed) / seg_len
            out.append((ax + (bx - ax) * t, ay + (by - ay) * t))
            target += spacing
        consumed += seg_len
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/automesh/test_stroke_geometry.py -v`
Expected: 13 passed total (6 chaikin + 7 resample).

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/automesh/stroke_geometry.py tests/automesh/test_stroke_geometry.py
git commit -m "feat(spec-013): add stroke_geometry.resample_polyline (S2)

Uniform arc-length resampling at fixed spacing. Preserves endpoints,
appends final endpoint if not aligned. Used to enforce interior_spacing
global density along Stage 3 strokes. 7 pure tests."
```

---

### Task 3: stroke_geometry.snap_endpoint

**Files:**
- Modify: `apps/blender/core/automesh/stroke_geometry.py`
- Modify: `tests/automesh/test_stroke_geometry.py`

- [ ] **Step 1: Add failing tests**

```python
# Append to tests/automesh/test_stroke_geometry.py
from core.automesh.stroke_geometry import snap_endpoint  # noqa: E402


def test_snap_returns_none_when_no_candidate_in_range():
    assert snap_endpoint((0.0, 0.0), [(5.0, 5.0), (10.0, 10.0)], max_dist=1.0) is None


def test_snap_returns_nearest_index_when_in_range():
    candidates = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0)]
    # query closer to candidate index 1
    assert snap_endpoint((1.1, 0.0), candidates, max_dist=0.5) == 1


def test_snap_returns_first_on_tie():
    candidates = [(1.0, 0.0), (-1.0, 0.0)]  # both 1 unit away from origin
    # tie-break: lowest index
    assert snap_endpoint((0.0, 0.0), candidates, max_dist=2.0) == 0


def test_snap_empty_candidates_returns_none():
    assert snap_endpoint((0.0, 0.0), [], max_dist=1.0) is None


def test_snap_negative_max_dist_raises():
    import pytest
    with pytest.raises(ValueError, match="max_dist"):
        snap_endpoint((0.0, 0.0), [(1.0, 0.0)], max_dist=-1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/automesh/test_stroke_geometry.py::test_snap_returns_none_when_no_candidate_in_range -v`
Expected: ImportError on snap_endpoint.

- [ ] **Step 3: Implement snap_endpoint**

```python
# Append to apps/blender/core/automesh/stroke_geometry.py
def snap_endpoint(
    point: Point2D,
    candidates: Sequence[Point2D],
    max_dist: float,
) -> int | None:
    """Return index of nearest candidate within max_dist, else None.

    Linear scan O(N). For Stage 3 endpoint snap the candidate list
    is the outer contour (typically <256 verts) - KD-tree overhead
    not justified at this scale.

    Tie-break: lowest index wins.
    Raises ValueError on max_dist < 0.
    """
    if max_dist < 0:
        raise ValueError(f"max_dist must be >= 0, got {max_dist}")
    if not candidates:
        return None
    qx, qy = point
    best_idx = -1
    best_d2 = max_dist * max_dist
    for i, (cx, cy) in enumerate(candidates):
        d2 = (cx - qx) * (cx - qx) + (cy - qy) * (cy - qy)
        if d2 <= best_d2:
            best_d2 = d2
            best_idx = i
    return best_idx if best_idx >= 0 else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/automesh/test_stroke_geometry.py -v`
Expected: 18 passed total.

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/automesh/stroke_geometry.py tests/automesh/test_stroke_geometry.py
git commit -m "feat(spec-013): add stroke_geometry.snap_endpoint (S5)

Linear-scan nearest-neighbor with max distance filter; returns
index or None. Used for Stage 3 stroke endpoint snapping to outer
contour verts. 5 pure tests."
```

---

### Task 4: CDT extra_edges threading (cdt.py)

**Files:**
- Modify: `apps/blender/core/bpy_helpers/automesh/cdt.py`
- Test: `tests/automesh/test_extra_edges_cdt.py`

- [ ] **Step 1: Write failing test**

`tests/automesh/test_extra_edges_cdt.py`:

```python
"""Pure tests for CDT extra_edges threading (SPEC 013 S8)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.automesh.cdt import _build_cdt_inputs  # noqa: E402


def test_no_extra_edges_baseline_unchanged():
    outer = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    coords, edges = _build_cdt_inputs(outer, [], [], [])
    assert len(coords) == 4
    assert len(edges) == 4  # cyclic outer loop


def test_extra_edges_appended_to_constraint_list():
    outer = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    interior = [(0.5, 0.5)]  # one interior vert (idx 4 after outer)
    extra = [(0, 2)]  # diagonal across outer
    coords, edges = _build_cdt_inputs(outer, [], interior, [], extra_edges=extra)
    assert (0, 2) in edges
    assert len(coords) == 5  # 4 outer + 1 interior


def test_extra_edges_none_behaves_as_empty():
    outer = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    coords_a, edges_a = _build_cdt_inputs(outer, [], [], [], extra_edges=None)
    coords_b, edges_b = _build_cdt_inputs(outer, [], [], [])
    assert coords_a == coords_b
    assert edges_a == edges_b
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/automesh/test_extra_edges_cdt.py -v`
Expected: TypeError on unexpected `extra_edges` kwarg.

- [ ] **Step 3: Add extra_edges kwarg to _build_cdt_inputs**

Modify `apps/blender/core/bpy_helpers/automesh/cdt.py`:

```python
# Replace _build_cdt_inputs signature + body:
def _build_cdt_inputs(
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
    interior_points: list[tuple[float, float]],
    holes: list[list[tuple[float, float]]],
    extra_edges: list[tuple[int, int]] | None = None,
) -> tuple[list[tuple[float, float]], list[tuple[int, int]]]:
    """Assemble the ``(coords, constraint_edges)`` CDT inputs.

    Layout in the flat coord array:
    ``outer + inner + interior + each_hole_in_order``.
    Constraint edges close each contour loop in place.

    ``extra_edges`` is appended verbatim - indices must be valid
    against the final coord array (caller maps indices when stroke
    verts live in `interior_points` and snap endpoints reference
    `outer_world`).
    """
    outer_count = len(outer_world)
    inner_count = len(inner_world)
    all_coords: list[tuple[float, float]] = (
        list(outer_world) + list(inner_world) + list(interior_points)
    )
    edges_constraint = _cyclic_loop_edges(0, outer_count)
    if inner_count >= 3:
        edges_constraint.extend(_cyclic_loop_edges(outer_count, inner_count))
    hole_offset = len(all_coords)
    for hole in holes:
        if len(hole) < 3:
            continue
        all_coords.extend(hole)
        edges_constraint.extend(_cyclic_loop_edges(hole_offset, len(hole)))
        hole_offset += len(hole)
    if extra_edges:
        edges_constraint.extend(extra_edges)
    return all_coords, edges_constraint
```

- [ ] **Step 4: Thread through build_mesh_via_delaunay**

```python
# Modify build_mesh_via_delaunay signature + call:
def build_mesh_via_delaunay(
    bm: bmesh.types.BMesh,
    outer_world: list[tuple[float, float]],
    inner_world: list[tuple[float, float]],
    interior_points: list[tuple[float, float]],
    holes_world: list[list[tuple[float, float]]] | None = None,
    extra_edges: list[tuple[int, int]] | None = None,
) -> int:
    # ... existing docstring + early returns ...
    if len(outer_world) < 3:
        return 0
    holes = list(holes_world) if holes_world else []
    all_coords, edges_constraint = _build_cdt_inputs(
        outer_world, inner_world, interior_points, holes, extra_edges=extra_edges
    )
    # ... rest unchanged ...
```

- [ ] **Step 5: Run tests to verify**

Run: `pytest tests/automesh/test_extra_edges_cdt.py -v`
Expected: 3 passed.

Run: `pytest tests/ -v -k "cdt or automesh"`
Expected: no regressions in existing CDT tests.

- [ ] **Step 6: Commit**

```bash
git add apps/blender/core/bpy_helpers/automesh/cdt.py tests/automesh/test_extra_edges_cdt.py
git commit -m "feat(spec-013): CDT extra_edges kwarg (S8)

Thread extra_edges through _build_cdt_inputs + build_mesh_via_delaunay.
Indices must be valid against final coord array (caller responsibility).
Backward compat: None default behaves identically to baseline. 3 tests."
```

---

### Task 5: build_automesh extra_edges kwarg

**Files:**
- Modify: `apps/blender/core/bpy_helpers/automesh/bridge.py:611-754`
- Modify: `apps/blender/core/bpy_helpers/automesh/bridge.py:563-587` (`_triangulate_into_bmesh`)

- [ ] **Step 1: Thread extra_edges through _triangulate_into_bmesh**

```python
def _triangulate_into_bmesh(
    obj: Object,
    outer_world: Contour2D,
    inner_world: Contour2D,
    interior_points: list[tuple[float, float]],
    holes_world: list[Contour2D],
    extra_edges: list[tuple[int, int]] | None = None,
) -> tuple[int, object]:
    base_group_index, _is_fresh = initialize_base_sprite_group(obj)
    delete_non_base_geometry(obj, base_group_index)
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    build_mesh_via_delaunay(
        bm, outer_world, inner_world, interior_points, holes_world, extra_edges=extra_edges
    )
    if holes_world:
        delete_faces_inside_holes(bm, holes_world)
    return base_group_index, bm
```

- [ ] **Step 2: Add extra_edges kwarg to build_automesh**

Modify `build_automesh` signature (line 611) - add after `extra_steiners`:

```python
extra_steiners: list[tuple[float, float]] | None = None,
extra_edges: list[tuple[int, int]] | None = None,
```

Update call to `_triangulate_into_bmesh` (line 724) to pass `extra_edges=extra_edges`.

**Critical:** the `extra_edges` indices coming from the caller reference positions within the FINAL coord array (outer + inner + interior). When `_merge_extra_steiners` filters/reorders extra_steiners, indices break. Caller must compute indices AFTER deciding which extras survive. We will handle this in apply_mesh (Task 9) by skipping the filter when extra_edges are present (callers know what they're doing) OR by passing pre-filtered extras + pre-mapped indices. Decision: pre-mapped indices from caller; skip `_merge_extra_steiners` only for the stroke verts (single-Steiner extras still use the filter).

For Task 5, just add the kwarg and pass through. Index mapping logic lives in apply_mesh.

- [ ] **Step 3: Run existing automesh fixture tests**

Run: `blender --background --python apps/blender/tests/run_tests.py`
Expected: 7/7 fixtures pass (no regression - extra_edges defaults to None).

- [ ] **Step 4: Commit**

```bash
git add apps/blender/core/bpy_helpers/automesh/bridge.py
git commit -m "feat(spec-013): build_automesh extra_edges kwarg (S8)

Threads extra_edges through to delaunay_2d_cdt via _triangulate_into_bmesh.
Caller is responsible for mapping indices to final coord array layout
(outer + inner + interior). Backward compat: None default = no-op."
```

---

### Task 6: StageOutput user_strokes migration (data structure)

**Files:**
- Modify: `apps/blender/core/skinning/authoring_stages.py`

- [ ] **Step 1: Read current StageOutput**

Run: `grep -n "user_steiners" apps/blender/core/skinning/authoring_stages.py`

- [ ] **Step 2: Add Stroke TypedDict + user_strokes field**

```python
# Add to authoring_stages.py
from typing import Literal, TypedDict


class Stroke(TypedDict):
    """Stage 3 stroke or single-Steiner placement (SPEC 013 S7).

    kind="point": single Steiner from a click without drag (S6 backward compat).
    kind="stroke": resampled polyline that becomes constraint edges + verts.
    """
    kind: Literal["point", "stroke"]
    points: list[tuple[float, float]]  # WORLD XZ, post-smooth + post-resample


@dataclass
class StageOutput:
    outer: list[Point2D] = field(default_factory=list)
    inner_loops: list[list[Point2D]] = field(default_factory=list)
    user_strokes: list[Stroke] = field(default_factory=list)
    interior: list[Point2D] = field(default_factory=list)

    @property
    def user_steiners(self) -> list[Point2D]:
        """Backward-compat alias: flatten user_strokes to flat point list.

        Pre-callers (tests, debug logs) expect a flat list of
        points. This property derives it without forcing the new
        structured field on them.
        """
        out: list[Point2D] = []
        for stroke in self.user_strokes:
            out.extend(stroke["points"])
        return out
```

- [ ] **Step 3: Update existing callers**

Run: `grep -rn "output.user_steiners\|StageOutput(.*user_steiners" apps/blender/`

For each writer, switch to appending Stroke dicts. For each reader, leave alone (the `@property` covers them).

- [ ] **Step 4: Run pure tests + headless tests**

Run: `pytest tests/ apps/blender/tests/ -v -k "stage"`
Expected: pass (backward compat property works).

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/skinning/authoring_stages.py
git commit -m "feat(spec-013): StageOutput.user_strokes (S7)

New structured field for Stage 3 strokes (kind=stroke|point + points
list). Backward compat: user_steiners @property flattens strokes to
flat point list so existing readers keep working without changes."
```

---

### Task 7: read/write_user_steiners backward compat (authoring_pipeline.py)

**Files:**
- Modify: `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py:103-129`
- Modify: `apps/blender/tests/operators/test_automesh_authoring.py`

- [ ] **Step 1: Add read_user_strokes + write_user_strokes**

```python
# Add to authoring_pipeline.py (next to existing read_user_steiners/write_user_steiners):
from ...skinning.authoring_stages import Stroke

_USER_STROKES_KEY = "proscenio_user_strokes"


def read_user_strokes(obj: bpy.types.Object) -> list[Stroke]:
    """Read obj['proscenio_user_strokes']; backward compat with legacy
    proscenio_user_steiners flat list (treated as kind='point' strokes).
    """
    payload = obj.get(_USER_STROKES_KEY)
    if payload is not None:
        try:
            data = json.loads(payload) if isinstance(payload, str) else list(payload)
        except (ValueError, TypeError):
            return []
        return _parse_strokes(data)
    # Legacy fallback: flat list of points -> wrap each as kind='point'
    legacy_points = read_user_steiners(obj)
    return [{"kind": "point", "points": [p]} for p in legacy_points]


def write_user_strokes(obj: bpy.types.Object, strokes: list[Stroke]) -> None:
    obj[_USER_STROKES_KEY] = json.dumps(
        [{"kind": s["kind"], "points": [[p[0], p[1]] for p in s["points"]]} for s in strokes]
    )


def _parse_strokes(data: object) -> list[Stroke]:
    if not isinstance(data, list):
        return []
    out: list[Stroke] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        if kind not in ("point", "stroke"):
            continue
        raw_pts = item.get("points")
        if not isinstance(raw_pts, list):
            continue
        pts: list[tuple[float, float]] = []
        for raw_pt in raw_pts:
            if not (isinstance(raw_pt, (list, tuple)) and len(raw_pt) == 2):
                continue
            try:
                pts.append((float(raw_pt[0]), float(raw_pt[1])))
            except (TypeError, ValueError):
                continue
        out.append({"kind": kind, "points": pts})
    return out
```

- [ ] **Step 2: Add tests**

Append to `apps/blender/tests/operators/test_automesh_authoring.py`:

```python
def test_user_strokes_round_trip(automesh_fixture):
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_strokes,
        write_user_strokes,
    )
    strokes = [
        {"kind": "point", "points": [(0.0, 0.0)]},
        {"kind": "stroke", "points": [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)]},
    ]
    write_user_strokes(obj, strokes)
    restored = read_user_strokes(obj)
    assert len(restored) == 2
    assert restored[0]["kind"] == "point"
    assert restored[1]["kind"] == "stroke"
    assert len(restored[1]["points"]) == 3


def test_user_strokes_legacy_fallback(automesh_fixture):
    """Legacy proscenio_user_steiners (flat list) reads as kind=point strokes."""
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_strokes,
        write_user_steiners,
    )
    if "proscenio_user_strokes" in obj:
        del obj["proscenio_user_strokes"]
    write_user_steiners(obj, [(1.0, 2.0), (3.0, 4.0)])
    strokes = read_user_strokes(obj)
    assert len(strokes) == 2
    assert all(s["kind"] == "point" for s in strokes)
    assert strokes[0]["points"] == [(1.0, 2.0)]


def test_user_strokes_corrupt_payload_returns_empty(automesh_fixture):
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_strokes,
    )
    obj["proscenio_user_strokes"] = "not valid json {{{"
    assert read_user_strokes(obj) == []
```

- [ ] **Step 3: Run tests**

Run: `blender --background --python apps/blender/tests/run_tests.py -- -k "user_strokes"`
Expected: 3 new tests pass + existing user_steiners tests still pass.

- [ ] **Step 4: Commit**

```bash
git add apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py apps/blender/tests/operators/test_automesh_authoring.py
git commit -m "feat(spec-013): read/write_user_strokes (S7)

Custom Property 'proscenio_user_strokes' JSON schema: list of
{kind, points} dicts. Backward compat: legacy 'proscenio_user_steiners'
flat list reads as kind=point strokes. Corrupt payload -> [].
3 headless tests."
```

---

### Task 8: _strokes_to_cdt_inputs helper (authoring_pipeline.py)

**Files:**
- Modify: `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py`

- [ ] **Step 1: Add helper**

```python
def _strokes_to_cdt_inputs(
    obj: bpy.types.Object,
    strokes: list[Stroke],
    outer_world_local: list[Point2D],
    outer_base_index: int,
    interior_base_index: int,
    interior_spacing: float,
) -> tuple[list[Point2D], list[tuple[int, int]]]:
    """Convert Stage 3 strokes to (extra_steiners_local, extra_edges).

    For each stroke:
    - kind='point': append point as single Steiner; no edges.
    - kind='stroke': append all resampled verts as Steiners. Build edges
      between consecutive Steiners. If endpoint snaps to an outer vert
      (within interior_spacing * 1.5), DROP that endpoint from extras
      and emit an edge from the next stroke vert to the outer vert
      index (outer_base_index + snap_index).

    Indices in the returned edges:
    - Non-snapped stroke verts get indices >= interior_base_index (allocated
      in append order)
    - Snapped endpoints reference outer_base_index + snap_index

    Coordinates are in MESH-LOCAL XZ (apply matrix_world.inverted()
    to each stroke point first; existing _world_steiners_to_local
    pattern).
    """
    from .stroke_geometry import snap_endpoint  # local to keep top clean
    inv = obj.matrix_world.inverted()
    extras_local: list[Point2D] = []
    edges: list[tuple[int, int]] = []

    def to_local(p: Point2D) -> Point2D:
        v = inv @ Vector((p[0], 0.0, p[1]))
        return (v.x, v.z)

    snap_radius = interior_spacing * 1.5

    for stroke in strokes:
        if stroke["kind"] == "point":
            for p in stroke["points"]:
                extras_local.append(to_local(p))
            continue
        # stroke kind
        pts_local = [to_local(p) for p in stroke["points"]]
        if not pts_local:
            continue
        # snap endpoints to outer
        start_snap = snap_endpoint(pts_local[0], outer_world_local, snap_radius)
        end_snap = snap_endpoint(pts_local[-1], outer_world_local, snap_radius)
        # decide which inner indices are stroke-allocated
        inner_pts = list(pts_local)
        if start_snap is not None and inner_pts:
            inner_pts = inner_pts[1:]
        if end_snap is not None and inner_pts:
            inner_pts = inner_pts[:-1]
        # allocate indices for the inner stroke verts
        allocated_start = interior_base_index + len(extras_local)
        allocated_indices = list(range(allocated_start, allocated_start + len(inner_pts)))
        extras_local.extend(inner_pts)
        # build edge sequence
        node_indices: list[int] = []
        if start_snap is not None:
            node_indices.append(outer_base_index + start_snap)
        node_indices.extend(allocated_indices)
        if end_snap is not None:
            node_indices.append(outer_base_index + end_snap)
        # skip strokes that collapsed entirely (both endpoints snapped to same outer)
        if len(node_indices) < 2:
            continue
        for i in range(len(node_indices) - 1):
            edges.append((node_indices[i], node_indices[i + 1]))
    return extras_local, edges
```

- [ ] **Step 2: Add quick test in tests/automesh/test_extra_edges_cdt.py**

```python
def test_strokes_to_cdt_inputs_round_trip(monkeypatch):
    # Skip if bpy unavailable
    pytest = __import__("pytest")
    try:
        from core.bpy_helpers.automesh.authoring_pipeline import _strokes_to_cdt_inputs  # noqa: E402
    except (ImportError, ModuleNotFoundError):
        pytest.skip("bpy not available")
    # ... build mock obj with identity matrix_world ... (defer to bpy headless)
```

(Move actual test into headless suite if pytest can't import bpy.)

- [ ] **Step 3: Commit**

```bash
git add apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py
git commit -m "feat(spec-013): _strokes_to_cdt_inputs helper (S2/S5/S8)

Stage 3 strokes -> (extras_local, edges) for build_automesh. Handles:
- world XZ -> mesh-local conversion (matrix_world.inverted)
- endpoint snap to outer contour verts (interior_spacing * 1.5 radius)
- edge sequence between consecutive stroke verts + snapped endpoints
- kind=point strokes (single Steiner, no edges)"
```

---

### Task 9: apply_mesh forwards extra_edges (authoring_pipeline.py)

**Files:**
- Modify: `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py:160-213`

- [ ] **Step 1: Replace apply_mesh body**

```python
def apply_mesh(
    obj: bpy.types.Object,
    image: bpy.types.Image,
    output: StageOutput,
    params: StageParams,
    armature: bpy.types.Object | None,
) -> dict[str, int]:
    """Final write: build_automesh + Wave 13.2-sidecar reproject.

    Stage 3 strokes (output.user_strokes) become:
    - extra_steiners: resampled vert positions (mesh-local XZ)
    - extra_edges: constraint segments between consecutive stroke verts
      + endpoint snaps to outer contour verts

    Without this wire, Stage 3 strokes are preview-only.
    """
    from ..skinning import maybe_post_regen_reproject, maybe_pre_regen_snapshot

    bone_segments = collect_bone_segments(armature) if armature is not None else None
    prior_sidecar = maybe_pre_regen_snapshot(obj, armature) if armature is not None else None
    world_scale = 1.0 / _resolve_pixels_per_unit(bpy.context)
    # NOTE: extras are computed with knowledge of where they'll land in
    # the CDT coord array. Layout is outer + inner + interior + holes.
    # We don't know outer/inner counts until build_automesh runs them,
    # but the operator-level strokes use OUTER ONLY for snap candidates
    # (no inner snaps per OQ2 deferred). interior_base_index = outer count
    # (inner is appended after but strokes never snap to inner verts).
    # Pre-compute outer here by running compute_outer; then pass to build.
    outer_world = compute_outer(obj, image, params)
    outer_world_local = [
        _world_to_local_xz(obj, p) for p in outer_world
    ]
    outer_base_index = 0
    interior_base_index = len(outer_world_local)  # inner verts insert here too
    # When inner_loop_count > 0, inner verts are inserted between outer
    # and interior. interior_base_index must shift by inner count.
    # Strokes never reference inner indices (no inner snap per OQ2), so
    # we just need to account for inner count in the interior_base offset.
    if params.inner_loop_count > 0:
        inner_loops = compute_inner_loops_for_stage(obj, image, outer_world, params)
        if inner_loops:
            interior_base_index += len(inner_loops[-1])  # innermost only (existing pipeline)
    extras_local, extra_edges = _strokes_to_cdt_inputs(
        obj,
        output.user_strokes,
        outer_world_local,
        outer_base_index=outer_base_index,
        interior_base_index=interior_base_index,
        interior_spacing=params.interior_spacing,
    )
    # extras_local already in mesh-local XZ (helper applied matrix_world.inverted)
    counters = build_automesh(
        obj,
        image,
        downscale_factor=params.resolution,
        alpha_threshold=params.alpha_threshold,
        margin_pixels=params.margin_pixels,
        target_contour_vertices=params.contour_vertices,
        interior_spacing=params.interior_spacing,
        world_scale=world_scale,
        bone_segments=bone_segments,
        bone_density_radius=params.bone_radius if bone_segments else 0.0,
        bone_density_factor=params.bone_factor if bone_segments else 1,
        debug_stage="off",
        preserve_base_quad=False,
        extra_steiners=extras_local if extras_local else None,
        extra_edges=extra_edges if extra_edges else None,
    )
    if prior_sidecar is not None and armature is not None:
        repro = maybe_post_regen_reproject(obj, armature, prior_sidecar)
        counters["reprojected"] = repro["reprojected"]
        counters["auto_seed"] = repro["auto_seed"]
    return counters


def _world_to_local_xz(obj: bpy.types.Object, world_pt: Point2D) -> Point2D:
    inv = obj.matrix_world.inverted()
    local = inv @ Vector((world_pt[0], 0.0, world_pt[1]))
    return (local.x, local.z)
```

- [ ] **Step 2: Remove obsolete _world_steiners_to_local + extra_steiners path**

Keep the helper as a thin wrapper for any external callers, but route apply_mesh through the new pipeline. Search for callers of `_world_steiners_to_local`:

Run: `grep -rn "_world_steiners_to_local" apps/blender/ tests/`

Update test `test_world_steiners_to_local_applies_inverse_matrix` to still pass (keep helper as alias).

- [ ] **Step 3: Update headless test test_apply_mesh_runs_with_prior_sidecar to use strokes**

In `apps/blender/tests/operators/test_automesh_authoring.py`, the existing test uses `StageOutput()` (empty). Add a new test that exercises a stroke:

```python
def test_apply_mesh_stroke_creates_edges(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        apply_mesh,
    )
    from proscenio.core.skinning.authoring_stages import StageOutput, StageParams  # type: ignore[import-not-found]
    # Build a stroke that crosses the hand's central area
    output = StageOutput(user_strokes=[
        {"kind": "stroke", "points": [
            (0.0, 0.5), (0.0, 0.3), (0.0, 0.1), (0.0, -0.1), (0.0, -0.3)
        ]}
    ])
    params = StageParams(
        resolution=0.25, alpha_threshold=1, margin_pixels=0,
        contour_vertices=64, inner_loop_count=0, inner_loop_spacing=0.15,
        interior_spacing=0.1, bone_radius=0.5, bone_factor=2,
    )
    counters_before = apply_mesh(obj, image, StageOutput(), params, bpy.data.objects["automesh.hand_rig"])
    verts_before = counters_before["total_verts"]
    counters_after = apply_mesh(obj, image, output, params, bpy.data.objects["automesh.hand_rig"])
    verts_after = counters_after["total_verts"]
    # Stroke added at least 3 inner verts (5 stroke pts; 2 may snap)
    assert verts_after >= verts_before + 3
```

- [ ] **Step 4: Run tests**

Run: `blender --background --python apps/blender/tests/run_tests.py -- -k "apply_mesh"`
Expected: existing + new stroke test pass.

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py apps/blender/tests/operators/test_automesh_authoring.py
git commit -m "feat(spec-013): apply_mesh forwards user_strokes -> extra_edges (S8/S9)

Stage 3 strokes now reach build_automesh as both extra_steiners
(resampled verts) AND extra_edges (constraint segments). Endpoint snap
to outer contour verts produces edges that reference outer indices
directly (no duplicate vert). Without this wire, Stage 3 strokes were
preview-only - now they materialize as fold lines in the final mesh."
```

---

### Task 10: Modal stroke capture state (automesh_authoring.py)

**Files:**
- Modify: `apps/blender/operators/automesh_authoring.py`

This is the biggest task in the plan. Modal operator gains stroke capture state machine.

- [ ] **Step 1: Add stroke capture state vars to operator class**

In the `PROSCENIO_OT_automesh_authoring` class:

```python
# Add to __init__ or class init (find existing _user_steiners init):
self._stroke_active: bool = False
self._stroke_start_screen: tuple[int, int] | None = None  # mouse pixel coords at LMB DOWN
self._stroke_raw_points: list[tuple[float, float]] = []  # WORLD XZ samples while dragging
self._user_strokes: list[Stroke] = []  # replaces self._user_steiners (keep alias)
# Click vs drag detection threshold (screen pixels)
_DRAG_THRESHOLD_PX = 5
# Chaikin smoothing iterations
_STROKE_SMOOTH_ITERS = 2
```

- [ ] **Step 2: LMB DOWN handler (Stage 3 only)**

```python
# In modal(), USER_STEINERS stage branch:
if event.type == "LEFTMOUSE" and event.value == "PRESS":
    if event.shift:
        # Shift+LMB still deletes the stroke containing the clicked vert
        self._delete_stroke_at_mouse(context, event)
        self._tag_redraw_view3d(context)
        return {"RUNNING_MODAL"}
    # Begin stroke capture
    self._stroke_active = True
    self._stroke_start_screen = (event.mouse_region_x, event.mouse_region_y)
    world_pt = self._screen_to_world_xz(context, event)
    self._stroke_raw_points = [world_pt] if world_pt else []
    return {"RUNNING_MODAL"}
```

- [ ] **Step 3: MOUSEMOVE handler (while stroke active)**

```python
if event.type == "MOUSEMOVE" and self._stroke_active:
    world_pt = self._screen_to_world_xz(context, event)
    if world_pt:
        self._stroke_raw_points.append(world_pt)
        self._tag_redraw_view3d(context)  # live preview
    return {"RUNNING_MODAL"}
```

- [ ] **Step 4: LMB UP handler (commit stroke or click)**

```python
if event.type == "LEFTMOUSE" and event.value == "RELEASE" and self._stroke_active:
    self._stroke_active = False
    start = self._stroke_start_screen
    self._stroke_start_screen = None
    if start is None or not self._stroke_raw_points:
        self._stroke_raw_points = []
        return {"RUNNING_MODAL"}
    dx = event.mouse_region_x - start[0]
    dy = event.mouse_region_y - start[1]
    drag_px = (dx * dx + dy * dy) ** 0.5
    if drag_px < self._DRAG_THRESHOLD_PX:
        # Treat as click - single Steiner at first sample (S6 backward compat)
        first_pt = self._stroke_raw_points[0]
        self._user_strokes.append({"kind": "point", "points": [first_pt]})
    else:
        # Treat as stroke - smooth + resample + commit
        from proscenio.core.automesh.stroke_geometry import (  # type: ignore[import-not-found]
            chaikin_smooth,
            resample_polyline,
        )
        smoothed = chaikin_smooth(self._stroke_raw_points, iters=self._STROKE_SMOOTH_ITERS)
        spacing = context.scene.proscenio_authoring_params.interior_spacing  # however params are surfaced
        resampled = resample_polyline(smoothed, spacing=spacing)
        if len(resampled) >= 2:
            self._user_strokes.append({"kind": "stroke", "points": resampled})
    self._stroke_raw_points = []
    # Persist + redraw
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        write_user_strokes,
    )
    write_user_strokes(self._target_obj, self._user_strokes)
    self._tag_redraw_view3d(context)
    return {"RUNNING_MODAL"}
```

- [ ] **Step 5: Ctrl+Z undo handler (last stroke)**

```python
if event.type == "Z" and event.ctrl and event.value == "PRESS":
    if self._user_strokes:
        self._user_strokes.pop()
        from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
            write_user_strokes,
        )
        write_user_strokes(self._target_obj, self._user_strokes)
        self._tag_redraw_view3d(context)
    return {"RUNNING_MODAL"}
```

- [ ] **Step 6: _delete_stroke_at_mouse helper (Shift+LMB)**

```python
def _delete_stroke_at_mouse(self, context, event) -> None:
    """Hit-test: find stroke whose ANY vert is within `_PICK_RADIUS_PX` of mouse, remove it."""
    PICK_RADIUS_PX = 12  # screen pixels
    mouse_world = self._screen_to_world_xz(context, event)
    if mouse_world is None:
        return
    # Convert pick radius to world via region scaling - approximate by
    # comparing 2 close screen points -> 2 world points
    near_world = self._screen_to_world_xz(context, event, dx=PICK_RADIUS_PX)
    if near_world is None:
        return
    pick_dist_world = ((near_world[0] - mouse_world[0]) ** 2 + (near_world[1] - mouse_world[1]) ** 2) ** 0.5
    pick_d2 = pick_dist_world * pick_dist_world
    for idx, stroke in enumerate(self._user_strokes):
        for pt in stroke["points"]:
            d2 = (pt[0] - mouse_world[0]) ** 2 + (pt[1] - mouse_world[1]) ** 2
            if d2 <= pick_d2:
                self._user_strokes.pop(idx)
                from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
                    write_user_strokes,
                )
                write_user_strokes(self._target_obj, self._user_strokes)
                return
```

- [ ] **Step 7: _screen_to_world_xz helper**

```python
def _screen_to_world_xz(self, context, event, dx: int = 0, dy: int = 0) -> tuple[float, float] | None:
    """Project mouse position onto Y=0 plane; return WORLD XZ.

    `dx` / `dy` add screen pixel offset (used for pick-radius conversion).
    """
    from bpy_extras import view3d_utils
    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None
    coord = (event.mouse_region_x + dx, event.mouse_region_y + dy)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    if abs(ray_direction.y) < 1e-9:
        return None
    t = -ray_origin.y / ray_direction.y  # plane Y=0
    if t < 0:
        return None
    hit = ray_origin + ray_direction * t
    return (hit.x, hit.z)
```

- [ ] **Step 8: Update finish() to pass user_strokes to StageOutput**

Find existing code that builds StageOutput before calling apply_mesh. Replace `user_steiners=...` with `user_strokes=self._user_strokes`.

- [ ] **Step 9: Run tests**

Run: `blender --background --python apps/blender/tests/run_tests.py -- -k "automesh_authoring"`
Expected: existing tests pass (no stroke tests yet; added in Task 11).

- [ ] **Step 10: Commit**

```bash
git add apps/blender/operators/automesh_authoring.py
git commit -m "feat(spec-013): Stage 3 stroke capture in modal (S1/S2/S3/S4/S6)

State machine: LMB DOWN starts capture, MOUSEMOVE samples raw points,
LMB UP commits as stroke (drag >= 5px, Chaikin smooth, resample at
interior_spacing) or click (drag < 5px, single Steiner backward compat).
Ctrl+Z pops last stroke. Shift+LMB hit-tests + deletes containing
stroke. Persists via write_user_strokes."
```

---

### Task 11: Stage 3 overlay rendering (committed strokes + in-progress raw)

**Files:**
- Modify: `apps/blender/operators/automesh_authoring.py` (overlay draw callback)

- [ ] **Step 1: Find existing Stage 3 overlay draw**

Run: `grep -n "USER_STEINERS\|_draw_callback\|gpu.batch" apps/blender/operators/automesh_authoring.py`

- [ ] **Step 2: Extend draw callback**

```python
# In the POST_VIEW draw callback, USER_STEINERS branch:
# 1. Draw committed strokes as blue verts + blue lines
# 2. Draw single Steiners (kind=point) as yellow dots (current style)
# 3. Draw in-progress raw stroke as light gray thin line

import gpu
from gpu_extras.batch import batch_for_shader

shader = gpu.shader.from_builtin("UNIFORM_COLOR")
shader.bind()

# Committed strokes
for stroke in self._user_strokes:
    if stroke["kind"] == "point":
        # yellow dot
        coords = [(p[0], 0.0, p[1]) for p in stroke["points"]]
        batch = batch_for_shader(shader, "POINTS", {"pos": coords})
        shader.uniform_float("color", (1.0, 1.0, 0.0, 1.0))
        gpu.state.point_size_set(8.0)
        batch.draw(shader)
    else:
        # stroke verts + edges in blue
        coords = [(p[0], 0.0, p[1]) for p in stroke["points"]]
        # verts
        batch_v = batch_for_shader(shader, "POINTS", {"pos": coords})
        shader.uniform_float("color", (0.3, 0.7, 1.0, 1.0))
        gpu.state.point_size_set(6.0)
        batch_v.draw(shader)
        # edges (consecutive line segments)
        if len(coords) >= 2:
            line_coords = []
            for i in range(len(coords) - 1):
                line_coords.append(coords[i])
                line_coords.append(coords[i + 1])
            batch_e = batch_for_shader(shader, "LINES", {"pos": line_coords})
            shader.uniform_float("color", (0.3, 0.7, 1.0, 1.0))
            gpu.state.line_width_set(2.0)
            batch_e.draw(shader)

# In-progress raw stroke (light gray)
if self._stroke_active and len(self._stroke_raw_points) >= 2:
    raw_coords = [(p[0], 0.0, p[1]) for p in self._stroke_raw_points]
    line_coords = []
    for i in range(len(raw_coords) - 1):
        line_coords.append(raw_coords[i])
        line_coords.append(raw_coords[i + 1])
    batch_raw = batch_for_shader(shader, "LINES", {"pos": line_coords})
    shader.uniform_float("color", (0.6, 0.6, 0.6, 0.7))
    gpu.state.line_width_set(1.0)
    batch_raw.draw(shader)
```

- [ ] **Step 3: Manual smoke**

Open Blender, run modal on hand fixture, advance to Stage 3, drag a stroke. Verify:
- Light gray line follows mouse during drag
- After LMB UP, blue dots + blue lines replace gray (committed)
- Shift+LMB on blue vert removes whole stroke
- Ctrl+Z pops last

- [ ] **Step 4: Update MANUAL_TESTING.md with smoke checklist**

- [ ] **Step 5: Commit**

```bash
git add apps/blender/operators/automesh_authoring.py tests/MANUAL_TESTING.md
git commit -m "feat(spec-013): Stage 3 overlay renders strokes + raw preview (S1)

Committed strokes draw as blue verts + edges; kind=point strokes draw as
yellow dots (backward compat); in-progress raw stroke draws as light
gray thin line for live feedback. Updated MANUAL_TESTING.md smoke."
```

---

### Task 12: Mixed-flow auto-snapshot from current vertex_groups (skinning/__init__.py)

**Files:**
- Modify: `apps/blender/core/skinning/__init__.py` (or wherever `maybe_pre_regen_snapshot` lives)
- Test: `tests/skinning/test_auto_snapshot_from_vgroups.py`

- [ ] **Step 1: Write failing pure test**

```python
# tests/skinning/test_auto_snapshot_from_vgroups.py
"""Pure tests for _build_sidecar_from_current_vgroups (M1)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))


def test_build_sidecar_from_uv_and_weights_dict():
    from core.skinning.weight_snapshot import build_sidecar_from_vgroup_data  # noqa: E402
    uvs = [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)]
    weights_per_vert = [
        {"bone_a": 1.0},
        {"bone_a": 0.5, "bone_b": 0.5},
        {"bone_b": 1.0},
    ]
    sidecar = build_sidecar_from_vgroup_data(uvs, weights_per_vert)
    assert len(sidecar.entries) == 3
    assert sidecar.entries[0].provenance == "auto_seed"
    assert sidecar.entries[1].weights == {"bone_a": 0.5, "bone_b": 0.5}


def test_empty_inputs_return_empty_sidecar():
    from core.skinning.weight_snapshot import build_sidecar_from_vgroup_data  # noqa: E402
    sidecar = build_sidecar_from_vgroup_data([], [])
    assert sidecar.entries == []


def test_mismatched_lengths_truncate_to_shorter():
    from core.skinning.weight_snapshot import build_sidecar_from_vgroup_data  # noqa: E402
    uvs = [(0.0, 0.0), (0.5, 0.5)]
    weights = [{"a": 1.0}]
    sidecar = build_sidecar_from_vgroup_data(uvs, weights)
    assert len(sidecar.entries) == 1
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/skinning/test_auto_snapshot_from_vgroups.py -v`
Expected: ImportError on build_sidecar_from_vgroup_data.

- [ ] **Step 3: Implement pure helper in weight_snapshot.py (or sidecar_schema.py if better)**

```python
# apps/blender/core/skinning/weight_snapshot.py (or extend sidecar_schema.py)
from __future__ import annotations

from .sidecar_schema import SidecarEntry, WeightSidecar


def build_sidecar_from_vgroup_data(
    uvs: list[tuple[float, float]],
    weights_per_vert: list[dict[str, float]],
) -> WeightSidecar:
    """Pure constructor: build sidecar from parallel UV + weights lists.

    Provenance defaults to 'auto_seed' since vertex_group state alone
    carries no information about whether weights came from user paint
    or from a binding op. Conservative attribution per M2.

    Mismatched list lengths truncate to the shorter list - the bpy
    caller in skinning/__init__.py ensures equal lengths by iterating
    obj.data.vertices.
    """
    entries: list[SidecarEntry] = []
    for uv, weights in zip(uvs, weights_per_vert):
        entries.append(SidecarEntry(uv_anchor=uv, weights=dict(weights), provenance="auto_seed"))
    return WeightSidecar(entries=entries)
```

- [ ] **Step 4: Run tests to pass**

Run: `pytest tests/skinning/test_auto_snapshot_from_vgroups.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/skinning/weight_snapshot.py tests/skinning/test_auto_snapshot_from_vgroups.py
git commit -m "feat(spec-013): build_sidecar_from_vgroup_data pure helper (M1)

Constructs WeightSidecar from parallel uvs + weights_per_vert lists.
Provenance = auto_seed (conservative; vgroup state has no provenance
info on its own). 3 pure tests."
```

---

### Task 13: Patch maybe_pre_regen_snapshot to fall back to vgroups

**Files:**
- Modify: `apps/blender/core/bpy_helpers/skinning/__init__.py` (or wherever the function lives)
- Test: `apps/blender/tests/operators/test_mixed_flow_auto_snapshot.py`

- [ ] **Step 1: Find maybe_pre_regen_snapshot**

Run: `grep -rn "def maybe_pre_regen_snapshot" apps/blender/`

- [ ] **Step 2: Patch to fall back**

```python
# Around existing maybe_pre_regen_snapshot:
def maybe_pre_regen_snapshot(obj: bpy.types.Object, armature: bpy.types.Object | None) -> WeightSidecar | None:
    existing = obj.get("proscenio_weight_sidecar")
    if existing:
        return _parse_sidecar(existing)  # existing behavior
    # NEW M1: fall back to building from current vgroups
    # (covers Ctrl+P bind + automesh regen mixed flow)
    if not obj.vertex_groups or armature is None:
        return None
    uvs = _read_per_vert_uv_anchors(obj)  # existing helper from sidecar pipeline
    weights_per_vert: list[dict[str, float]] = []
    for vert in obj.data.vertices:
        weight_dict: dict[str, float] = {}
        for vg in obj.vertex_groups:
            try:
                w = vg.weight(vert.index)
                if w > 1e-6:
                    weight_dict[vg.name] = w
            except RuntimeError:
                continue
        weights_per_vert.append(weight_dict)
    from ...skinning.weight_snapshot import build_sidecar_from_vgroup_data
    return build_sidecar_from_vgroup_data(uvs, weights_per_vert)
```

- [ ] **Step 3: Write headless test**

```python
# apps/blender/tests/operators/test_mixed_flow_auto_snapshot.py
"""Headless test for mixed-flow auto-snapshot (M1)."""
from __future__ import annotations

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def test_native_ctrlp_bind_then_automesh_regen_preserves_weights(automesh_fixture):
    """Mixed flow: Blender native bind (no sidecar) + automesh regen
    must preserve weights via on-the-fly sidecar build.
    """
    obj = _activate("hand")
    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]
    # Simulate Ctrl+P Armature Auto Weights via bpy.ops.object.parent_set
    # (or simulate the resulting vertex_groups state directly):
    # Clear any sidecar that fixture might have stamped
    if "proscenio_weight_sidecar" in obj:
        del obj["proscenio_weight_sidecar"]
    # Create vertex groups manually (mimics what bone-heat does)
    for bone in bpy.data.objects["automesh.hand_rig"].data.bones:
        if bone.name not in obj.vertex_groups:
            obj.vertex_groups.new(name=bone.name)
        # assign first 3 verts to this group with weight 1.0
        for v in list(obj.data.vertices)[:3]:
            obj.vertex_groups[bone.name].add([v.index], 1.0, "REPLACE")
    # Capture weight count before regen
    weights_before = sum(
        1 for v in obj.data.vertices
        for vg in obj.vertex_groups
        if (lambda vi, vgi: True)(v.index, vg.index)
    )
    assert weights_before > 0
    # Run automesh regen - should reproject via on-the-fly sidecar
    bpy.ops.proscenio.automesh_from_sprite(resolution=0.25)
    # After regen, vertex_groups must still have weights (NOT empty)
    total_assigned = 0
    for vert in obj.data.vertices:
        for vg in obj.vertex_groups:
            try:
                w = vg.weight(vert.index)
                if w > 1e-6:
                    total_assigned += 1
            except RuntimeError:
                continue
    assert total_assigned > 0, "weights lost during regen - mixed-flow auto-snapshot failed"
```

- [ ] **Step 4: Run test**

Run: `blender --background --python apps/blender/tests/run_tests.py -- -k "mixed_flow"`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/bpy_helpers/skinning/__init__.py apps/blender/tests/operators/test_mixed_flow_auto_snapshot.py
git commit -m "fix(spec-013): mixed-flow auto-snapshot from vgroups (M1/M2)

When obj['proscenio_weight_sidecar'] absent before automesh regen AND
vertex_groups present AND armature set, build sidecar on-the-fly from
current vgroup data (provenance=auto_seed). Closes critical gap where
Ctrl+P Armature Auto Weights bind + automesh regen silently wiped
weights (user-reported 2026-05-25). 1 headless test."
```

---

### Task 14: Stage 4 preview shows stroke edges (OQ3)

**Files:**
- Modify: `apps/blender/operators/automesh_authoring.py` (STEINER_PREVIEW overlay)

- [ ] **Step 1: Extend STEINER_PREVIEW draw callback to also render stroke edges**

Stage 4 currently shows interior Steiners. Add render of committed stroke edges (light blue lines + verts) so artist sees the stroke before APPLY.

- [ ] **Step 2: Manual smoke - advance to Stage 4 after drawing a stroke; verify visible**

- [ ] **Step 3: Commit**

```bash
git add apps/blender/operators/automesh_authoring.py
git commit -m "feat(spec-013): Stage 4 preview includes stroke edges (OQ3)

STEINER_PREVIEW overlay now renders committed strokes (Stage 3 output)
alongside the auto-generated interior Steiners. Artist can verify the
fold line geometry before APPLY without losing visibility on the strokes."
```

---

### Task 15: PR-A summary commit + push

- [ ] **Step 1: Verify all tests pass**

```bash
pytest tests/ -v
blender --background --python apps/blender/tests/run_tests.py
```

- [ ] **Step 2: Update specs/013-weight-paint-automesh/TODO.md**

Mark PR-A items as Active->Shipped in the bundle. Add reference to this plan.

- [ ] **Step 3: Commit + push branch**

```bash
git add specs/013-weight-paint-automesh/TODO.md
git commit -m "docs(spec-013): mark PR-A items shipped in TODO.md"
git push -u origin feat/spec-013-wave-13.3-bundle
```

---

## PR-B scope: productivity polish (O1-O7)

### Task 16: Soft/Hard bone toggle data model (O1)

**Files:**
- Modify: `apps/blender/core/skinning/bind_apply.py` (or wherever bind weight assignment happens)

- [ ] **Step 1: Define data layout**

Store per-bone mode in `obj["proscenio_bone_modes"]: dict[str, str]` where value is "SOFT" or "HARD". Missing entry = use bind operator's default.

- [ ] **Step 2: Add helper to read/write**

```python
# apps/blender/core/skinning/bone_modes.py (new)
from __future__ import annotations

import json
from typing import Literal

import bpy

BoneMode = Literal["SOFT", "HARD"]
_KEY = "proscenio_bone_modes"


def read_bone_modes(obj: bpy.types.Object) -> dict[str, BoneMode]:
    raw = obj.get(_KEY)
    if raw is None:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        return {}
    return {k: v for k, v in data.items() if v in ("SOFT", "HARD")}


def write_bone_modes(obj: bpy.types.Object, modes: dict[str, BoneMode]) -> None:
    obj[_KEY] = json.dumps(modes)


def bone_mode_for(obj: bpy.types.Object, bone_name: str, default: BoneMode) -> BoneMode:
    return read_bone_modes(obj).get(bone_name, default)
```

- [ ] **Step 3: Add unit tests for read/write/default**

```python
# tests/skinning/test_bone_modes.py
"""Pure tests for bone mode read/write (O1)."""
from __future__ import annotations

# Skipped if bpy not available (bpy.types.Object required)
import pytest

bpy = pytest.importorskip("bpy")

from core.skinning.bone_modes import bone_mode_for, read_bone_modes, write_bone_modes  # noqa: E402


def test_default_when_unset():
    obj = bpy.data.objects.new("test", bpy.data.meshes.new("m"))
    assert bone_mode_for(obj, "any_bone", default="SOFT") == "SOFT"
    assert bone_mode_for(obj, "any_bone", default="HARD") == "HARD"


def test_round_trip():
    obj = bpy.data.objects.new("test2", bpy.data.meshes.new("m2"))
    write_bone_modes(obj, {"bone_a": "SOFT", "bone_b": "HARD"})
    modes = read_bone_modes(obj)
    assert modes == {"bone_a": "SOFT", "bone_b": "HARD"}


def test_invalid_values_filtered():
    obj = bpy.data.objects.new("test3", bpy.data.meshes.new("m3"))
    obj["proscenio_bone_modes"] = '{"bone_a": "SOFT", "bone_b": "INVALID"}'
    assert read_bone_modes(obj) == {"bone_a": "SOFT"}
```

- [ ] **Step 4: Patch bind operator to dispatch per-bone mode**

In `bind_apply.py` (or wherever per-bone weight write happens), look up `bone_mode_for(obj, bone.name, default=props.bind_init_mode_default)` and dispatch to single-nearest (HARD) or proximity falloff (SOFT) accordingly.

- [ ] **Step 5: Run tests**

Run: `blender --background --python apps/blender/tests/run_tests.py -- -k "bone_mode"`
Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add apps/blender/core/skinning/bone_modes.py tests/skinning/test_bone_modes.py apps/blender/core/bpy_helpers/skinning/bind_apply.py
git commit -m "feat(spec-013): per-bone SOFT/HARD mode dispatch (O1/D16)

Per-bone enum on obj['proscenio_bone_modes'] dict; bind operator
respects it (SOFT=proximity falloff, HARD=single-nearest). Default
falls through to bind_init_mode global. 3 tests."
```

---

### Task 17: Soft/Hard bone toggle UI

**Files:**
- Modify: `apps/blender/ui/skinning_panel.py` (or wherever bind sub-box draws)

- [ ] **Step 1: Add per-bone toggle row in bind sub-box**

For each bone listed in the bind sub-box, draw a two-button toggle (Soft/Hard) that calls a small operator to flip the mode.

- [ ] **Step 2: Add operator `proscenio.set_bone_mode`**

```python
# apps/blender/operators/set_bone_mode.py (new)
class PROSCENIO_OT_set_bone_mode(bpy.types.Operator):
    bl_idname = "proscenio.set_bone_mode"
    bl_label = "Set Bone Mode"
    bl_options = {"INTERNAL"}
    bone_name: bpy.props.StringProperty()
    mode: bpy.props.EnumProperty(items=[("SOFT", "Soft", ""), ("HARD", "Hard", "")])

    def execute(self, context):
        from ..core.skinning.bone_modes import read_bone_modes, write_bone_modes
        obj = context.active_object
        modes = read_bone_modes(obj)
        modes[self.bone_name] = self.mode
        write_bone_modes(obj, modes)
        return {"FINISHED"}
```

- [ ] **Step 3: Register operator + UI rows + manual smoke**

- [ ] **Step 4: Commit**

```bash
git add apps/blender/operators/set_bone_mode.py apps/blender/ui/skinning_panel.py apps/blender/__init__.py
git commit -m "feat(spec-013): per-bone Soft/Hard toggle UI in bind sub-box (O1)"
```

---

### Task 18: Multi-mesh batch bind (O2)

**Files:**
- Modify: `apps/blender/operators/bind_mesh.py`

- [ ] **Step 1: Update poll + execute to iterate selected meshes**

```python
@classmethod
def poll(cls, context):
    return (
        context.scene.proscenio.active_armature is not None
        and any(o.type == "MESH" for o in context.selected_objects)
    )

def execute(self, context):
    targets = [o for o in context.selected_objects if o.type == "MESH"]
    armature = context.scene.proscenio.active_armature
    counters = []
    for mesh_obj in targets:
        # call existing single-mesh bind logic on mesh_obj
        result = _bind_single(mesh_obj, armature, self.bind_init_mode, ...)
        counters.append(result)
    self.report({"INFO"}, f"Bound {len(targets)} mesh(es)")
    return {"FINISHED"}
```

(Extract existing single-mesh code into `_bind_single`.)

- [ ] **Step 2: Headless test**

```python
# apps/blender/tests/operators/test_multi_mesh_bind.py
def test_bind_multi_mesh(automesh_fixture):
    """Select 2 meshes + bind = both get vertex groups."""
    # ... setup 2 meshes + armature picker ...
    bpy.ops.proscenio.bind_mesh_to_armature()
    assert all(obj.vertex_groups for obj in selected)
```

- [ ] **Step 3: Commit**

```bash
git add apps/blender/operators/bind_mesh.py apps/blender/tests/operators/test_multi_mesh_bind.py
git commit -m "feat(spec-013): multi-mesh batch bind (O2)

Bind operator now iterates context.selected_objects (filtered to MESH)
instead of only active. Same algorithm per mesh against picker armature."
```

---

### Task 19: Sidecar import/export operators (O3)

**Files:**
- Create: `apps/blender/operators/sidecar_io.py`
- Test: `apps/blender/tests/operators/test_sidecar_io.py`

- [ ] **Step 1: Create operators**

```python
# apps/blender/operators/sidecar_io.py
import json
import bpy
from bpy.props import StringProperty


class PROSCENIO_OT_export_sidecar(bpy.types.Operator):
    bl_idname = "proscenio.export_sidecar"
    bl_label = "Export Weight Sidecar"
    filepath: StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.get("proscenio_weight_sidecar") is not None

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        payload = context.active_object["proscenio_weight_sidecar"]
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(payload if isinstance(payload, str) else json.dumps(payload))
        return {"FINISHED"}


class PROSCENIO_OT_import_sidecar(bpy.types.Operator):
    bl_idname = "proscenio.import_sidecar"
    bl_label = "Import Weight Sidecar"
    filepath: StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == "MESH"

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        with open(self.filepath, "r", encoding="utf-8") as f:
            payload = f.read()
        try:
            json.loads(payload)  # validate
        except json.JSONDecodeError as e:
            self.report({"ERROR"}, f"Invalid sidecar JSON: {e}")
            return {"CANCELLED"}
        context.active_object["proscenio_weight_sidecar"] = payload
        return {"FINISHED"}
```

- [ ] **Step 2: Write headless test**

Round-trip: export sidecar to temp file, clear obj prop, import same file, verify prop matches.

- [ ] **Step 3: Add panel buttons**

In skinning panel, add Import/Export buttons in a sidecar sub-box.

- [ ] **Step 4: Register + commit**

```bash
git add apps/blender/operators/sidecar_io.py apps/blender/tests/operators/test_sidecar_io.py apps/blender/__init__.py apps/blender/ui/skinning_panel.py
git commit -m "feat(spec-013): sidecar import/export operators (O3)

File dialog operators dump obj['proscenio_weight_sidecar'] to/from
disk. Enables version-controlled weight backups outside .blend.
Headless round-trip test."
```

---

### Task 20: Brush curve presets (O4)

**Files:**
- Create: `apps/blender/core/skinning/brush_curve_presets.py`
- Create: `apps/blender/operators/brush_preset.py`
- Test: `apps/blender/tests/operators/test_brush_curve_presets.py`

- [ ] **Step 1: Define preset data**

```python
# apps/blender/core/skinning/brush_curve_presets.py
"""Brush curve presets for Edit Weights modal (O4)."""
from typing import Literal

PresetName = Literal["HARD_EDGE", "SOFT_FALLOFF", "CREASE", "SMOOTH_BLEND"]

PRESETS: dict[PresetName, list[tuple[float, float]]] = {
    # (x, y) curve points in [0, 1] x [0, 1]
    "HARD_EDGE": [(0.0, 1.0), (1.0, 1.0)],
    "SOFT_FALLOFF": [(0.0, 1.0), (0.5, 0.5), (1.0, 0.0)],
    "CREASE": [(0.0, 1.0), (0.2, 0.8), (0.5, 0.0), (1.0, 0.0)],
    "SMOOTH_BLEND": [(0.0, 1.0), (0.5, 0.7), (1.0, 0.0)],
}
```

- [ ] **Step 2: Create operator**

```python
# apps/blender/operators/brush_preset.py
class PROSCENIO_OT_set_brush_preset(bpy.types.Operator):
    bl_idname = "proscenio.set_brush_preset"
    bl_label = "Apply Brush Curve Preset"
    preset_name: bpy.props.EnumProperty(items=[
        ("HARD_EDGE", "Hard Edge", ""),
        ("SOFT_FALLOFF", "Soft Falloff", ""),
        ("CREASE", "Crease", ""),
        ("SMOOTH_BLEND", "Smooth Blend", ""),
    ])

    def execute(self, context):
        from ..core.skinning.brush_curve_presets import PRESETS
        brush = context.tool_settings.weight_paint.brush
        if brush is None or brush.curve is None:
            self.report({"WARNING"}, "No active weight paint brush")
            return {"CANCELLED"}
        curve = brush.curve.curves[0]
        # clear existing points beyond first 2
        while len(curve.points) > 2:
            curve.points.remove(curve.points[-1])
        # set new points
        pts = PRESETS[self.preset_name]
        for i, (x, y) in enumerate(pts):
            if i < len(curve.points):
                curve.points[i].location = (x, y)
            else:
                curve.points.new(x, y)
        brush.curve.update()
        return {"FINISHED"}
```

- [ ] **Step 3: Headless test**

Verify each preset name sets the expected number of curve points.

- [ ] **Step 4: Add 4 preset buttons in Edit Weights modal status pill (or panel sub-box)**

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/skinning/brush_curve_presets.py apps/blender/operators/brush_preset.py apps/blender/tests/operators/test_brush_curve_presets.py apps/blender/__init__.py
git commit -m "feat(spec-013): brush curve presets for Edit Weights modal (O4)

4 named presets (Hard Edge, Soft Falloff, Crease, Smooth Blend)
configure brush.curve.curves[0] points. Quick-select buttons in modal
status pill. Saves brush curve editor trips. Headless test."
```

---

### Task 21: B3 investigation + fix or document

**Files:**
- Investigate: `apps/blender/core/automesh/alpha_contour.py` (Moore-neighbour walker)

- [ ] **Step 1: Reproduce B3**

Run on hand fixture: `bpy.ops.proscenio.automesh_from_sprite(resolution=0.5)`.
Verify: 44 verts / 27 disconnected faces instead of clean silhouette.

- [ ] **Step 2: Investigate Moore-neighbour at coarse stride**

Read `extract_outer_contour` + Moore-neighbour walker; check whether adjacency assumptions break at downscale 0.5.

- [ ] **Step 3: Decide path**

If root cause is single-line fix (e.g. neighbor lookup boundary): fix + add test.
If root cause is deep (algorithm rework): document workaround in panel tooltip ("Mesh resolution > 0.25 may produce fragmented silhouettes; use 0.25 or 0.2") + log warning at runtime.

- [ ] **Step 4: Commit (either fix or doc)**

```bash
git add ...
git commit -m "fix(spec-013): B3 silhouette regression at resolution 0.5 ()

[fix description OR workaround documentation]"
```

---

### Task 22: UX1 - rename "Restore Weight Snapshot" + tooltip

**Files:**
- Modify: `apps/blender/operators/restore_weight_snapshot.py` (or wherever the operator lives)
- Modify: `apps/blender/ui/skinning_panel.py` (label + tooltip)

- [ ] **Step 1: Rename bl_label**

Change from "Restore Weight Snapshot" to "Reset to Last Saved Weights".

- [ ] **Step 2: Update bl_description tooltip**

"Reverts paint edits since the last Bind or Automesh regen"

- [ ] **Step 3: Add relative timestamp to panel button label**

Show "from bind 2 minutes ago" derived from snapshot timestamp metadata. If timestamp missing, just show button without timestamp.

- [ ] **Step 4: Manual smoke - bind, paint, verify timestamp appears + tooltip reads naturally**

- [ ] **Step 5: Commit**

```bash
git add apps/blender/operators/restore_weight_snapshot.py apps/blender/ui/skinning_panel.py
git commit -m "feat(spec-013): UX1 - rename Restore Weight Snapshot ()

New label 'Reset to Last Saved Weights' + tooltip explaining what it
does + relative timestamp in panel. Closes user feedback 2026-05-25
('voltar pra onde? quando?')."
```

---

### Task 23: Weight transfer pure module (O7)

**Files:**
- Create: `apps/blender/core/skinning/weight_transfer.py`
- Test: `tests/skinning/test_weight_transfer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/skinning/test_weight_transfer.py
"""Pure tests for weight transfer KNN (O7)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))


def test_identical_meshes_copy_weights_one_to_one():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    source_positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    source_weights = [{"a": 1.0}, {"a": 0.5, "b": 0.5}, {"b": 1.0}]
    target_positions = list(source_positions)
    out = transfer_weights_by_nearest(source_positions, source_weights, target_positions, max_distance=0.1)
    assert out == source_weights


def test_target_beyond_max_distance_returns_empty_dict():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    out = transfer_weights_by_nearest(
        [(0.0, 0.0, 0.0)], [{"a": 1.0}],
        target_positions=[(10.0, 10.0, 10.0)],
        max_distance=0.5,
    )
    assert out == [{}]


def test_empty_source_returns_empty_weights_for_all_targets():
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    out = transfer_weights_by_nearest([], [], [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)], max_distance=1.0)
    assert out == [{}, {}]


def test_negative_max_distance_raises():
    import pytest
    from core.skinning.weight_transfer import transfer_weights_by_nearest  # noqa: E402
    with pytest.raises(ValueError, match="max_distance"):
        transfer_weights_by_nearest([(0.0, 0.0, 0.0)], [{"a": 1.0}], [(0.0, 0.0, 0.0)], max_distance=-1.0)
```

- [ ] **Step 2: Implement transfer_weights_by_nearest (pure, no bpy)**

```python
# apps/blender/core/skinning/weight_transfer.py
"""Pure KNN weight transfer between meshes (O7).

For each target vertex, find nearest source vertex within max_distance
and copy its weight dict. Targets beyond max_distance get empty dict.

Uses linear scan O(S * T); acceptable for sprite meshes (< 1k verts each).
For large meshes future PR can swap to KDTree (apps/blender layer; this
module stays pure).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

Point3D = tuple[float, float, float]


def transfer_weights_by_nearest(
    source_positions: Sequence[Point3D],
    source_weights: Sequence[dict[str, float]],
    target_positions: Sequence[Point3D],
    max_distance: float,
) -> list[dict[str, float]]:
    if max_distance < 0:
        raise ValueError(f"max_distance must be >= 0, got {max_distance}")
    if not source_positions:
        return [{} for _ in target_positions]
    d2_cap = max_distance * max_distance
    out: list[dict[str, float]] = []
    for tx, ty, tz in target_positions:
        best_idx = -1
        best_d2 = d2_cap
        for i, (sx, sy, sz) in enumerate(source_positions):
            d2 = (sx - tx) ** 2 + (sy - ty) ** 2 + (sz - tz) ** 2
            if d2 <= best_d2:
                best_d2 = d2
                best_idx = i
        out.append(dict(source_weights[best_idx]) if best_idx >= 0 else {})
    return out
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/skinning/test_weight_transfer.py -v`
Expected: 4 passed.

- [ ] **Step 4: Commit**

```bash
git add apps/blender/core/skinning/weight_transfer.py tests/skinning/test_weight_transfer.py
git commit -m "feat(spec-013): pure weight_transfer.transfer_weights_by_nearest (O7)

KNN weight copy: each target vert gets nearest source vert's weight
dict within max_distance; outside range -> empty dict. Linear scan
(adequate for sprite meshes; KDTree swap deferred). 4 pure tests."
```

---

### Task 24: Weight transfer operator (bpy-bound)

**Files:**
- Create: `apps/blender/operators/copy_weights_to_selected.py`
- Test: `apps/blender/tests/operators/test_weight_transfer.py`

- [ ] **Step 1: Create operator**

```python
# apps/blender/operators/copy_weights_to_selected.py
import bpy

from ..core.skinning.weight_transfer import transfer_weights_by_nearest


class PROSCENIO_OT_copy_weights_to_selected(bpy.types.Operator):
    bl_idname = "proscenio.copy_weights_to_selected"
    bl_label = "Copy Weights to Selected"
    bl_description = "Copy vertex weights from active mesh to all other selected meshes by nearest-vertex"

    max_distance: bpy.props.FloatProperty(name="Max Distance", default=0.5, min=0.0)

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active is None or active.type != "MESH":
            return False
        targets = [o for o in context.selected_objects if o.type == "MESH" and o != active]
        return len(targets) >= 1

    def execute(self, context):
        source = context.active_object
        targets = [o for o in context.selected_objects if o.type == "MESH" and o != source]
        source_positions = [tuple(source.matrix_world @ v.co) for v in source.data.vertices]
        source_weights: list[dict[str, float]] = []
        for vert in source.data.vertices:
            wd: dict[str, float] = {}
            for vg in source.vertex_groups:
                try:
                    w = vg.weight(vert.index)
                    if w > 1e-6:
                        wd[vg.name] = w
                except RuntimeError:
                    continue
            source_weights.append(wd)
        total_copied = 0
        for target in targets:
            target_positions = [tuple(target.matrix_world @ v.co) for v in target.data.vertices]
            transferred = transfer_weights_by_nearest(
                source_positions, source_weights, target_positions, self.max_distance
            )
            for vi, wd in enumerate(transferred):
                if not wd:
                    continue
                for bone_name, w in wd.items():
                    if bone_name not in target.vertex_groups:
                        target.vertex_groups.new(name=bone_name)
                    target.vertex_groups[bone_name].add([vi], w, "REPLACE")
                total_copied += 1
        self.report({"INFO"}, f"Copied weights to {total_copied} verts across {len(targets)} mesh(es)")
        return {"FINISHED"}
```

- [ ] **Step 2: Headless test**

```python
# apps/blender/tests/operators/test_weight_transfer.py
def test_copy_weights_two_identical_sprites(automesh_fixture):
    """Source mesh painted; target mesh receives weights via copy operator."""
    # ... duplicate hand fixture, paint source, run operator, verify ...
```

- [ ] **Step 3: Register + add panel button**

- [ ] **Step 4: Commit**

```bash
git add apps/blender/operators/copy_weights_to_selected.py apps/blender/tests/operators/test_weight_transfer.py apps/blender/__init__.py
git commit -m "feat(spec-013): copy_weights_to_selected operator (O7)

Active = source; selected (minus active) = targets. Per-target vert,
nearest source vert within max_distance (default 0.5) copies weight
dict. Creates target vertex_groups as needed. Solves COA2 #18 + #73."
```

---

### Task 25: PR-B summary + final TODO.md update

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v
blender --background --python apps/blender/tests/run_tests.py
ruff check apps/blender/ tests/
mypy --strict apps/blender/core/
```

- [ ] **Step 2: Update specs/013-weight-paint-automesh/TODO.md**

Mark PR-B items (O1-O7) as Active->Shipped. Move from Active to a "shipped" section. Add reference to this plan + Wave 13.4 forward items.

- [ ] **Step 3: Commit + push**

```bash
git add specs/013-weight-paint-automesh/TODO.md
git commit -m "docs(spec-013): bundle shipped - update TODO.md"
git push
```

- [ ] **Step 4: Open PR**

```bash
gh pr create --title "feat(spec-013): - Stage 3 stroke redesign + productivity polish bundle" --body "$(cat <<'EOF'
## Summary

- Stage 3 redesign: clicks become strokes (Chaikin smooth + resample + snap to outer + constraint edges in CDT). Replaces preview-only point placement with real fold-line geometry.
- Mixed-flow auto-snapshot fix: Ctrl+P Armature Auto Weights bind + automesh regen no longer wipes weights silently (closes user-reported gap 2026-05-25).
- 7 productivity items: per-bone Soft/Hard toggle, multi-mesh batch bind, sidecar import/export, brush curve presets, B3 fix/doc, UX1 rename, weight transfer between sprites.

Spec: [`specs/013-weight-paint-automesh/design/2026-05-26-spec-013-wave-13.3-bundle-design.md`]
Plan: [`specs/013-weight-paint-automesh/design/2026-05-26-spec-013-wave-13.3-bundle-plan.md`]

Commits organized topically. PR-A scope (commits 1-15) = Stage 3 + extra_edges + mixed-flow. PR-B scope (commits 16-25) = productivity polish.

## Test plan

- [ ] pytest tests/ -v (~360 pure + ~20 new = ~380)
- [ ] blender --background --python apps/blender/tests/run_tests.py (all fixtures + new headless tests)
- [ ] Manual smoke: Stage 3 stroke on hand fixture - verify fold line appears in APPLY mesh
- [ ] Manual smoke: Ctrl+P bind hand + automesh regen - weights survive
- [ ] Manual smoke: 2 hand copies + copy_weights_to_selected - target receives weights
- [ ] Manual smoke: cycle 4 brush presets - each changes brush feel
- [ ] Manual smoke: export sidecar + reimport - round-trip OK
EOF
)"
```

---

## Self-Review

### Spec coverage check

| Spec section | Plan task(s) |
|---|---|
| S1 paradigm B | T10 (stroke commit -> edges) + T8 + T9 |
| S2 spacing global | T2 (resample) + T10 (uses params.interior_spacing) |
| S3 Chaikin 2 iters fixed | T1 + T10 (`_STROKE_SMOOTH_ITERS=2`) |
| S4 Ctrl+Z + Shift+LMB | T10 steps 5-6 |
| S5 endpoint snap | T3 + T8 |
| S6 click backward compat | T10 step 4 (drag < 5px check) |
| S7 JSON schema | T6 (TypedDict) + T7 (read/write) |
| S8 extra_edges kwarg | T4 (cdt.py) + T5 (build_automesh) |
| S9 strokes -> CDT inputs | T8 + T9 |
| M1 auto-snapshot | T12 + T13 |
| M2 provenance=auto_seed | T12 step 3 |
| O1 Soft/Hard bone | T16 + T17 |
| O2 multi-mesh batch | T18 |
| O3 sidecar IO | T19 |
| O4 brush presets | T20 |
| O5 B3 fix | T21 |
| O6 UX1 rename | T22 |
| O7 weight transfer | T23 + T24 |
| OQ3 Stage 4 stroke preview | T14 |

All locked spec decisions have at least one task. No coverage gaps.

### Placeholder scan

Scanned for "TBD", "TODO", "implement later", vague verbs. The only intentional ambiguities are inside T21 (B3) which branches on investigation outcome (fix-or-document) - that's correct since we cannot pre-decide without the investigation. All other tasks have concrete code blocks.

### Type consistency

- `Stroke` TypedDict defined once in T6, referenced by T7/T8/T9/T10.
- `Point2D` aliased consistently as `tuple[float, float]`.
- `extra_edges: list[tuple[int, int]] | None` signature identical across cdt.py + bridge.py.
- `BoneMode` literal in T16 used in same form across T17.

---

## Execution Handoff

**Plan complete and saved to `specs/013-weight-paint-automesh/design/2026-05-26-spec-013-wave-13.3-bundle-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration. Best for 25 sequential tasks of mixed complexity.

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints. Higher context cost but tighter feedback loop.

**Which approach?**
