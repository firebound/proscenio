# SPEC 005 — TODO

Builds the authoring panel that turns the Blender side of Proscenio from "raw Custom Properties on Objects" into a typed, validating, iteration-friendly UI. See [STUDY.md](STUDY.md) for the design rationale and the eight open questions (D1–D8).

## Decision lock-in

- [ ] Confirm D1 — panel lives in the 3D View N-key sidebar (extends `PROSCENIO_PT_main`).
- [ ] Confirm D2 — `PropertyGroup` wraps existing Custom Properties round-trip; no migration, no breakage.
- [ ] Confirm D3 — inline validation for cheap checks, lazy validation for I/O-bound ones.
- [ ] Confirm D4 — two severity levels: error (blocks export) and warning (informs).
- [ ] Confirm D5 — sticky export path stored per-document on `bpy.types.Scene`.
- [ ] Confirm D6 — Validate button reports through a dedicated panel section, not a toast.
- [ ] Confirm D7 — no stub Slots subpanel; SPEC 004 ships its own.
- [ ] Confirm D8 — vertex-group summary inspector lands in 005; atlas region + ortho helpers defer to 005.1.

## Property infrastructure

- [ ] Add `blender-addon/properties/__init__.py` with two `PropertyGroup` subclasses:
  - `ProscenioObjectProps` — `sprite_type` (`EnumProperty`: `polygon` / `sprite_frame`), `hframes` / `vframes` / `frame` (`IntProperty` with sane min/default), `centered` (`BoolProperty`). Each has an `update` callback that writes the same Custom Property the writer reads (`proscenio_type`, etc.) so the contract stays unchanged.
  - `ProscenioSceneProps` — `last_export_path` (`StringProperty(subtype="FILE_PATH")`), `pixels_per_unit` (`FloatProperty(default=100.0, min=0.0001)`).
- [ ] Register property groups via `bpy.types.Object.proscenio = PointerProperty(type=ProscenioObjectProps)` and `bpy.types.Scene.proscenio = PointerProperty(type=ProscenioSceneProps)`.
- [ ] On `register()`, hydrate the PropertyGroup from existing Custom Properties so `.blend` files authored before SPEC 005 show their values in the new UI without manual re-entry.
- [ ] On `unregister()`, clean up: remove `bpy.types.Object.proscenio` and `bpy.types.Scene.proscenio`. Verify no leak between addon reloads.

## Panel restructure

- [ ] Refactor [`blender-addon/panels/__init__.py`](../../blender-addon/panels/__init__.py): keep `PROSCENIO_PT_main` as the parent panel header (project banner + version) and split current contents into child panels.
- [ ] Add `PROSCENIO_PT_active_sprite` — child panel, only `poll()`-true when the active object is a mesh. Renders the sprite-type dropdown plus the conditional `sprite_frame` widgets and the polygon vertex-group summary.
- [ ] Add `PROSCENIO_PT_skeleton` — child panel, summary section: bone count, warning when scene has no armature.
- [ ] Add `PROSCENIO_PT_export` — child panel, sticky path field, pixels-per-unit field, Validate button, Export button.
- [ ] Add `PROSCENIO_PT_diagnostics` — keep existing smoke test button under here; can grow to host the validation results section.

## Validation

- [ ] Add `blender-addon/core/validation.py` with two entry points:
  - `validate_active_sprite(obj) -> list[Issue]` — cheap structural checks (sprite_frame missing hframes, etc.) for inline feedback.
  - `validate_export(scene) -> list[Issue]` — full lazy pass: armature presence, every sprite resolves a bone, every vertex group resolves to a bone, atlas file exists on disk.
- [ ] Define `Issue` as a `dataclass` with `severity: Literal["error", "warning"]`, `message: str`, optional `obj_name: str` for "select offending object" UX later.
- [ ] In each panel's `draw()`, call the cheap validator, render `row.label(text=..., icon="ERROR")` or `icon="INFO"` per issue.
- [ ] Add `PROSCENIO_OT_validate_export` operator wired to the Validate button. Stores the issue list on `bpy.types.Scene.proscenio_validation_results` (transient PropertyGroup or scene-level dict). The export panel renders that list when present.

## Export flow

- [ ] Modify `PROSCENIO_OT_export_godot` to:
  - Run `validate_export(scene)`. If any errors, abort with a clear `self.report({"ERROR"}, ...)` and surface the issue list on the panel.
  - On success, write to `scene.proscenio.last_export_path` if non-empty; otherwise fall back to `ExportHelper`'s file dialog.
  - Update `scene.proscenio.last_export_path` after a successful export so the next click is one-shot.
- [ ] Add a "Re-export" button in the export panel that runs the operator with the sticky path silently. Visible only when `last_export_path` is non-empty.

## Tests

- [ ] Add `blender-addon/tests/test_properties.py` (run-as-Blender-script, like `run_tests.py`):
  - Loads a `.blend` with a mesh that has raw `proscenio_type = "sprite_frame"` Custom Property; asserts that after `register()`, the PropertyGroup field reports `"sprite_frame"`.
  - Sets the PropertyGroup field to `"polygon"`; asserts the Custom Property follows.
- [ ] Extend `run_tests.py` to also schedule the new test (or document a separate runner script).
- [ ] Add a unit-style test for `core/validation.py` that does not need Blender — the validator surface accepts a typed dict, lets pytest exercise it standalone.

## Documentation

- [ ] Major rewrite of `.ai/skills/blender-addon-dev.md`:
  - "Project layout" section gains `panels/`, `properties/`, `core/validation.py`.
  - "Painting weights for skinning" stays; new section "Authoring sprites in the panel" walks the user through dropdown → fields → export.
  - The legacy "raw Custom Properties" path is documented as still valid for power users (D2 contract).
- [ ] Update `STATUS.md` when SPEC 005 closes — moves to shipped, mentions which subpanels exist, links a screenshot.
- [ ] Add a one-paragraph "Authoring UX" entry in `README.md`'s iteration loop step (the rough authoring flow as a list).

## Manual validation

- [ ] Reload addon. Open `examples/dummy/dummy.blend`. The Active sprite panel should show the head's sprite type as `sprite_frame` (read from existing Custom Property) and the legs/torso as `polygon`.
- [ ] Toggle the head dropdown back to `polygon`; verify the writer's output stops including the sprite-frame metadata for the head.
- [ ] Set the sticky export path to `examples/dummy/dummy.proscenio`; click Re-export; verify the file updates without a file dialog.
- [ ] Click Validate with a deliberately broken state (sprite_frame mesh with hframes = 0). Expected: panel surfaces the issue, Export button reports an error.
- [ ] Open a `.blend` from before SPEC 005; verify the panel reads existing Custom Properties without breaking, and edits round-trip cleanly.

## Defer (potential SPEC 005.1 if demand emerges)

- Atlas region helper (D8 — "Snap UV bounds → texture_region").
- Camera ortho preview helper (matches `pixels_per_unit`).
- Vertex weight visualization overlay (color by dominant bone).
- Drag-and-drop reordering of subpanels or attachment lists.
- Per-user default export-path preference.
- Localization scaffolding (`i18n_id` discipline).
- Properties Editor placement of the Active sprite section (D1.B).
- A "Reset to defaults" button per subpanel.
