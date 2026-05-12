# SPEC 006 - Photoshop → Blender importer

## Problem

The Photoshop → Blender step is **manual** today: the JSX exporter writes per-layer PNGs + a manifest JSON, but there is no Blender-side importer. Users have to:

1. Run JSX exporter in Photoshop.
2. Open Blender, manually create one mesh per PNG, position it, link the texture, build the armature, parent meshes to bones.

This SPEC closes the loop. The Blender addon gains an "Import Photoshop Manifest" operator that reads the JSX-emitted manifest and stamps planes, materials, and a stub armature in one click.

## Reference: similar tools

- **COA Tools 2** - "Sprite import from JSON" operator that reads its own JSON format and stamps planes.
- **DUIK Auto-Rig** - auto-generates a rig from layered PSD names (After Effects, but the pattern transfers).
- **Spine** - imports `.psd` directly via Photoshop bridge or `.json` manifest from the bundled PSD-to-Spine script.

The shared pattern: "manifest tells the importer where each layer goes, what its naming convention implies, and how it relates to other layers".

## JSX exporter manifest contract - current shape (v0)

The JSX exporter today writes:

```json
{
  "doc": "dummy.psd",
  "size": [1024, 1024],
  "layers": [
    { "name": "torso",
      "path": "dummy/images/torso.png",
      "position": [120, 340],
      "size": [180, 240] }
  ]
}
```

Convention: hidden layers skipped, layer names prefixed `_` skipped, layer groups walked recursively (output names join with `__`). No `format_version`, no `z_order`, no kind field, no sprite_frame grouping.

SPEC 006 evolves this schema to v1 (D1) and bumps the JSX exporter to emit it (Wave 6.1).

## JSX exporter manifest contract - locked v1 (D1)

```json
{
  "format_version": 1,
  "doc": "firebound.psd",
  "size": [1024, 1024],
  "pixels_per_unit": 100,
  "layers": [
    { "kind": "polygon",
      "name": "torso",
      "path": "firebound/images/torso.png",
      "position": [120, 340],
      "size": [180, 240],
      "z_order": 5 },
    { "kind": "sprite_frame",
      "name": "eye",
      "position": [350, 200],
      "size": [32, 32],
      "z_order": 8,
      "frames": [
        { "index": 0, "path": "firebound/images/eye/0.png" },
        { "index": 1, "path": "firebound/images/eye/1.png" },
        { "index": 2, "path": "firebound/images/eye/2.png" },
        { "index": 3, "path": "firebound/images/eye/3.png" }
      ] }
  ]
}
```

Schema lives at `schemas/psd_manifest.schema.json`. Validated by `check-jsonschema` in CI alongside `proscenio.schema.json`.

Field semantics:

- `format_version` - integer, currently `1`. Bump when manifest shape changes.
- `doc` - original PSD filename (display only).
- `size` - `[doc_width_px, doc_height_px]`.
- `pixels_per_unit` - Blender pixels-per-unit factor; importer divides PSD pixels by this when stamping mesh size and position. Default 100 (matches existing addon convention).
- `layers[]` - z-ordered, top-to-bottom. Each entry has a discriminator `kind`.
  - `polygon` - single PNG, single quad mesh.
  - `sprite_frame` - N frames, single quad mesh sized to the bbox of the largest frame, animated via `proscenio.frame`.

The `kind` discriminator is the **single source of truth**: the importer obeys it without re-deriving from layer names. JSX has all the information at export time, so it emits the explicit kind.

## Sprite_frame source mechanism (D9)

Two mechanisms for the artist to mark a layer set as a sprite_frame, primary + fallback:

### Primary - PSD layer group with numeric children

Natural Photoshop workflow. The artist puts frames inside a Photoshop group:

```text
eye/                     (LayerSet)
├── 0                    (frame 0)
├── 1                    (frame 1)
├── 2                    (frame 2)
└── 3                    (frame 3)
```

Or `frame_0` / `frame_1` / `frame_2` / `frame_3`, or `eye_0` / `eye_1` / ...

JSX detection rule:

- The LayerSet's visible children are **all non-LayerSet** (no nested groups).
- Children names match one of: `^\d+$` | `^frame[_-]?\d+$` | `^<groupname>[_-]?\d+$`.

If both rules pass, JSX emits the LayerSet as a single `sprite_frame` manifest entry, with frames sorted by extracted index. The group name becomes the mesh name; child names contribute only an index.

### Fallback - flat `<name>_<index>` naming

Already locked in SPEC 007 D4. Top-level layers `eye_0`, `eye_1`, `eye_2`, `eye_3` get grouped by stripping the `_<index>` suffix and aggregating frames in index order. Used for users who do not group their frames in Photoshop.

The fallback is implemented at the **JSX side**, not the importer: JSX walks layers and groups them itself, emits a single `sprite_frame` manifest entry. The importer never has to pattern-match - it trusts the explicit `kind`.

## Frame size mismatch (D10)

Frames inside a sprite_frame group can have slightly different bounding boxes (artist paints each frame a pixel or two off). Spritesheet construction requires uniform tile size.

**Locked: pad all frames to the bbox of the largest frame, transparent fill, at importer side.** Pillow handles this naturally; output spritesheet is N × tile_max horizontally, with each frame anchored to its own bbox center inside the tile. The mesh quad is sized to the largest tile so the visual result is correct regardless of which frame is displayed.

JSX continues to emit raw per-frame PNGs untouched. Importer composes the spritesheet at import time and writes it to `examples/<fixture>/_spritesheets/<name>.png` (D8).

## Importer responsibilities

1. **Read manifest** at user-specified path. Validate against `schemas/psd_manifest.schema.json`.
2. **For each layer entry**:
   - `kind: polygon` → stamp a quad mesh sized to `size_px / pixels_per_unit`, position derived from PSD top-left to Blender XZ centre via the conversion below. Material with `ShaderNodeTexImage` pointing at the layer's PNG. Tag `proscenio.sprite_type = "polygon"`.
   - `kind: sprite_frame` → load each frame PNG, pad each to the bbox of the largest frame (transparent fill), concatenate horizontally into one spritesheet PNG, write to `_spritesheets/<name>.png`. Stamp a single quad mesh sized to the largest tile; material points at the spritesheet. Tag `proscenio.sprite_type = "sprite_frame"`, `hframes = N`, `vframes = 1`, `frame = 0`.
3. **Build a stub armature** (D3) - single `root` bone at the world origin. Parent every stamped mesh to `root` via `parent_type = 'BONE'`. User adds the rest of the rig manually.
4. **Optionally pack atlas** - leave per-PNG by default (D2). User clicks the existing Pack Atlas operator (SPEC 005.1.c.2) when ready.
5. **Surface UI** - operator `PROSCENIO_OT_import_photoshop` + sidebar button "Import Photoshop Manifest" + file picker.

### Coordinate conversion (D6)

PSD origin is top-left, Y down, pixels. Blender XZ is bottom-up, world units at `pixels_per_unit`. For a layer with `position = [px_x, px_y]` and `size = [px_w, px_h]` inside a doc of `doc_size = [W, H]`:

```text
mesh_center.x = (px_x + px_w / 2 - W / 2) / pixels_per_unit
mesh_center.z = (H / 2 - px_y - px_h / 2) / pixels_per_unit
mesh_center.y = z_order * Z_EPSILON  # avoid Z-fight, configurable
mesh_size.x  = px_w / pixels_per_unit
mesh_size.z  = px_h / pixels_per_unit
```

`Z_EPSILON` defaults to `0.001`. User can override via scene property if too small for their rig.

### Re-import semantics (D5)

Idempotent: meshes are identified by their manifest `name`. Re-import replaces the existing mesh with the same name (same vertex data, fresh material, fresh image), preserving any user-set rotation, parenting, or vertex weights via a `proscenio.import_origin = "psd:<layer_name>"` tag on the mesh. Meshes whose name no longer appears in the manifest are **left alone** (user may have repurposed them) but logged as orphans for the user to clean up manually.

## Decisions locked

| ID | Decision | Choice |
| --- | --- | --- |
| D1 | Manifest format | **v1 schema with `format_version`, `kind` discriminator, `pixels_per_unit`, `z_order`, `frames[]` for sprite_frame.** Locked at `schemas/psd_manifest.schema.json`. |
| D2 | Atlas strategy | **Leave per-PNG.** User runs the existing Pack Atlas operator (SPEC 005.1.c.2) post-import. |
| D3 | Armature stub | **Auto: single `root` bone, every mesh parented to it.** User adds the rest manually. |
| D4 | Sprite_frame naming | `<name>_<index>` (already locked in SPEC 007 D4). Importer respects via the `kind` discriminator. |
| D5 | Re-import semantics | **Idempotent by manifest name.** User-modified rotation / parenting / weights survive re-imports tagged via `proscenio.import_origin`. |
| D6 | Coordinate conversion | PSD top-left → Blender XZ centre at `pixels_per_unit`. `mesh_center.y = z_order * Z_EPSILON` to avoid Z-fight. |
| D7 | `.psd` direct vs JSX | **JSX manifest only.** `.psd` direct read deferred (fragile cross-version, duplicates JSX work). |
| D8 | Frame source PNGs after compose | **Keep individuals; spritesheet goes to `_spritesheets/<name>.png`.** Clean separation; gitignore-able. |
| D9 | Sprite_frame source mechanism | **Primary: PSD layer group with numeric children. Fallback: flat `<name>_<index>` naming.** Both detected at JSX side; importer trusts explicit `kind`. |
| D10 | Frame size mismatch | **Importer pads each frame to bbox of largest, transparent fill, via Pillow.** |

## Out of scope

- Re-export Blender → PSD (one-way pipeline only).
- Photoshop UI integration beyond the JSX exporter (one-shot script, no panel).
- Live link Blender ↔ Photoshop (backlog).
- `.psd` direct read (D7).

## Successor considerations

- **SPEC 007** gains a `simple_psd/` fixture after this SPEC lands - a tiny PSD source + JSX-exported manifest + expected post-import `.blend`. Locked in SPEC 007 STUDY.md "Successor considerations".
- **SPEC 004 (slots)** can use PSD layer groups as slot hints once both SPECs ship. Group naming convention TBD when SPEC 004 opens.

## Surface (LOC estimate)

| Wave | LOC | Files |
| --- | --- | --- |
| 6.0 - manifest schema + parser | ~150 | `schemas/psd_manifest.schema.json`, `apps/blender/core/psd_manifest.py`, `apps/blender/tests/test_psd_manifest.py` |
| 6.1 - JSX exporter v1 | ~80 | bump `apps/photoshop/proscenio_export.jsx` to emit format_version + kind + frames |
| 6.2 - naming convention parser | ~120 | `apps/blender/core/psd_naming.py`, `apps/blender/tests/test_psd_naming.py` |
| 6.3 - importer core | ~250 | `apps/blender/importers/photoshop/__init__.py` (manifest reader, plane stamper, material builder, spritesheet composer) |
| 6.4 - operator + panel | ~100 | `apps/blender/operators/import_photoshop.py`, panel button in `apps/blender/panels/__init__.py` |
| 6.5 - fixture `simple_psd/` | ~60 | tiny PSD source + JSX manifest + expected post-import `.blend` (and golden `.proscenio` via `export_proscenio.py`) |

Total: ~760 LOC + manifest schema lock-in.

PR strategy:

1. **PR-A - foundation**: Wave 6.0 + 6.1 + 6.2. Branch `feat/spec-006.0-foundation`. Deliverable: schema lockdown, JSX bumped, naming parser tested.
2. **PR-B - importer**: Wave 6.3 + 6.4. Branch `feat/spec-006.1-importer`. Deliverable: working operator end-to-end.
3. **PR-C - fixture**: Wave 6.5. Branch `feat/spec-006.2-simple-psd-fixture`. Deliverable: `examples/generated/simple_psd/` end-to-end test.
