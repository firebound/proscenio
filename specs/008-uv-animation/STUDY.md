# SPEC 008 - UV animation

**Status**: stub. Captured for future reference. **Not yet greenlit** - needs a concrete use case before work starts. Until then, lives here so the design surface is not lost.

## Problem

The existing animation tracks (`bone_transform`, `sprite_frame`, `slot_attachment`, `visibility`) cover skeletal motion + frame-index swap + attachment swap + on/off. They do **not** cover continuous UV animation - sub-pixel scrolling textures, animated water flow, gradient sweeps, animated mask reveals, etc.

The user mentioned this as a future need: "texture swap em certo ângulo ou ponto da animação", "UV animation". Some of these are slot-system territory (discrete swap), some are UV-region animation (continuous scroll), some are shader tricks (out of scope).

## Use cases worth distinguishing

1. **Discrete swap** - eye opens, equipment changes, expression shifts. Already covered: `slot_attachment` track (SPEC 004) for whole-image swap, `sprite_frame` track (SPEC 002) for grid-index changes.
2. **Continuous UV scroll** - water surface flowing, conveyor belt moving, force-field shimmer. Animate `texture_region` over time - sub-pixel sampling, looped UV coordinates.
3. **Texture fade / cross-fade** - face A morphs into face B over N frames. Either two stacked sprites with opacity tracks (existing `visibility` track + future opacity extension) or shader-driven blend.
4. **Region resize** - sprite "grows" or "shrinks" by animating region width/height. Possible but unusual.

Cases 2 + 4 are the SPEC 008 scope. Cases 1 + 3 are not.

## Reference

- **Spine** - has UV animation via attachment-level uv keys. Continuous, supports sub-pixel.
- **Godot native** - `Sprite2D.region_rect` is a Rect2 you can animate via `AnimationPlayer` track without a plugin.
- **DragonBones** - supports `displayFrame` mostly; UV continuous is via shader.

Godot's native support is the leverage point: the importer can write an `AnimationPlayer` track targeting `region_rect.x` / `region_rect.y` etc. directly, no custom node, no plugin runtime.

## Design surface (sketch)

### Schema impact

New track type:

```json
{
  "type": "texture_region",
  "target": "water_surface",
  "keys": [
    {"time": 0.0, "x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5},
    {"time": 1.0, "x": 0.5, "y": 0.0, "w": 0.5, "h": 0.5},
    {"time": 2.0, "x": 0.0, "y": 0.0, "w": 0.5, "h": 0.5}
  ]
}
```

Schema bump probably triggers `format_version` 2 - coordinated migrator + 005 PG `region_x/y/w/h` already there as the per-key shape blueprint.

### Writer side

Reads keyframes on `Object.proscenio.region_x/y/w/h` from a Blender action, emits `texture_region` track per sprite that has any region_* fcurve.

### Importer side

For each `texture_region` track:

- For sprite_frame target → animate `Sprite2D.region_rect` directly.
- For polygon target → animate the UV coords (rebuild at runtime) or shader uniform - likely means polygon UV animation needs a custom approach (`SubViewport`? texture_region is Sprite2D-only). May restrict the track type to `sprite_frame` sprites only in v1.

### Authoring side (Blender panel)

Active Sprite panel already exposes `region_x/y/w/h` floats. Just keyframable - user right-clicks → Insert Keyframe in standard Blender flow. Animation panel surfaces the resulting fcurves.

## Decisions to lock when SPEC opens

- **D1** - track type name: `texture_region` (consistent with schema field) or `uv_animation` (more descriptive)?
- **D2** - apply to polygon sprites or sprite_frame only? (sprite_frame easy via `Sprite2D.region_rect`; polygon needs UV-animate which is harder. Limit v1 to sprite_frame.)
- **D3** - interp options: linear, constant, cubic? (match other track types - linear default).
- **D4** - schema bump path: format v2 with migrator, or additive v1 (track type list is open in current schema)?
- **D5** - Blender authoring UX: just keyframable region_*, or new "Animate UV" operator with sensible defaults?

## Out of scope (definitively)

- Polygon UV animation (deferred to v3 or never - Spine-only feature, niche).
- Shader-driven UV scroll (no schema, runtime-only - user writes Godot shader).
- Per-vertex UV animation (FFD territory - different SPEC entirely).

## Successor considerations

- Once shipped, SPEC 007 gets a `flow_water/` fixture - single sprite_frame mesh, action animating `region_x` 0→1 over a loop.
- May trigger new validation: `texture_region` track on a polygon mesh (warn in v1, error if scope locked to sprite_frame).
