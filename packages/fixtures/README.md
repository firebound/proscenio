# packages/fixtures/

Build scripts for the fixture set + the photoshop importer fixtures under `examples/`. Organised **by fixture**, not by tool, so finding "the script that builds the doll PSD manifest" is one folder hop.

## Layout

```text
packages/fixtures/
├── _shared/
│   ├── _draw.py                    Pillow shape rasterizer (used by every Pillow-driven fixture)
│   └── export_proscenio.py         Bpy: open <fixture>.blend, write godot/<fixture>.expected.proscenio
├── doll/                            (moved to examples/authored/doll/scripts/)
│   ├── render_layers.py            Bpy: doll_base.blend  → 00_blender_base/render_layers/*.png (Workbench flat)
│   ├── export_psd_manifest.py      Bpy: doll_base.blend  → 00_blender_base/doll_base.photoshop_manifest.json
│   └── preview_pieces.py           Pillow: 00_blender_base/render_layers/*.png → .../pieces_sheet.png
├── blink_eyes/
│   ├── draw_layers.py              Pillow → pillow_layers/eye_0..3.png + eye_spritesheet.png
│   └── build_blend.py              Bpy: load spritesheet, build blink_eyes.blend
├── mouth_drive/
│   ├── draw_layers.py              Pillow → pillow_layers/mouth_0..3.png + mouth_spritesheet.png
│   └── build_blend.py              Bpy: 2-bone armature (mouth_pos + mouth_drive) + driver + action → mouth_drive.blend
├── slot_swap/
│   ├── draw_layers.py              Pillow → pillow_layers/arm.png + club.png + sword.png
│   └── build_blend.py              Bpy: 1-bone armature + arm mesh + slot Empty + 2 attachments + swing+swap actions → slot_swap.blend
├── shared_atlas/
│   ├── draw_atlas.py               Pillow → atlas.png (256x256, three colored quadrants)
│   └── build_blend.py              Bpy: load atlas, build shared_atlas.blend (3 sliced quads)
├── simple_psd/
│   ├── draw_layers.py              Pillow → pillow_layers/square.png + arrow_0..3.png + arrow_spritesheet.png
│   └── build_blend.py              Bpy: run addon importer on simple_psd.photoshop_manifest.json → simple_psd.blend
├── slot_cycle/
│   ├── draw_layers.py              Pillow → pillow_layers/attachment_red|green|blue.png (32x32 each)
│   └── build_blend.py              Bpy: armature + slot Empty + 3 polygon attachments + cycle action → slot_cycle.blend
└── atlas_pack/
    ├── draw_layers.py              Pillow → pillow_layers/sprite_1..9.png (32x32 each, distinct color + digit)
    └── build_blend.py              Bpy: 1-bone armature + 9 quads + 9 materials/textures (3x3 grid) → atlas_pack.blend
```

## Script → output map

| Fixture | Script | Input | Output |
| --- | --- | --- | --- |
| doll | `examples/authored/doll/scripts/render_layers.py` | `examples/authored/doll/00_blender_base/doll_base.blend` | `examples/authored/doll/00_blender_base/render_layers/*.png` |
| doll | `examples/authored/doll/scripts/preview_pieces.py` | `examples/authored/doll/00_blender_base/render_layers/*.png` | `examples/authored/doll/00_blender_base/render_layers/pieces_sheet.png` |
| doll | `examples/authored/doll/scripts/export_psd_manifest.py` | `examples/authored/doll/00_blender_base/doll_base.blend` | `examples/authored/doll/00_blender_base/doll_base.photoshop_manifest.json` |
| doll | `_shared/export_proscenio.py` | `examples/authored/doll/00_blender_base/doll_base.blend` | `examples/authored/doll/00_blender_base/doll_base.expected.proscenio` |
| blink_eyes | `blink_eyes/draw_layers.py` | (Pillow primitives) | `examples/generated/blink_eyes/pillow_layers/eye_0..3.png` + `eye_spritesheet.png` |
| blink_eyes | `blink_eyes/build_blend.py` | `examples/generated/blink_eyes/pillow_layers/eye_spritesheet.png` | `examples/generated/blink_eyes/blink_eyes.blend` |
| blink_eyes | `_shared/export_proscenio.py` | `examples/generated/blink_eyes/blink_eyes.blend` | `examples/generated/blink_eyes/blink_eyes.expected.proscenio` |
| mouth_drive | `mouth_drive/draw_layers.py` | (Pillow primitives) | `examples/generated/mouth_drive/pillow_layers/mouth_0..3.png` + `mouth_spritesheet.png` |
| mouth_drive | `mouth_drive/build_blend.py` | `examples/generated/mouth_drive/pillow_layers/mouth_spritesheet.png` | `examples/generated/mouth_drive/mouth_drive.blend` |
| mouth_drive | `_shared/export_proscenio.py` | `examples/generated/mouth_drive/mouth_drive.blend` | `examples/generated/mouth_drive/mouth_drive.expected.proscenio` |
| slot_swap | `slot_swap/draw_layers.py` | (Pillow primitives) | `examples/generated/slot_swap/pillow_layers/arm.png` + `club.png` + `sword.png` |
| slot_swap | `slot_swap/build_blend.py` | `examples/generated/slot_swap/pillow_layers/*.png` | `examples/generated/slot_swap/slot_swap.blend` |
| slot_swap | `_shared/export_proscenio.py` | `examples/generated/slot_swap/slot_swap.blend` | `examples/generated/slot_swap/slot_swap.expected.proscenio` |
| shared_atlas | `shared_atlas/draw_atlas.py` | (Pillow primitives) | `examples/generated/shared_atlas/atlas.png` |
| shared_atlas | `shared_atlas/build_blend.py` | `examples/generated/shared_atlas/atlas.png` | `examples/generated/shared_atlas/shared_atlas.blend` |
| shared_atlas | `_shared/export_proscenio.py` | `examples/generated/shared_atlas/shared_atlas.blend` | `examples/generated/shared_atlas/shared_atlas.expected.proscenio` |
| simple_psd | `simple_psd/draw_layers.py` | (Pillow primitives) | `examples/generated/simple_psd/pillow_layers/square.png` + `arrow_0..3.png` + `arrow_spritesheet.png` |
| simple_psd | `simple_psd/build_blend.py` | `examples/generated/simple_psd/simple_psd.photoshop_manifest.json` | `examples/generated/simple_psd/simple_psd.blend` |
| simple_psd | `_shared/export_proscenio.py` | `examples/generated/simple_psd/simple_psd.blend` | `examples/generated/simple_psd/simple_psd.expected.proscenio` |
| slot_cycle | `slot_cycle/draw_layers.py` | (Pillow primitives) | `examples/generated/slot_cycle/pillow_layers/attachment_red.png` + `_green.png` + `_blue.png` |
| slot_cycle | `slot_cycle/build_blend.py` | `examples/generated/slot_cycle/pillow_layers/*.png` | `examples/generated/slot_cycle/slot_cycle.blend` |
| slot_cycle | `_shared/export_proscenio.py` | `examples/generated/slot_cycle/slot_cycle.blend` | `examples/generated/slot_cycle/slot_cycle.expected.proscenio` |
| atlas_pack | `atlas_pack/draw_layers.py` | (Pillow primitives) | `examples/generated/atlas_pack/pillow_layers/sprite_1..9.png` |
| atlas_pack | `atlas_pack/build_blend.py` | `examples/generated/atlas_pack/pillow_layers/*.png` | `examples/generated/atlas_pack/atlas_pack.blend` |
| atlas_pack | `_shared/export_proscenio.py` | `examples/generated/atlas_pack/atlas_pack.blend` | `examples/generated/atlas_pack/atlas_pack.expected.proscenio` |

## Run modes

- `_shared/_draw.py` is a library, not an entry point.
- `_shared/export_proscenio.py` runs inside Blender: `blender --background <fixture>.blend --python packages/fixtures/_shared/export_proscenio.py`.
- `examples/authored/doll/scripts/*.py` mostly run inside Blender (`render_layers.py`, `export_psd_manifest.py`); `preview_pieces.py` is pure Python + Pillow (`python examples/authored/doll/scripts/preview_pieces.py`).
- `blink_eyes/draw_layers.py` and `shared_atlas/draw_atlas.py` are pure Python + Pillow.
- `*/build_blend.py` runs inside Blender (`blender --background --python packages/fixtures/<fixture>/build_blend.py`).

## Why subfolders by fixture

Each fixture has its own input/output rules (a `.blend` lives at `examples/<fixture>/`, layers live under `render_layers/` or `pillow_layers/`, goldens under `godot/`). Bundling the fixture's scripts together makes it obvious which file generates which output without grepping. The `_shared/` package holds the only cross-fixture utilities (the Pillow rasterizer + the goldenwriter).

## Conventions for new pixel-art fixtures

When adding a new isolated / minimal fixture (the kind that exercises ONE feature end-to-end - like `blink_eyes` for sprite_frame tracks or `mouth_drive` for Drive-from-Bone), follow the patterns below. The reference implementations are `blink_eyes/build_blend.py` and `mouth_drive/build_blend.py`; copy from them rather than the older fixtures, which carry pre-convention quirks.

### Pillow side - `draw_layers.py`

- Pure Python, no Blender. Run with `py packages/fixtures/<name>/draw_layers.py`.
- Use `_shared/_draw.py` primitives (`Canvas`, `rect`, `circle`, `capsule`, `triangle`, `trapezoid`).
- Emit per-frame PNGs (one per cell) AND the concatenated spritesheet. The per-frame PNGs are documentation; the spritesheet is what the .blend references.
- Cells default to 32x32 px. Spritesheet is `frame_w * hframes` by `frame_h * vframes`. Layout horizontal first (`vframes=1` covers most cases).
- Keep visual differences between frames clearly distinguishable - the goal is validating the pipeline, not winning art awards.

### Blender side - `build_blend.py`

- Run with `blender --background --python packages/fixtures/<name>/build_blend.py` (no input .blend; the script wipes and rebuilds from scratch).
- `_wipe_blend()` clears `objects`, `meshes`, `armatures`, `materials`, `images`, `actions` first so re-runs are deterministic.
- **Axis convention**: the Front Orthographic camera sits at **-Y looking toward +Y**; **+Z is up**, **+X is screen RIGHT**. The XZ plane is the picture plane; Y is depth (into the screen is +Y, away from camera). The exporter projects `world_to_godot_xy(p) = (p.x*ppu, -p.z*ppu)` (drops Y, flips Z because Godot Y is down).
- **Bone orientation**: tail along **+Y** from head (INTO the screen, away from the camera). A **-Y** tail makes Blender bone-parenting rotate every bone-parented child 180deg about Z, which MIRRORS the cutout in X (reversed order + flipped glyphs) in both Blender world space and the export - this was the root cause fixed in spec 039. `+Y` keeps bone-parented quads un-flipped, in the XZ picture plane, facing the camera (`atlas_pack` is the canonical proof: a 3x3 grid of digits 1-9 reads correctly). The bone exports at angle 0 either way (it is runtime-invisible). `+Z`/`+X` tails tilt the quad out of plane and collapse it to a line on import. Skinned meshes (under an armature with weights, NOT bone-parented) are exempt - they may use in-plane bones (`automesh` does).
- **Image filepath relativeization**: after `bpy.ops.wm.save_as_mainfile(...)`, walk `bpy.data.images` and assign `img.filepath = bpy.path.relpath(...)`, then `bpy.ops.wm.save_mainfile()` again to persist. Without this, the absolute path bakes into the .blend and the fixture breaks on any other machine. Pattern:

  ```python
  def _rewrite_image_to_relpath() -> None:
      rel = bpy.path.relpath(str(SHEET_PATH))
      for img in bpy.data.images:
          if img.filepath:
              img.filepath = rel
  ```

- **UV layout**: with the `+Y` bone convention above, the standard quad maps directly - `+X` is screen RIGHT, so no U-flip is needed. `atlas_pack` proves it: each cell uses direct UVs (`uv[v0] = (0,0)` at `(-w/2, 0, -h/2)`) and the digits 1-9 read correctly, un-mirrored, in both Blender and Godot.

  ```python
  # Standard quad in the XZ picture plane, face normal toward the camera (-Y):
  vertices = [
      (-w/2, 0, -h/2),  # v0 bottom-left
      (+w/2, 0, -h/2),  # v1 bottom-right
      (+w/2, 0, +h/2),  # v2 top-right
      (-w/2, 0, +h/2),  # v3 top-left
  ]
  faces = [(0, 1, 2, 3)]
  # Direct UVs - no flip. See atlas_pack/build_blend.py.
  uv.data[0].uv = (0.0, 0.0)
  uv.data[1].uv = (1.0, 0.0)
  uv.data[2].uv = (1.0, 1.0)
  uv.data[3].uv = (0.0, 1.0)
  ```

  (Historical note: before spec 039 the fixtures used `-Y` bones, which mirrored every bone-parented cutout in X; the old advice to "flip the U axis" was a workaround for that mirror. With `+Y` bones the mirror is gone, so the flip is removed.)
- **Sprite quads (multi-frame)**: a `sprite` element renders in Godot as a `Sprite2D` showing ONE frame at its native pixel size (`region_px / hframes`), while Blender shows the whole authored quad. To keep the BOUNDS matching, size the quad `w = frame_px / PIXELS_PER_UNIT` (see `blink_eyes`). Sprite UVs do NOT enter the golden (only region + frame metadata do), so they affect the Blender preview only; map them onto the sprite's atlas region so the preview shows the right cells. Pixel-exact Blender==Godot is not achievable for multi-frame sprites by design - the invariant is geometry/bounds, not pixels.

- **Image Texture interpolation**: set `tex.interpolation = "Closest"` on every `ShaderNodeTexImage`. Blender defaults to bilinear (`"Linear"`), which smears 32x32 pixel-art cells in Eevee's Material Preview. Closest (nearest-neighbor) keeps edges crisp:

  ```python
  tex = nt.nodes.new(type="ShaderNodeTexImage")
  tex.image = bpy.data.images.load(str(SHEET_PATH), check_existing=True)
  tex.interpolation = "Closest"
  ```

- **PropertyGroup + Custom Property mirror**: write both `obj.proscenio.<field>` (when the addon is registered) and `obj["proscenio_<field>"]` (always). The headless writer reads CPs when the addon is not loaded; the PG path is for the panel UX.
- **Driver wiring** (when the fixture exercises Drive-from-Bone): mirror the panel operator's defaults exactly --
  - `target.transform_type = "ROT_Y"` (camera-axis rotation in Blender Front Ortho)
  - `target.transform_space = "WORLD_SPACE"` for `ROT_*`, `"LOCAL_SPACE"` for `LOC_*`
  - `target.rotation_mode = "XYZ"` (Euler in radians, not quaternion)
  - Strip the default seed keyframes after `driver_add(...)`:

    ```python
    fcurve = sprite_obj.driver_add("proscenio.frame")
    while fcurve.keyframe_points:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0])
    ```

- **Action keyframes**: when animating bone rotation that drives the sprite, keyframe `pose_bone.rotation_euler[1]` (Y component) at `index=1`. `R Y` in pose mode + ROT_Y driver picks it up cleanly.
- **Save sequence at the end of `main()`**:

  ```python
  _save_blend()                    # save_as_mainfile - sets the .blend's path
  _rewrite_image_to_relpath()      # rewrite image filepaths to // form
  bpy.ops.wm.save_mainfile()       # persist the rewritten paths
  ```

### Test integration

- Drop a `<name>.expected.proscenio` golden next to the `.blend` - `apps/blender/tests/run_tests.py` discovers fixtures via `examples/**/*.expected.proscenio` recursive glob (so nested `examples/authored/<name>/` works too).
- Goldens regenerate by running the writer against the rebuilt `.blend`. The `_shared/export_proscenio.py` script handles this.
- Include the fixture in the global headless run before opening a PR: `blender --background --python apps/blender/tests/run_tests.py` should print `N/N fixture(s) passed`.
