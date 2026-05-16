# SPEC 012 - TODO

Quick Armature UX overhaul. See [STUDY.md](STUDY.md) for the full design + decisions D1-D16 (D1-D9 locked at planning time, D10-D15 added with Wave 12.2, D16 emerged mid-iteration). Wave 12.1 + Wave 12.2 + 9 iterative refinement commits shipped together on PR #50. Wave 12.1 closed the "inviabiliza" gap surfaced in [tests/MANUAL_TESTING.md:167-177](../../tests/MANUAL_TESTING.md#L167-L177); Wave 12.2 layered the productivity polish; the refinement log below records each post-Wave-12.2 delta with commit hash + user-feedback rationale.

## Decision lock-in

- [x] D1 - preview rendering = `gpu.draw_handler_add` overlay (no scene mutation during drag).
- [x] D2 - naming prefix = `AddonPreferences.quick_armature_name_prefix` default `"qbone"` + F3 redo `BoneNameProperty` override.
- [x] D3 - Front-Ortho auto-snap restores original `view_perspective` + `view_matrix` on `_finish` and `cancel`.
- [x] D4 - empty-QuickRig sweep on exit only when `self._created_armature_this_session is True`.
- [x] D5 - in-viewport Confirm/Cancel = `POST_PIXEL` header text only ("Esc/RMB exit | Enter confirm"); no floating buttons, no Esc-discard dialog.
- [x] D6 - modifier-list cheatsheet always visible while modal active (no toggle, no fade).
- [x] D7 - per-bone undo = `self._session_bone_names: list[str]` session-local stack; `_finish` wraps cumulative state in single `bpy.ops.ed.undo_push`.
- [x] D8 - `Ctrl+Shift` chord superseded by D14 - see below.
- [x] D9 - shipping = Wave 1 (preview + lifecycle hygiene + Front-Ortho + cheatsheet) then Wave 2 (modifiers + naming + in-modal undo + axis lock + grid snap + panel). Each wave = 1 PR.
- [x] D10 - default no-modifier = chain connected (Blender E extrude convention); `Shift+LMB drag` = new chain root (unparented).
- [x] D11 - `X` / `Z` keys mid-drag = axis lock + colored axis line overlay in POST_VIEW handler.
- [x] D12 - `Ctrl` held mid-drag = snap projected cursor to scene grid (hardcoded 1.0 world unit for first ship).
- [x] D13 - angle snap deferred to future SPEC; chord vocabulary collision with `Shift` is not worth resolving today.
- [x] D14 - `Ctrl` = grid snap (D12); `Alt` re-reserved for future "snap to nearby bone tip" gesture (was D8's reservation).
- [x] D15 - defaults exposed via `bpy.types.Scene.proscenio.quick_armature` PropertyGroup + inline UI in Skeleton subpanel; F3 redo override remains for per-invoke tweaks.

## Wave 12.1 - visual feedback + lifecycle hygiene (Blender)

Branch: `feat/spec-012.1-quick-armature-feedback`. **SHIPPED** via commit `f8813f2` (`feat(blender): rewrite Quick Armature with preview, snap, lifecycle`).

**Goal:** make the operator usable. After this wave a user can author bones interactively without trial-and-error and without leaking orphan rigs.

**Operator option + view snapshot** (D3):

- [x] `lock_to_front_ortho: BoolProperty(default=True)` on `PROSCENIO_OT_quick_armature`. `bl_description` covers the opt-out path.
- [x] `invoke` snapshots `view_perspective` + `view_location` + `view_rotation` + `view_distance` (refined post-ship to decomposed values - matrix had float drift across mode toggles; see refinement log).
- [x] `invoke` snaps to Front-Ortho when `lock_to_front_ortho` is True and current view differs. Detection via `viewport_state.is_front_ortho` (bpy-free helper).
- [x] `_finish` / `cancel` restore decomposed pose; matrix comparison replaced with `_view_pose_equal` so a user-driven orbit is detected and respected.

**GPU preview overlay** (D1):

- [x] `core/bpy_helpers/modal_overlay.py` (bpy-bound) ships `draw_line_3d`, `draw_circle_3d`, `draw_dashed_line_3d`, `draw_text_panel_2d`. Pure vertex math lives in `core/modal_overlay_geometry.py`.
- [x] `quick_armature.py` registers `POST_VIEW` handler; `_draw_preview_3d` renders bone line + anchor circle. Color now varies by chord mode (refinement: orange = connected, cyan = unparented, yellow = disconnected, red = cursor-outside-canvas).
- [x] `MOUSEMOVE` updates `_cursor_world` (with grid-snap + axis-lock post-processing in Wave 12.2) + `area.tag_redraw()`. No timer.
- [x] Anchor circle 12-segments, radius 0.05 world units, line width 2 px.

**Cheatsheet + status overlay** (D5 + D6):

- [x] `draw_text_panel_2d` ships in `modal_overlay.py` with `top-left` / `top-center` / `bottom-center` alignments + optional `origin_override` for cursor-following tooltips. The 2-line POST_PIXEL cheatsheet shipped first, then was retired in favour of the icon-rich STATUSBAR + viewport header pair (see refinement log entry "Icon-rich hints"). Cursor-outside-canvas tooltip stayed (cursor-tracking, not a chord cheatsheet).
- [x] `workspace.status_text_set` hint shipped initially, then dropped when the icon-rich `STATUSBAR_HT_header.prepend` covered the same surface with native Blender event icons.

**Empty-QuickRig sweep on cancel** (D4):

- [x] `_created_armature_this_session: ClassVar[bool]` tracked in `_ensure_armature`.
- [x] `cancel(self, context)` method present; walks same exit path as `_finish`; sweeps the auto-created QuickRig when it ended the session empty. Sweep skips any pre-existing rig the user picked as target (refinement: `arm_obj.name` stored to defeat Blender auto-rename when an orphan data block existed).
- [x] `_finish` ends with the same sweep call.
- [x] `modal` `Esc/RMB` returns `{'CANCELLED'}` only when no bones were authored this session; otherwise `{'FINISHED'}`.

**Handler lifecycle safety**:

- [x] `_unregister_handlers` helper called from every exit path; nulls `_preview_handle_3d`, `_cursor_warning_handle_2d`, plus the `_statusbar_appended` / `_view3d_header_appended` flags added during refinement.
- [x] Addon-level `_sweep_orphan_handlers` in `unregister()` walks every handler we own and detaches it, guarding script-reload leaks.

**Tests** (pytest, bpy-free):

- [x] `tests/test_viewport_state.py` covers Front-Ortho detection.
- [x] `tests/test_modal_overlay_geometry.py` covers circle / rect vertex builders.
- [x] (Lifecycle / view-snapshot Blender-headless tests deferred - bpy-free pure helpers cover the logic; the modal-state ClassVar dance is hard to exercise without booting Blender. Smoke covers it manually.)

**Manual verification** (logged in `tests/MANUAL_TESTING.md` 1.14):

- [x] re-test of session 1.14 checklist - every previously-skipped item PASS.
- [x] Reload-Scripts safety smoke - no double overlay, no orphan handler, no console exception.

**Docs**:

- [x] [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) gained the "Modal overlay pattern" subsection (later expanded with the icon-hint convention during refinement).
- [x] Backlog "Quick Armature: Front-Ortho UX guard" entry marked absorbed by SPEC 012.

## Wave 12.2 - modifiers + naming + in-modal undo (Blender)

Branch: `feat/spec-012.1-quick-armature-feedback` (kept same branch; PR #50 carries Wave 12.1 + 12.2 + refinements). **SHIPPED** across commits `cefd30d`, `265b59b`, `16c7995`.

**Goal:** make the operator pleasant for serial bone authoring. After this wave a user can build a branching skeleton (humanoid with separate spine, arm chains, head) in one modal session without exits.

**Default behavior inversion** (D10):

- [x] `_handle_leftmouse` press-time inverted via `resolve_press_mode` helper. Vocabulary later refined to Blender-aligned `connected` / `unparented` / `disconnected` labels (refinement log).
- [x] `_create_bone` accepts `parent_to_last` + `connect` params; `connect=True` snaps head to parent.tail.
- [x] Cheatsheet copy reflects landed vocabulary (both the deprecated POST_PIXEL text version and the surviving STATUSBAR + viewport header icon versions).
- [x] Manual re-test 1.14: chain-default confirmed.

**Axis lock during drag** (D11):

- [x] `modal` handles `X` / `Z` PRESS (no modifiers) toggling `_axis_lock`. Press same axis twice clears.
- [x] `_handle_leftmouse` RELEASE applies the clamp via `apply_axis_lock` helper before bone creation.
- [x] `_draw_axis_guideline` renders red (X) / blue (Z) line through the drag head when lock is active.
- [x] `tests/test_quick_armature_math.py` exercises `apply_axis_lock` for X / Z / None.

**Grid snap during drag** (D12):

- [x] `_handle_mousemove` + `_handle_leftmouse` apply `snap_world_point_xz(point, increment)` when `_ctrl_held` is True. Read `snap_increment` from the PG.
- [x] Cheatsheet mentions Ctrl = grid snap (status bar + viewport header icon rows).
- [x] `tests/test_quick_armature_math.py` exercises snap rounding for several increments.

**Bone-name prefix preference** (D2 + D15):

- [x] `ProscenioQuickArmatureProps` PG in `scene_props.py` with `lock_to_front_ortho`, `name_prefix`, `default_chain`, `snap_increment`. Pointer wired on `ProscenioSceneProps.quick_armature`.
- [x] `quick_armature.py` reads defaults from the PG at invoke time. (Per-invoke operator-option override was scoped down: only `lock_to_front_ortho` remained as an operator option; other defaults edit through the panel.)
- [x] `_create_bone` uses `format_bone_name(prefix, len(edit_bones))`. `sanitize_prefix` enforces non-empty whitespace-stripped fallback to `qbone`.
- [x] `tests/test_quick_armature_math.py` covers sanitize + format.

**Panel exposure** (D15):

- [x] `panels/skeleton.py` renders the "Quick Armature defaults" sub-box with all 4 PG fields. Always visible (no foldout; the sub-box is short).
- [ ] Help-topic for `quick_armature_defaults` - deferred, not blocking. Panel already self-describes via field tooltips.

**In-modal per-bone undo** (D7):

- [x] `_session_records: ClassVar[list[_BoneRecord]]` records every bone authored (frozen dataclass with name + geometry + parent context). Reset on invoke.
- [x] `_undo_last_bone` enters Edit Mode, removes the named bone, restores selection, pushes the record onto `_redo_records`.
- [x] `_redo_last_bone` re-creates from the saved record; `_create_bone` clears `_redo_records` on a new bone to match standard semantics.
- [x] Modal handles `Ctrl+Z` -> undo, `Ctrl+Shift+Z` -> redo via dedicated event predicates.
- [x] `_finish` wraps the cumulative state in a single `bpy.ops.ed.undo_push(message="Quick Armature: N bones")` so post-modal Ctrl-Z removes the entire session.

**Cheatsheet copy update**:

- [x] Cheatsheet vocabulary regenerated; refinement replaced the 2 / 3-line POST_PIXEL text version with STATUSBAR + viewport header rows that render native Blender event icons (`MOUSE_LMB_DRAG`, `EVENT_SHIFT`, `EVENT_ALT`, `EVENT_CTRL`, `EVENT_X` / `Z`, `EVENT_RETURN`, `EVENT_ESC`).
- [x] `workspace.status_text_set` retired in favour of the icon-rich header (single-hint cleanup; see refinement log).

**Tests** (pytest, bpy-free):

- [x] `tests/test_quick_armature_math.py` covers `resolve_press_mode`, `resolve_press_mode_label`, `snap_world_point_xz`, `apply_axis_lock`, `sanitize_prefix`, `format_bone_name`. 27 cases, all green.
- [x] `tests/test_skeleton_target.py` covers the active-armature resolver added in refinement (7 cases).
- [ ] Headless undo / axis-lock interaction tests not split out - the helper-level math is covered; the ClassVar dance is hard to test without booting Blender, manual smoke covers it.

**Docs**:

- [x] `bl_description` covers `lock_to_front_ortho`. The richer modifier set is documented in the always-visible cheatsheet headers + the panel sub-box.
- [x] [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) gained both the modal-overlay pattern (Wave 12.1) and the modal-hint placement convention (refinement).

**Codebase audit (drive-by from Wave 12.1 PEP 563 bug) - CONCLUDED**:

Audit ran headless via `--background --python` querying every Operator class for declared bpy.props vs RNA-registered props. Initial false-positive showed all operators "missing" their props because `bl_rna.properties.keys()` does not expose operator-declared props (they live in a separate namespace; runtime `self.<prop>` works regardless).

Refined diagnosis (see [`tests/BUGS_FOUND.md`](../../tests/BUGS_FOUND.md)): bug is a triple-condition combo (`from __future__ import annotations` + `ClassVar[X | None]` + `X` only imported under `if TYPE_CHECKING:`). Only `quick_armature.py` triggered it; every other operator in the addon uses ClassVar with builtin types only and is immune.

- [x] Audit complete - no further operator changes required.
- [x] BUGS_FOUND.md entry rewritten with the refined root cause and a clear "what to avoid" rule.
- [ ] Future polish: add the rule to `.ai/conventions.md` Static typing section + `.ai/skills/blender-dev.md` (deferred, low priority - bug rare enough).

## Refinement log (post-Wave-12.2 iterative feedback)

PR #50 carried Wave 12.1 + 12.2 on the same branch, then absorbed 8 refinement commits driven by manual-smoke feedback rounds. Each is a deliberate delta vs the STUDY-locked design, so they are listed here so a future reader can see what the operator actually does today vs what the original D1-D15 decisions said.

| Commit | Change | Why |
| --- | --- | --- |
| `16c7995` | Chord vocabulary aligned to Blender (`connected` / `unparented` / `disconnected`). Alt+drag added = parented-disconnected. Preview anchor in connected mode moved to `parent.tail` (matches the snapped head). Color-coded preview per chord (orange / cyan / yellow). Active-object armature wins as target when picker is empty. | "new root" was misleading wording; the user wanted Blender-native terms. Connected preview lied by drawing from press point. Alt covers branching skeletons without forcing Edit Mode. |
| `254d03f` | Alt-disconnected dashed preview line from `parent.tail` to head. Native Blender event icons in the STATUSBAR header. `scene.proscenio.active_armature` PointerProperty + auto-populate handler (load_post + deferred_hydrate) + Skeleton subpanel picker. | Visual clarity for the parent relationship in disconnected mode. Icons match Blender's modal hint convention. Explicit target avoids "what rig is this editing?" surprise in multi-armature scenes. |
| `69aff3d` | Three overlapping hints (POST_PIXEL + plain status_text + icon header) collapsed to two icon-rich surfaces (STATUSBAR prepend + VIEW3D header append) sharing one chord-layout helper. Skeleton picker auto-fills via the load_post handler when a single armature is in the scene. | User feedback: redundant text hints clutter. Single source of truth via shared layout helper. Picker visibly reflects what skeleton ops target. |
| `43b4d36` | Removed the draw-time picker auto-fill that crashed (`AttributeError: Writing to ID classes in this context is not allowed`). Logged the "Modal operator hint placement" convention in `.ai/skills/blender-dev.md`. | Panel.draw cannot mutate ID props. The convention captures the SPEC 012 modal-hint pattern for the next modal operator (Quick Mesh, etc) to reuse. |
| `a4f0eec` | `resolve_skeleton_target` simplified: picker pointer is the only source of truth at operator time. Heuristics (active object, single-armature scene) live only in `auto_populate_active_armature`. New `proscenio.set_active_armature` operator + "Use existing instead" button row. Empty-picker warning recoloured from red to INFO box. | Clearing the picker via "x" must mean "create new QuickRig" - the heuristic-resurrection behaviour lied to the user. Button avoids hunting through dropdown when the user wants the only rig. |
| `7d5a099` | "Use existing instead" buttons stacked vertically (column) so long armature names stay readable. `on_depsgraph_update` handler clears the picker when the targeted armature is deleted / unlinked and tags VIEW_3D areas for redraw. | Horizontal buttons truncated names once two rigs were in scene. Stale picker after delete was a sync gap. |
| `9eb5a52` | `_target_armature_name` stores `arm_obj.name` (Blender's post-dedup name) instead of the literal `_QUICK_RIG_NAME`. | When an orphan `Proscenio.QuickRig` data block existed, Blender renamed the new one to `.001`; the literal lookup silently dropped every drag while the bone count reflected the orphan. |
| `ff12680` | `on_depsgraph_update` wrapped in `try / except Exception` with `ReferenceError` handling on the validity check. | Depsgraph callbacks fire inside Blender's draw loop; a Python exception bubble can leave the C side mid-state and turn into a follow-up draw crash. Defensive layer; also paired with the gizmo-crash post-mortem in BUGS_FOUND.md. |
| `c1ef7d7` | Replaced every PT-BR word I had added without accents (`atraves`, `icones`, `mutacao`, ...) with the correctly-accented form across the docs + cspell dictionary. | Project convention is hard PT-BR orthography. Logged as a persistent rule in agent memory. |

Plus the post-merge docs / status passes:

| Commit | Change |
| --- | --- |
| `c05abba` | SPEC 012 STUDY + TODO planning artifacts. |
| `03c3606` | `.ai/skills/blender-dev.md` Modal overlay pattern subsection. |
| `25a5590` | First MANUAL_TESTING smoke log (post-Wave-12.1). |
| `3189f61` | PEP 563 root cause refined in BUGS_FOUND.md. |
| `cefd30d` | PG + panel sub-box (D15). |
| `265b59b` | Wave 12.2 operator changes (D10 invert + D11 axis lock + D12 grid snap + D7 undo + D2 prefix). |
| `f8813f2` | Wave 12.1 operator rewrite (preview + lifecycle + Front-Ortho snap + cheatsheet). |
| `88b9b8d` | Conventions PEP 563 rule + MANUAL_TESTING Wave 12.2 status block. |

## Out of scope (deferred to 012.3 or backlog)

Per [STUDY out-of-scope](STUDY.md#out-of-scope-deferred-to-0121-or-backlog), still deferred after refinement:

- Auto-attach underlying mesh / sprite (couples to SPEC 004).
- Pick-parent-in-viewport modifier (Shift-click an existing bone tip during modal).
- Numeric length input (`Tab` 0.5 Enter).
- Mirror auto-suffix `_L`/`_R` with X-Mirror.
- Discard-confirm dialog on Esc when `>=N` bones created.
- Bone naming patterns with auto-numbering inside a chain (`spine_01`, `spine_02`).

Landed during refinement (originally listed as deferred):

- Per-modifier color-coded preview line. Shipped in `16c7995`.
- Selected-set restore on `_finish`. Shipped in `f8813f2` (full selection + active object snapshot / restore).

Permanently rejected:

- Floating Confirm/Cancel buttons in the viewport (header text + cursor warning tooltip cover the same UX without modal hit-testing complexity).

## Successor SPECs

- A future SPEC pairing Wave 12.x with SPEC 004's slot machinery would ship the DragonBones-style auto-attach gesture (`Ctrl+Shift+drag` over a sprite = bone + slot bind in one stroke). Captured in STUDY successor section.
- A "Quick Mesh" operator (COA-Tools-style click-stroke vertex contour drawing) would lift the Wave 12.1 modal-overlay scaffolding wholesale. If/when it lands, refactor `core/bpy_helpers/modal_overlay.py` from SPEC 012 helpers into a `ModalOverlay` class managing handle lifecycle.
