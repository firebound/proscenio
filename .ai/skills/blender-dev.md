---
name: blender-dev
description: Develop, install, lint, and test the Blender addon
---

# Blender addon development

## Target versions

- **Minimum:** Blender 4.2 LTS - required for the Extensions system (`blender_manifest.toml`).
- **Tested:** Blender 4.5 LTS, latest 5.x.
- **Python:** 3.11 (bundled with Blender 4.x).

## Project layout

```text
apps/blender/
├── blender_manifest.toml     Blender Extensions system manifest
├── __init__.py               addon entry - chains submodule register / unregister
├── pyproject.toml            ruff + mypy strict config
├── core/                     bpy-free helpers (top-level imports never touch bpy)
│   ├── bpy_helpers/          bpy-bound helpers split by concern
│   └── validation/           per-validator subpackage, re-exported from __init__.py
├── properties/               PropertyGroup classes + handlers
├── operators/                bpy.types.Operator subclasses, grouped by concern
├── panels/                   bpy.types.Panel subclasses, one file per concern
├── importers/photoshop/      PSD manifest -> Blender meshes
├── exporters/godot/writer/   .proscenio writer (package, one file per emission concern)
└── tests/                    pytest suite + headless run_tests.py
```

The addon ID is `proscenio` (set in the manifest). The on-disk directory `apps/blender/` is repo-only; when packaged the contents are zipped and Blender extracts to `<extensions>/proscenio/`.

### Where to add new code

- Pure-Python helper (math, parsing, dataclass walks) -> `core/<name>.py`.
- Helper that calls `bpy.data` / `bpy.ops` / `bpy.context` -> `core/bpy_helpers/<name>.py`.
- New operator -> `operators/<concern>.py` (or a sub-package when the concern grows multi-file). Each submodule owns its `_classes` tuple + `register()` / `unregister()`.
- New panel -> `panels/<concern>.py`.
- New validator -> add a function under `core/validation/<scope>.py` and re-export from the package `__init__.py`.
- Custom Property literals -> add a constant to `core/cp_keys.py` and import the constant; never spell the key inline.

When a single file grows past roughly 300 LOC, ask whether it has absorbed multiple concerns. If yes, split it.

## Install for development

Symlink (Windows: directory junction) the contents of `apps/blender/` into Blender's extensions directory:

```text
%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\proscenio
```

Reload via **Preferences → Get Extensions → Reload**, or restart Blender.

## Headless tests

Two suites, two runners:

```sh
# Pure Python - no Blender needed.
pytest tests/

# Blender round-trip - re-exports every fixture and diffs against the golden.
blender --background --python apps/blender/tests/run_tests.py
```

Pytest tests use `SimpleNamespace` mocks so the validation module is exercised in isolation. The Blender suite uses the real `bpy`. Each fixture lives at `examples/<name>/<name>.blend` with its golden alongside as `<name>.expected.proscenio`. Importer-side fixtures stay under `apps/godot/tests/fixtures/`.

### Adding a fixture

1. Hand-author the `.blend` (mesh objects + armature + materials + weights + actions) or, for procedural fixtures, keep a builder script under `scripts/fixtures/<name>/`.
2. Render or draw the source layers; populate the `.blend` from them.
3. Generate the golden by running the writer headlessly against the freshly built `.blend`.
4. Verify locally: `blender --background --python apps/blender/tests/run_tests.py`. The runner auto-discovers new fixtures.

For procedural pixel-art fixtures (Pillow-drawn spritesheets feeding a single-feature `.blend`), copy the conventions from the newest builder under `scripts/fixtures/` rather than older ones - bone tail along world -Y, relative `//` filepaths, `tex.interpolation = "Closest"`, driver wiring matching the panel operator's defaults.

## Coding rules

- Strict static typing on every function signature (`from __future__ import annotations` at the top of new files).
- `Any` only at the `bpy` boundary, documented inline.
- No global mutable state. Use `bpy.types.Scene` properties or operator properties.
- Operators must be undoable: `bl_options = {'REGISTER', 'UNDO'}`.
- All UI strings should be wrappable for `bpy.app.translations` (i18n hooks now, translations later).
- Lazy-import inside operator methods if a top-level import would break Blender's reload cycle.
- Always `unregister()` cleanly - leaked classes break reload.
- Lint: `ruff check apps/blender/`. Format: `ruff format apps/blender/`. Type-check: `mypy` against the addon's pyproject.

## Modal operators with in-viewport overlay

Pattern lifted from SPEC 012.1 (`operators/quick_armature.py`). Reusable for any operator that needs preview feedback while a modal session is active.

- **Two draw handlers per operator.** Register one `POST_VIEW` handler on `bpy.types.SpaceView3D` for world-space hints (preview line, anchor circle); register one `POST_PIXEL` handler for screen-space hints (modifier cheatsheet, status header). Store both handles as class attributes so they survive any modal exit path.
- **Single unregister helper.** Call `_unregister_handlers(self)` from `_finish`, `cancel`, and every error-return path. Wrap each `draw_handler_remove` in `contextlib.suppress(ValueError, RuntimeError)` so reload-scripts paths that already dropped the handle do not raise.
- **Sweep orphans on addon `unregister()`.** When the addon is disabled or reloaded, walk the operator's class attributes and remove any leftover handles before the operator class itself is unregistered. Cheap insurance against Blender's reload-scripts loop.
- **Geometry helpers stay bpy-free.** Vertex math (`build_circle_vertices`, `build_rect_vertices`) lives under `core/modal_overlay_geometry.py` so pytest can verify it without booting Blender. The bpy-bound wrappers (`draw_line_3d`, `draw_circle_3d`, `draw_text_panel_2d`) live under `core/bpy_helpers/modal_overlay.py` and consume those vertices.
- **Tag area for redraw on `MOUSEMOVE`.** Modal handlers do not redraw spontaneously; call `context.area.tag_redraw()` after updating any state the draw handler reads. Cap the work to mouse-event cadence - no timers needed.
- **Snapshot-and-restore view state.** If the operator changes `view_perspective` or `view_matrix` (auto-snap to a specific orientation), save the originals in `invoke` and restore them in every exit path. Operators should not silently mutate user view state.

## Authoring panel overview

The addon ships a `Proscenio` sidebar tab in the 3D Viewport (open with **N**). Subpanels expose every Proscenio knob - sprite type and metadata, skeleton helpers, slot anchors, animation summary, atlas pack / apply / unpack, validation issues, export controls, diagnostics. Each subpanel header carries a status badge (`godot-ready` / `blender-only` / `planned` / `out-of-scope`) and a `?` button that opens an in-panel help popup.

Panel widgets read and write `bpy.types.Object.proscenio` and `bpy.types.Scene.proscenio` (PropertyGroups). The PropertyGroup mirrors the legacy raw Custom Properties (`proscenio_*` keys) so power users can keep editing raw data - both paths round-trip.

### One-click re-export

After the first **File → Export → Proscenio** (or panel **Export**), the path is stored on the Scene PropertyGroup. The **Re-export** button silently re-runs the writer to that path. Saved with the `.blend` so the document carries its export target.

### Validate before export

Both Export and Re-export gate on the export validator. If any issue carries severity `error`, the operator aborts with a clear report and the panel's Validation list shows what to fix.

## Painting weights for skinning

The writer turns Blender vertex groups into the `weights` array on a `polygon`-typed sprite. To author a skinned sprite:

1. Parent the mesh to the armature with **Set Parent → Armature Deform** (or skip the modifier and create vertex groups manually).
2. Create one vertex group per influencing bone. **The group name must match the bone name exactly** - the writer matches by name only.
3. Weight Paint as usual. The writer normalises per-vertex sums to `1.0`, so additive painting is safe.
4. Vertices left at zero total weight fall back to the sprite's resolved bone. A mesh with vertex groups but **no** matching bones raises `RuntimeError` at export - fix the names or remove the groups.
5. Vertex groups whose names do not match any bone are dropped with a console warning per group.

A sprite without any vertex groups stays rigid-attached (parent of `Bone2D`). `sprite_frame` sprites ignore weights entirely.

## Common pitfalls

- Reloading addons leaks registered classes - always `unregister()` cleanly.
- `bpy.context` differs between operator and panel scope - read it carefully.
- File paths: use `bpy.path.abspath()` to resolve `//` relative paths.
- Drivers and handlers registered at register time must clean up in `unregister()`.
