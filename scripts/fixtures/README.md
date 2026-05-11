# scripts/fixtures/

Build scripts for the SPEC 007 + SPEC 006 fixtures under `examples/`. Organised **by fixture**, not by tool, so finding "the script that builds the doll PSD manifest" is one folder hop.

## Layout

```text
scripts/fixtures/
├── _shared/
│   ├── _draw.py                    Pillow shape rasterizer (used by every Pillow-driven fixture)
│   └── export_proscenio.py         Bpy: open <fixture>.blend, write godot/<fixture>.expected.proscenio
├── doll/
│   ├── render_layers.py            Bpy: doll.blend  -> 01_to_photoshop/render_layers/*.png (Workbench flat)
│   ├── export_psd_manifest.py      Bpy: doll.blend  -> 01_to_photoshop/doll.photoshop_manifest.json
│   └── preview_pieces.py           Pillow: 01_to_photoshop/render_layers/*.png -> .../pieces_sheet.png
├── blink_eyes/
│   ├── draw_layers.py              Pillow -> pillow_layers/eye_0..3.png + eye_spritesheet.png
│   └── build_blend.py              Bpy: load spritesheet, build blink_eyes.blend
├── mouth_drive/
│   ├── draw_layers.py              Pillow -> pillow_layers/mouth_0..3.png + mouth_spritesheet.png
│   └── build_blend.py              Bpy: 2-bone armature (mouth_pos + mouth_drive) + driver + action -> mouth_drive.blend
├── slot_swap/
│   ├── draw_layers.py              Pillow -> pillow_layers/arm.png + club.png + sword.png
│   └── build_blend.py              Bpy: 1-bone armature + arm mesh + slot Empty + 2 attachments + swing+swap actions -> slot_swap.blend
├── shared_atlas/
│   ├── draw_atlas.py               Pillow -> atlas.png (256x256, three colored quadrants)
│   └── build_blend.py              Bpy: load atlas, build shared_atlas.blend (3 sliced quads)
├── simple_psd/
│   ├── draw_layers.py              Pillow -> pillow_layers/square.png + arrow_0..3.png + arrow_spritesheet.png
│   └── build_blend.py              Bpy: run addon importer on simple_psd.photoshop_manifest.json -> simple_psd.blend
├── slot_cycle/
│   ├── draw_layers.py              Pillow -> pillow_layers/attachment_red|green|blue.png (32x32 each)
│   └── build_blend.py              Bpy: armature + slot Empty + 3 polygon attachments + cycle action -> slot_cycle.blend
└── atlas_pack/
    ├── draw_layers.py              Pillow -> pillow_layers/sprite_1..9.png (32x32 each, distinct color + digit)
    └── build_blend.py              Bpy: 1-bone armature + 9 quads + 9 materials/textures (3x3 grid) -> atlas_pack.blend
```

## Script -> output map

| Fixture | Script | Input | Output |
| --- | --- | --- | --- |
| doll | `doll/render_layers.py` | `examples/authored/doll/doll.blend` | `examples/authored/doll/01_to_photoshop/render_layers/*.png` |
| doll | `doll/preview_pieces.py` | `examples/authored/doll/01_to_photoshop/render_layers/*.png` | `examples/authored/doll/01_to_photoshop/render_layers/pieces_sheet.png` |
| doll | `doll/export_psd_manifest.py` | `examples/authored/doll/doll.blend` | `examples/authored/doll/01_to_photoshop/doll.photoshop_manifest.json` |
| doll | `_shared/export_proscenio.py` | `examples/authored/doll/doll.blend` | `examples/authored/doll/doll.expected.proscenio` |
| blink_eyes | `blink_eyes/draw_layers.py` | (Pillow primitives) | `examples/blink_eyes/pillow_layers/eye_0..3.png` + `eye_spritesheet.png` |
| blink_eyes | `blink_eyes/build_blend.py` | `examples/blink_eyes/pillow_layers/eye_spritesheet.png` | `examples/blink_eyes/blink_eyes.blend` |
| blink_eyes | `_shared/export_proscenio.py` | `examples/blink_eyes/blink_eyes.blend` | `examples/blink_eyes/blink_eyes.expected.proscenio` |
| mouth_drive | `mouth_drive/draw_layers.py` | (Pillow primitives) | `examples/mouth_drive/pillow_layers/mouth_0..3.png` + `mouth_spritesheet.png` |
| mouth_drive | `mouth_drive/build_blend.py` | `examples/mouth_drive/pillow_layers/mouth_spritesheet.png` | `examples/mouth_drive/mouth_drive.blend` |
| mouth_drive | `_shared/export_proscenio.py` | `examples/mouth_drive/mouth_drive.blend` | `examples/mouth_drive/mouth_drive.expected.proscenio` |
| slot_swap | `slot_swap/draw_layers.py` | (Pillow primitives) | `examples/slot_swap/pillow_layers/arm.png` + `club.png` + `sword.png` |
| slot_swap | `slot_swap/build_blend.py` | `examples/slot_swap/pillow_layers/*.png` | `examples/slot_swap/slot_swap.blend` |
| slot_swap | `_shared/export_proscenio.py` | `examples/slot_swap/slot_swap.blend` | `examples/slot_swap/slot_swap.expected.proscenio` |
| shared_atlas | `shared_atlas/draw_atlas.py` | (Pillow primitives) | `examples/shared_atlas/atlas.png` |
| shared_atlas | `shared_atlas/build_blend.py` | `examples/shared_atlas/atlas.png` | `examples/shared_atlas/shared_atlas.blend` |
| shared_atlas | `_shared/export_proscenio.py` | `examples/shared_atlas/shared_atlas.blend` | `examples/shared_atlas/shared_atlas.expected.proscenio` |
| simple_psd | `simple_psd/draw_layers.py` | (Pillow primitives) | `examples/simple_psd/pillow_layers/square.png` + `arrow_0..3.png` + `arrow_spritesheet.png` |
| simple_psd | `simple_psd/build_blend.py` | `examples/simple_psd/simple_psd.photoshop_manifest.json` | `examples/simple_psd/simple_psd.blend` |
| simple_psd | `_shared/export_proscenio.py` | `examples/simple_psd/simple_psd.blend` | `examples/simple_psd/simple_psd.expected.proscenio` |
| slot_cycle | `slot_cycle/draw_layers.py` | (Pillow primitives) | `examples/slot_cycle/pillow_layers/attachment_red.png` + `_green.png` + `_blue.png` |
| slot_cycle | `slot_cycle/build_blend.py` | `examples/slot_cycle/pillow_layers/*.png` | `examples/slot_cycle/slot_cycle.blend` |
| slot_cycle | `_shared/export_proscenio.py` | `examples/slot_cycle/slot_cycle.blend` | `examples/slot_cycle/slot_cycle.expected.proscenio` |
| atlas_pack | `atlas_pack/draw_layers.py` | (Pillow primitives) | `examples/atlas_pack/pillow_layers/sprite_1..9.png` |
| atlas_pack | `atlas_pack/build_blend.py` | `examples/atlas_pack/pillow_layers/*.png` | `examples/atlas_pack/atlas_pack.blend` |
| atlas_pack | `_shared/export_proscenio.py` | `examples/atlas_pack/atlas_pack.blend` | `examples/atlas_pack/atlas_pack.expected.proscenio` |

## Run modes

- `_shared/_draw.py` is a library, not an entry point.
- `_shared/export_proscenio.py` runs inside Blender: `blender --background <fixture>.blend --python scripts/fixtures/_shared/export_proscenio.py`.
- `doll/*.py` mostly run inside Blender (`render_layers.py`, `export_psd_manifest.py`); `preview_pieces.py` is pure Python + Pillow (`python scripts/fixtures/doll/preview_pieces.py`).
- `blink_eyes/draw_layers.py` and `shared_atlas/draw_atlas.py` are pure Python + Pillow.
- `*/build_blend.py` runs inside Blender (`blender --background --python scripts/fixtures/<fixture>/build_blend.py`).

## Why subfolders by fixture

Each fixture has its own input/output rules (a `.blend` lives at `examples/<fixture>/`, layers live under `render_layers/` or `pillow_layers/`, goldens under `godot/`). Bundling the fixture's scripts together makes it obvious which file generates which output without grepping. The `_shared/` package holds the only cross-fixture utilities (the Pillow rasterizer + the goldenwriter).

## Conventions for new pixel-art fixtures

When adding a new isolated / minimal fixture (the kind that exercises ONE feature end-to-end -- like `blink_eyes` for sprite_frame tracks or `mouth_drive` for Drive-from-Bone), follow the patterns below. The reference implementations are `blink_eyes/build_blend.py` and `mouth_drive/build_blend.py`; copy from them rather than the older fixtures, which carry pre-convention quirks.

### Pillow side -- `draw_layers.py`

- Pure Python, no Blender. Run with `py scripts/fixtures/<name>/draw_layers.py`.
- Use `_shared/_draw.py` primitives (`Canvas`, `rect`, `circle`, `capsule`, `triangle`, `trapezoid`).
- Emit per-frame PNGs (one per cell) AND the concatenated spritesheet. The per-frame PNGs are documentation; the spritesheet is what the .blend references.
- Cells default to 32x32 px. Spritesheet is `frame_w * hframes` by `frame_h * vframes`. Layout horizontal first (`vframes=1` covers most cases).
- Keep visual differences between frames clearly distinguishable -- the goal is validating the pipeline, not winning art awards.

### Blender side -- `build_blend.py`

- Run with `blender --background --python scripts/fixtures/<name>/build_blend.py` (no input .blend; the script wipes and rebuilds from scratch).
- `_wipe_blend()` clears `objects`, `meshes`, `armatures`, `materials`, `images`, `actions` first so re-runs are deterministic.
- **Bone orientation**: tail along **-Y** from head (so the bone points TOWARD the Front Orthographic camera, which sits at +Y looking down -Y). Bones appear as small octahedral dots from the front -- the Spine / 2D-cutout convention. Authoring rotations: pose-mode `R Y` rotates around the camera axis (visible 2D rotation); pose-mode `R Z` is for spin-in-plan-view; pose-mode `R X` tilts out of plane.
- **Image filepath relativeization**: after `bpy.ops.wm.save_as_mainfile(...)`, walk `bpy.data.images` and assign `img.filepath = bpy.path.relpath(...)`, then `bpy.ops.wm.save_mainfile()` again to persist. Without this, the absolute path bakes into the .blend and the fixture breaks on any other machine. Pattern:

  ```python
  def _rewrite_image_to_relpath() -> None:
      rel = bpy.path.relpath(str(SHEET_PATH))
      for img in bpy.data.images:
          if img.filepath:
              img.filepath = rel
  ```

- **UV layout for asymmetric content**: in Blender's Front Orthographic view, the camera convention maps world `+X` to screen LEFT. A naive UV mapping (`uv[v0] = (0,0)` at vertex `(-w/2, 0, -h/2)`) renders the PIL image MIRRORED horizontally on screen. Symmetric sprites (`blink_eyes` eye, `mouth_drive` mouth, `slot_swap` arm with horizontally-symmetric club / sword) hide this. Asymmetric content (digits, text, anything with handedness) needs the U axis flipped:

  ```python
  # Standard quad with face normal toward camera (-Y):
  vertices = [
      (-w/2, 0, -h/2),  # v0
      (+w/2, 0, -h/2),  # v1
      (+w/2, 0, +h/2),  # v2
      (-w/2, 0, +h/2),  # v3
  ]
  faces = [(0, 1, 2, 3)]
  # U flipped (1.0 / 0.0 swapped) so PIL image renders unmirrored
  # in Front Ortho. See atlas_pack/build_blend.py for the canonical
  # example.
  uv.data[0].uv = (1.0, 0.0)
  uv.data[1].uv = (0.0, 0.0)
  uv.data[2].uv = (0.0, 1.0)
  uv.data[3].uv = (1.0, 1.0)
  ```

  The existing symmetric fixtures keep the un-flipped UVs because regenerating their goldens for a cosmetic-only fix is busywork. New fixtures should adopt the flipped layout by default.

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
  _save_blend()                    # save_as_mainfile -- sets the .blend's path
  _rewrite_image_to_relpath()      # rewrite image filepaths to // form
  bpy.ops.wm.save_mainfile()       # persist the rewritten paths
  ```

### Test integration

- Drop a `<name>.expected.proscenio` golden next to the `.blend` -- `apps/blender/tests/run_tests.py` discovers fixtures via `examples/**/*.expected.proscenio` recursive glob (so nested `examples/authored/<name>/` works too).
- Goldens regenerate by running the writer against the rebuilt `.blend`. The `_shared/export_proscenio.py` script handles this.
- Include the fixture in the global headless run before opening a PR: `blender --background --python apps/blender/tests/run_tests.py` should print `N/N fixture(s) passed`.
