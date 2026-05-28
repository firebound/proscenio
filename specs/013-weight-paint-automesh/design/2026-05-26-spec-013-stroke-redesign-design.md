# SPEC 013 - Stroke Redesign + Productivity Polish

**Date:** 2026-05-26
**Branch target:** `feat/spec-013-stroke-redesign` (created from main)
**Builds on:** prior interactive-modal work (PR #59, #61, #62 merged)
**Spec parent:** `specs/013-weight-paint-automesh/`

## Why this exists

Two pressures converged after Wave 13.2 shipped:

1. **User manifested frustration with Stage 3's click-place-vert paradigm** (2026-05-25: "a ideia dessa feature nao era criar verts extras, mas manipular a criacao de malha para que certas edges fossem criadas nas areas pintadas / idealmente eu tava pensando em um stroke"). Wave 13.2 shipped 1-click=1-Steiner; correct mental model is stroke=fold-line.
2. **Mixed-flow silent data loss** (user-reported 2026-05-25): users who bind via `Ctrl+P -> Armature Auto Weights` (no sidecar) lose all weights on next automesh regen. `maybe_pre_regen_snapshot` early-aborts when `proscenio_weight_sidecar` is absent.

User requested aggregating "everything into one PR / feature / single work session". This spec covers Stage 3 stroke redesign + mixed-flow auto-snapshot fix + 7 productivity items (per-bone Soft/Hard, multi-mesh batch bind, sidecar import/export, brush curve presets, B3 fix, UX1 rename, weight transfer), with a scope-and-landing note recommending a 2-PR split if the bundle exceeds the reviewer's reading budget.

## Decisions table (locked via brainstorm 2026-05-26)

| # | Decision | Locked | Rationale |
|---|----------|--------|-----------|
| **Stage 3 paradigm** ||||
| S1 | Stroke = polyline CDT constraint (paradigm **B**), NOT density bias | yes | Bates com intencao user: "edges sendo criadas nas areas pintadas". Paradigm A (density) wrongly adds verts when artist just wants alignment. Paradigm C (Steiner-only) is what Wave 13.2 already does (just point-wise). |
| S2 | Stroke resampling cadence = `interior_spacing` global (no custom Stage 3 spacing) | yes | User instructed "respeitando a resolucao". Resampled verts have same density as the rest of the mesh; no adensamento. |
| S3 | Path smoothing = Chaikin 2 iterations fixed, no slider | yes | Raw mouse path is noisy; resample direto = edges tremidas. Chaikin = industry standard, ~30 LOC, no deps. Slider = YAGNI v1 (add later if artists complain). Pondera: Chaikin encurta as pontas levemente; mitigado pelo auto-snap em S5. |
| S4 | Multi-stroke management = Ctrl+Z (modal-local undo stack) + Shift+LMB-on-vert (deletes whole stroke containing that vert) | yes | Cobre "errei agora" (Ctrl+Z) + "errei 3 strokes atras" (Shift+LMB). Sem conflito com gesto atual (Shift+LMB ja deleta single Steiner; com strokes vira "deleta stroke contendo este vert"). |
| S5 | Endpoint snapping = auto-snap if dist < `interior_spacing * 1.5` to nearest outer contour vert | yes | Fold lines no cotovelo conectam na borda real (junta dobra direito); strokes internos puramente preservam free-float. Threshold reusa `interior_spacing` - zero new prop. Ponder: linear scan O(N) por endpoint OK pra N<256 outer verts; KD-tree desnecessario. |
| S6 | Single-click coexistence = drag distance &lt; 5px treats input as click (= 1 single Steiner, atual comportamento); drag &gt;= 5px = stroke | yes | Backward compat com modal Wave 13.2; nao quebra muscle memory. Pondera: o threshold 5px e em screen pixels; deve ser const em vez de prop. |
| S7 | Stroke serialization in `proscenio_user_steiners` JSON = list of stroke objects, NOT flat list of points. Schema: `[{kind: "stroke" \| "point", points: [[x,z], ...]}, ...]` | yes | Stroke groups precisam sobreviver round-trip (Ctrl+Z, delete-stroke). Backward compat: reader trata array-of-2-floats legacy como `{kind:"point", points:[[x,z]]}` so `read_user_steiners` nao quebra com .blends antigos. |
| **Automesh pipeline** ||||
| S8 | `build_automesh` gains `extra_edges: list[tuple[int, int]] \| None = None` kwarg, paralelo ao `extra_steiners` ja existente. Indices are into the `extra_steiners` array (or absolute if combined - design pendente, ver Open questions). | yes | CDT lib = `mathutils.geometry.delaunay_2d_cdt` (Blender built-in), ja aceita `edges_constraint` list. Extensao mecanica em `_build_cdt_inputs` + thread kwarg. |
| S9 | Stage 3 stroke -> apply_mesh: cada stroke resampleado vira `(N steiner points + N-1 edges)` adicionados ao extra_steiners / extra_edges lists. Snap endpoints sao substituidos pelo indice do outer contour vert (NAO duplica vert). | yes | Garante que a fold line seja literalmente uma edge entre o outer e o resto. |
| **Mixed-flow auto-snapshot (mixed-flow fix - critical)** ||||
| M1 | When `obj["proscenio_weight_sidecar"]` absent before automesh regen AND `obj.vertex_groups` non-empty AND `obj.armature` set, build sidecar on-the-fly from current vertex_groups + per-vert UV anchor before regen | yes | Closes mixed-flow gap user identified 2026-05-25 (Ctrl+P bind + automesh = silent weight loss). |
| M2 | Auto-built sidecar entries get `provenance="auto_seed"` (NOT `user_paint`) since they're inferred from whatever paint exists, with no record of whether they were ever artist-touched | yes | Conservative; artist nao deve receber credito por paint que pode ter vindo do bone-heat. Se quiser preservar user_paint do bind dele, ele deve fazer paint explicito antes do regen. |
| **Other Active items** ||||
| O1 | Soft vs Hard bone toggle (D16, per-bone enum) - vertex_group prop `proscenio_bone_mode: "SOFT" \| "HARD"`; rebind respects it | yes (Active) | Per-bone control instead of per-mesh. UI: small button next to each bone in the bind sub-box. |
| O2 | Multi-mesh batch bind - operator iterates selected meshes; same algorithm per mesh against picker armature | yes (Active) | Currently active-only; trivial scope. |
| O3 | Sidecar import/export to file - operator dumps `proscenio_weight_sidecar` JSON to disk; load operator restores | yes (Active) | Version-controlled weight backups outside the .blend. |
| O4 | Brush curve presets - quick-select buttons in Edit Weights modal: "Hard edge", "Soft falloff", "Crease", "Smooth blend" | yes (Active) | Each preset sets `brush.curve_preset` + curve mapping points. ~100 LOC. |
| O5 | B3 fix - resolution 0.5 silhouette walker regression | yes (Active) | Investigate first; if root cause is deep (Moore-neighbour adjacency loss at coarse stride), downgrade to "document workaround in panel tooltip" (~30 LOC) per existing TODO. |
| O6 | UX1 - rename "Restore Weight Snapshot" -> "Reset to Last Saved Weights" + tooltip "Reverts paint edits since the last Bind or Automesh regen" + relative timestamp ("from bind 2 minutes ago") | yes (Active) | User feedback: original label gave no temporal anchor. |
| O7 | Weight Transfer between sprites - `proscenio.copy_weights_to_selected` operator; source = active, targets = selected; per-vertex KNN by world position copies weight dict | yes (bundled) | Originally Deferred; promoted because KNN-based, well-defined, zero UX ambiguity. ~250 LOC. |

## Architecture

### Stage 3 redesign components

```text
authoring_pipeline.py
    StageOutput.user_steiners (list[Point2D]) -> StageOutput.user_strokes (list[Stroke])
    Stroke = TypedDict { kind: "stroke" | "point", points: list[Point2D] }
    + flatten_strokes_to_points(strokes) -> list[Point2D]  (for legacy callers)
    + strokes_to_edge_pairs(strokes, base_index) -> list[tuple[int, int]]

operators/automesh_authoring.py
    Stage 3 (USER_STEINERS) gains stroke capture state:
        _stroke_start: tuple[float, float] | None  (where LMB pressed)
        _stroke_active: bool
        _stroke_raw_points: list[Point2D]  (mouse samples while dragging)
    LMB DOWN:
        - record _stroke_start, _stroke_active=True
        - start collecting raw points on MOUSEMOVE
    MOUSEMOVE while _stroke_active:
        - append (x, z) to _stroke_raw_points
        - tag_redraw for live preview (render raw path in light gray)
    LMB UP:
        - if dist(start, end) < 5px screen units:
            - treat as click; add single Steiner at start (current behavior, S6)
        - else:
            - smooth raw_points via chaikin_smooth(raw_points, iters=2)
            - resample smoothed to interior_spacing cadence
            - snap endpoints to nearest outer contour vert if within interior_spacing*1.5
            - build Stroke { kind: "stroke", points: [...] }
            - append to _user_strokes
            - clear stroke state
        - tag_redraw

stroke_geometry.py (new, pure)
    chaikin_smooth(points, iters) -> list[Point2D]
    resample_polyline(points, spacing) -> list[Point2D]
    snap_endpoint(point, candidates, max_dist) -> int | None

GPU overlay (weight_overlay.py / authoring_overlay.py)
    Two modes during Stage 3:
        - in-progress stroke: raw path (light gray, thin line)
        - committed strokes: resampled verts (blue dots) + edges (blue lines)
        - single Steiners (S6 fallback): yellow dots (current overlay color)
```

### apply_mesh pipeline change

```text
def apply_mesh(obj, image, output, params, armature):
    # ... existing setup ...
    extra_steiners_local, extra_edges_local = _strokes_to_cdt_inputs(
        obj, output.user_strokes, outer_world_local, params.interior_spacing
    )
    counters = build_automesh(
        obj, image, ...,
        extra_steiners=extra_steiners_local,
        extra_edges=extra_edges_local,
    )
    # ... reproject as before ...
```

`_strokes_to_cdt_inputs` handles:
- World -> mesh-local conversion (existing `_world_steiners_to_local` extended)
- Resampling (if not already done at stroke commit time - decision: do it on commit, not here, so re-apply with same data is deterministic)
- Edge index assembly (consecutive resampled points get edges; snap endpoints reference outer contour vert indices)

### cdt.py extension

```python
def _build_cdt_inputs(
    outer_world, inner_world, interior_points, holes,
    extra_edges: list[tuple[int, int]] | None = None,  # NEW
):
    # ... existing layout ...
    if extra_edges:
        edges_constraint.extend(extra_edges)  # indices already mapped by caller
    return all_coords, edges_constraint
```

`build_mesh_via_delaunay` threads the kwarg through. Caller in `bridge.build_automesh` adds `extra_edges` arg, computes index offsets, passes down.

### Mixed-flow auto-snapshot

New helper in `skinning/__init__.py`:

```python
def _build_sidecar_from_current_vgroups(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
) -> WeightSidecar | None:
    """Reconstruct sidecar from current vertex_groups (no prior snapshot)."""
    if not obj.vertex_groups or armature is None:
        return None
    uvs = _read_per_vert_uv_anchors(obj)  # existing helper
    entries = []
    for vert_idx, uv in enumerate(uvs):
        weights = {}
        for vg in obj.vertex_groups:
            try:
                w = vg.weight(vert_idx)
                if w > 1e-6:
                    weights[vg.name] = w
            except RuntimeError:
                continue
        entries.append(SidecarEntry(uv_anchor=uv, weights=weights, provenance="auto_seed"))
    return WeightSidecar(entries=entries)

# Patch maybe_pre_regen_snapshot:
def maybe_pre_regen_snapshot(obj, armature):
    existing = obj.get("proscenio_weight_sidecar")
    if existing:
        return _parse_sidecar(existing)
    # NEW: fall back to building from current vgroups
    return _build_sidecar_from_current_vgroups(obj, armature)
```

### Soft/Hard bone toggle (O1)

```python
# vertex group metadata stored in obj["proscenio_bone_modes"]: dict[str, "SOFT" | "HARD"]
# UI: per-bone row in bind sub-box with two-button toggle
# Bind operator reads the dict; missing bone -> default = current binding-mode default
```

### Multi-mesh batch bind (O2)

```python
# bind operator's poll() already allows multiple selected; execute() iterates context.selected_objects
# filter to MESH type + skip those without armature modifier OR active_armature
```

### Sidecar import/export (O3)

```python
# operator with filepath prop; export writes obj["proscenio_weight_sidecar"] verbatim to file
# import reads file, validates schema, writes to obj custom prop
```

### Brush curve presets (O4)

```python
# 4 enum buttons in Edit Weights status pill
# clicking each calls brush.curve.curves[0].points configuration helper
# stored as named tuple of curve points per preset
```

### Weight Transfer (O7)

```python
# proscenio.copy_weights_to_selected operator
# poll: active mesh + at least 1 other selected mesh
# build KDTree of source mesh world positions
# for each target mesh vert: nearest source vert (within max_distance, configurable, default 0.5)
# copy weight dict to target vertex_groups (create groups as needed)
# entries marked provenance="auto_seed" in target sidecar if armature attached
```

## Data flow

```text
User clicks/drags in Stage 3 modal
    -> raw stroke captured (LMB DOWN -> MOUSEMOVE -> LMB UP)
    -> if click: single Steiner appended to user_strokes as {kind:"point"}
    -> if drag: smoothed (Chaikin 2x) + resampled (interior_spacing) + snapped (endpoints)
       + appended as {kind:"stroke"}
User advances to Stage 4 / Stage 5 (APPLY)
    -> StageOutput.user_strokes flattened by _strokes_to_cdt_inputs
    -> world -> mesh-local conversion
    -> indices computed (Steiner points + edges between consecutive in same stroke)
    -> build_automesh(..., extra_steiners=steiners, extra_edges=edges)
    -> CDT respects edges as hard constraints; fold lines materialize in mesh
    -> sidecar reproject from prior weights (or auto-built if mixed-flow, M1)
```

## Error handling

- **Empty stroke** (drag without movement -> 0 resampled points): silently ignored (no-op).
- **Stroke entirely outside outer polygon**: filtered by existing `_merge_extra_steiners` (point_in_polygon check); reported in `[automesh] N stroke verts filtered (outside silhouette)` log line.
- **Snap endpoint pulls stroke duration to 0** (artist drew a tiny stroke entirely within snap radius of one outer vert): treat as click (single Steiner at that outer vert? OR skip entirely?) - **decision: skip entirely** to avoid duplicate vert; log warning.
- **Mixed-flow auto-snapshot reads vertex_group weight on vert not in group**: `vg.weight(idx)` raises RuntimeError; caught + treated as 0.0 weight (omit from entry).
- **Import sidecar from incompatible schema**: validate version field; reject + show INFO message with version mismatch.
- **Weight transfer with no source verts in range**: target verts outside max_distance get `weights={}` (no groups assigned); count reported.

## Testing

### Pure tests (apps/blender-independent)

- `tests/automesh/test_stroke_geometry.py` (NEW):
  - `chaikin_smooth`: identity for 0 iters; converges to known centroid for symmetric input; preserves endpoints (or documents Chaikin shrinkage)
  - `resample_polyline`: spacing respected within tolerance; single-segment polyline; degenerate same-point input
  - `snap_endpoint`: returns None when no candidate within radius; returns nearest index when ties
- `tests/skinning/test_auto_snapshot_from_vgroups.py` (NEW):
  - vgroups present + no prior sidecar -> sidecar built with N entries, provenance=auto_seed
  - vgroups absent -> None
  - vert outside any vgroup -> entry has empty weights dict
- `tests/skinning/test_weight_transfer.py` (NEW):
  - identical meshes -> 1:1 weight copy
  - target vert beyond max_distance -> empty weights
  - source has bones target armature doesn't -> groups auto-created
- `tests/automesh/test_extra_edges_cdt.py` (NEW):
  - 4-vert square with extra_edges=[(0,2)] (diagonal) -> output contains that edge
  - extra_edges referencing out-of-range index -> graceful skip + warn
  - empty extra_edges -> no behavior change vs baseline

### Headless bpy tests (apps/blender/tests)

- `apps/blender/tests/operators/test_automesh_authoring.py` (extend):
  - existing test_world_steiners_to_local_applies_inverse_matrix stays
  - NEW: test_stroke_capture_round_trip - simulate LMB down + 3 mousemove + LMB up; assert user_strokes len 1 + kind=="stroke" + smoothed point count
  - NEW: test_single_click_still_creates_single_steiner - assert backward compat per S6
  - NEW: test_undo_stack_pops_last_stroke - Ctrl+Z handler removes most recent
  - NEW: test_shift_lmb_deletes_stroke_containing_vert - hit-test on resampled vert removes whole stroke
- `apps/blender/tests/operators/test_mixed_flow_auto_snapshot.py` (NEW):
  - bind via Ctrl+P sim (no sidecar write) + automesh regen -> assert weights survive
- `apps/blender/tests/operators/test_weight_transfer.py` (NEW):
  - 2 identical sprites with armature attached; source painted; transfer to target; assert weights match
- `apps/blender/tests/operators/test_brush_curve_presets.py` (NEW):
  - operator sets brush.curve.curves[0].points per preset name; assert curve point count + positions
- `apps/blender/tests/operators/test_sidecar_io.py` (NEW):
  - export then import round-trip preserves entries

### Manual smoke (tests/MANUAL_TESTING.md additions)

- Stage 3 stroke flow: paint a fold line at the hand fixture's wrist joint; verify edge appears in APPLY mesh
- Mixed-flow: Ctrl+P bind hand fixture, paint a stroke, regen automesh, verify weights present after
- Weight transfer: 2 hand copies, paint left, copy to right, verify right has weights
- Brush presets: cycle 4 presets, verify each changes brush feel
- Sidecar IO: export, edit JSON manually, reimport, verify changes applied

## Open questions (asked, deferred to implementation, can be revisited in review)

- **OQ1**: extra_edges index space - relative to extra_steiners array or absolute into combined coords? Recommendation: relative to extra_steiners, with helper converting at apply time. Less error-prone for callers.
- **OQ2**: snap-endpoint to inner contour verts too (not just outer)? Defer: inner loops are auto-generated, less likely to be where artist intends fold to anchor. Add later if requested.
- **OQ3**: stroke preview during Stage 4 (STEINER_PREVIEW)? Today Stage 4 shows interior Steiners. Should it also show stroke edges? Recommendation: yes, render stroke edges in Stage 4 overlay so artist can verify before APPLY.
- **OQ4**: legacy `proscenio_user_steiners` JSON migration - silent backward compat per S7; do we ever need to upgrade format if user opens an older fixture with this build? Recommendation: yes, silent migration on read (treat legacy points as `{kind:"point"}` strokes); no write-back unless user modifies.
- **OQ5**: weight transfer max_distance default? Recommendation: 0.5 world units (same as reproject default after B2 fix).

## Scope and landing strategy

**Estimated total LOC (impl + tests):** ~1700 LOC across ~20 files. This is large for one PR.

### Option A (user's request, default): single PR

- Branch: `feat/spec-013-wave-13.3-bundle`
- Single PR titled "feat(spec-013): Stage 3 stroke redesign + productivity polish bundle"
- Commits organized topically (one commit per spec section: S1-S9 = stroke flow; M1-M2 = mixed-flow; O1-O7 = Active items)
- PR description maps commits to spec sections so reviewer can read in order
- CodeRabbit will exceed comment limit (likely 30+ comments at this size)

### Option B (recommended if reviewer budget matters): split into 2 PRs on same feature branch

- **PR-A: "Stage 3 stroke redesign + extra_edges CDT extension + mixed-flow auto-snapshot"** (~900 LOC)
  - S1-S9 (Stage 3 redesign) + M1-M2 (mixed-flow fix) - these are tightly coupled and benefit from unified review
- **PR-B: "Productivity polish (per-bone toggle, batch bind, sidecar IO, brush presets, weight transfer)"** (~800 LOC)
  - O1-O7 (all 7 Active items + weight transfer) - independent of Stage 3 flow; can land in parallel

PR-A and PR-B both target main; PR-B can be opened after PR-A merges to avoid merge conflicts in shared files (`bind_panel.py`, `__init__.py`).

**My recommendation:** Option B. PR-A is the meaty / risky bit (CDT change + paradigm shift in modal); deserves focused review. PR-B is mostly mechanical operator additions; can be reviewed faster. Both fit one feature effort.

User explicitly requested "agregar tudo numa PR" so Option A respects that. Will await user override before splitting.

## Out of scope for this bundle (re-deferred)

These items remain deferred to future dedicated efforts (each needs its own brainstorm):

- Bone strength region painting (Moho lift) - needs widget UX brainstorm (~600 LOC)
- User-drawn density markers - needs paint-mode integration brainstorm (~400 LOC)
- Live pose-mode preview - needs hotkey/sub-mode UX brainstorm (~400 LOC)

## Scope amendment 2026-05-27 (manual smoke findings)

PR #63 (Part A + Part B) completed all planned tasks + CI green, but manual smoke on the hand fixture (2026-05-27) revealed visual artifacts + a feature gap that block ship-readiness. Decision: expand scope in same PR rather than ship a baseline that produces low-quality output by default.

### What smoke revealed

Smoke run: hand fixture, Stage 3 modal, 2 strokes drawn across the palm, APPLY. Console reported `delaunay output_type=1 input=258v/70e output=259v/452f` (clean count) but the rendered mesh showed clearly visible **edge fans** - clusters of edges radiating from individual interior verts, spanning long distances across the silhouette. Two distinct fans in the middle of the palm + lower thumb region.

### Root causes (2 confirmed)

1. **Auto-fill cluster near stroke verts** (visual fan #1, dense triangulation): `interior_points_for_annulus` computes the uniform Steiner grid BEFORE knowing where the artist's strokes will land. When strokes are committed, their resampled verts are appended via `_merge_extra_steiners`, sharing space with auto-fill verts at sub-`interior_spacing` distance. CDT triangulates both → degenerate slivers + fan patterns around stroke-vicinity clusters.

2. **Silent index drift on vert drop** (visual fan #2, long-spanning edges): `_merge_extra_steiners` in `bridge.py:551-559` filters extras silently when they fall outside outer silhouette / inside inner ring / inside a hole. The `extra_edges` index list passed in parallel is NOT updated to reflect the drops. Result: edges that should connect surviving stroke verts end up referencing wrong positions in the final coord array → long-distance edges crossing the mesh interior. Especially triggered when stroke vert sits marginally on outer boundary (raw walker outer vs smoothed-resampled outer have slightly different shapes → "I drew inside" verts can land outside post-smooth).

### Feature gap (user-requested 2026-05-27)

Stage 3 today produces fold lines (constraint edges, both sides have geometry). User needs **cuts** (separates mesh into 2 sides) for use cases like:

- Articulating finger joints without inner-elbow stretch
- Removing a chunk of silhouette the auto-walker mis-traced
- Splitting a humanoid sprite at the waist for independent torso/legs deformation

Cuts emerge naturally from the same constraint-edge machinery via 2 offset loops + face-prune between them (reuses existing hole detection post-process).

### New stage in the modal (USER_OUTER)

Today's 5-stage modal becomes 6 stages by inserting `USER_OUTER` between `OUTER` (1/6) and `INNER_LOOPS` (3/6):

1/6 `OUTER` (auto-walker output, view-only as today)
**2/6 `USER_OUTER` (NEW) - artist edits silhouette via stroke**
3/6 `INNER_LOOPS`
4/6 `USER_STEINERS` (interior, today's Stage 3, redesigned to stroke per S1-S9)
5/6 `STEINER_PREVIEW`
6/6 `APPLY`

Stage 2 enables silhouette-focused editing before any interior work. Strokes are stored separately on the mesh as `proscenio_outer_strokes` (parallel to `proscenio_user_strokes` for Stage 4).

### Locked decisions (amendment AS-AM1 through AS-AM10)

| # | Decision | Rationale |
|---|----------|-----------|
| AS-AM1 | Stroke pipeline silently dropping verts via `_merge_extra_steiners` is a bug class - filter must happen in `_strokes_to_cdt_inputs` BEFORE index allocation, with INFO report of dropped count. | Index drift causes long-spanning fan edges (visual fan #2). Earlier filter keeps indices stable + gives artist feedback. |
| AS-AM2 | `interior_points_for_annulus` gains `exclude_zones: list[(x, z, radius)] \| None` kwarg. Stroke verts populate exclude zones with radius = `interior_spacing * 0.5` to prevent auto-fill cluster. | Closes visual fan #1. Zone-based exclusion is generic (could later carry inner ring exclusion the same way). |
| AS-AM3 | New stage `AuthoringStage.USER_OUTER` between OUTER and INNER_LOOPS. Modal goes 5 → 6 stages, statusbar labels renumber. | Artist mental model: "fix silhouette first, then add interior detail". Wave 13.2 had no separation; this is the natural next refinement. |
| AS-AM4 | Modifier scheme per stage: Stage 2 (USER_OUTER) is **location-driven** (mouse position decides intent); Stage 4 (USER_STEINERS) is **modifier-driven** (no location ambiguity inside silhouette). Ctrl+drag = delete in BOTH stages (consistent). | Stage 2 has a natural inside/outside split (extend vs cut) that Stage 4 doesn't have. Forcing the same scheme on both is artificial. |
| AS-AM5 | Stage 2 gestures: LMB drag outside silhouette = extend (splice stroke verts into outer contour). LMB drag inside silhouette = cut (remove silhouette chunk). LMB drag crossing border = clipped to inside + cut (with WARNING "stroke clipped to silhouette"). Ctrl+drag = delete. | Permissive UX: artist can rabiscar without aiming precisely. Clip + WARNING signals what happened. |
| AS-AM6 | Stage 4 gestures: LMB drag = fold-line stroke (today's behavior); Shift+LMB drag = cut (NEW); Ctrl+LMB drag = delete (was Shift+LMB drag). Single click (< 5px) still = 1 Steiner. | Ctrl+drag delete is consistent with Stage 2. Shift+drag cut keeps the modifier-modifier-intent pattern. |
| AS-AM7 | ~~`Stroke.kind = "cut"` joins the existing `"point"` and `"stroke"` values. Cut implementation: resample stroke + smooth per S2/S3, compute 2 offset loops (perpendicular to stroke direction at each sample, distance = `cut_width / 2`), add both loops as CDT constraint edges, post-CDT face-prune removes faces whose centroid lies between the loops (reuses `delete_faces_inside_holes` pattern from `cdt.py`).~~ **SUPERSEDED by AS-AM7-REV (2026-05-27).** | Original lens + face-prune removes mesh material; wrong semantic for the "isolate fingers" use case where artist wants topological RIP without losing area. Lens machinery still applies to Stage 2 outer-cut (chunk removal IS appropriate for silhouette refinement). |
| AS-AM7-REV | (2026-05-27) `Stroke.kind = "cut"` on Stage 4 USER_STEINERS = **rip via `bmesh.ops.split_edges`**. Stroke goes into CDT as single polyline constraint (identical to `kind="stroke"`). Post-CDT, the stroke's constraint edges are identified in the bmesh + passed to `split_edges`. Result: stroke verts duplicated, left + right faces topologically separated, zero material removed. Optional `cut_margin > 0` translates the 2 vert copies perpendicular to the stroke by `±margin/2` for visible gap (default 0 = co-located, invisible at rest). Stage 2 outer-cut keeps the lens/face-prune machinery (chunk removal is the correct semantic for silhouette refinement). | Lifts Blender's V (rip vertices) behavior into the modal: the artist's cut becomes a topological split so rigged fingers/limbs deform independently, without losing mesh area. cut_margin slider lets the artist preview the cut visually if desired. |
| AS-AM8 | ~~`StageParams.cut_width` slider (default `interior_spacing * 0.3`, min 0.01, max `interior_spacing * 2.0`).~~ **SUPERSEDED by AS-AM8-REV.** | cut_width was sized for lens-based remove (AS-AM7); the rip-based AS-AM7-REV needs different semantics (gap visibility, not material removal width). |
| AS-AM8-REV | (2026-05-27) `StageParams.cut_margin` slider (default `0.0`, min `0.0`, max `interior_spacing * 2.0`). Default 0 = pure rip (co-located duplicated verts, invisible at rest). Values > 0 translate the 2 vert copies perpendicular to the stroke by `±margin/2` for visible gap. Replaces AS-AM8's cut_width. | cut_width was sized for lens-based remove machinery; cut_margin is sized for visible-gap controls atop the rip-based machinery. Same prop name space, semantic shift. |
| AS-AM9 | Tooltip near mouse cursor via `blf.draw` at `(mouse_x + 15, mouse_y - 15)`. Updates per MOUSEMOVE. Text reflects current intent (e.g. "Extend outer", "Cut silhouette", "Fold-line stroke", "Cut", "Delete: stroke"). Color = white + 1px black shadow for legibility. Size 11px. | Modal modes are non-obvious; tooltip eliminates "which gesture does what" memorization. Mirrors Blender's tool-active hints. |
| AS-AM9-REV | (2026-05-27) Stroke overlay color differentiates intent: fold-line `kind="stroke"` = blue (current), Stage 4 `kind="cut"` (rip) = RED, Stage 2 `kind="cut"` (chunk-remove) = ORANGE. Tooltip text + overlay color together signal artist intent at draw time and at preview time. | Manual smoke revealed that lens-cut + fold-line drew identical blue overlay; artist could not tell what they had drawn after the fact. Color encoding distinguishes rip from chunk-remove + fold-line at a glance. |
| AS-AM10 | Stage 2 extend mechanic: stroke verts outside silhouette are appended to outer contour pre-CDT via splice. Splice point = closest existing outer vert; stroke verts inserted in sequence between splice points. Smooth-and-resample then runs on the spliced outer as a whole (so extended portion gets the same target_contour_vertices treatment). | Splice into raw outer keeps the smoothing pipeline coherent. Splicing into smoothed outer would lose the extension on the next regen. |

### Scope estimate

~970 LOC + ~18 tests across 10 tasks. PR #63 grows from 25 → ~40 commits. Tightly bundled per user preference; reviewer-friendly via topical commit ordering (amendment doc first, then bug fixes, then feature additions, then UI/tooltip, then smoke).

## References

- Wave 13.2 modal: `apps/blender/operators/automesh_authoring.py`
- Pipeline dispatch: `apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py`
- CDT wrapper: `apps/blender/core/bpy_helpers/automesh/cdt.py`
- build_automesh: `apps/blender/core/bpy_helpers/automesh/bridge.py`
- Sidecar: `apps/blender/core/skinning/weight_reproject.py` + `sidecar_schema.py`
- TODO: `specs/013-weight-paint-automesh/TODO.md` (productivity polish section)
- Brainstorm session mockups: under `.superpowers/brainstorm/` (gitignored; local-only artifacts, see brainstorming companion notes)
