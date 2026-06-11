# Spec 028: Schema expressiveness - TODO

Execution checklist derived from [STUDY.md](STUDY.md). Now chunks are PR-sized; deferred and gated rows keep their backlog entries, with each gate's trigger restated here.

## Now

- [ ] *Appearance fields in the schema*: add optional `modulate`, `z_index`, `flip_h` / `flip_v` to the element models in [proscenio.py](../../packages/models/src/proscenio_models/proscenio.py) (additive, defaulted, v1-safe - no `format_version` bump), regenerate the codegen artifacts (JSON schema, GDScript `schema_bindings/`, TS types), and pin the new fields with pydantic round-trip units.
- [ ] *Writer emission for appearance and pivot*: in [sprites.py](../../apps/blender/exporters/godot/writer/sprites.py), derive `z_index` from the PSD-stamped depth (the object's Y location), `modulate` from the object color when it is not opaque white, and the flips from negative scale signs; compute `Sprite2D.offset` from the Blender origin against the quad bounds in `build_sprite`; no new panel properties and no new PG/CP mirror rows in this cut; headless-bpy units plus goldens regeneration.
- [ ] *Godot stamping plus the filter-clip rider*: stamp `modulate` / `z_index` on [mesh_builder.gd](../../apps/godot/addons/proscenio/builders/mesh_builder.gd) and `modulate` / `z_index` / `flip_h` / `flip_v` on [sprite_builder.gd](../../apps/godot/addons/proscenio/builders/sprite_builder.gd), set `region_filter_clip_enabled` wherever `region_enabled` is set (the w4 polish row rides here for free), assert in the Godot suite, and sync the example fixtures.
- [ ] *Sprite-frame track export path*: in the writer (pattern in [slot_animations.py](../../apps/blender/exporters/godot/writer/slot_animations.py)), read keyframes on the sprite `frame` channel and bake the drive-from-bone driver into a `sprite_frame` track with `interp: "constant"` keys; add or extend a fixture whose golden carries the track so the re-export diff covers the path; flip the `drive_from_bone` badge in [feature_status.py](../../apps/blender/core/_shared/feature_status.py) to godot-ready once it round-trips.
- [ ] *Retire the visibility track*: remove `"visibility"` from the `Track` literal and `visible` from `Key` in [proscenio.py](../../packages/models/src/proscenio_models/proscenio.py), regenerate the bindings, and delete the stub branch in [animation_builder.gd](../../apps/godot/addons/proscenio/builders/animation_builder.gd); no golden carries the track, so the fixtures diff is expected to be a no-op - assert that.
- [ ] *Orientation guards (warn-only)*: validator warnings for armature rest bones off the XZ plane and for non-flat (3D) meshes in `core/validation`; pure validation units; sequence after the export-correctness blocking validator rows so the two specs do not collide on the same files.

## Deferred

- **Blend-mode passthrough** (defer, w1) - the manifest and the Blender material already carry it (`proscenio_blend_mode` Custom Property); emit it on the elements and map to `CanvasItemMaterial` (additive / multiply / subtract), downgrading screen and friends to normal with a warning.
- **Mask sprite** (gate) - trigger: a character actually needs clipping; run a masking-strategy study (`CanvasGroup` vs `clip_children`) before any schema field.
- **Bezier curve handles** (gate) - trigger: an animator reports the imported animation misses Blender beyond visual tolerance; answer first with denser baked sampling, schema tangents only if that fails.
- **Per-key interpolation mixing** (gate) - same trigger and design pass as the Bezier handles; one decision covers both.
- **Animation event tracks** (gate) - trigger: a game needs a synced cue (footstep, impact, particle) from an imported animation; design the pose-marker authoring and the Godot method-call contract then.
- **Continuous UV animation** (gate) - trigger: a user asks for animated water, conveyor, or region-resize effects; slot swap and sprite-frame tracks cover the discrete cases today.
- **Multiple atlas pages** (gate) - trigger: a real character pack overflows the 4096 max page (the packer returns `None`); interim answer is per-element `texture` plus the atlas-packing exclude flag.
- **NLA strips to actions** (gate) - trigger: an animator layers strips on the NLA and exports; until then the native `Bake Action` workflow is the documented norm.
- **Transform constraint export** (gate) - trigger: a Copy Rotation / Copy Transforms rig exports and the target bone does not follow in Godot; bake-at-export is the first answer, `RemoteTransform2D` only for full-channel copies.
- **Path constraint export** (gate) - trigger: an animator authors a path constraint and asks why nothing happens in Godot; bake-at-export first.
- **Bone physics export** (gate) - trigger: a character design has dangly parts that baked secondary motion cannot serve; study a deterministic Godot-side solver before wiring `Joint2D` chains.
- **Full XY-plane rig support** (gate) - trigger: a real user authors a rig in the XY plane; the warn-only guard above covers detection until then.
- **Format migration path** (gate) - trigger: the first breaking schema bump is scheduled (the storage split is the known candidate); build version detection plus the v1-to-v2 migrator inside that bump's PR series; the storage-split spec stays blocked behind this row.
- **Node-name collision polish** (defer, w4) - document the `_001` convention instead of prefixing, which would churn track target lookups.

## Dropped

- **Visibility track** - the format advertised a track neither side implements; slot attachment tracks already animate show / hide, and finishing it would add hide-keyframe authoring that collides with the writer's `hide_viewport` export dance - the retirement chunk in Now removes the enum value, the `Key` field, and the importer stub.
