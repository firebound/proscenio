---
name: blender-dev
description: Develop, install, lint, and test the Blender addon
---

# Blender addon development

## Target versions

- **Minimum:** Blender 4.2 LTS — required for the Extensions system (`blender_manifest.toml`).
- **Tested:** Blender 4.5 LTS, latest 5.x.
- **Python:** 3.11 (bundled with Blender 4.x).

## Project layout

Post SPEC 009 (May 2026). Every package below is multi-file: the `__init__.py` orchestrates registration; topical submodules carry the actual classes / helpers.

```text
apps/blender/
├── blender_manifest.toml          Blender Extensions system manifest
├── __init__.py                    addon entry — chains submodule register() / unregister()
├── pyproject.toml                 ruff + mypy strict config
├── core/                          bpy-free helpers
│   ├── __init__.py                package contract docstring
│   ├── cp_keys.py                 Custom Property string registry (proscenio_*)
│   ├── feature_status.py          status badge dispatch (5.1.d.5)
│   ├── help_topics.py             in-panel help dispatch (5.1.d.5)
│   ├── hydrate.py                 CP -> PG hydration logic
│   ├── mirror.py                  PG -> CP mirror logic
│   ├── pg_cp_fallback.py          PG-first / CP-fallback reader
│   ├── props_access.py            scene_props / object_props typed accessors
│   ├── psd_manifest.py            Photoshop manifest reader
│   ├── psd_naming.py              PSD layer-name parsing
│   ├── region.py                  texture region resolver
│   ├── report.py                  operator report helpers ("Proscenio: " prefix)
│   ├── slot_emit.py               slot dict projection (SPEC 004)
│   ├── uv_bounds.py               UV bbox math
│   ├── atlas_packer.py            MaxRects packer
│   ├── bpy_helpers/               bpy-bound helpers (atlas_io, sprite_frame_shader,
│   │                                 psd_spritesheet, select, viewport_math)
│   └── validation/                per-validator subpackage (issue, active_sprite,
│                                    active_slot, export, _shared)
├── properties/                    PropertyGroup classes
│   ├── __init__.py                3 PGs + register/unregister
│   ├── _dynamic_items.py          EnumProperty items + PointerProperty poll filters
│   └── _handlers.py               persistent load_post / save_pre handlers
├── operators/                     bpy.types.Operator subclasses
│   ├── __init__.py                orchestrator
│   ├── help_dispatch.py           status_info, help, smoke_test
│   ├── export_flow.py             validate_export, export_godot, reexport_godot
│   ├── selection.py               select_issue, select_outliner, toggle_favorite
│   ├── authoring_camera.py        create_ortho_camera
│   ├── authoring_ik.py            toggle_ik_chain
│   ├── uv_authoring.py            reproject_sprite_uv, snap_region_to_uv
│   ├── driver.py                  create_driver (5.1.d.1)
│   ├── pose_library.py            save_pose_asset, bake_current_pose
│   ├── quick_armature.py          quick_armature modal (5.1.d.3)
│   ├── slot/                      create_slot, add_attachment, set_default,
│   │                                preview_shader (SPEC 004)
│   ├── atlas_pack/                pack, apply, unpack + shared _paths.py
│   └── import_photoshop.py        Photoshop manifest importer (SPEC 006)
├── panels/                        bpy.types.Panel subclasses
│   ├── __init__.py                root PROSCENIO_PT_main + orchestrator
│   ├── _helpers.py                draw_subpanel_header + mode predicates
│   ├── active_sprite.py           sprite type, region, driver shortcut, validation row
│   ├── active_slot.py             slot anchor, attachments list (SPEC 004)
│   ├── skeleton.py                bone count + UL_bones + pose-mode shortcuts
│   ├── outliner.py                sprite-centric flat list (5.1.d.4)
│   ├── animation.py               actions UIList
│   ├── atlas.py                   atlas filename + packer box
│   ├── validation.py              issue list, click-to-select
│   ├── export.py                  sticky path + Validate / Export / Re-export
│   ├── help.py                    F3 cheat-sheet
│   └── diagnostics.py             smoke test
├── importers/photoshop/           PSD manifest -> Blender meshes
└── exporters/godot/writer/        .proscenio writer (package)
    ├── __init__.py                public export() entry
    ├── _schema.py                 TypedDicts mirroring schema
    ├── scene_discovery.py         find_armature / sprites / atlas
    ├── skeleton.py                coord conversion + Bone2D world transforms
    ├── sprites.py                 polygon body + sprite_frame + weights pipeline
    ├── slots.py                   slot Empty walker (SPEC 004)
    ├── slot_animations.py         slot_attachment track emission
    └── animations.py              bone_transform track emission

tests/                             repo-root pytest suite (no Blender required)
├── test_cp_keys.py                wave 9.1 helpers
├── test_props_access.py           wave 9.1 helpers
├── test_pg_cp_fallback.py         wave 9.1 helpers
├── test_validation.py             core/validation/ subpackage
└── (others)
```

The addon ID is `proscenio` (set in the manifest). The directory name `apps/blender/` is purely repo-side; when packaged the contents are zipped, and Blender extracts to `<extensions>/proscenio/`.

### Where to add new code

- A pure-Python helper that does math, parses strings, walks dataclasses → `core/<name>.py`.
- A helper that calls `bpy.data` / `bpy.ops` / `bpy.context` / etc. → `core/bpy_helpers/<name>.py`.
- A new operator → `operators/<concern>.py` (or grow an existing concern's module). Each submodule owns its `_classes` tuple + `register()` / `unregister()`.
- A new panel → `panels/<concern>.py` (or split if it already crowds `_helpers.py`).
- A new validator → add a function under `core/validation/<scope>.py` and re-export from `core/validation/__init__.py`.
- A Custom Property literal → add a constant to `core/cp_keys.py` and import the constant.

When a single file grows past ~300 LOC, ask whether it has absorbed multiple concerns. If yes, split it (the SPEC 009 STUDY documents the rationale).

## Install for development

Symlink (Windows: directory junction) the contents of `apps/blender/` into Blender's extensions directory:

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
blender --background --python apps/blender/tests/run_tests.py
```

Pytest tests use `SimpleNamespace` mocks so the validation module is exercised in isolation. The Blender suite uses the real `bpy` and lives in `apps/blender/tests/`. Goldens live alongside their fixture: `examples/<name>/<name>.expected.proscenio`. Importer-side fixtures stay under `apps/godot/tests/fixtures/`.

### Adding a fixture

1. Hand-author `examples/<name>/<name>.blend` (mesh objects + armature + materials + weights + actions). For procedural fixtures (`blink_eyes/`, `shared_atlas/`, `mouth_drive/`), keep the `scripts/fixtures/<name>/build_blend.py` builder.
2. For hand-authored fixtures: render layers from the `.blend` with `blender --background examples/<name>/<name>.blend --python scripts/fixtures/<name>/render_layers.py`. For procedural ones: run `py scripts/fixtures/<name>/draw_layers.py` then `blender --background --python scripts/fixtures/<name>/build_blend.py`.
3. Generate the golden: `blender --background examples/<name>/<name>.blend --python scripts/fixtures/_shared/export_proscenio.py`.
4. Add `<Name>.tscn` + `<Name>.gd` wrapper following the SPEC 001 pattern (see `examples/authored/doll/Doll.gd` for the canonical template).
5. Verify locally: `blender --background --python apps/blender/tests/run_tests.py`. The runner auto-discovers the new fixture.

For **procedural pixel-art fixtures** (Pillow-drawn spritesheets feeding a single-feature `.blend`), follow the conventions in [`scripts/fixtures/README.md`](../../scripts/fixtures/README.md) -- bone tail along world -Y, image filepath relative (`//pillow_layers/...`), `tex.interpolation = "Closest"`, driver wiring matches the panel operator's defaults, etc. Copy from `mouth_drive/build_blend.py` (newest, follows every convention) rather than older builders.

## Coding rules

- All UI strings should be wrapped for `bpy.app.translations` (i18n later, hooks now).
- No global mutable state. Use `bpy.types.Scene` properties or operator properties.
- Operators must be undoable: `bl_options = {'REGISTER', 'UNDO'}`.
- Lint: `ruff check apps/blender/`. Format: `ruff format apps/blender/`.
- Lazy-import inside operator methods if a top-level import would break Blender's reload cycle.
- Always `unregister()` cleanly — leaked classes break reload.

## Manifest

`blender_manifest.toml` follows the Blender Extensions schema. Required fields: `id`, `version`, `name`, `tagline`, `maintainer`, `type = "add-on"`, `blender_version_min`, `license`. See <https://docs.blender.org/manual/en/latest/extensions/getting_started.html>.

## Authoring sprites in the panel (SPEC 005)

The addon ships a `Proscenio` sidebar tab in the 3D Viewport (open with N). Inside, child panels expose every Proscenio-relevant knob. Every subpanel header carries two icons on the right: a **status badge** (`godot-ready` / `blender-only` / `planned` / `out-of-scope` — hover for the band-specific tooltip) and a **`?` button** that opens a topic-specific in-panel help popup. The full topic dispatch lives in [`apps/blender/core/help_topics.py`](../../apps/blender/core/help_topics.py).

- **Active sprite** — sprite type dropdown (`polygon` / `sprite_frame`), sprite_frame metadata (`hframes`, `vframes`, `frame`, `centered`), texture region (auto / manual + Snap-to-UV), in-viewport sprite_frame preview slicer (5.1.d.5), polygon vertex-group summary, **Drive from Bone** picker (5.1.d.1), **Import Photoshop Manifest** button (5.1.b → 6.x integration), and inline validation icons next to broken rows. Active Slot subpanel surfaces when an Empty with `is_slot=True` is selected — pick the default attachment via SOLO icons.
- **Skeleton** — armature bone count + warnings (no armature, multiple armatures), pose-mode helpers (**Bake Current Pose**, **Toggle IK**, **Save Pose to Library** — 5.1.d.2 wraps `POSELIB_OT_create_pose_asset`), **Quick Armature** modal (5.1.d.3 — click-drag bone draw on z=0), **Create Slot** (5.1.b SPEC 004 — wraps selected meshes into an Empty as attachments).
- **Outliner** (5.1.d.4) — sprite-centric flat list of slots, attachments, sprite meshes, armatures. Substring filter + favorites toggle. Click a row to activate the target object. SOLO icon next to each row pins it as a favorite.
- **Animation** — read-only summary of every Action that the writer would emit.
- **Atlas** — read-only atlas filename discovered from materials, **Pack Atlas / Apply Packed Atlas / Unpack Atlas** flow.
- **Validation** — populated by the Validate button. Lists every issue the export-time checker found (errors block export, warnings inform). Click a row to activate the offending object.
- **Export** — sticky `last_export_path`, `pixels_per_unit`, **Preview Camera** (orthographic camera matching `pixels_per_unit`), **Validate / Export / Re-export** buttons.
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
