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

1. Hand-author the `.blend` (mesh objects + armature + materials + weights + actions) or, for procedural fixtures, keep a builder script under `packages/fixtures/<name>/`.
2. Render or draw the source layers; populate the `.blend` from them.
3. Generate the golden by running the writer headlessly against the freshly built `.blend`.
4. Verify locally: `blender --background --python apps/blender/tests/run_tests.py`. The runner auto-discovers new fixtures.

For procedural pixel-art fixtures (Pillow-drawn spritesheets feeding a single-feature `.blend`), copy the conventions from the newest builder under `packages/fixtures/` rather than older ones - bone tail along world -Y, relative `//` filepaths, `tex.interpolation = "Closest"`, driver wiring matching the panel operator's defaults.

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

Pattern lifted from the Quick Armature operator (`operators/quick_armature.py`). Reusable for any operator that needs preview feedback while a modal session is active.

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

### Edit Weights modal pattern

The `proscenio.edit_weights` operator wraps Blender's native Weight Paint mode with a 2D-safe preset + GPU provenance overlay + per-stroke provenance tagging. Pattern when an operator needs to enter a modal paint context with restorable side effects:

- **Capture session at invoke.** Snapshot the world state into a frozen dataclass (`EditWeightsSession` in `core/bpy_helpers/skinning/modal_session.py`): prior active object + selection + object mode + armature mode + paint preset + bone collection visibility + relevant PG flags. Store **names** not object refs so undo-driven object recreation cannot stale the restore path.
- **Symmetric apply / restore.** Pure dataclasses (`PaintPresetSnapshot`) hold the desired state; bpy bridge (`paint_preset_bind.snapshot_paint_preset` / `apply_paint_preset` / `restore_paint_preset`) writes them onto `context.tool_settings.weight_paint`. Defensive `hasattr` guards tolerate Blender API drift across versions.
- **Bone Collections visibility** (`bone_collection_visibility.py`) lifts COA Tools 2's `bone.hide` global state to Blender 4.0+ `bone_collections` per-collection `is_visible`. 3.x falls back to per-bone hide. Module is bpy-free (duck-typed inputs) so tests use `SimpleNamespace` mocks.
- **Per-stroke diff for provenance tagging.** `StrokeDiffTracker` snapshots the active vertex group's weights on `LEFTMOUSE PRESS`; on `LEFTMOUSE RELEASE` it diffs against current weights + flips touched sidecar entries' `provenance` to `user_paint` + rewrites the sidecar JSON. `WINDOW_DEACTIVATE` + `MOUSEMOVE` with `event.pressure == 0` flush in-flight strokes so alt-tab / tablet pen-lift don't lose paint.
- **Hard ESC + try/finally restore.** Modal's `_finish(cancel=True)` runs every cleanup step inside try/finally; restoration MUST survive partial failure (any one `select_set` raise should not abort the rest of the restore chain - wrap each step in `contextlib.suppress(RuntimeError, ReferenceError)`). Iterate `list(context.selected_objects)` (not the live coll) so mutation during cleanup doesn't skip items.
- **Single undo push wraps cumulative paint.** Call `bpy.ops.ed.undo_push(message="Edit Weights")` once at `_finish` so `Ctrl+Z` reverts the whole modal session, not stroke by stroke.
- **GPU overlay** lives in a sibling helper (`weight_overlay.py`) registered via `bpy.types.SpaceView3D.draw_handler_add(... "POST_VIEW")`. Group draws by color into batched `POINTS` primitives so per-vert disc rendering stays cheap regardless of vert count. Wrap the draw loop in try/finally so `gpu.state.point_size_set` + `blend_set` always reset (state leak into other overlays otherwise).

Reference implementation: `apps/blender/operators/edit_weights.py` (the modal) + `apps/blender/core/bpy_helpers/skinning/` (paint_preset_bind / bone_collection_visibility / weight_overlay / stroke_diff / modal_session).

## Modal operator hint placement

Standard for **every** modal operator that needs to surface a chord cheatsheet:

- **Bottom STATUS BAR (canonical, always wired):** append a draw callback via `bpy.types.STATUSBAR_HT_header.prepend(fn)` so the chord vocabulary lands on the LEFT of the bottom bar (where Blender's own modal tools place their hints - knife tool, loop cut). The right side stays for Blender's stats widgets.
- **3D viewport header (optional):** append a second draw callback via `bpy.types.VIEW3D_HT_header.append(fn)` when the operator runs inside a VIEW_3D and benefits from a hint visible without looking down (drawing-style modals, e.g. Quick Armature). Use `layout.separator_spacer()` first so the hint sits on the right edge of the viewport header instead of pushing Blender's mode/select/view dropdowns around. Both callbacks share a single `_emit_chord_layout(layout, cls)` helper so the vocabulary stays in sync.
- **Render real Blender icons** via `layout.label(text="", icon="MOUSE_LMB_DRAG")`, `EVENT_SHIFT`, `EVENT_ALT`, `EVENT_CTRL`, `EVENT_X`, `EVENT_Z`, `EVENT_RETURN`, `EVENT_ESC`, etc. Do NOT render text-only POST_PIXEL "cheatsheets" for chord hints - they cannot match the native icons and become noise next to the real ones.
- **Cleanup is mandatory.** Track each registration with a class-level `bool` (`_statusbar_appended`, `_view3d_header_appended`); remove via `bpy.types.STATUSBAR_HT_header.remove(fn)` and `bpy.types.VIEW3D_HT_header.remove(fn)` in every exit path (`_finish`, `cancel`, error returns) AND in the addon's `unregister()` orphan sweep.
- **POST_PIXEL is reserved for cursor-tracking overlays** (preview lines in 3D space, tooltips that follow the cursor, axis guidelines). Static chord vocabulary belongs in the headers, not in the canvas.

Reference implementation: `apps/blender/operators/quick_armature.py` (`_emit_chord_layout`, `_draw_statusbar_quick_armature`, `_draw_view3d_header_quick_armature`).

## Pure-Python image processing

The addon refuses third-party Python deps at runtime (no OpenCV, no numpy, no Pillow). COA Tools 2's `cv2` requirement is its single biggest adoption blocker - corp / ISP firewalls block PyPI, version mismatches break ABI on manual cv2 copies, see [Aodaruma/coa_tools2#94](https://github.com/Aodaruma/coa_tools2/issues/94) + [#107](https://github.com/Aodaruma/coa_tools2/issues/107). Proscenio implements alpha-channel image processing in plain Python loops at the scales the addon targets (sprites downscaled to <=256x256 before tracing).

Pattern when an operator needs image processing:

- **bpy bridge reads `bpy.types.Image.pixels`** (flat float RGBA array) into a `list[list[int]]` alpha grid via a downscale factor. The downscale lets pure-Python morphology scale to HD source PNGs without quadratic cost on the full image.
- **Pure helpers in `core/`** (no `bpy` import) do the math: Moore Neighbour contour tracing + 4-connectivity binary morphology (dilate / erode) + Laplacian smoothing + arc-length resampling + point-in-polygon clipping + distance-to-segment. Each helper is unit-tested in isolation.
- **Pure helpers produce float-tuple outputs** the bpy bridge converts to world XZ coordinates on the Y=0 picture plane (Proscenio convention, parallel to the Quick Armature axis lock).
- **bpy bridge writes back via `bmesh`** - `bmesh.new()`, add verts + edges, `bmesh.ops.triangle_fill(edges=..., use_beauty=True)` for the Delaunay triangulation, `bm.to_mesh(mesh)`, `bm.free()`.
- **Cap defensive iteration limits** in any walker (`_MAX_CONTOUR_STEPS=200_000` in `core/automesh/contour.py`) so a pathological input cannot hang the Blender UI thread.

Reference implementation - pure side (no `bpy`): `apps/blender/core/automesh/contour.py` (pure walker), `apps/blender/core/automesh/geometry.py` (smoothing + resample), `apps/blender/core/automesh/density.py` (interior points + bone-aware density), `apps/blender/core/automesh/erosion_loops.py`, `apps/blender/core/automesh/cut_geometry.py`, `apps/blender/core/automesh/stroke_geometry.py`, `apps/blender/core/automesh/outer_splice.py`. bpy bridge: `apps/blender/core/bpy_helpers/automesh/bridge.py` (orchestrator), `cdt.py` (Delaunay), `base_sprite.py` (vertex group), `uv.py` (UV stamp), `debug.py` (visual stages). Operators: `apps/blender/operators/automesh.py` + `apps/blender/operators/automesh_authoring.py`. Pytest coverage: `tests/automesh/test_*.py` (~200 cases covering the pure side).

The same no-third-party-deps rule extends to the weight sidecar reproject: `apps/blender/core/skinning/weight_reproject.py` does hand-rolled O(n) KNN + 2D barycentric over UV anchors. No `mathutils.kdtree` (would couple the module to bpy), no numpy. Typical sprite mesh has < 2000 verts; O(n) per query is fine. Pure module + 10 unit tests so the algorithm is testable in vanilla Python.

## Common pitfalls

- Reloading addons leaks registered classes - always `unregister()` cleanly.
- `bpy.context` differs between operator and panel scope - read it carefully.
- File paths: use `bpy.path.abspath()` to resolve `//` relative paths.
- Drivers and handlers registered at register time must clean up in `unregister()`.
- **Never write to ID data blocks (Scene, Object, etc) from within `Panel.draw`.** Blender raises `AttributeError: Writing to ID classes in this context is not allowed`. Auto-fill / sync logic that mutates a PG must run from `bpy.app.handlers.load_post`, `depsgraph_update_post`, a deferred timer, or an explicit operator. Reading is always safe.
