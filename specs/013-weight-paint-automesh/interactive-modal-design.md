# Wave 13.2 - Interactive Modal Automesh Authoring: Design

Status: design locked 2026-05-21. Decisions taken autonomously per user delegation; UX-touching items confirmed via questions.

Scope: 5-stage modal operator that lifts each existing automesh debug stage to an interactive preview (GPU overlay + slider-driven re-run + user input). Coexists with the one-shot `automesh_from_sprite` operator so power users get in-flight course correction without breaking the quick-path workflow. Closes "Interactive modal automesh authoring" line item from SPEC 013 Wave 13.2.

Foundation:

- Wave 13.1 (automesh) shipped the pipeline (alpha walker, smoothing, CDT, hole detection, bone-aware density)
- Wave 13.2-paint shipped the modal scaffold this wave lifts (session capture/restore, GPU overlay handlers, statusbar pill, try/finally crash safety)
- Wave 13.2-sidecar shipped reproject so existing weights survive the modal's APPLY stage

## Decisions

### Technical (autonomous)

| # | Decision | Locked value | Rationale |
| --- | --- | --- | --- |
| T1 | Inner loops source | Morphological erosions only v1 (reuse `core/automesh/alpha_contour.dilate/erode`) | Auto-compute keeps the modal deterministic + testable; user-drawn polylines defer to Wave 13.3 |
| T2 | User-pointed Steiner persistence | Custom Property `obj["proscenio_user_steiners"]: list[(x,z)]` (survives addon disable per SPEC 005) | Consistent with D6 sidecar pattern (artist work persists across automesh regens) |
| T3 | Stage 4 (Steiner preview) editing | Read-only (Stage 3 IS the edit step) | Single-responsibility per stage; editing in Stage 4 would duplicate Stage 3's interaction model |
| T4 | Existing sidecar collision | Auto-integrate with `preserve_on_regen` flag - final APPLY invokes `maybe_pre_regen_snapshot` + `maybe_post_regen_reproject` from Wave 13.2-sidecar | Reuses the shipped reproject; B1 fix preserves `user_paint` provenance through the regen |
| T5 | Stage navigation keys | ENTER advance / BACKSPACE back / ESC cancel | Matches the TODO L226 sketch + Blender modal conventions (Quick Armature uses ENTER confirm + ESC cancel) |
| T6 | Live re-run on parameter change | Throttled timer ~100ms - modal detects dirty PG state + recomputes current stage | Sliders feel responsive without recomputing per mouse move |
| T7 | Trigger surface | Skinning panel button (new sub-box between Automesh + Bind) + F3 search via `bl_label` | Matches paint wave precedent (button + F3, no global keymap) |
| T8 | GPU overlay shader | POST_VIEW SpaceView3D draw handlers via `modal_overlay._shader()` (UNIFORM_COLOR) | Reuses the SPEC 012 / 013.2 paint shader stack; one entry point, one cleanup path |
| T9 | Per-stage parameters | `scene.proscenio.skinning.authoring_*` fields (PG persists across .blend reloads) | Same persistence pattern as Wave 13.2-panel bind fields |
| T10 | Final APPLY pipeline | Pipes through existing `build_automesh` + `_delete_faces_inside_holes` with outer + inner_loops + user_steiners + bone_steiners as constraints | Reuses Wave 13.1 implementation; only the constraint set changes |
| T11 | Cleanup prerequisite (cognitive-47 monolith refactor, TODO L271) | SKIPPED - not blocking | Documented as risk: if `build_automesh` proves too tangled to lift, in-wave extract refactor OR split prerequisite mini-wave |
| T12 | Stage state machine | `IntEnum` with 5 values + frozen `StageParams` + frozen `StageOutput` dataclasses | Pure dataclasses keep state inspectable + testable; IntEnum allows arithmetic (`stage + 1`) for advance/retreat |
| T13 | Overlay refresh on stage change | `refresh_overlay(handles, stage, output)` rebuilds batches in-place | Single function for both stage-change refresh + slider-driven dirty recompute |
| T14 | Click-to-place Steiner | LEFTMOUSE PRESS only adds; Shift+LEFTMOUSE removes nearest within threshold | Matches the U2 decision (click-only v1); drag-stroke deferred to Wave 13.3 |
| T15 | Cursor world projection | `region_to_world_xz` helper projecting region pixel coords to Y=0 XZ plane | Proscenio convention (camera at -Y looking +Y); same projection Quick Armature uses |
| T16 | Crash safety | try/finally around all bpy mutations; finally calls `session.restore`; uncaught exception logs traceback + reports INFO | Same pattern as paint wave's edit_weights operator |

### UX-touching (user confirmed)

| # | Decision | Locked value |
| --- | --- | --- |
| U1 | Modal vs one-shot | **Coexist** - 2 operators side by side; one-shot stays as quick path, modal is the guided path |
| U2 | Stage 3 Steiner placement | **Click-only point-by-point** - LEFTMOUSE add / Shift+LEFTMOUSE delete nearest. Drag-stroke + free-draw polyline defer to Wave 13.3 |

## Scope split

**This wave (interactive modal) ships:**

- `PROSCENIO_OT_automesh_authoring` operator with 5-stage state machine
- Per-stage GPU overlay (POST_VIEW UNIFORM_COLOR shader, batched primitives)
- Live re-run on slider drag (throttled 100ms via TIMER)
- User Steiner click placement + Custom Property persistence
- Final APPLY pipes existing `build_automesh` with all constraint sets + reproject existing sidecar via Wave 13.2-sidecar hook
- Skinning panel sub-box (button entry, between Automesh + Bind)
- Tests (pure + headless) + MANUAL_TESTING 1.23

**Deferred to Wave 13.3:**

- User-drawn inner loops (free-draw polylines as CDT constraint edges)
- Drag-stroke Steiner placement (multiple points per drag)
- Brush stroke for alpha-boundary trace (D1.B paradigm enum)
- Stage 4 editable Steiners (drag-to-move, delete-with-X)

**Deferred to later waves:**

- Cleanup prerequisite (cognitive-47 `build_automesh` refactor) - in-wave only if blocking; otherwise track separately
- Pose-mode preview mid-modal (Wave 13.3 feature)

## Architecture

```text
apps/blender/core/automesh/
└── erosion_loops.py              [NEW] pure: compute N concentric inner loops via dilate/erode

apps/blender/core/skinning/
└── authoring_stages.py           [NEW] pure: AuthoringStage IntEnum + StageParams + StageOutput dataclasses

apps/blender/core/bpy_helpers/automesh/
├── authoring_overlay.py          [NEW] GPU draw handlers per stage (polylines + dots)
├── authoring_session.py          [NEW] AuthoringSession dataclass (prior viewport state)
└── authoring_pipeline.py         [NEW] dispatch: compute_stage(stage, params) -> StageOutput

apps/blender/operators/
└── automesh_authoring.py         [NEW] PROSCENIO_OT_automesh_authoring modal

apps/blender/properties/scene_props.py [AMEND] ProscenioSkinningProps gains authoring_* fields
apps/blender/panels/skinning.py    [AMEND] _draw_authoring_box between Automesh + Bind

tests/skinning/
├── test_erosion_loops.py         [NEW] 5 tests
└── test_authoring_stages.py      [NEW] 3 tests

apps/blender/tests/operators/
└── test_automesh_authoring.py    [NEW] 5 headless tests
```

## Components

### Pure - `erosion_loops.py` (NEW, ~80 LOC)

```python
def compute_inner_loops(
    outer_polyline: list[Point2D],
    *,
    count: int,
    spacing_world: float,
) -> list[list[Point2D]]:
    """N concentric inner polylines via successive morphological erosion.

    Each loop is eroded `spacing_world` further inward than the prior.
    Empty result when count==0 OR erosion collapses to <3 points.
    Reuses dilate/erode from alpha_contour (pure module).
    """
```

### Pure - `authoring_stages.py` (NEW, ~60 LOC)

```python
class AuthoringStage(IntEnum):
    OUTER = 0
    INNER_LOOPS = 1
    USER_STEINERS = 2
    STEINER_PREVIEW = 3
    APPLY = 4


@dataclass(frozen=True)
class StageParams:
    """Snapshot of all PG fields the modal reads.

    Frozen so re-run logic can compare via equality to detect dirty state.
    """
    resolution: float
    alpha_threshold: int
    margin_pixels: int
    contour_vertices: int
    inner_loop_count: int
    inner_loop_spacing: float
    interior_spacing: float
    bone_radius: float
    bone_factor: int


@dataclass(frozen=True)
class StageOutput:
    """What each stage produces; subsequent stages consume + extend."""
    outer: list[Point2D] = field(default_factory=list)
    inner_loops: list[list[Point2D]] = field(default_factory=list)
    user_steiners: list[Point2D] = field(default_factory=list)
    all_steiners: list[Point2D] = field(default_factory=list)
```

### bpy - `authoring_pipeline.py` (NEW, ~120 LOC)

```python
def compute_outer(obj, image, params) -> list[Point2D]:
    """Run alpha walker -> smooth -> resample; returns outer polyline.

    Reuses Wave 13.1 helpers via core/automesh/.
    """

def compute_inner_loops_for_stage(outer, params) -> list[list[Point2D]]:
    """Delegate to pure erosion_loops.compute_inner_loops."""

def read_user_steiners(obj) -> list[Point2D]:
    """Read obj['proscenio_user_steiners']; empty list when absent."""

def write_user_steiners(obj, points: list[Point2D]) -> None:
    """Persist via Custom Property; serializes as list of length-2 tuples."""

def compute_all_steiners(
    outer, inner_loops, user, bone_segments, params
) -> list[Point2D]:
    """Uniform interior grid + bone density + merge user steiners.

    Reuses core/automesh/density.py uniform grid helper + Wave 13.1
    bone-density logic.
    """

def apply_mesh(
    obj, image, output: StageOutput, params, armature
) -> dict[str, int]:
    """Final write: build_automesh w/ outer + inner_loops + holes + all_steiners
    as constraints. If existing populated sidecar + preserve_on_regen ON,
    invoke maybe_pre_regen_snapshot / maybe_post_regen_reproject around
    the regen so user_paint provenance survives (B1 fix carries it).

    Counters: {outer_verts, inner_verts, user_steiners_used, total_verts,
    total_faces, reprojected, auto_seed}.
    """
```

### bpy - `authoring_overlay.py` (NEW, ~150 LOC)

```python
class OverlayHandles(TypedDict):
    outer: object | None
    inner: object | None
    steiners: object | None
    user_dots: object | None


def register_overlay(stage: AuthoringStage, output: StageOutput) -> OverlayHandles:
    """Add POST_VIEW SpaceView3D draw handlers per stage's overlay set."""


def unregister_overlay(handles: OverlayHandles) -> None:
    """No-op-safe cleanup; tolerates partial registration via contextlib.suppress."""


def refresh_overlay(
    handles: OverlayHandles, stage: AuthoringStage, output: StageOutput
) -> OverlayHandles:
    """Replace draw handlers when stage data changes (slider drag or stage advance)."""


# Internal: per-stage batch builders
# OUTER: cyan polyline (0.0, 0.8, 1.0, 0.9), LINE_STRIP primitive
# INNER_LOOPS: outer dim + N green polylines (alpha decay per loop index)
# USER_STEINERS: outer dim + inner dim + yellow dots (1.0, 1.0, 0.0, 0.9), POINTS at 8px
# STEINER_PREVIEW: outer dim + inner dim + red dots (1.0, 0.3, 0.3, 0.7) at 4px + user yellow 8px
```

### bpy - `authoring_session.py` (NEW, ~60 LOC)

```python
@dataclass(frozen=True)
class AuthoringSession:
    """Captured viewport state at modal invoke."""
    prior_active: bpy.types.Object | None
    prior_selected_names: list[str] = field(default_factory=list)
    prior_mode: str = "OBJECT"
    prior_show_overlays: bool = True
    obj_name: str | None = None


def capture(context, obj) -> AuthoringSession: ...


def restore(context, session: AuthoringSession) -> None:
    """Symmetric restore in safe order; suppress per-step failures."""
```

### Operator - `automesh_authoring.py` (NEW, ~250 LOC)

```python
class PROSCENIO_OT_automesh_authoring(bpy.types.Operator):
    bl_idname = "proscenio.automesh_authoring"
    bl_label = "Proscenio: Automesh Authoring"
    bl_description = (
        "Multi-stage modal preview of the automesh pipeline. Each stage "
        "(outer contour / inner loops / user Steiner points / Steiner preview "
        "/ apply) surfaces a GPU overlay + slider-driven re-run so the artist "
        "iterates on the mesh shape before any geometry commits. ENTER advances "
        "stages; BACKSPACE goes back; ESC cancels. Coexists with the one-shot "
        "automesh_from_sprite operator (quick path stays)"
    )
    bl_options = {"REGISTER", "UNDO"}

    _stage: AuthoringStage
    _output: StageOutput
    _handles: OverlayHandles
    _session: AuthoringSession | None
    _last_params: StageParams | None
    _timer: bpy.types.Timer | None
    _statusbar_appended: bool

    @classmethod
    def poll(cls, context): ...  # mesh + image texture present

    def invoke(self, context, event):
        # validate, capture session, compute OUTER, register overlay,
        # add timer, append statusbar, WM_modal_handler_add
        ...

    def modal(self, context, event):
        if event.type == "ESC":
            return self._finish(context, cancel=True)
        if event.type == "RET" and event.value == "PRESS":
            return self._advance(context)
        if event.type == "BACK_SPACE" and event.value == "PRESS":
            return self._retreat(context)
        if self._stage == AuthoringStage.USER_STEINERS:
            if event.type == "LEFTMOUSE" and event.value == "PRESS":
                if event.shift:
                    return self._delete_nearest_steiner(context, event)
                return self._add_steiner(context, event)
        if event.type == "TIMER":
            current = StageParams.from_pg(context)
            if current != self._last_params:
                self._recompute_current_stage(context, current)
                self._last_params = current
        return {"PASS_THROUGH"}

    def _advance(self, context) -> set[str]:
        # if APPLY: run apply_mesh + _finish(cancel=False) -> FINISHED
        # else: bump stage, compute next stage's output, refresh overlay
        ...

    def _retreat(self, context) -> set[str]: ...
    def _recompute_current_stage(self, context, params) -> None: ...
    def _add_steiner(self, context, event) -> set[str]: ...
    def _delete_nearest_steiner(self, context, event) -> set[str]: ...

    def _finish(self, context, *, cancel: bool) -> set[str]:
        try:
            unregister_overlay(self._handles)
            if self._timer is not None:
                context.window_manager.event_timer_remove(self._timer)
            self._remove_statusbar()
            if self._session is not None:
                session_restore(context, self._session)
        finally:
            report_info(self, "Authoring modal restored")
        return {"CANCELLED" if cancel else "FINISHED"}
```

### Panel - `_draw_authoring_box`

Position: between `_draw_automesh_box` and `_draw_bind_box`.

```text
+- Automesh authoring -----------------+
| Multi-stage modal preview            |
| Inner loops: 2 | Spacing: 0.15       |
| [   Automesh (modal)            ]    |
+--------------------------------------+
```

Two readonly labels echo the PG settings the modal will use; button greys out when active obj is not MESH or has no image texture.

### PropertyGroup amend

```python
authoring_inner_loop_count: IntProperty(
    name="Inner loops",
    description=(
        "Concentric inner polylines computed via morphological erosion of "
        "the outer contour. Higher count = more edge loops the CDT respects "
        "= more deformation control near the silhouette boundary"
    ),
    default=2,
    min=0,
    max=10,
)
authoring_inner_loop_spacing: FloatProperty(
    name="Inner loop spacing",
    description=(
        "World-unit gap between adjacent inner loops. Smaller = denser "
        "loops near the boundary; larger = single loop closer to mesh center"
    ),
    default=0.15,
    min=0.01,
    soft_max=1.0,
)
```

## Data flow

```text
User clicks Skinning panel > Automesh authoring > Automesh (modal):
  invoke()
    validate (mesh + image texture)
    session = capture(context, obj)
    params = StageParams.from_pg(context)
    output.outer = compute_outer(obj, image, params)
    handles = register_overlay(AuthoringStage.OUTER, output)
    timer = context.window_manager.event_timer_add(0.1, window=...)
    _append_statusbar
    WM_modal_handler_add -> RUNNING_MODAL

User scrubs Mesh resolution slider in N-panel:
  TIMER fires (every 100ms)
    current = StageParams.from_pg(context)
    if current != self._last_params:
      output.outer = compute_outer(obj, image, current)  # OR appropriate stage
      handles = refresh_overlay(handles, OUTER, output)
      self._last_params = current

User presses ENTER (OUTER -> INNER_LOOPS):
  _advance()
    output.inner_loops = compute_inner_loops_for_stage(output.outer, params)
    handles = refresh_overlay(handles, INNER_LOOPS, output)
    _stage = INNER_LOOPS
    update statusbar pill

User presses ENTER (INNER_LOOPS -> USER_STEINERS):
  _advance()
    output.user_steiners = read_user_steiners(obj)
    refresh_overlay
    _stage = USER_STEINERS

User left-clicks in viewport (USER_STEINERS):
  modal() catches LEFTMOUSE PRESS without Shift
    _add_steiner(context, event)
      world_xz = region_to_world_xz(event.mouse_region_x, event.mouse_region_y)
      output.user_steiners.append(world_xz)
      write_user_steiners(obj, output.user_steiners)
      refresh_overlay

User shift+clicks near a point (USER_STEINERS):
  _delete_nearest_steiner
    find nearest point within threshold; remove; persist; refresh

User presses ENTER (USER_STEINERS -> STEINER_PREVIEW):
  _advance()
    bone_segments = collect_bone_segments(picker_armature) if picker else []
    output.all_steiners = compute_all_steiners(
      outer, inner_loops, user_steiners, bone_segments, params
    )
    refresh_overlay (red dots + user yellow)
    _stage = STEINER_PREVIEW

User presses ENTER (STEINER_PREVIEW -> APPLY):
  _advance()
    counters = apply_mesh(obj, image, output, params, armature)
      # build_automesh with all constraints
      # if existing sidecar populated + preserve_on_regen:
      #   prior = maybe_pre_regen_snapshot(obj, armature)
      #   ... build runs ...
      #   maybe_post_regen_reproject(obj, armature, prior)  # B1 fix preserves user_paint
    unregister_overlay + remove timer + restore session
    return {"FINISHED"} (no cancel - APPLY is the terminal success state)

User presses ESC (any stage):
  _finish(cancel=True)
    try/finally:
      unregister_overlay
      event_timer_remove
      remove statusbar
      session.restore
    return {"CANCELLED"}
```

## Error matrix

| Condition | Action | Message |
| --- | --- | --- |
| Active obj not MESH | ERROR + abort | `active object must be a mesh` |
| Active mesh has no image texture | ERROR + abort | `active mesh has no image texture - add a material with a TEX_IMAGE node first` |
| Stage compute raises (alpha walker / erosion / CDT) | WARN + stay on current stage | `stage {name} failed: {exc} - adjust params or BACKSPACE` |
| User clicks outside silhouette in USER_STEINERS | INFO (no abort) | `Steiner outside silhouette - point added anyway (may be deleted on apply)` |
| Final APPLY: CDT degenerate | ERROR + stay on STEINER_PREVIEW | `CDT failed: {exc} - reduce loop count or increase spacing` |
| Exception in modal | hard cleanup via try/finally | console traceback + INFO `Authoring modal restored` |

## Test plan

### Pure pytest

`tests/skinning/test_erosion_loops.py` (NEW, 5 tests):

- `test_simple_circle_erodes_by_spacing` - circle radius 1.0 + spacing 0.1 + count 1 → returns 1 loop with smaller radius
- `test_count_zero_returns_empty` - count=0 → empty list
- `test_erosion_collapses_when_spacing_too_large` - spacing > radius → loops cut off early; returns fewer than count
- `test_non_convex_outer_respects_concavity` - L-shape outer → erosion stays inside L
- `test_three_loops_returns_nested` - count=3 + spacing=0.1 + circle radius 0.5 → 3 nested polylines with decreasing radius

`tests/skinning/test_authoring_stages.py` (NEW, 3 tests):

- `test_authoring_stage_enum_order` - 5 values in expected order (OUTER=0 ... APPLY=4)
- `test_stage_params_frozen_equality` - 2 identical StageParams compare equal; mutation raises
- `test_stage_output_defaults_empty_lists` - StageOutput() has empty outer/inner/user/all

### Headless operator pytest

`apps/blender/tests/operators/test_automesh_authoring.py` (NEW, 5 tests):

- `test_invoke_aborts_without_image_texture` - mesh w/o material → CANCELLED with `image texture` error
- `test_invoke_enters_outer_stage` - hand fixture → invoke returns RUNNING_MODAL; `_stage == OUTER`; `_handles["outer"] is not None`
- `test_advance_runs_pure_pipeline_through_all_stages` - drive `_advance` programmatically; assert each stage's output field populated; assert TIMER recompute fires once when PG params change
- `test_user_steiners_persist_via_custom_property` - synthetic LEFTMOUSE events at known coords → `obj["proscenio_user_steiners"]` has matching count + values
- `test_apply_invokes_sidecar_reproject_when_prior_sidecar_populated` - bind hand first, invoke authoring, advance to APPLY with same params, assert post-mesh sidecar entries include reprojected provenance

### MANUAL_TESTING.md 1.23

6 T-cases:

- T1: Enter modal → OUTER overlay (cyan polyline matching sprite silhouette)
- T2: Scrub resolution slider → overlay re-runs live (throttled ~100ms)
- T3: Advance to USER_STEINERS → left-click viewport adds yellow dot; shift+click near it removes
- T4: Advance to STEINER_PREVIEW → red dots cover interior; user yellows remain
- T5: APPLY → mesh commits with all constraints respected (visual check vs one-shot output at same params)
- T6: APPLY with prior bind sidecar → sidecar pill shows reprojected count > 0 + user_paint preserved if pre-painted

## Out of scope (deferred)

- User-drawn inner loops (free-draw polylines as CDT constraint edges) -> Wave 13.3
- Drag-stroke Steiner placement (multiple points per drag) -> Wave 13.3
- Brush stroke for alpha-boundary trace (D1.B paradigm enum) -> Wave 13.3
- Stage 4 editable Steiners (drag-to-move, delete-with-X) -> Wave 13.3
- Pose-mode preview mid-modal -> Wave 13.3
- Cleanup prerequisite (cognitive-47 build_automesh refactor) -> in-wave only if blocking; otherwise separate effort
