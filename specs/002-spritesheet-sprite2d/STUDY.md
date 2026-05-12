# SPEC 002 - Spritesheet support / `Sprite2D` path

Status: **locked**, ready for implementation. All open questions resolved 2026-05-05 - see [Locked decisions](#locked-decisions) below for the answers.

## Problem

The Phase 1 importer renders every sprite as a [`Polygon2D`](https://docs.godotengine.org/en/stable/classes/class_polygon2d.html) - a mesh of vertices with UV coordinates. That fits cutout characters with deformable meshes (the use case that justifies the project) but is overkill or outright unsuitable for:

- **Frame-by-frame pixel art animation** - a walk cycle authored as a horizontal strip of N frames in a single texture.
- **Particle / effect sprites** - sparks, smoke puffs, hit flashes that animate by stepping through frames.
- **Mixed characters** - a cutout body with a spritesheet-driven face for expressions, or a cutout protagonist that emits spritesheet effects from a hand bone.

`Sprite2D` is the natural Godot node for these cases: it carries `hframes`/`vframes`/`frame` indices and renders a single rectangular region of an atlas without per-vertex geometry.

The decision: how does the `.proscenio` schema model the choice between `Polygon2D` and `Sprite2D`, and how does the importer dispatch?

## Constraints

- **Backwards-compatible with v1 fixtures.** Existing `.proscenio` documents (without any new field) must still import as `Polygon2D` exactly as today. No `format_version` bump.
- **Per-sprite decision.** A single character can mix `Polygon2D` and `Sprite2D` sprites. The choice is local to each sprite entry.
- **No-GDExtension preserved.** Generated scenes use `Sprite2D` as a built-in node; no native code anywhere.
- **Polygon2D is not deprecated.** It remains the default and the only path that supports `Polygon2D.skeleton` + per-vertex bone weights (SPEC 003 territory). `Sprite2D` is an *alternative*, not a *replacement*.

## Design options

### Option A - Explicit `type` discriminator field

Each sprite declares its rendering path with a `type` string:

```json
{ "name": "head", "bone": "head", "type": "polygon",       "polygon": [...], "uv": [...] }
{ "name": "spark", "bone": "hand", "type": "sprite_frame", "hframes": 4, "vframes": 1, "frame": 0 }
```

Default value: `"polygon"`. Omitting `type` keeps current v1 behavior.

**Pros.**

- Explicit beats implicit. Discriminator string is exact and self-documenting.
- Schema-side, JSON Schema `oneOf` with discriminator is a known idiom; static analyzers and IDE tooling handle it cleanly.
- Mirrors the established pattern of `tracks[].type` (`"bone_transform"`, `"sprite_frame"`, etc) - same discriminator vocabulary as the animation side.
- Importer dispatch is a single switch; failure modes ("unknown type") have clear error messages.

**Cons.**

- One extra field per sprite.
- Pending duplication: a sprite with `type: "sprite_frame"` cannot carry `polygon` (and vice versa); the schema enforces this via `oneOf`, but documentation must call it out.

### Option B - Implicit duck-typing

The schema infers the path from which fields are present:

```json
{ "name": "head", "polygon": [...], "uv": [...] }              // → Polygon2D
{ "name": "spark", "hframes": 4, "vframes": 1, "frame": 0 }    // → Sprite2D
```

**Pros.**

- Schema stays narrower.

**Cons.**

- A sprite with both `polygon` and `frame` fields is ambiguous; schema validation has to invent an arbitrary precedence rule.
- Importer must probe field existence on every sprite - slower to read, slower to debug.
- Future sprite kinds (e.g. a hypothetical `MeshInstance2D` path) make the inference rules combinatorial.

### Option C - JSON Schema `oneOf` without explicit discriminator

Schema accepts either shape via `oneOf` but does not require a literal `type` field; a downstream tool sniffs the variant.

**Pros.**

- Schema is formal.

**Cons.**

- Combines the worst of A and B: still requires `oneOf`, still requires probe-style importer dispatch.

## Recommendation

**Adopt Option A.** Explicit `type: "polygon" | "sprite_frame"` per sprite, default `"polygon"`. Schema models the choice as `oneOf` with the discriminator field as the const distinguisher.

Reasons:

- "Explicit > implicit" already governs the rest of the project (typed Python, typed GDScript, typed JSDoc).
- Discriminator strings are exactly how `tracks[].type` already works (`"bone_transform"` is a const). Two parts of the schema using the same idiom keeps the format readable.
- Sprite kinds are likely to grow (SPEC 004 slots would benefit, future `MeshInstance2D` path is plausible). A discriminator scales; duck-typing does not.
- Pylance and GDScript both treat tagged unions well when the tag is a literal string.

## Schema additions

Additive only - no `format_version` bump.

```jsonc
"sprites": {
  "type": "array",
  "items": {
    "oneOf": [
      { "$ref": "#/$defs/PolygonSprite" },
      { "$ref": "#/$defs/SpriteFrameSprite" }
    ]
  }
}

"$defs": {
  "PolygonSprite": {
    "required": ["name", "bone", "polygon", "uv"],
    "properties": {
      "type": { "const": "polygon", "default": "polygon" },
      "name": { "type": "string" },
      "bone": { "type": "string" },
      "polygon": { "$ref": "#/$defs/PolygonPoints" },
      "uv":      { "$ref": "#/$defs/PolygonPoints" },
      "weights": { "$ref": "#/$defs/Weights" },
      "texture_region": { "$ref": "#/$defs/Rect" }
    }
  },
  "SpriteFrameSprite": {
    "required": ["name", "bone", "type", "hframes", "vframes"],
    "properties": {
      "type":     { "const": "sprite_frame" },
      "name":     { "type": "string" },
      "bone":     { "type": "string" },
      "hframes":  { "type": "integer", "minimum": 1 },
      "vframes":  { "type": "integer", "minimum": 1 },
      "frame":    { "type": "integer", "minimum": 0, "default": 0 },
      "region":   { "$ref": "#/$defs/Rect" },
      "offset":   { "$ref": "#/$defs/Vec2",    "default": [0, 0] },
      "centered": { "type": "boolean",          "default": true }
    }
  }
}
```

`type` on `PolygonSprite` is optional with default `"polygon"` for backwards-compat; on `SpriteFrameSprite` it is required and `const`.

## Animation track - `sprite_frame`

The track type already exists in the schema enum; only the importer wiring is missing. Each key carries an integer frame index:

```json
{
  "type": "sprite_frame",
  "target": "spark",
  "keys": [
    { "time": 0.0, "frame": 0 },
    { "time": 0.1, "frame": 1 },
    { "time": 0.2, "frame": 2 },
    { "time": 0.3, "frame": 3 }
  ]
}
```

Importer translates this to a Godot `Animation` value track at path `<sprite_name>:frame` with `INTERPOLATION_NEAREST` - frames are discrete; smooth blending between integer indices is meaningless.

## Authoring (Blender side)

How does a user mark "this sprite is `sprite_frame`, not `polygon`" inside the `.blend`?

**Custom Properties on the Object data block.** Blender exposes them in the Properties → Object → Custom Properties panel without any addon code:

| Property | Type | Default |
| --- | --- | --- |
| `proscenio_type` | string (`"polygon"` or `"sprite_frame"`) | `"polygon"` |
| `proscenio_hframes` | int | 1 |
| `proscenio_vframes` | int | 1 |
| `proscenio_frame` | int | 0 |
| `proscenio_centered` | bool | true |

The writer reads with `obj.get("proscenio_type", "polygon")`. A future polish pass (backlog) can ship a Blender UI panel with a dropdown + spinners; the custom-property path stays as the canonical contract.

## Importer dispatch

Two options for the Godot side:

### D1 - Single `sprite_builder.gd` with internal switch

`polygon_builder.gd` is renamed to `sprite_builder.gd`. The dispatcher reads `sprite_data.get("type", "polygon")` and runs the matching branch in the same file.

**Pros.** One entry point. Simpler import graph.

**Cons.** File grows; mixes two unrelated rendering paths.

### D2 - Two builders + dispatcher in `importer.gd`

`polygon_builder.gd` stays (handles only the polygon path). New `sprite_frame_builder.gd` ships next to it. `importer.gd` (or a thin `sprite_dispatcher.gd`) loops `sprites_data` and routes each entry to the right builder.

**Pros.** Each builder is small and single-purpose. Natural place for SPEC 003 to add a third path (skinned `Polygon2D` will likely warrant its own builder or a flag).

**Cons.** Two files instead of one.

**Recommendation: D2.** The "one builder per node type" pattern matches `skeleton_builder.gd` and `animation_builder.gd` already in place.

## Locked decisions

Confirmed 2026-05-05. Each was an open question; the chosen answer is bold, the rationale follows.

- **D1 - Discriminator field name: `type`.** Consistent with `tracks[].type` already in the schema; same idiom on both sides of the format.
- **D2 - Default when `type` is omitted: `"polygon"`.** Keeps every existing `.proscenio` fixture valid without edits. Importer treats absence of `type` as an alias for `"polygon"`.
- **D3 - Frame addressing: `frame: int` row-major only.** No `frame_coords`. Users who think in `(col, row)` compute `frame = row * hframes + col`. Importer is one less branch.
- **D4 - `bone` field stays required on every sprite.** Standalone effects attach to the root bone. Keeps the importer's parent-resolution logic uniform across both sprite kinds.
- **D5 - `region` field is included in this SPEC as optional.** Trivial cost on the importer; covers the realistic case of a spritesheet packed inside a larger shared atlas. Absent → sprite uses the full texture as its source.
- **D6 - Builder split: D2 (two builders + dispatcher).** `polygon_builder.gd` keeps only the `Polygon2D` path; new `sprite_frame_builder.gd` handles the `Sprite2D` path; `importer.gd` dispatches by `sprite.type`. Matches the existing one-builder-per-concept convention.
- **D7 - Animation track interpolation for `sprite_frame`: `INTERPOLATION_NEAREST`.** Frames are discrete integers; linear blending between indices has no visual meaning.
- **D8 - Authoring UX: Blender Object Custom Properties.** `proscenio_type`, `proscenio_hframes`, `proscenio_vframes`, `proscenio_frame`, `proscenio_centered`. A dedicated Blender sidebar panel is a backlog polish item, not a gate for this SPEC.
- **D9 - Worked example fixture name: `effect`.** Single-bone, single-sprite spritesheet asset under `examples/effect/` exercises the full new path independent of the cutout fixture.

### Non-decisions

These were considered and explicitly *not* part of SPEC 002:

- **`SpriteFrames` resource / `AnimatedSprite2D`.** We use raw `Sprite2D` + `:frame` value track instead. More flexible, no extra resource type.
- **Animation event / method tracks.** Sound or particle cues on frame transitions are a natural sibling feature; tracked in `specs/backlog.md` under "Animation events / method tracks".
- **Hybrid sprites.** Same mesh acting as both `Polygon2D` and `Sprite2D` at once. No use case found.

## Out of scope

- `AnimatedSprite2D` + `SpriteFrames` resource path (see non-decisions).
- Animation events / method tracks.
- Multiple atlases per character (separate backlog item).
- Bone-less standalone sprites - every sprite attaches to a bone, even if it is the root (D4).
- Authoring UX polish (Blender UI panel for custom properties) - backlog.

## Successor considerations

- SPEC 003 (skinning weights) layers onto `Polygon2D` only. The discriminator chosen here means SPEC 003 inherits a clean place to define skinned vs unskinned `Polygon2D` if needed (`type: "polygon_skinned"` is plausible; a flag is also fine).
- SPEC 004 (slots) interacts with sprite identity. The discriminator field name (`type`) does not collide with anything slot-related.
- A future `MeshInstance2D` or `TileMapLayer` path can drop in as a third `oneOf` variant without touching v1.
