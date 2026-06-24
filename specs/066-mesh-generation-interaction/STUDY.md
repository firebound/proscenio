# Spec 066: Mesh generation interaction

The interactive mesh-generation modal (`automesh_authoring`) carries two unfinished interaction goals that share one input layer and so share one spec. First, a Spine / Live2D-style contour pen-tool: click to drop hull points one at a time, keep adding until the loop closes, with a live preview of the triangulated result as the contour is authored - reusing the precepts the toolset already ships (dense vs simple interior, optional fill / automesh of the interior after the outline is set, marked areas for cut and fold). Second, a full redesign of the modal's chord scheme, a need mapped repeatedly and deferred each time because the current scheme is bad and a real redesign cannot be done piecemeal: the tap-to-toggle-mode-on-Shift/Ctrl gesture is bad, but hold-to-mode is also bad, so the spec has to design a third way that still preserves Ctrl+Z undo, the X/Z axis lock, and reparent.

These two goals are merged because the contour pen-tool cannot be added without touching the same chord-and-mode state machine the redesign rewrites. The contour pen-tool is the gated `manual-hull-pen-tool` item ([gated.md](../gated.md) "Mesh authoring"); building it here is a deliberate reopening of that gate, justified by the pre-v1 interest in a real hull-authoring gesture rather than the Edit Mode + Reproject UV fallback. The interior pen mode the modal already ships (interior strokes, cut-draw, X/Z lock, Ctrl+Z) is the working precedent the outer-contour gesture extends, and spec 058 (Quick Armature) explicitly borrowed "the automesh-authoring precedent" for its Tab-cycles-mode status bar - so the redesign here is reworking the very pattern other modals copied.

## Scope

- **The contour pen-tool** - author the outer hull by clicking points until the loop closes, with a live triangulation preview, integrated with the existing dense/simple interior modes and the post-contour fill / cut / fold marking. Reopens the gated `manual-hull-pen-tool`.
- **The chord / mode redesign** - replace the Shift/Ctrl tap-to-toggle mode scheme with an interaction that is neither tap-toggle nor hold-to-mode, while preserving Ctrl+Z, the X/Z axis lock, and reparent.
- **Preserve the working precedents** - the interior pen mode, the SIMPLE/DENSE stage walk, the status-bar per-mode chord layout, and the outer-stroke undo must survive or improve, not regress.

## Open decisions

### 1. The contour gesture: how the outer hull is authored and previewed

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`_handle_pen_event`, `_on_modifier_tap`, `_enter_draw` / `_exit_draw` - the interior pen mode that already adds verts, free-draws on drag, X/Z-locks, and undoes via Ctrl+Z; `_outer_stroke_undo`, `_delete_outer_stroke_at_mouse`, `_remove_outer_stroke` - the outer-stroke layer the contour would feed; the `AuthoringStage` SIMPLE/DENSE stage orders and `_stages_for_mode`); `apps/blender/operators/automesh/automesh.py` (the non-interactive automesh entry - the triangulation the preview must mirror); `apps/blender/core/bpy_helpers/skinning/automesh_hook.py` (the trace/triangulate core the preview calls). Locked context: `decisions.md` mesh-authoring entries; the gated `manual-hull-pen-tool` trigger and its "Edit Mode + Reproject UV is a workable fallback" framing.

**Question:** A contour is an ordered ring of clicked points that closes into a loop and then triangulates. The modal already has a pen mode for interior strokes - does the outer contour reuse that pen state machine as a new stage, or is it a distinct authoring surface? And how does the live triangulation preview stay cheap enough to redraw per added point?

**Options:** (A) New outer-contour stage in the existing pen state machine, reusing `_handle_pen_event` vert-adding and the outer-stroke undo. (B) A separate contour sub-mode with its own state, sharing only the preview renderer. (C) ...

**Recommendation:** TBD - lock during STUDY. Key tension: reuse keeps one input code path (cheaper, less regression surface) but overloads a pen mode that was built for interior strokes; a separate sub-mode is cleaner conceptually but duplicates undo/preview wiring. Decide alongside decision 2, since the gesture and the chord scheme are the same machine.

### 2. The chord / mode scheme: the third way past tap-toggle and hold-to-mode

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (lines ~261-486: the toggle-pen state - "a clean Shift/Ctrl tap (press + release with no intervening press) toggles draw mode", `_SHIFT_CTRL_KEYS`, `_press_modifier`, `_on_modifier_tap`, the modifier-tap-vs-Ctrl+Z disambiguation that exists precisely because tap-toggle collides with Ctrl+Z); `apps/blender/operators/automesh/_status_bar.py` (`emit_authoring_chord_layout` - the per-mode status-bar chord display the redesign must keep coherent); `_apply_interior_mode_change`, `_current_interior_mode`. Locked context: spec 058 `_index.md` entry (Tab cycles modes, status bar swaps to the active mode's chords - "the automesh-authoring precedent"); the no-hard-wrap and definitive-step conventions.

**Question:** The current scheme overloads a Shift/Ctrl tap to toggle draw mode, which forces an explicit tap-vs-hold disambiguation so Ctrl+Z is not eaten - the source of the badness. What replaces it? A Tab-cycles-mode model (058's own borrowing of this modal), a dedicated key per mode, a radial / pie menu, or a click-to-confirm-mode? Whatever it is must leave Ctrl+Z, X/Z lock, and reparent unambiguous.

**Options:** (A) Tab cycles interior mode (symmetry with 058), discrete mode keys for the rest. (B) Pie/radial mode menu on a held key. (C) Dedicated single-press keys per mode, no toggle. (D) ...

**Recommendation:** TBD - lock during STUDY. Constraint set the redesign must satisfy verbatim: Ctrl+Z undo survives, X/Z axis lock survives, reparent survives. Strong prior: 058 already validated Tab-cycles-mode + status-bar-per-mode as the house pattern, so symmetry argues for adopting it back here unless the contour pen-tool needs more modes than a single Tab cycle reads cleanly.

### 3. Interior fill, cut, and fold marking after the contour closes

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`_handle_user_steiners_event`, the SIMPLE vs DENSE interior stage `PREVIEW_INTERIOR`, `_stage_base_name`); `apps/blender/core/bpy_helpers/skinning/automesh_hook.py` (interior densification); the existing cut/hole handling (`decisions.md` 052 "degenerate Constrained Delaunay holes filtered before the with-holes output").

**Question:** Once the contour is closed, the existing dense-vs-simple interior fill and the cut / fold area marking must compose with the new contour. Is the post-contour flow identical to today's interior stage, or does authoring the hull first change the stage order?

**Options:** (A) Contour becomes a new first stage; the existing interior stages run unchanged after it. (B) Contour replaces the outer-stroke stage and reuses the same interior follow-on. (C) ...

**Recommendation:** TBD - lock during STUDY. Lean: keep the existing interior stages untouched and slot the contour ahead of them, so dense/simple and cut/fold marking carry over with no behavioral change.

## Verdict summary

Skeleton STUDY - decisions framed, not yet locked. Three coupled decisions over one modal: the contour gesture (decision 1), the chord/mode redesign (decision 2), and the post-contour interior/cut/fold composition (decision 3). The contour pen-tool reopens the gated `manual-hull-pen-tool`; that reopening is the spec's premise and should be confirmed before TODO. The redesign must satisfy a fixed constraint set (Ctrl+Z, X/Z lock, reparent all survive) and has a strong prior in spec 058's Tab-cycles-mode pattern, which itself was copied from this very modal. Lock decisions 1 and 2 together (same state machine), then 3 follows. Size estimate pending decision 1/2 lock; likely L (new interactive gesture + a full chord rewrite + preview rendering).

## Sources

Reopens the gated `manual-hull-pen-tool` ([gated.md](../gated.md) "Mesh authoring"). Builds on pruned spec 029 (mesh-authoring) and the interior pen mode shipped since. The chord-redesign need was deferred repeatedly and recorded as "the automesh-authoring precedent" in spec 058's `_index.md` entry. Spine / Live2D / Moho are the design precedent for click-to-add-point contour authoring.
