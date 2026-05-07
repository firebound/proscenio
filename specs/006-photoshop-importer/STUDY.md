# SPEC 006 — Photoshop → Blender importer

**Status**: stub. Captures the design surface so we don't lose context. Real decisions get locked when the SPEC actually starts.

## Problem

Today the Photoshop → Blender step is **manual**: the JSX exporter writes per-layer PNGs + a manifest JSON, but there is no Blender-side importer. Users have to:

1. Run JSX exporter in Photoshop.
2. Open Blender, manually create one mesh per PNG, position it, link the texture, build the armature, parent meshes to bones.

This is the missing leg of the pipeline. SPEC 006 closes it.

## Reference: similar tools

- **COA Tools 2** — has a "Sprite import from JSON" operator that reads its own JSON format and stamps planes.
- **DUIK Auto-Rig** — auto-generates a rig from layered PSD names (After Effects, but the pattern transfers).
- **Spine** — imports `.psd` directly via Photoshop bridge or `.json` manifest from the bundled PSD-to-Spine script.

The pattern is "manifest tells the importer where each layer goes, what its naming convention implies, and how it relates to other layers".

## JSX exporter manifest contract (already shipping today)

The Photoshop side writes (roughly):

```json
{
  "format_version": 1,
  "psd_path": "firebound.psd",
  "psd_size": [1024, 1024],
  "layers": [
    {
      "name": "head",
      "path": "layers/head.png",
      "offset_px": [240, 180],
      "size_px": [128, 128],
      "z_order": 0
    },
    ...
  ]
}
```

(Real shape may differ — verify when the SPEC starts.)

## Design surface

Naming conventions the importer interprets (locked in SPEC 007 D4 + future):

- `<name>_<index>` (e.g. `eye_0`, `eye_1`, `eye_2`) — group as a sprite_frame mesh with `hframes = N`. Indexes ≥ 0 contiguous.
- `<name>` (no index suffix) — polygon mesh, 1 sprite = 1 PNG.
- `<group>/<name>` (PSD group) — possibly group hint for slots (SPEC 004 territory).
- `<name>.<modifier>` (e.g. `body.front`, `body.back`) — possibly slot attachments.

Importer responsibilities:

1. Read manifest at user-specified path.
2. For each layer (or layer group when grouping convention applies):
   - Stamp a plane mesh sized to `size_px` / `pixels_per_unit`, positioned at `offset_px`-derived world coords.
   - Create / link a material whose image-textured node points at the layer's PNG.
   - Tag the mesh's `proscenio.sprite_type` based on naming convention.
3. Optionally:
   - Auto-pack atlas via the existing Pack Atlas operator (SPEC 005.1.c.2).
   - Build a stub armature + parent meshes by Z-order.
4. Surface a panel button "Import Photoshop Manifest" + file picker.

## Decisions to lock when SPEC opens

- **D1** — manifest format: keep current JSX shape, or evolve schema? (probably evolve — current shape is not future-proof for groups / slot hints).
- **D2** — atlas: importer auto-packs, leaves per-PNG, or asks user? (pattern: leave per-PNG, user clicks Pack Atlas later).
- **D3** — armature stub: built automatically from Z-order + offset, or always manual? (lean toward "auto with optional toggle" — saves time on first import).
- **D4** — sprite_frame grouping by `<name>_<index>` — already locked in SPEC 007 D4. Importer must respect.
- **D5** — re-import: idempotent (replace existing) or additive (stamp again)? (idempotent + diffable; matches SPEC 001 reimport-merge philosophy).
- **D6** — coordinate space: PSD origin is top-left, Blender XZ is bottom-up. Conversion at import time.
- **D7** — handle `.psd` directly (read PSD format in Python via `psd-tools`) or only via JSX exporter manifest? (only via manifest — JSX is canonical, PSD parsing is fragile cross-version).

## Out of scope

- Re-export Blender → PSD (one-way pipeline only).
- Photoshop UI integration beyond the JSX exporter (one-shot script, no panel).
- Live link Blender ↔ Photoshop (backlog).

## Successor considerations

- SPEC 007 fixtures gain `simple_psd/` after SPEC 006 lands: PSD source + JSX-exported manifest + expected post-import `.blend`.
- SPEC 004 slot system can use PSD layer groups as slot hints once both SPECs ship.

## Surface (LOC estimate)

- `blender-addon/importers/photoshop/__init__.py` — read manifest, stamp planes, build materials. ~250 LOC.
- `core/psd_naming.py` — bpy-free convention parser (sprite_frame grouping, slot hints). ~80 LOC.
- New operator `PROSCENIO_OT_import_photoshop` + panel button in main sidebar. ~100 LOC.
- Tests: `tests/test_psd_naming.py`. ~60 LOC.

Total: ~500 LOC + manifest schema lock-in.
