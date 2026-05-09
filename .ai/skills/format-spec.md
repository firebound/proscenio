---
name: format-spec
description: .proscenio JSON format — fields, semantics, versioning, migrations
---

# `.proscenio` format

JSON file with extension `.proscenio`. Source of truth: [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json). Any change to this skill must also change the schema and vice versa.

## Top level

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `format_version` | int | yes | bump on breaking change |
| `name` | string | yes | character/asset name |
| `pixels_per_unit` | number | yes | Blender unit ↔ Godot pixel ratio (e.g. 100) |
| `atlas` | string | no | path to packed atlas texture |
| `skeleton` | object | yes | bone hierarchy |
| `sprites` | array | yes | mesh + texture data |
| `slots` | array | no | sprite swap groups |
| `animations` | array | no | track data |

## Sprite kinds (`type` discriminator)

Each entry in `sprites` is one of two shapes, distinguished by a `type` field:

| `type` | Renders as | Required fields | Use when |
| --- | --- | --- | --- |
| `polygon` (default) | `Polygon2D` | `name`, `texture_region`, `polygon`, `uv` | cutout-style mesh, deformable, eligible for skinning weights (SPEC 003) |
| `sprite_frame` | `Sprite2D` | `type`, `name`, `bone`, `hframes`, `vframes` | frame-by-frame animation (pixel art, particles, effects) |

`type` is **optional** on `polygon` sprites — absence means `polygon`, keeping every v1 fixture valid without edits. On `sprite_frame` sprites it is required and constant.

A sprite of `type: "sprite_frame"` carries an optional `texture_region` (the sub-rectangle of the atlas where the spritesheet lives) plus the frame grid (`hframes` × `vframes`), the initial `frame` index (row-major), and the standard `Sprite2D` knobs `offset` and `centered`. Animations advance the frame via a `sprite_frame` track on the matching sprite.

A single `.proscenio` may freely mix both kinds — a cutout body with a spritesheet face, for example.

## UV coordinates

UVs in `.proscenio` (under `polygon` sprites) are **normalized to `[0, 1]`** of the atlas image, regardless of atlas resolution. The format stays engine-agnostic. Engine-specific importers convert to whatever convention the target uses (e.g. Godot's `Polygon2D` wants UVs in atlas pixel space, so the importer multiplies by atlas size). `sprite_frame` sprites have no `uv` field — Godot derives the UV automatically from `frame` × `hframes`/`vframes`.

## Coordinate system

- 2D plane: Blender XY → Godot XY.
- Y is up in Blender, down in Godot. The exporter flips Y.
- Rotations are in radians, CCW in Blender, CW in Godot. The exporter negates.
- Scales are Vec2 multipliers around the bone origin.
- **Origin.** The character origin is the scene-root `Node2D` at `(0, 0)`. The `Skeleton2D` lives at `(0, 0)` relative to it. Any global offset is carried by the `root` bone.

The Godot importer trusts the exporter — it does not re-flip. If you write a non-Blender exporter, follow Godot conventions in the file.

## Atlas packing (v1)

The `atlas` field is an optional path to a single packed texture. The Blender addon ships an in-tool **atlas packer** (SPEC 005.1.c.2) that emits the packed atlas + per-sprite `texture_region` rectangles directly from the rigged scene. Sliced-atlas authoring + Unpack support let the artist round-trip a packed atlas back to source images, edit, and repack. External packers (TexturePacker, Free Texture Packer, etc.) remain compatible — the writer reads whatever `texture_region` the user supplies.

Multi-atlas per character is not supported in v1; multi-atlas characters split into multiple `.proscenio` files. Multi-atlas via an `atlas_pages[]` array is a deferred SPEC tracked in [`docs/DEFERRED.md`](../../docs/DEFERRED.md).

## Skinning weights

The `weights` array on a `polygon`-typed sprite drives Godot `Polygon2D` skinning — `Polygon2D.skeleton` resolves to the character's `Skeleton2D` and each bone receives a per-vertex weight array. Shape:

```json
"weights": [
  { "bone": "torso", "values": [1.0, 1.0, 0.7, 0.3] },
  { "bone": "legs",  "values": [0.0, 0.0, 0.3, 0.7] }
]
```

`values` is indexed by the sprite's vertex order — `values[i]` is the weight that bone applies to vertex `i`. Per-vertex sums are normalized by the writer to `1.0`; vertices with zero total weight fall back to the sprite's resolved bone (the same one rigid-attach would have used, see [SPEC 003](../../specs/003-skinning-weights/STUDY.md)).

Sprites with the field absent or empty stay rigid-attached (a child of the `Bone2D`, riding its transform) — backwards-compatible with v1 documents and the workflow for sprites that do not need deformation. `sprite_frame` sprites (SPEC 002) ignore `weights` entirely; Godot's `Sprite2D` has no skinning concept.

## Versioning policy

- `format_version` is integer, monotonic.
- Breaking change → bump.
- Adding an optional field with a safe default → no bump.
- The schema is validated in CI for every `examples/**/*.proscenio` and every `tests/fixtures/**/*.proscenio`.

## Migration

Each version bump ships a migrator under the writer package:

```text
apps/blender/exporters/godot/writer/migrations/v{N}_to_v{N+1}.py
```

The directory is created when the first migration lands. Today the writer is `format_version=1` only; no migrations exist yet.

The Godot importer rejects unknown future versions with a clear error message and refuses to import.

## Track types

| Track type | Targets | Per-key data |
| --- | --- | --- |
| `bone_transform` | `Bone2D` | `position`, `rotation`, `scale` |
| `sprite_frame` | `Sprite2D` (sprite of `type: "sprite_frame"`) | `frame` (spritesheet index) — importer wires this to a value track at `:frame` with `INTERPOLATION_NEAREST` |
| `slot_attachment` | slot | `attachment` (sprite name) |
| `visibility` | any | `visible` (bool) |

Per-key `interp` field: `linear` or `constant`. Default `linear` if omitted.

**Track-level interpolation override**: the Godot importer applies cubic interpolation at the track level for `bone_transform` tracks, regardless of per-key `interp`:

- Rotation track: `INTERPOLATION_CUBIC_ANGLE` (handles wrap-around at ±π).
- Position / scale tracks: `INTERPOLATION_CUBIC`.
- `sprite_frame` and `slot_attachment` tracks: `INTERPOLATION_NEAREST` (hard cuts).

This means per-key `interp` is currently ignored for transform tracks — the track-level cubic spline always wins. Per-key interpolation mixing (linear / constant / cubic on different keys of the same track) is a deferred SPEC tracked in [`docs/DEFERRED.md`](../../docs/DEFERRED.md). True Bezier preservation (in/out tangent handles per key) is also deferred — it requires schema fields the v1 shape does not model.
