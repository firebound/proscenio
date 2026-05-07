---
name: blender-addon-dev
description: Develop, install, lint, and test the Blender addon
---

# Blender addon development

## Target versions

- **Minimum:** Blender 4.2 LTS — required for the Extensions system (`blender_manifest.toml`).
- **Tested:** Blender 4.5 LTS, latest 5.x.
- **Python:** 3.11 (bundled with Blender 4.x).

## Project layout

```text
blender-addon/
├── blender_manifest.toml   # Blender Extensions system manifest
├── __init__.py             # entry point — registers properties, operators, panels
├── pyproject.toml          # ruff config + mypy strict config
├── core/                   # pure-Python helpers (validation.py, future data classes)
├── properties/             # bpy.types.PropertyGroup — typed widgets backing the panel
├── operators/              # bpy.types.Operator subclasses
├── panels/                 # bpy.types.Panel subclasses (sidebar tab + child panels)
├── importers/              # PSD JSON, Krita JSON, etc.
├── exporters/godot/        # .proscenio writer
└── tests/                  # headless test suite (Blender-driven round-trip)

tests/                      # repo-root pytest suite (no Blender required)
└── test_validation.py      # core/validation.py unit tests
```

The addon ID is `proscenio` (set in the manifest). The directory name `blender-addon/` is purely repo-side; when packaged the contents are zipped, and Blender extracts to `<extensions>/proscenio/`.

## Install for development

Symlink (Windows: directory junction) the contents of `blender-addon/` into Blender's extensions directory:

```text
%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\proscenio
```

Reload via **Preferences → Get Extensions → Reload**, or restart Blender.

## Headless tests

Two suites, two runners:

```sh
# Pure Python (validation, future utility tests) — no Blender needed.
pytest tests/

# Blender round-trip — walks every fixture under examples/<name>/<name>.blend,
# re-exports each, diffs against examples/<name>/<name>.expected.proscenio.
blender --background --python blender-addon/tests/run_tests.py
```

Pytest tests use `SimpleNamespace` mocks so the validation module is exercised in isolation. The Blender suite uses the real `bpy` and lives in `blender-addon/tests/`. Goldens live alongside their fixture: `examples/<name>/<name>.expected.proscenio`. Importer-side fixtures stay under `godot-plugin/tests/fixtures/`.

### Adding a fixture

1. Hand-author `examples/<name>/<name>.blend` (mesh objects + armature + materials + weights + actions). For procedural fixtures (`blink_eyes/`, `shared_atlas/`), keep the `scripts/fixtures/build_<name>.py` builder.
2. For hand-authored fixtures: render layers from the `.blend` with `blender --background examples/<name>/<name>.blend --python scripts/fixtures/render_<name>_layers.py`. For procedural ones: run `python scripts/fixtures/draw_<name>.py` then the `build_<name>.py`.
3. Generate the golden: `blender --background examples/<name>/<name>.blend --python scripts/fixtures/export_proscenio.py`.
4. Add `<Name>.tscn` + `<Name>.gd` wrapper following the SPEC 001 pattern (see `examples/doll/Doll.gd` for the canonical template).
5. Verify locally: `blender --background --python blender-addon/tests/run_tests.py`. The runner auto-discovers the new fixture.

## Coding rules

- All UI strings should be wrapped for `bpy.app.translations` (i18n later, hooks now).
- No global mutable state. Use `bpy.types.Scene` properties or operator properties.
- Operators must be undoable: `bl_options = {'REGISTER', 'UNDO'}`.
- Lint: `ruff check blender-addon/`. Format: `ruff format blender-addon/`.
- Lazy-import inside operator methods if a top-level import would break Blender's reload cycle.
- Always `unregister()` cleanly — leaked classes break reload.

## Manifest

`blender_manifest.toml` follows the Blender Extensions schema. Required fields: `id`, `version`, `name`, `tagline`, `maintainer`, `type = "add-on"`, `blender_version_min`, `license`. See <https://docs.blender.org/manual/en/latest/extensions/getting_started.html>.

## Authoring sprites in the panel (SPEC 005)

The addon ships a `Proscenio` sidebar tab in the 3D Viewport (open with N). Inside, child panels expose every Proscenio-relevant knob:

- **Active sprite** — sprite type dropdown (`polygon` / `sprite_frame`), sprite_frame metadata fields (`hframes`, `vframes`, `frame`, `centered`), polygon vertex-group summary. Inline validation icons appear next to broken rows (e.g. `sprite_frame` with `hframes < 1`).
- **Skeleton** — armature bone count + warnings (no armature, multiple armatures).
- **Animation** — read-only summary of every Action that the writer would emit.
- **Atlas** — read-only atlas filename discovered from materials.
- **Validation** — populated by the Validate button. Lists every issue the export-time checker found (errors block export, warnings inform).
- **Export** — sticky `last_export_path`, `pixels_per_unit`, Validate / Export / Re-export buttons.
- **Diagnostics** — smoke test + future addon-health buttons.

The panel widgets read and write `bpy.types.Object.proscenio` (a `PropertyGroup` registered by SPEC 005). The PropertyGroup mirrors the legacy raw Custom Properties (`proscenio_type`, `proscenio_hframes`, etc.) so power users can keep editing raw data — both paths round-trip.

### One-click re-export

After the first **File → Export → Proscenio** (or panel **Export** button) the path is stored on the Scene PropertyGroup. The **Re-export** button silently re-runs the writer to that path — no file dialog. Saved with the `.blend` so the document carries its export target.

### Validate before export

Both Export and Re-export gate on `validate_export(scene)`. If any issue carries severity `error`, the operator aborts with a clear `self.report` message and the panel's Validation list shows what to fix.

## Painting weights for skinning (SPEC 003)

The writer turns Blender vertex groups into the `weights` array on a `polygon`-typed sprite. To author a skinned sprite:

1. Parent the mesh to the armature with `Set Parent → Armature Deform` (or skip the modifier and create vertex groups manually).
2. Create one vertex group per bone you want to influence the mesh. **The group name must match the bone name exactly** — that is the writer's only matching rule (D7 of [SPEC 003](../../specs/003-skinning-weights/STUDY.md)).
3. Enter Weight Paint mode and paint per-bone influence on the mesh. The writer normalizes per-vertex sums to `1.0` (D1), so additive painting is safe — paint where you want it, no need to manually subtract elsewhere.
4. Vertices left with zero total weight fall back to the sprite's resolved bone (D2). A mesh with vertex groups but **no** matching bones raises a `RuntimeError` at export time — fix the names or remove the groups.
5. Vertex groups whose names do not match any armature bone are dropped with a console warning per group (D3). Useful when you keep auxiliary groups for selection or unrelated tooling.

A sprite without any vertex groups stays rigid-attached (current Phase 1 behavior). `sprite_frame` sprites ignore weights entirely — Godot's `Sprite2D` has no skinning concept.

## Common pitfalls

- Reloading addons leaks registered classes — always `unregister()` cleanly.
- `bpy.context` differs between operator and panel scope — read it carefully.
- File paths: use `bpy.path.abspath()` to resolve `//` relative paths.
- Driver and handler registration must clean up in `unregister()`.
