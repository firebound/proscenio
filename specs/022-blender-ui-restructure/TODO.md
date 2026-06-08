# Blender addon UI restructure - TODO

See [STUDY.md](STUDY.md) for the problem, the locked decisions D1-D12, and the target 13-panel tree. This is the implementation plan: five phases, each one PR, each gated by the Blender gate set plus an in-editor smoke. Grounded in the current `apps/blender/panels/` code (verified against [`../021-blender-ui-audit/INVENTORY.md`](../021-blender-ui-audit/INVENTORY.md)).

Conventions this plan holds to ([`.ai/conventions/code.md`](../../.ai/conventions/code.md)): one panel module per tool; `panels/__init__.py` orchestrates registration only; panels call operators by `bl_idname` string, never import operator classes; `core/_shared/feature_status` is the single source for badges; new panel files keep `from __future__ import annotations` (panels declare no problematic `bpy.props` ClassVars, so the PEP 563 carve-out does not apply). Use `git mv` for renames so history follows.

## Gate set (every phase)

- [ ] `uvx ruff check apps/blender/`
- [ ] `uvx ruff format --check apps/blender/`
- [ ] `uv run --with mypy mypy --config-file apps/blender/pyproject.toml`
- [ ] `uv run pytest tests/` (repo root)
- [ ] Blender fixture suite (7/7) + operator suite (`blender --background --python apps/blender/tests/run_operator_tests.py`)
- [ ] Whole-addon import sweep
- [ ] In-editor smoke (the phase's panels render + the listed behaviour)

## Phase 1 - flatten the root, reorder, footer

Goal: every tool becomes a sibling top-level panel; the version line stops being everyone's parent.

- [ ] [`panels/__init__.py`](../../apps/blender/panels/__init__.py): repurpose `PROSCENIO_PT_main` as a footer - it keeps the `Pipeline v0.1.0` label and the root `?` (`pipeline_overview`), adds a GitHub link (`wm.url_open`), and is registered LAST. It is no longer a parent.
- [ ] Remove `bl_parent_id = "PROSCENIO_PT_main"` from every panel: `active_element`, `active_slot`, `skeleton`, `skinning`, `outliner`, `animation`, `atlas`, `validation`, `export`, `help`, `diagnostics`. They become top-level in `bl_category="Proscenio"`.
- [ ] Set the default top-level order via registration order in `__init__.py` (Outliner first, footer last); add `bl_order` where the category sort needs pinning.
- [ ] Confirm `DEFAULT_CLOSED` policy per panel is intentional now that they are top-level (Validation + Export currently open; decide their default-open state as siblings).
- Smoke: the Proscenio tab shows sibling panels, none indented under the version; the version + GitHub + `?` sit in a footer at the bottom.

## Phase 2 - renames, isolated selectors, accordion subpanels

Goal: the per-tool internal structure. No operators move yet (Phase 3); weights do not split yet (Phase 4).

Element (was Active Element):

- [ ] `git mv panels/active_element.py panels/element.py`; rename `PROSCENIO_PT_active_element` -> `PROSCENIO_PT_element`, `bl_label = "Element"`. The parent draws the isolated `element_type` selector only.
- [ ] Add child subpanels (parent `PROSCENIO_PT_element`): `PROSCENIO_PT_active_mesh` (poll `element_type == "mesh"`, body from `_draw_mesh.draw_body`), `PROSCENIO_PT_active_sprite` (poll `"sprite"`, body from `_draw_sprite.draw_body`), `PROSCENIO_PT_texture_region` (body `_draw_region.draw_box`), `PROSCENIO_PT_drive_from_bone` (body `_draw_driver_shortcut.draw_box`).
- [ ] Drop the inline weight-paint mirror (`_draw_mesh.draw_weight_paint`) from the Element draw path (it moves conceptually to Weight Paint in Phase 4; the paint-mode warning lands in Phase 5).

Skeleton:

- [ ] [`panels/skeleton.py`](../../apps/blender/panels/skeleton.py): the parent draws the isolated project-wide Active Armature selector. Add child subpanels: `PROSCENIO_PT_armature` (bone list), `PROSCENIO_PT_pose_mode` (Bake Pose / Toggle IK / Save Pose), `PROSCENIO_PT_quick_armature` (defaults box + Quick Armature button).
- [ ] `PROSCENIO_UL_bones.draw_item`: replace the `parent: X` + `len` columns with depth-indented names + the connected / relative-parent flags; drop `length`. (Flat UIList: indent by bone depth in the label; a real tree widget is Bucket C.)

Mesh Generation (was Skinning):

- [ ] `git mv panels/skinning.py panels/mesh_generation.py`; rename `PROSCENIO_PT_skinning` -> `PROSCENIO_PT_mesh_generation`, `bl_label = "Mesh Generation"`. Parent draws the isolated Interior Mode selector + the picker readout.
- [ ] Add child subpanels: `PROSCENIO_PT_automesh_alpha` (the `_draw_automesh_box`, label "Automesh from Alpha"), `PROSCENIO_PT_automesh_interactive` (the `_draw_authoring_box`, label "Automesh Interactive"), `PROSCENIO_PT_debug_pipeline` (the `_draw_debug_box`).
- [ ] Rename the operator `proscenio.automesh_from_sprite` -> `proscenio.automesh_from_alpha`: grep the id repo-wide and update every call site (`operators/automesh/automesh.py` `bl_idname`, `panels/mesh_generation.py`, any `tests/operators/test_automesh*.py`). The "from Sprite" term is wrong - it traces the alpha contour.
- [ ] Bind + weight boxes (`_draw_bind_box`, `_draw_edit_weights_box`, `_draw_weight_transfer_box`, `_draw_snapshot_box`, `_draw_sidecar_io_box`) STAY here this phase; they move in Phase 4.

Pipeline (was Export):

- [ ] `git mv panels/export.py panels/pipeline.py`; rename `PROSCENIO_PT_export` -> `PROSCENIO_PT_pipeline`, `bl_label = "Pipeline"`. Add child subpanels `PROSCENIO_PT_import` (Import Photoshop) and `PROSCENIO_PT_export` (PPU + last path + Export + Re-export). The Validate + Preview Camera buttons stay in the Export subpanel until Phase 3 moves them.

Registration:

- [ ] [`panels/__init__.py`](../../apps/blender/panels/__init__.py): register every new subpanel class after its parent; update the imports (`element`, `mesh_generation`, `pipeline` modules).
- Smoke: each renamed panel renders; the Active Mesh / Active Sprite subpanel swaps by `element_type`; the accordions collapse independently.

## Phase 3 - operator relocations

Goal: every operator lives where its concept lives.

Slots (was Active Slot):

- [ ] `git mv panels/active_slot.py panels/slots.py`; rename `PROSCENIO_PT_active_slot` -> `PROSCENIO_PT_slots`, `bl_label = "Slots"`, poll broadened so it is always visible. The parent draws the project slot list (iterate scene Empties with `is_slot`, each clickable) + the **Create Slot** button.
- [ ] Add `PROSCENIO_PT_active_slot` as a child subpanel (poll EMPTY + `is_slot`) carrying the current attachment detail + Add Selected Mesh.
- [ ] [`panels/skeleton.py`](../../apps/blender/panels/skeleton.py): remove the `proscenio.create_slot` button (it now lives in Slots).
- [ ] [`panels/validation.py`](../../apps/blender/panels/validation.py): add the `proscenio.validate_export` button (the **Validate** button moves here from Pipeline).
- [ ] `panels/pipeline.py`: remove the Validate button.
- [ ] New `panels/helpers.py`: `PROSCENIO_PT_helpers` + the `proscenio.create_ortho_camera` (Preview Camera) button, moved out of Pipeline.
- [ ] Register `helpers` + the new Slots subpanel.
- Smoke: select a mesh and Add Selected Mesh to a slot WITHOUT the Slots panel vanishing (the bug the audit found); Validate runs from the Validation panel.

## Phase 4 - Weight Paint panel

Goal: split weight painting out of Mesh Generation into its own mesh-only panel.

- [ ] New `panels/weight_paint.py`: `PROSCENIO_PT_weight_paint` (poll `element_type == "mesh"`) + child subpanels `PROSCENIO_PT_bind`, `PROSCENIO_PT_edit_weights`, `PROSCENIO_PT_snapshot`, `PROSCENIO_PT_sidecar_io`, `PROSCENIO_PT_weight_transfer`.
- [ ] Move the five weight draws out of `mesh_generation.py` into the new subpanels (`_draw_bind_box`, `_draw_edit_weights_box`, `_draw_snapshot_box`, `_draw_sidecar_io_box`, `_draw_weight_transfer_box`).
- [ ] `mesh_generation.py` keeps only the picker readout, Interior Mode, and the automesh subpanels.
- [ ] Register `weight_paint` (after `mesh_generation`).
- Smoke: Weight Paint full on a mesh element; on a sprite it shows the mesh-only warning (no weight UI).

## Phase 5 - warn-not-hide, header convention, prefs flag, ride-alongs

Goal: nothing hides on the wrong selection; every header is consistent; the debug flag + bugfix land.

Warn-not-hide:

- [ ] Broaden `poll()` on `PROSCENIO_PT_element`, `PROSCENIO_PT_mesh_generation`, `PROSCENIO_PT_weight_paint`, `PROSCENIO_PT_slots` to render in VIEW_3D regardless of selection; each `draw()` shows an inline warning when its context is absent (Element: "select a mesh or sprite"; Weight Paint: mesh-only; etc.).
- [ ] `PROSCENIO_PT_pose_mode` subpanel: always visible under Skeleton, warns outside pose mode.
- [ ] `PROSCENIO_PT_element` in paint-weight mode: show the warning that the element type cannot change there.

Header convention (badge + `?` everywhere):

- [ ] Add `draw_header_preset` -> `draw_subpanel_header(feature_id, help_topic)` to every panel and subpanel that lacks it: `texture_region`, the Mesh Generation subpanels, every Weight Paint subpanel, `slots` subpanel, `helpers`, the Pipeline Import/Export subpanels, `help`, `diagnostics`.
- [ ] [`core/_shared/feature_status.py`](../../apps/blender/core/_shared/feature_status.py): add the correct band for every new/renamed feature id (`element`, `active_mesh`, `active_sprite`, `mesh_generation`, `automesh_alpha`, `automesh_interactive`, `debug_pipeline`, `weight_paint`, `bind`, `edit_weights`, `snapshot`, `sidecar_io`, `weight_transfer`, `pipeline`, `import`, `helpers`, `diagnostics`, `help`); remove the stale `skinning` fallback. Weight bind/transfer = `GODOT_READY` (weights export); the automesh/edit/debug authoring rows = `BLENDER_ONLY`.

Minimal addon preferences:

- [ ] New `apps/blender/addon_prefs.py` (or `properties/addon_prefs.py`): `ProscenioAddonPreferences(bpy.types.AddonPreferences)`, `bl_idname` = the addon package name, a single `debug_mode: BoolProperty` + a `draw` showing it. Follow the `object_props.py` property-declaration pattern.
- [ ] Register the preferences from the addon root [`apps/blender/__init__.py`](../../apps/blender/__init__.py) (alongside `properties.register()`).
- [ ] Debug gating: `PROSCENIO_PT_diagnostics.poll` and `PROSCENIO_PT_debug_pipeline.poll` return `context.preferences.addons[<pkg>].preferences.debug_mode`.

Ride-along bugfix:

- [ ] [`panels/skeleton.py`](../../apps/blender/panels/skeleton.py): the "no Armature in scene" early `return` must not block the Quick Armature subpanel. With Quick Armature now its own subpanel, ensure it renders + its operator runs with zero armatures in the scene (the no-rig bug from [`../backlog-bugs-found.md`](../backlog-bugs-found.md) / the audit).

- Smoke: panels warn instead of vanishing; every panel + subpanel header shows a badge + `?`; toggling `debug_mode` in the addon prefs shows/hides Diagnostics + Debug Pipeline; Quick Armature creates a rig in an empty scene.

## Out of scope (do not creep)

Per STUDY D12 + Non-goals: no help-popup doc links / tooltips / custom Godot icon / i18n isolation (spec 023); no preferences beyond the `debug_mode` flag (spec 024); no bone-collections management or Atlas packing features (Bucket C); no `.proscenio` / schema / writer / importer change.
