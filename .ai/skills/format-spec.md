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
| `polygon` (default) | `Polygon2D` | `polygon`, `uv`, `texture_region` | cutout-style mesh, deformable, eligible for skinning weights (SPEC 003) |
| `sprite_frame` | `Sprite2D` | `hframes`, `vframes`, `bone` | frame-by-frame animation (pixel art, particles, effects) |

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

The `atlas` field is an optional path to a single pre-packed texture. **Atlases are packed externally** (TexturePacker, Free Texture Packer, etc.) before the Blender pipeline runs. The Blender addon consumes the atlas plus per-sprite `texture_region` rectangles; it does **not** pack atlases itself in v1. Multi-atlas characters split into multiple `.proscenio` files.

## Skinning weights (v1)

The `weights` array on a sprite is **accepted by the schema** but **ignored by the v1 Godot importer**. Sprites without weights are attached rigidly to their `bone` (a child of the `Bone2D`, riding the bone transform). Full skinning (`Polygon2D.skeleton` path + `set_bones()`) lands in Phase 2 (SPEC 003). Until then, exporters may emit weights and the importer will log a one-line console warning.

## Versioning policy

- `format_version` is integer, monotonic.
- Breaking change → bump.
- Adding an optional field with a safe default → no bump.
- The schema is validated in CI for every `examples/**/*.proscenio` and every `tests/fixtures/**/*.proscenio`.

## Migration

Each version bump ships a migrator at:

```text
blender-addon/exporters/godot/migrations/v{N}_to_v{N+1}.py
```

The Godot importer rejects unknown future versions with a clear error message and refuses to import.

## Track types

| Track type | Targets | Per-key data |
| --- | --- | --- |
| `bone_transform` | `Bone2D` | `position`, `rotation`, `scale` |
| `sprite_frame` | `Sprite2D` (sprite of `type: "sprite_frame"`) | `frame` (spritesheet index) — importer wires this to a value track at `:frame` with `INTERPOLATION_NEAREST` |
| `slot_attachment` | slot | `attachment` (sprite name) |
| `visibility` | any | `visible` (bool) |

Per-key interpolation: `interp` field with values `linear` or `constant`. Default is `linear` if omitted. Cubic Bézier was considered for v1 but dropped — proper cubic interpolation needs in/out tangent handles per key, which the schema does not yet model. Add in a future format bump if real demand surfaces.
