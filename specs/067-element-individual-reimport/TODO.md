# Spec 067 TODO: Element individual reimport

Drives the implementation of the locked [STUDY](STUDY.md). All three decisions resolved (A): name-keyed Element->entry resolution via the stamped origin, the 055 contract per entry with no whole-figure re-anchor, and a per-object remembered manifest path. TDD: each behavior gets a headless test under `apps/blender/tests/operators/` before its implementation.

## 1. Remember the source manifest path per object

- [ ] Add `PROSCENIO_IMPORT_MANIFEST = "proscenio_import_manifest"` to [`core/_shared/cp_keys.py`](../../apps/blender/core/_shared/cp_keys.py), in the "Photoshop import tags" block, documented as the absolute source manifest path stamped per imported object so a per-Element reimport finds its origin file.
- [ ] In [`importers/photoshop/__init__.py`](../../apps/blender/importers/photoshop/__init__.py) `import_manifest`, stamp `obj[PROSCENIO_IMPORT_MANIFEST] = str(manifest.source_path)` on every stamped mesh / sprite object (alongside the existing per-object tags). `manifest.source_path` already exists (used by `planes.stamp_sprite`).

## 2. Factor the per-entry dispatch out of the manifest loop

- [ ] Extract the mesh/sprite branch of the `for layer in manifest.layers` loop into a private `_stamp_layer(layer, manifest, armature_obj, result)` that stamps one entry and appends to the `ImportResult` (meshes / spritesheets / skipped). Behavior-preserving for `import_manifest`.

## 3. `reimport_element` (single-entry path)

- [ ] Add `SingleReimportResult` dataclass (`status: Literal["restamped", "skipped", "missing"]`, `obj`, `layer_name`, `warning`).
- [ ] Add `reimport_element(obj, manifest_path) -> SingleReimportResult` to `importers/photoshop/__init__.py`:
  - Load the manifest (`psd_manifest.load`).
  - Resolve the layer via `_layer_for_object(obj, manifest)`: read `PROSCENIO_IMPORT_ORIGIN`, strip `psd:`, look up `layer_by_name`; fall back to `obj.name`. `None` -> `status="missing"` warn-and-no-op.
  - Reuse the existing armature with `build_root_armature(name=_armature_name(manifest))` (it reuses by name; no fresh rig).
  - Dispatch the one layer through `_stamp_layer`. A returned mesh -> `status="restamped"`; a skip (missing PNG) -> `status="skipped"` with a warning.
  - Do NOT call `_anchor_meshes_at_feet` (whole-figure shift; would move the Element off its siblings).

## 4. Operator

- [ ] Add `PROSCENIO_OT_reimport_element` (new file `operators/reimport_element.py` or fold into `import_photoshop.py`), `bl_options {"REGISTER", "UNDO"}`, mixing `ImportHelper` for the picker fallback.
  - `poll`: active object is a MESH carrying `proscenio_type` (an actual element).
  - `invoke`: read `obj[PROSCENIO_IMPORT_MANIFEST]`; if present and the file exists, set `self.filepath` and call `execute` directly (silent, one click); else open the file browser (ImportHelper `invoke`).
  - `execute`: `reimport_element(obj, Path(self.filepath))`, then `report_*` per status (restamped / skipped-missing-PNG / missing-layer); guard the call in try/except like `import_photoshop` so a failure reports instead of crashing the UI.
- [ ] Register it in [`operators/__init__.py`](../../apps/blender/operators/__init__.py).

## 5. Panel button

- [ ] In [`panels/element.py`](../../apps/blender/panels/element.py) `PROSCENIO_PT_element.draw`, add a `proscenio.reimport_element` button (icon `FILE_REFRESH`) shown only when the active object is an imported element (has `proscenio_import_origin`), placed near the element-type fields.

## 6. Tests (headless, in-Blender via `run_operator_tests.py`)

Add to `apps/blender/tests/operators/test_psd_reimport.py` (or a sibling `test_psd_reimport_single.py`):

- [ ] `reimport_element` re-stamps only the active Element and leaves a sibling Element's mesh data / weights untouched (two-layer manifest, paint a sibling, reimport one, assert the sibling identical).
- [ ] Same-bounds single reimport preserves painted weights on the target (rides `_ensure_mesh` short-circuit through the single path).
- [ ] Changed-bounds (edit the manifest layer's size between imports) rebuilds + reprojects, not wipes.
- [ ] A renamed / removed source layer returns `status="missing"` and leaves the Element intact (no exception, no geometry change).
- [ ] The manifest-path stamp round-trips: after `import_manifest`, every mesh carries `PROSCENIO_IMPORT_MANIFEST` equal to the source path.
- [ ] Single reimport does not re-anchor: a sibling Element's Z is unchanged after reimporting only the other Element.

## 7. Gates

- [ ] `run_operator_tests.py` (full set, was 207 on 5.x) + `run_tests.py` goldens (8/8 byte-unchanged - this spec stamps a new idprop but does not touch the writer, so goldens must stay green).
- [ ] `mypy` strict + `ruff format --check` + `ruff check` on `apps/blender`.
- [ ] gdlint not needed (no GDScript touched).

## 8. Post-impl cleanup (per the post-impl-cleanup discipline)

- [ ] QA Companion: add the per-Element reimport to [`tools/qa-companion/checklist/blender.md`](../../tools/qa-companion/checklist/blender.md) (Element panel).
- [ ] Lock the call in [`decisions.md`](../decisions.md).
- [ ] Prune this spec folder, index it in [`_index.md`](../_index.md) with the PR number.
