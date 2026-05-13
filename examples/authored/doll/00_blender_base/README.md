# 00 - Blender base

**Source of truth.** Authored `.blend` + the derived inputs that the
Photoshop import step (`../01_photoshop_base/`) consumes.

## Contents

| File | Origin | Notes |
| --- | --- | --- |
| `doll_base.blend` | hand-authored | the canonical doll geometry / materials |
| `doll_base.blend1` | Blender autosave | gitignored |
| `doll_base.photoshop_manifest.json` | `../scripts/export_psd_manifest.py` | SPEC 006 v1 / SPEC 011 v2 manifest the PS importer reads |
| `render_layers/<name>.png` | `../scripts/render_layers.py` | one PNG per mesh (front-ortho, Workbench flat). Drives the PSD placement step. |
| `render_layers/pieces_sheet.png` | `../scripts/preview_pieces.py` | contact-sheet preview (reviewer aid; not consumed by the pipeline) |
| `doll_base.expected.proscenio` | `scripts/fixtures/_shared/export_proscenio.py` | CI golden for the **direct Blender -> Godot writer** (not part of the artist workflow; protects the addon writer from regression) |

## Regenerate

From the repo root:

```sh
# render per-mesh PNG layers
blender --background examples/authored/doll/00_blender_base/doll_base.blend \
    --python examples/authored/doll/scripts/render_layers.py

# emit the SPEC 011 v2 PSD manifest
blender --background examples/authored/doll/00_blender_base/doll_base.blend \
    --python examples/authored/doll/scripts/export_psd_manifest.py

# (optional) contact sheet for visual review
python examples/authored/doll/scripts/preview_pieces.py

# CI golden for the direct Blender -> Godot path
blender --background examples/authored/doll/00_blender_base/doll_base.blend \
    --python scripts/fixtures/_shared/export_proscenio.py
```

## Outputs going downstream

Step 01 (`../01_photoshop_base/`) consumes:

- `doll_base.photoshop_manifest.json` (path layout + per-layer bbox)
- `render_layers/<name>.png` (texture for each layer placed inside the PSD)

Both paths are relative to this folder; the manifest references PNGs as `render_layers/<name>.png`.
