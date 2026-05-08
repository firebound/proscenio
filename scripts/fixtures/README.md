# scripts/fixtures/

Build scripts for the SPEC 007 + SPEC 006 fixtures under `examples/`. Organised **by fixture**, not by tool, so finding "the script that builds the doll PSD manifest" is one folder hop.

## Layout

```text
scripts/fixtures/
├── _shared/
│   ├── _draw.py                    Pillow shape rasterizer (used by every Pillow-driven fixture)
│   └── export_proscenio.py         Bpy: open <fixture>.blend, write godot/<fixture>.expected.proscenio
├── doll/
│   ├── render_layers.py            Bpy: doll.blend  -> render_layers/*.png (Workbench flat)
│   ├── export_psd_manifest.py      Bpy: doll.blend  -> photoshop_export/doll.psd_manifest.json
│   └── preview_pieces.py           Pillow: render_layers/*.png -> render_layers/pieces_sheet.png
├── blink_eyes/
│   ├── draw_layers.py              Pillow -> pillow_layers/eye_0..3.png + eye_spritesheet.png
│   └── build_blend.py              Bpy: load spritesheet, build blink_eyes.blend
└── shared_atlas/
    ├── draw_atlas.py               Pillow -> atlas.png (256x256, three colored quadrants)
    └── build_blend.py              Bpy: load atlas, build shared_atlas.blend (3 sliced quads)
```

## Script -> output map

| Fixture | Script | Input | Output |
| --- | --- | --- | --- |
| doll | `doll/render_layers.py` | `examples/doll/doll.blend` | `examples/doll/render_layers/*.png` |
| doll | `doll/preview_pieces.py` | `examples/doll/render_layers/*.png` | `examples/doll/render_layers/pieces_sheet.png` |
| doll | `doll/export_psd_manifest.py` | `examples/doll/doll.blend` | `examples/doll/doll.photoshop_manifest.json` |
| doll | `_shared/export_proscenio.py` | `examples/doll/doll.blend` | `examples/doll/doll.expected.proscenio` |
| blink_eyes | `blink_eyes/draw_layers.py` | (Pillow primitives) | `examples/blink_eyes/pillow_layers/eye_0..3.png` + `eye_spritesheet.png` |
| blink_eyes | `blink_eyes/build_blend.py` | `examples/blink_eyes/pillow_layers/eye_spritesheet.png` | `examples/blink_eyes/blink_eyes.blend` |
| blink_eyes | `_shared/export_proscenio.py` | `examples/blink_eyes/blink_eyes.blend` | `examples/blink_eyes/blink_eyes.expected.proscenio` |
| shared_atlas | `shared_atlas/draw_atlas.py` | (Pillow primitives) | `examples/shared_atlas/atlas.png` |
| shared_atlas | `shared_atlas/build_blend.py` | `examples/shared_atlas/atlas.png` | `examples/shared_atlas/shared_atlas.blend` |
| shared_atlas | `_shared/export_proscenio.py` | `examples/shared_atlas/shared_atlas.blend` | `examples/shared_atlas/shared_atlas.expected.proscenio` |

## Run modes

- `_shared/_draw.py` is a library, not an entry point.
- `_shared/export_proscenio.py` runs inside Blender: `blender --background <fixture>.blend --python scripts/fixtures/_shared/export_proscenio.py`.
- `doll/*.py` mostly run inside Blender (`render_layers.py`, `export_psd_manifest.py`); `preview_pieces.py` is pure Python + Pillow (`python scripts/fixtures/doll/preview_pieces.py`).
- `blink_eyes/draw_layers.py` and `shared_atlas/draw_atlas.py` are pure Python + Pillow.
- `*/build_blend.py` runs inside Blender (`blender --background --python scripts/fixtures/<fixture>/build_blend.py`).

## Why subfolders by fixture

Each fixture has its own input/output rules (a `.blend` lives at `examples/<fixture>/`, layers live under `render_layers/` or `pillow_layers/`, goldens under `godot/`). Bundling the fixture's scripts together makes it obvious which file generates which output without grepping. The `_shared/` package holds the only cross-fixture utilities (the Pillow rasterizer + the goldenwriter).
