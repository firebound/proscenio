# SPEC 003 — Skinning weights and `Polygon2D.skeleton` wiring

Status: **locked**, ready for implementation. All seven decisions confirmed 2026-05-05 — see the Locked decisions section below.

## Problem

Today every sprite is rigid-attached to a single bone — the importer makes the sprite a child of the matching `Bone2D` and lets it ride that bone's transform. Move the bone, the entire sprite moves as one piece. There is no per-vertex deformation: a torso vertex above the hip and a torso vertex at the waist behave identically.

That is a Spine/COA Tools-style cutout pipeline missing its defining feature. The whole reason `Polygon2D` (mesh) was chosen over `Sprite2D` (single quad) for the default rendering path is that Godot's `Polygon2D.skeleton` + `set_bones()` API supports per-vertex weighted skinning. The writer already collects vertex groups when it picks a bone for rigid attach; the schema already accepts a `weights` array on each sprite; the importer already logs a warning ("full skinning lands in Phase 2") when it sees one. SPEC 003 fills the gap.

After SPEC 003: a vertex on the torso mesh painted 1.0 to `legs` and 0.0 to `torso` follows the legs bone; one painted 0.5/0.5 follows their midpoint smoothly. The mesh bends instead of jumps.

## Constraints

- **No GDExtension preserved.** All wiring is GDScript at editor-import time.
- **`Polygon2D` only.** `Sprite2D` (the SPEC 002 path) does not support per-vertex skinning in Godot — `sprite_frame` sprites stay rigid.
- **Backwards-compatible.** Sprites without `weights` keep the rigid-attach behavior. Existing fixtures (no `weights`) must still import unchanged.
- **No `format_version` bump.** The `weights` field is already in the schema (accepted since v1, ignored by the importer). This SPEC only adds wiring.
- **Author once in Blender.** Vertex groups + weight painting is the native Blender authoring story; the writer must not require parallel custom-property setup.

## Schema reminder (already in place)

```jsonc
"weights": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["bone", "values"],
    "properties": {
      "bone":   { "type": "string" },
      "values": {
        "type": "array",
        "items": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    }
  }
}
```

One entry per bone the sprite is influenced by; `values` is indexed by vertex (so `values[i]` is the weight that bone applies to vertex `i`). Empty / missing `weights` → rigid-attach fallback (current behavior).

## Locked decisions

Confirmed 2026-05-05. Each was an open question; the chosen answer is bold, the rationale follows.

- **D1 — Weight normalization: writer normalizes per-vertex sums to 1 before emitting.** Centralizes the math where context is richest, frees the importer from ambiguity, and lets Blender weight painting stay additive without ceremony. Vertices with zero total weight get a deterministic fallback (D2).
- **D2 — Zero-weight vertex falls back to the sprite's resolved bone.** The same bone rigid-attach would have used. Asset stays functional while painting is in progress; mental model matches the rigid case.
- **D3 — Vertex group whose name does not match a bone is dropped with a warning.** Aligns with the existing "warn but ship" pattern (animation actions, etc.). Hard-erroring on stale group names would block the user mid-edit unnecessarily.
- **D4 — Keep the bone-major schema shape: `weights: [{bone, values[]}]`.** Already validated by every fixture, no `format_version` bump. Vertex-major would be a churn for negligible win.
- **D5 — Single `polygon_builder.gd` with an internal data-driven branch.** `Polygon2D` is one Godot node type; the skinned/non-skinned distinction is data, not type. SPEC 002's two-builder split was for two node types.
- **D6 — Animation builder unchanged.** `bone_transform` tracks animate `Bone2D` transforms; `Polygon2D.skeleton` consumes them at draw time. Baking would add file size and brittleness for zero benefit.
- **D7 — Authoring is implicit by data.** Vertex groups whose names match armature bones turn skinning on. No new Custom Property. The writer logs which sprites picked up skinning so the user can verify.

## Out of scope

- **`Sprite2D` skinning** (SPEC 002 path). Godot does not support it on a single-quad sprite.
- **Bone weight visualization in Godot editor** post-import — Godot's built-in inspector covers this enough.
- **Auto vertex-group creation from bone proximity** in Blender — that is a Blender-side authoring feature, not a pipeline concern.
- **Dual quaternion skinning** or any non-linear scheme — Godot's `Polygon2D` does linear blend skinning only.
- **GPU-side skinning compute shader** — the GDExtension escape hatch in `specs/backlog.md` covers this for a future stretch case.
- **Animation event tracks** — independent, listed in backlog.
- **Slot-aware skinning** (sprite swap interactions) — SPEC 004 territory; design carefully ordered so SPEC 003 lands first.

## Successor considerations

- SPEC 004 (slots) interacts with skinned sprites — when a slot swaps `head_normal` for `head_angry`, both attachments may have different weight sets. Plan: each attachment carries its own `weights`. SPEC 003's per-sprite weights model already supports this without change.
- A future "rest pose vs deformed pose" debug visualizer is plausible. Out of scope here, but the per-vertex weight data is the prerequisite.
- Skeleton edits in Blender (bone added/removed/renamed) interact with downstream `weights` — a renamed bone makes existing weights orphan. The writer warns (D3); a future migration helper could remap.
