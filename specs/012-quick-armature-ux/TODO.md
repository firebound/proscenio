# SPEC 012 - TODO

Quick Armature UX overhaul. See [STUDY.md](STUDY.md) for the full design + decisions D1-D9. Two waves, one PR each. Wave 1 closes the "inviabiliza" gap surfaced in [tests/MANUAL_TESTING.md:167-177](../../tests/MANUAL_TESTING.md#L167-L177); Wave 2 is productivity polish.

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

Branch: `feat/spec-012.1-quick-armature-feedback`. **Pending.**

**Goal:** make the operator usable. After this wave a user can author bones interactively without trial-and-error and without leaking orphan rigs.

**Operator option + view snapshot** (D3):

- [ ] [`apps/blender/operators/quick_armature.py`](../../apps/blender/operators/quick_armature.py): add `lock_to_front_ortho: BoolProperty(default=True)` to `PROSCENIO_OT_quick_armature`. Description in `bl_description` covers the opt-out path.
- [ ] `invoke`: snapshot `region_3d.view_perspective` + `region_3d.view_matrix.copy()` into `self._restore_view_perspective` + `self._restore_view_matrix` before any view mutation.
- [ ] `invoke`: when `lock_to_front_ortho is True` and the snapshot is not Front-Ortho, call `bpy.ops.view3d.view_axis(type="FRONT")`. Detect Front-Ortho via `view_perspective == 'ORTHO' and (view_matrix.to_3x3() - Matrix.Identity(3)).length < 1e-4`.
- [ ] `_finish` and `cancel`: restore the snapshot (`region_3d.view_perspective = ...`; `region_3d.view_matrix = ...`; `region_3d.update()`).

**GPU preview overlay** (D1):

- [ ] New module `apps/blender/core/bpy_helpers/modal_overlay.py` (bpy-bound). Helpers: `draw_line_3d(start, end, color, width)`, `draw_circle_3d(center, radius, segments, color)`. Use `gpu.shader.from_builtin('UNIFORM_COLOR')` + `batch_for_shader`.
- [ ] `quick_armature.py`: register `POST_VIEW` draw handler in `invoke`, store handle on `self._preview_handle_3d`. Callback reads `self._drag_head` (anchor) + `self._cursor_world_y0` (current cursor projected on Y=0) and draws line + 12-segment circle when `self._drag_head is not None`.
- [ ] `modal`: on `MOUSEMOVE`, update `self._cursor_world_y0` via `mouse_event_to_plane_point(context, event, plane_axis="Y")` and `context.area.tag_redraw()`. Cap redraws to mouse-event rate; no timer.
- [ ] Color: `(1.0, 0.6, 0.0, 0.9)` (Blender modal-in-progress orange). Line width: 2 px. Anchor circle radius: 0.05 world units (visible across typical 2D-cutout zoom ranges).

**Cheatsheet + status overlay** (D5 + D6):

- [ ] `modal_overlay.py`: helper `draw_text_panel_2d(lines: list[str], origin: tuple[int, int], padding: int, bg_color, text_color)`. Uses `blf.size`, `blf.position`, `blf.draw` for text; uses the shared `UNIFORM_COLOR` shader for the background rect.
- [ ] `quick_armature.py`: register `POST_PIXEL` draw handler in `invoke`, store on `self._cheatsheet_handle_2d`. Callback renders fixed-position cheatsheet at top-left of the region (origin = `(16, region.height - 16)`):
  - Line 1: `Quick Armature  -  drag = bone  |  Shift = chain  |  Esc/RMB exit  |  Enter confirm`
  - Wave 1 ships only the modifiers it owns. Wave 2 expands the cheatsheet copy.
- [ ] Background: `(0.0, 0.0, 0.0, 0.55)` rounded rect (or plain rect for Wave 1; rounding deferred). Text: `(1.0, 1.0, 1.0, 1.0)` 12 px.
- [ ] Existing `workspace.status_text_set` hint stays as the short canonical form ([quick_armature.py:50-53](../../apps/blender/operators/quick_armature.py#L50-L53)).

**Empty-QuickRig sweep on cancel** (D4):

- [ ] `quick_armature.py`: track `self._created_armature_this_session: bool` set in `_ensure_armature` (`True` when the armature is freshly created, `False` when the operator found an existing `Proscenio.QuickRig`).
- [ ] Add a `cancel(self, context)` method (currently absent). Walks the same exit path as `_finish` (handler unregister, status clear, view restore) plus: when `self._created_armature_this_session` and the armature has zero bones, call `bpy.data.armatures.remove(armature.data, do_unlink=True)`.
- [ ] `_finish`: same sweep at the end. Sweep target = the `Proscenio.QuickRig` armature looked up by name; bail silently if it was already removed.
- [ ] Returning `{'CANCELLED'}` from `modal` on Esc/RMB calls `cancel`; ensure no path returns `{'FINISHED'}` after a zero-bone Esc.

**Handler lifecycle safety**:

- [ ] Single `_unregister_handlers(self)` helper called from `_finish`, `cancel`, and any error return. Sets `self._preview_handle_3d = None` + `self._cheatsheet_handle_2d = None` after `gpu.draw_handler_remove` / `bpy.types.SpaceView3D.draw_handler_remove`.
- [ ] `unregister()` at addon level walks any leftover `SpaceView3D` draw handlers tagged with the operator's class id and removes them (guards reload-scripts path that drops the operator without firing `_finish`).

**Tests** (Blender-headless via `apps/blender/tests/run_tests.py`):

- [ ] `apps/blender/tests/test_quick_armature_lifecycle.py`: invoke + immediate cancel = no orphan armature when no pre-existing QuickRig; pre-existing QuickRig with bones survives a zero-bone session.
- [ ] `apps/blender/tests/test_quick_armature_view_snapshot.py`: starting view = Persp; `lock_to_front_ortho=True`; after `_finish` view returns to Persp.
- [ ] `apps/blender/tests/test_modal_overlay_helpers.py`: pure-Python tests of geometry-builder helpers (line vertices, circle vertex math) without booting Blender. The bpy-bound `gpu` calls are skipped under headless.

**Manual verification** (logged in `tests/MANUAL_TESTING.md` 1.14):

- [ ] [x] re-test of session 1.14 checklist with the operator now usable; previously skipped items expected to land green.
- [ ] [x] verify draw handlers do not survive Reload Scripts (smoke check: invoke, Reload, attempt invoke again - no double-overlay, no console exception).

**Docs**:

- [ ] [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md): add a "Modal overlay pattern" subsection pointing to `core/bpy_helpers/modal_overlay.py` and the SPEC 012 lifecycle pattern.
- [ ] Backlog: remove ["Quick Armature: Front-Ortho UX guard"](../backlog.md#quick-armature-front-ortho-ux-guard) since SPEC 012.1 ships it.

## Wave 12.2 - modifiers + naming + in-modal undo (Blender)

Branch: `feat/spec-012.2-quick-armature-productivity`. **Blocked on Wave 12.1.**

**Goal:** make the operator pleasant for serial bone authoring. After this wave a user can build a branching skeleton (humanoid with separate spine, arm chains, head) in one modal session without exits.

**Default behavior inversion** (D10):

- [ ] `quick_armature.py` `_handle_leftmouse`: invert the press-time interpretation. No-modifier press -> `parent_to_last=True` + `connect=True`. `Shift` press -> `parent_to_last=False` (new root). First bone of a session always lands unparented (no previous bone exists).
- [ ] `_create_bone`: collapse `parent_to_last` + new `connect` parameter; when `connect=True` and a parent exists, force `new_bone.head = parent.tail` before assigning the user's drag head to `new_bone.tail`. Set `new_bone.use_connect = True`.
- [ ] Cheatsheet copy update reflects the inverted default (covered in the cheatsheet bullet below).
- [ ] Manual re-test of session 1.14 with chain-default - confirms the most common case (continue the chain) is now zero-modifier.

**Axis lock during drag** (D11):

- [ ] `quick_armature.py` `modal`: handle `event.type in {"X", "Z"}` with `event.value == "PRESS"`. Toggle `self._axis_lock: Literal["X", "Z"] | None`. Pressing the same axis twice clears the lock (toggle off). Pressing the other axis switches lock.
- [ ] `_handle_leftmouse` RELEASE path: when `self._axis_lock == "X"`, clamp `tail.z = head.z` (preserve head's Z, allow X to follow cursor). When `"Z"`, clamp `tail.x = head.x`.
- [ ] `core/bpy_helpers/modal_overlay.py`: add `draw_axis_line_3d(head, axis_axis, plane_axis, length, color)` helper. Color: `(1.0, 0.3, 0.3, 0.9)` for X (Blender red); `(0.3, 0.55, 1.0, 0.9)` for Z (Blender blue). Length: 1000 world units (effectively infinite within the picture plane).
- [ ] `_draw_preview_3d`: when `cls._axis_lock` is set, draw the axis line through the head before drawing the bone preview line. The preview line itself reflects the clamped tail position.
- [ ] Tests: `tests/test_quick_armature_axis_lock.py` (bpy-free): exercise the clamp math via `core/viewport_state.py` helper `clamp_to_axis(head, tail, axis)`.

**Grid snap during drag** (D12):

- [ ] `quick_armature.py` `modal` MOUSEMOVE branch: read `event.ctrl` and `context.scene.proscenio.quick_armature.snap_increment`. When `event.ctrl is True`, round `_cursor_world` X and Z to the nearest `snap_increment` multiple before storing.
- [ ] Update the cheatsheet to mention `Ctrl = snap to grid`.
- [ ] Tests: `tests/test_quick_armature_grid_snap.py` (bpy-free): exercise `snap_to_grid(point, increment)` helper in `core/modal_overlay_geometry.py` (or a new `core/snap_math.py` if it grows).

**Bone-name prefix preference** (D2 + D15):

- [ ] [`apps/blender/properties/scene_props.py`](../../apps/blender/properties/scene_props.py): add nested `ProscenioQuickArmatureProps(PropertyGroup)` with fields `lock_to_front_ortho: BoolProperty(default=True)`, `name_prefix: StringProperty(default="qbone")`, `default_chain: BoolProperty(default=True)`, `snap_increment: FloatProperty(default=1.0, min=0.001)`. Pointer on `ProscenioSceneProps.quick_armature`.
- [ ] `quick_armature.py`: add the matching operator options as sentinel-overrideable values. Operator's `invoke` reads from `context.scene.proscenio.quick_armature.<field>` when its own option is at the sentinel value; explicit F3 redo override beats the scene default.
- [ ] `_create_bone`: name = `f"{prefix}.{len(edit_bones):03d}"` (was `f"qbone.{...}"`). Sanitize prefix: strip whitespace, fall back to `"qbone"` if empty.
- [ ] Test: `apps/blender/tests/test_quick_armature_naming.py` covers default prefix, scene-PG override, F3 option override, sanitize fallback.

**Panel exposure** (D15):

- [ ] [`apps/blender/panels/skeleton.py`](../../apps/blender/panels/skeleton.py): add a "Quick Armature defaults" sub-box under the `Quick Armature` button. Rows: lock-to-front-ortho checkbox, name-prefix string, default-chain checkbox, snap-increment float. Each row binds to `scene.proscenio.quick_armature.<field>`.
- [ ] Same panel: collapse the sub-box by default via a child `bool` toggle on the Skeleton subpanel state (or a labeled foldout) - keep the panel quiet until user wants to tweak.
- [ ] Help-topic entry in `core/help_topics.py` for the new defaults sub-box (`quick_armature_defaults`).

**In-modal per-bone undo** (D7):

- [ ] `quick_armature.py`: add `self._session_bone_names: list[str] = []`. `_create_bone` appends the new bone's name; sets state in `invoke`.
- [ ] New `_undo_last_bone(self, context)` method: pops `_session_bone_names`, enters Edit Mode on the QuickRig, removes the named bone via `armature.edit_bones.remove(armature.edit_bones[name])`, restores prior selection (mirrors `_create_bone`'s save/restore dance).
- [ ] New `_redo_last_bone(self, context)` method: requires a `self._redo_stack: list[tuple[str, tuple, tuple, bool, bool]]` (name, head, tail, parent_to_last, connect) populated by `_undo_last_bone` on each pop; `_redo_last_bone` re-creates the bone with the saved geometry.
- [ ] `modal`: handle `event.type == 'Z'` with `event.ctrl` (without Shift) -> `_undo_last_bone`; with `event.ctrl and event.shift` -> `_redo_last_bone`. Both swallow the event (`return {'RUNNING_MODAL'}`).
- [ ] Any new bone created via `_create_bone` clears the redo stack (matches standard undo/redo semantics).
- [ ] **No** intermediate `bpy.ops.ed.undo_push` calls inside the modal. `_finish` issues a single `bpy.ops.ed.undo_push(message=f"Quick Armature: {len(self._session_bone_names)} bones")` so post-modal Ctrl-Z removes the entire session.

**Cheatsheet copy update**:

- [ ] Cheatsheet line regenerated to cover Wave 12.2 modifiers:
  - Line 1: `Quick Armature`
  - Line 2: `drag = chain  |  Shift+drag = new root  |  X / Z = axis lock  |  Ctrl = grid snap`
  - Line 3: `Ctrl+Z = undo  |  Ctrl+Shift+Z = redo  |  Enter = confirm  |  Esc/RMB = exit`
- [ ] Status bar text in `workspace.status_text_set` updated to a shorter mirror of the cheatsheet.

**Tests**:

- [ ] `tests/test_quick_armature_modifiers.py` (bpy-free helper coverage): exercise `resolve_press_mode(shift_held, is_first_bone)` -> `("chain_connected" | "new_root")` decision tree (D10 inversion logic).
- [ ] `tests/test_quick_armature_undo.py` (bpy-free): after creating 3 bones + 2x undo, 1 bone remains; 1x redo restores 2; new PRESS clears the redo stack. Mock the bone list via SimpleNamespace.
- [ ] `tests/test_quick_armature_axis_lock.py` (bpy-free): `clamp_to_axis(head, tail, axis)` produces expected coords for X and Z locks; toggle semantics (press X twice clears) verified.
- [ ] `tests/test_quick_armature_grid_snap.py` (bpy-free): `snap_to_grid(point, increment)` rounds X and Z to nearest multiple; increment=0 raises; passes through Y unchanged.
- [ ] `tests/test_quick_armature_naming.py` (bpy-free): prefix sanitize (whitespace strip, empty -> default), formatted name pattern, length-aware suffix.

**Docs**:

- [ ] Update `bl_description` to enumerate every modifier shipped through Wave 12.2.
- [ ] Update [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) with the "session-local undo stack" pattern (D7 implementation note from STUDY).

**Codebase audit (drive-by from Wave 12.1 PEP 563 bug)**:

See [`tests/BUGS_FOUND.md`](../../tests/BUGS_FOUND.md) "bpy.props annotations em Operator nao registram com `from __future__ import annotations`". SPEC 012.1 removed `from __future__ import annotations` from `quick_armature.py` to make `lock_to_front_ortho` register. Wave 12.2 needs `name_prefix: StringProperty(...)` on the same operator -> already covered. But every other file with bpy.props annotations + PEP 563 is a latent landmine.

- [ ] Grep `: \w+Property\(` across `apps/blender/operators/`, `apps/blender/properties/`, `apps/blender/panels/`. List every class that declares a bpy.props annotation.
- [ ] For each class, check whether any `self.<prop>` access exists in the same module (or `op.<prop>` / `prop_group.<prop>` from callers).
- [ ] For classes that access via `self.<prop>`: remove `from __future__ import annotations` from the file. Adjust forward references (use string quotes) and import any runtime-needed types (`Matrix`, etc.) at module top.
- [ ] For classes that never access via `self.<prop>`: either remove the dead annotation or document why it stays (e.g. ExportHelper-injected `filter_glob`).
- [ ] Update [`.ai/conventions.md`](../../.ai/conventions.md) "Static typing" section with a callout: Blender-registered classes (`Operator`, `PropertyGroup`, `Panel`) that declare bpy.props cannot use `from __future__ import annotations`. Pure `core/` modules can keep PEP 563.
- [ ] Update [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) Coding rules with the same callout.

## Out of scope (deferred to 012.3 or backlog)

Per [STUDY out-of-scope](STUDY.md#out-of-scope-deferred-to-0121-or-backlog):

- Auto-attach underlying mesh / sprite (couples to SPEC 004).
- Pick-parent-in-viewport modifier (Shift-click an existing bone tip during modal).
- Numeric length input (`Tab` 0.5 Enter).
- Mirror auto-suffix `_L`/`_R` with X-Mirror.
- Floating Confirm/Cancel buttons (vs Wave 12.1's header text only).
- Per-modifier color-coded preview line.
- Discard-confirm dialog on Esc when `>=N` bones created.
- Bone naming patterns with auto-numbering inside a chain (`spine_01`, `spine_02`).
- Selected-set restore on `_finish` (operator currently restores active object only).

## Successor SPECs

- A future SPEC pairing Wave 12.x with SPEC 004's slot machinery would ship the DragonBones-style auto-attach gesture (`Ctrl+Shift+drag` over a sprite = bone + slot bind in one stroke). Captured in STUDY successor section.
- A "Quick Mesh" operator (COA-Tools-style click-stroke vertex contour drawing) would lift the Wave 12.1 modal-overlay scaffolding wholesale. If/when it lands, refactor `core/bpy_helpers/modal_overlay.py` from SPEC 012 helpers into a `ModalOverlay` class managing handle lifecycle.
