# the productivity follow-up - Edit Weights Modal + Provenance Overlay: Design

Status: design locked 2026-05-21. Decisions taken autonomously per user delegation; UX-touching items confirmed via questions.

Scope: one-button entry into a 2D-safe weight paint context with custom GPU provenance overlay, per-stroke `user_paint` provenance tagging, hard exit guarantees, and `Edit Weights` sub-box in the Skinning panel. Closes D6 (provenance overlay GPU draw), D7 (modal wrapper - includes Bone Collections visibility snapshot per COA2 lift), D8 (2D paint preset), D9 (paint diff tagging), D10 (ESC hard-exit), D12 (tablet release), D14 (mirror axis source from picker rig).

Foundation: the sidecar work shipped (entries populated, `show_provenance_overlay` PG flag reserved, `SidecarEntry.provenance` literal supports `auto_seed` / `user_paint` / `reprojected`).

## Decisions

### Technical (autonomous)

| # | Decision | Locked value | Rationale |
| --- | --- | --- | --- |
| T1 | Modal shape | Mono-operator `PROSCENIO_OT_edit_weights_modal` (single class owning snapshot + preset + overlay + diff lifecycle) | Matches COA2 `EditWeights` pattern + TODO.md pre-scope; splitting into wrapper + child operator over-engineers a contained scaffold |
| T2 | Paint preset shape | Frozen `PaintPresetSnapshot` dataclass (8 brush toggle fields); `apply_2d_preset` returns prior values for restore | Pure stdlib data class is testable bpy-free; symmetric apply/restore avoids drift |
| T3 | Mirror axis source | `scene.proscenio.active_armature.get("proscenio_mirror_x", False)` Custom Property (read once at invoke) | Picker owns rig metadata; per-modal toggle would create two sources of truth. Custom Property used instead of dedicated PG field so X-mirror persists on the rig data block, not scene state |
| T4 | Bone visibility | Blender 4.0+ Bone Collections snapshot/restore; 3.x fallback uses `bone.hide` | Future-proof; 4.0+ is project baseline |
| T5 | ESC behavior | Hard exit via `_finish(cancel=True)` - restores session even mid-stroke | Matches D10; no "are you sure" prompt; cumulative paint stays in single undo push so Ctrl+Z reverts everything |
| T6 | Stroke detection | LEFTMOUSE press = snapshot, LEFTMOUSE release = diff (modal `PASS_THROUGH` during drag so Blender owns brush motion) | Avoids reimplementing brush; only intercepts boundaries |
| T7 | Tablet pressure | `event.pressure` check on `MOUSEMOVE` for pen-lift fallback (D12); pressure==0 mid-drag triggers diff | Workaround for known tablet bugs (T82432, T73377, T93069) |
| T8 | WINDOW_DEACTIVATE | Flushes in-flight stroke diff before yielding focus | Prevents lost provenance updates when user alt-tabs mid-stroke |
| T9 | Overlay handler | Single `register_handler(obj, mode)` returning handle; mode is `Literal["weight", "provenance"]` (only `provenance` used this wave) | Same module supports the future weight-gradient overlay; one entry point, one cleanup |
| T10 | Overlay shader | POST_VIEW `UNIFORM_COLOR` shader, per-vert 6px disc batched as POINTS primitive | Reuses the quick-armature spec `modal_overlay.py` shader; batched draw beats per-vert immediate mode |
| T11 | Provenance colors | cyan = reprojected (0.0, 0.8, 1.0, 0.9), white = user_paint (1.0, 1.0, 1.0, 0.9), gray = auto_seed (0.5, 0.5, 0.5, 0.6) | Matches TODO.md sketch; gray alpha lower so user_paint stands out as foreground |
| T12 | Diff storage | `StrokeDiffTracker` keeps in-memory pre-stroke weights dict; writes sidecar JSON only on post-stroke flip | One JSON serialize per stroke (not per mouse move) |
| T13 | Single undo push | Wrap cumulative paint in single `bpy.ops.ed.undo_push(message="Edit Weights")` at `_finish` | Spec D7 - one Ctrl+Z reverts the whole session |
| T14 | Crash safety | All bpy mutations inside try/finally; finally calls `session.restore`; uncaught exception logs traceback + reports INFO with restoration confirmation | D10 hard-exit guarantee extends to crashes |
| T15 | F3 visibility | Operator `bl_idname` follows project convention; F3 search matches via `bl_label` `Proscenio: Edit Weights` | No extra menu wiring needed; F3 auto-discovers registered operators |
| T16 | Edit Weights sub-box position | New `_draw_edit_weights_box` between `_draw_bind_box` and `_draw_snapshot_box` | Reads top-to-bottom as workflow: bind -> edit -> snapshot/restore |

### UX-touching (user confirmed)

| # | Decision | Locked value |
| --- | --- | --- |
| U1 | Scope split | **Single wave** - modal + brush preset + bone collections + ESC + tablet + overlay + diff tagging + Edit Weights sub-box all ship together |
| U2 | Diff timing | **Per-stroke** (LEFTMOUSE release fires diff + provenance flip + sidecar write) |
| U3 | Modal trigger | **Button in Skinning panel + F3 search** (no global keymap) |
| U4 | Overlay default | **Auto-ON when modal opens** - modal forces `show_provenance_overlay=True`, session restores prior flag on exit |

## Scope split

**This wave (paint) ships:**

- `PROSCENIO_OT_edit_weights_modal` operator with full session restore
- 2D paint preset (Front Faces off, brush radius unit, mirror axis from picker)
- Bone Collections snapshot/restore (Blender 4.0+ with 3.x fallback)
- GPU provenance overlay (cyan/white/gray per-vert discs)
- Per-stroke `user_paint` provenance flip via diff
- `Edit Weights` sub-box in Skinning panel (button + status text)
- Header pill via the quick-armature spec D6 chord-layout helper
- Tests (pure pytest + headless operator pytest)

**Deferred to successor work:**

- Weight-gradient overlay mode (the `mode="weight"` branch of `register_handler` - data shape supported but UI does not toggle)
- Per-bone soft/hard mode toggle (D16)
- Cross-mesh weight copy (`proscenio.copy_weights_to_selected`)
- Region-blending paint sources (D14 amendment direction)

**Deferred to later waves:**

- Smart Bones / corrective-action drivers (a future animation-system spec)
- Live pose-mode preview in weight paint (TODO.md L293)
- Brush settings curve presets (TODO.md L295)

## Architecture

```text
apps/blender/core/skinning/
├── paint_preset_2d.py            [NEW] pure PaintPresetSnapshot + apply/restore
└── weight_diff.py                [NEW] pure: diff_weights(before, after) -> set[int]

apps/blender/core/bpy_helpers/skinning/
├── paint_preset_bind.py          [NEW] reads/writes tool_settings.weight_paint
├── bone_collection_visibility.py [NEW] snapshot + restore (4.0+ Bone Collections / 3.x bone.hide)
├── weight_overlay.py             [NEW] GPU draw_handler 6-stop colorband + provenance discs
├── stroke_diff.py                [NEW] StrokeDiffTracker class (per-stroke snapshot + flip)
└── modal_session.py              [NEW] EditWeightsSession dataclass (prior state container)

apps/blender/operators/
└── edit_weights.py               [NEW] PROSCENIO_OT_edit_weights_modal

apps/blender/panels/skinning.py    [AMEND] _draw_edit_weights_box helper

tests/skinning/
├── test_paint_preset_2d.py       [NEW] 4 tests
├── test_weight_diff.py           [NEW] 4 tests
└── test_bone_collection_visibility.py [NEW] 3 tests (uses SimpleNamespace mocks)

apps/blender/tests/operators/
└── test_edit_weights_modal.py    [NEW] 5 headless tests
```

## Components

### Pure - `paint_preset_2d.py` (NEW, ~60 LOC)

```python
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class PaintPresetSnapshot:
    """8 brush toggles + 2 numeric fields tied to weight-paint UX."""
    use_front_faces: bool
    use_normal: bool
    use_accumulate: bool
    use_pressure_size: bool
    use_pressure_strength: bool
    use_x_mirror: bool
    brush_radius: int
    brush_strength: float


PRESET_2D = PaintPresetSnapshot(
    use_front_faces=False,        # T46254 / Front Faces Only breaks thin planes
    use_normal=False,
    use_accumulate=True,
    use_pressure_size=True,
    use_pressure_strength=True,
    use_x_mirror=False,           # overridden at invoke from picker.proscenio_mirror_x
    brush_radius=24,
    brush_strength=0.5,
)


def apply_2d_preset(
    current: PaintPresetSnapshot, mirror_x: bool
) -> PaintPresetSnapshot:
    """Apply PRESET_2D (with mirror override) to current; return prior for restore."""
    # implementation: shallow merge mirror_x into PRESET_2D
```

### Pure - `weight_diff.py` (NEW, ~30 LOC)

```python
def diff_weights(
    before: dict[int, float],
    after: dict[int, float],
    *,
    eps: float = 1e-4,
) -> set[int]:
    """Return vert indices whose weight changed by more than eps.

    Missing vert in `after` (group removed) counts as changed.
    """
```

### bpy - `bone_collection_visibility.py` (NEW, ~80 LOC)

```python
@dataclass(frozen=True)
class BoneCollectionSnapshot:
    """Visibility state of every Bone Collection (4.0+) or per-bone hide (3.x)."""
    visible_names: list[str]      # 4.0+: collection names with is_visible=True
    bone_hide_states: dict[str, bool]  # 3.x fallback: bone.name -> hide

def snapshot(armature) -> BoneCollectionSnapshot:
    """Capture current visibility. Detects API generation."""

def restore(armature, snap: BoneCollectionSnapshot) -> None:
    """Reapply visibility. Reverses snapshot symmetrically."""
```

### bpy - `paint_preset_bind.py` (NEW, ~60 LOC)

```python
def snapshot_paint_preset(context) -> PaintPresetSnapshot:
    """Read current weight_paint brush + tool_settings into a snapshot."""

def apply_paint_preset(context, preset: PaintPresetSnapshot) -> None:
    """Write 8 toggles + 2 numerics onto tool_settings.weight_paint + active brush."""
```

### bpy - `weight_overlay.py` (NEW, ~120 LOC)

```python
OverlayMode = Literal["weight", "provenance"]

def register_handler(obj, mode: OverlayMode) -> object:
    """Add a POST_VIEW draw handler; return handle for unregister."""

def unregister_handler(handle: object) -> None:
    """Remove the draw handler. No-op safe if already removed."""

# Internal: per-vert disc batch builder + colorband lookup
# Provenance mode: read sidecar JSON, look up entries[i].provenance, color per T11
# Weight mode (data-supported, not user-toggleable this wave): 6-stop colorband per active VG weight
```

### bpy - `stroke_diff.py` (NEW, ~70 LOC)

```python
class StrokeDiffTracker:
    """Per-stroke weight snapshot + flip provenance in sidecar."""

    def __init__(self, obj, sidecar: WeightSidecar) -> None: ...
    def snapshot_active_vg(self) -> None:
        """Capture weights for the currently-active vertex group."""
    def flip_touched_after_stroke(self) -> int:
        """Diff current vs snapshot, flip touched entries to 'user_paint',
        rewrite obj[SIDECAR_KEY] JSON, return touched count."""
```

### bpy - `modal_session.py` (NEW, ~70 LOC)

```python
@dataclass(frozen=True)
class EditWeightsSession:
    """Container for all prior state captured at modal invoke."""
    prior_active: bpy.types.Object | None
    prior_selected: list[bpy.types.Object]
    prior_mode: str
    prior_armature_mode: str
    prior_paint_preset: PaintPresetSnapshot
    prior_bone_collections: BoneCollectionSnapshot
    prior_overlay_flag: bool

def capture(context, obj, armature) -> EditWeightsSession: ...
def restore(context, session: EditWeightsSession) -> None:
    """Symmetric restore. try/finally-safe; logs but does not raise on partial failure."""
```

### Operator - `edit_weights.py` (NEW, ~180 LOC)

```python
class PROSCENIO_OT_edit_weights_modal(bpy.types.Operator):
    bl_idname = "proscenio.edit_weights"
    bl_label = "Proscenio: Edit Weights"
    bl_description = (
        "Enter a 2D-safe weight paint context for the active mesh. Applies a "
        "weight-paint preset tuned for 2D sprites (Front Faces off, mirror from "
        "picker rig), shows the provenance overlay (cyan=reprojected / white=user "
        "paint / gray=auto seed), and tags brushed verts as user_paint in the "
        "sidecar via per-stroke diff. ESC hard-exits and restores brush + bone "
        "visibility + mode + selection"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        # mesh + sidecar with entries + picker armature
        ...

    def invoke(self, context, event):
        # validate, capture session, apply preset, switch modes, force overlay ON,
        # register overlay, build status pill, WM_modal_handler_add
        ...

    def modal(self, context, event):
        if event.type == "ESC":
            return self._finish(context, cancel=True)
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            self._stroke_tracker.snapshot_active_vg()
            return {"PASS_THROUGH"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            touched = self._stroke_tracker.flip_touched_after_stroke()
            if touched:
                context.area.tag_redraw()
            return {"PASS_THROUGH"}
        if event.type == "WINDOW_DEACTIVATE":
            self._stroke_tracker.flip_touched_after_stroke()  # flush in-flight
            return {"PASS_THROUGH"}
        if event.type == "MOUSEMOVE" and getattr(event, "pressure", 1.0) == 0.0:
            # T7: pen-lift fallback for tablets that skip LEFTMOUSE RELEASE
            self._stroke_tracker.flip_touched_after_stroke()
            return {"PASS_THROUGH"}
        return {"PASS_THROUGH"}

    def _finish(self, context, *, cancel: bool) -> set[str]:
        try:
            bpy.ops.ed.undo_push(message="Edit Weights")
            session_restore(context, self._session)
            unregister_handler(self._overlay_handle)
        finally:
            ...
        return {"CANCELLED" if cancel else "FINISHED"}
```

### Panel - `_draw_edit_weights_box`

Position: between `_draw_bind_box` and `_draw_snapshot_box`.

```text
+- Edit Weights ----------------------+
| Active group: wrist                 |
| [        Edit Weights         ]     |
+-------------------------------------+
```

Button disabled when (a) no picker armature, (b) sidecar missing/empty, (c) mesh has no vertex groups. Active group label reads `obj.vertex_groups.active.name` or `(none)`.

## Data flow

```text
User clicks Skinning panel > Edit Weights button:
  invoke()
    validate -> mesh + populated sidecar + picker armature; abort with ERROR otherwise
    session = capture(context, obj, armature)
    apply_2d_preset(context, PRESET_2D, mirror_x=picker.proscenio_mirror_x)
    armature.mode = "POSE"
    obj.mode = "WEIGHT_PAINT"
    if first_selected_pose_bone.name in obj.vertex_groups:
      obj.vertex_groups.active_index = obj.vertex_groups[first_selected_pose_bone.name].index
    skinning_props.show_provenance_overlay = True
    overlay_handle = register_handler(obj, mode="provenance")
    stroke_tracker = StrokeDiffTracker(obj, sidecar_loaded_from_json)
    WM_modal_handler_add -> RUNNING_MODAL

User paints stroke (LEFTMOUSE down + drag + up):
  modal()
    LEFTMOUSE PRESS -> stroke_tracker.snapshot_active_vg()
    drag mouse -> PASS_THROUGH (Blender's native weight paint owns motion)
    LEFTMOUSE RELEASE -> stroke_tracker.flip_touched_after_stroke()
      -> reads current weights for active VG via vert.groups loop
      -> diff_weights(snapshot, current) -> touched: set[int]
      -> for i in touched: sidecar.entries[i].provenance = "user_paint"
      -> obj[SIDECAR_KEY] = to_json(sidecar)
      -> context.area.tag_redraw()  # overlay re-runs with updated colors

User presses ESC:
  modal() catches ESC
  _finish(cancel=True)
    try:
      bpy.ops.ed.undo_push(message="Edit Weights")  # one undo step for whole session
      session.restore(context)  # paint preset, bone collections, modes, active, selected, overlay flag
      unregister_handler(overlay_handle)
    finally:
      clear status pill
    return {"CANCELLED"}

User alt-tabs mid-stroke (WINDOW_DEACTIVATE):
  modal() flushes in-flight stroke via flip_touched_after_stroke()
  PASS_THROUGH (Blender handles focus loss)

Crash during modal (unexpected exception):
  finally block in _finish runs session.restore + unregister_handler
  console traceback; status bar INFO `Edit Weights modal restored`
```

## Error matrix

| Condition | Action | Message |
| --- | --- | --- |
| Active obj not MESH | ERROR + abort | `active object must be a mesh` |
| No picker armature set | ERROR + abort | `no picker armature - pick one in Skeleton panel first` |
| Sidecar missing | ERROR + abort | `no sidecar - run Bind to Picker Armature first` |
| Sidecar entries empty (pre-wave bind) | ERROR + abort | `sidecar has no entries (pre-wave bind) - re-bind to populate` |
| Sidecar JSON corrupt | ERROR + abort | `existing sidecar is corrupt: {exc} - re-bind to reset` |
| Mesh has no vertex groups | ERROR + abort | `mesh has no vertex groups - run Bind first` |
| Bone Collections 4.0+ API missing | INFO + use fallback | `using legacy bone.hide fallback (Blender < 4.0)` |
| Exception during modal | cleanup via try/finally | console traceback + INFO `Edit Weights modal restored` |

## Test plan

### Pure pytest

`tests/skinning/test_paint_preset_2d.py` (NEW, 4 tests):

- `test_apply_2d_preset_returns_prior` - apply_2d_preset called on current state returns dataclass identical to that state
- `test_apply_2d_preset_overrides_mirror_x` - mirror_x arg overrides PRESET_2D.use_x_mirror
- `test_restore_round_trip_is_idempotent` - apply -> restore -> apply produces same final state as single apply
- `test_preset_2d_locks_front_faces_off` - PRESET_2D.use_front_faces is False (regression guard for T46254 fix)

`tests/skinning/test_weight_diff.py` (NEW, 4 tests):

- `test_identical_dicts_return_empty_set` - same weights = no touched
- `test_single_vert_changed_returns_singleton` - one weight differs by > eps = 1-element set
- `test_eps_threshold_respected` - change below eps does NOT count as touched
- `test_missing_vert_in_after_counts_as_changed` - vert dropped from after dict = touched (weight set to 0)

`tests/skinning/test_bone_collection_visibility.py` (NEW, 3 tests):

- `test_snapshot_4x_captures_visible_collection_names` - SimpleNamespace mock with bone_collections list, snapshot reads is_visible
- `test_snapshot_3x_fallback_captures_bone_hide` - SimpleNamespace without bone_collections, snapshot falls back to bone.hide
- `test_restore_round_trip` - snapshot -> mutate visibility -> restore = original visibility

### Headless operator pytest

`apps/blender/tests/operators/test_edit_weights_modal.py` (NEW, 5 tests):

- `test_invoke_aborts_without_sidecar` - select hand without bind, invoke, expect CANCELLED with `no sidecar` error
- `test_invoke_enters_weight_paint_with_preset_applied` - bind + invoke, assert `obj.mode == "WEIGHT_PAINT"` + `tool_settings.weight_paint.brush.use_frontface == False`
- `test_stroke_flips_provenance_to_user_paint` - bind, invoke, simulate LEFTMOUSE PRESS + mutate vert weight + LEFTMOUSE RELEASE, assert sidecar entries for mutated verts have `provenance == "user_paint"`
- `test_escape_restores_session` - bind, invoke, fire ESC event, assert `obj.mode` restored + `tool_settings` restored + `show_provenance_overlay` restored to prior value
- `test_finish_writes_sidecar` - bind, invoke, stroke, ESC, assert `obj[SIDECAR_KEY]` JSON reflects updated provenance counts

### MANUAL_TESTING.md 1.22

```text
T1 - Enter Edit Weights modal:
  Bind hand sprite. Skinning panel > Edit Weights > click Edit Weights.
  Mode switches to Weight Paint. Provenance overlay visible (gray discs over all verts since fresh bind = all auto_seed).
  Status bar: `Edit Weights: ESC=exit | brush ready`.

T2 - Paint stroke flips provenance:
  Continue from T1. Paint over wrist area with Add brush.
  Release mouse - overlay discs in painted area flip from gray to white.
  Snapshot pill in panel updates: N paint / M seed / 0 reprojected (paint count > 0).

T3 - ESC hard-exits + restores state:
  Continue from T2. Press ESC.
  Mode returns to Object. Brush settings restored to pre-modal values (Front Faces back ON if it was ON before).
  Overlay disappears (show_provenance_overlay restored to prior state, default OFF).
  Bone visibility unchanged.

T4 - Reload Scripts mid-modal:
  Bind, invoke modal, do NOT exit, run Edit > Preferences > Reload Scripts.
  Modal closes cleanly, no orphan draw handler, no Python error in console.

T5 - Single undo push:
  Bind, invoke modal, paint stroke A, paint stroke B, ESC.
  Press Ctrl+Z once - both strokes A + B revert to pre-modal weights.

T6 - Button disabled affordance:
  Open fixture, select hand, do NOT bind. Skinning panel > Edit Weights button greyed out.
  Label below button: `bind first to enable`. Click does nothing.
  Bind - button enables.
```

## Out of scope (deferred)

- Weight-gradient overlay UI toggle (data shape supported, no panel button) -> successor work
- Per-bone soft/hard mode toggle (D16) -> successor work
- Region painting (paint into a procedural region rather than per-vert) -> successor work
- `proscenio.copy_weights_to_selected` cross-mesh transfer -> successor work
- Smart Bones / corrective-action drivers -> a future animation-system spec
- Live pose-mode preview in weight paint -> successor work
- Brush curve presets ("Hard edge" / "Soft falloff" / "Crease") -> successor work
- Bezier brush stroke for alpha-boundary trace -> successor work
