# Spec 028: Schema expressiveness

Make the format carry real game art - add the schema fields, writer emission, and Godot import for the appearance, animation, and constraint data the pipeline currently drops.

## Scope

- **Sprite appearance (light)** - carry tint (modulate), draw order (z_index), and flip from Blender to the Godot sprite.
- **Sprite appearance (heavy)** - carry blend mode and a masking strategy to Godot.
- **Finish the sprite-frame track** - add the missing Blender export path so frame-by-frame animation actually emits.
- **Finish the visibility track** - implement both sides instead of the "not implemented yet" stub.
- **Bezier curve handles** - transmit animation tangents instead of flattening every curve to linear.
- **Per-key interpolation** - let a single track mix interpolation modes per keyframe.
- **Animation event tracks** - fire method/event keys for audio and particles.
- **Continuous UV animation** - a texture-region track for scrolling or sweeping textures.
- **Multiple atlases per character** - an `atlas_pages` array instead of one optional atlas.
- **Sprite pivot offset** - compute `Sprite2D.offset` from the Blender origin on the writer side.
- **NLA strips to actions** - bake NLA strips into flat Actions on export.
- **Constraint export** - emit bone-physics joint chains, path constraints, and cross-bone transform copies as Godot nodes.
- **Rig orientation detection** - detect XZ vs XY plane and 2D-rig vs 3D-mesh instead of assuming a flat quad.
- **Format migration path** - version detection plus a v1-to-v2 migrator so breaking schema changes do not break old files.
- **Godot importer polish** - node-name collision handling and region-filter-clip on packed sprite frames.

## Study

### Surface notes

What the code shows today, read against `packages/models/src/proscenio_models/proscenio.py`, the writer under `apps/blender/exporters/godot/writer/`, and the builders under `apps/godot/addons/proscenio/`:

- **Track inventory.** The `Track` literal names four types (`proscenio.py:227`). Two are fully wired: `bone_transform` (emitted from pose fcurves in `animations.py`, consumed in `animation_builder.gd:52-60`) and `slot_attachment` (emitted from slot Empties in `slot_animations.py`, consumed at `:79-84`). One is consumed but never produced: `sprite_frame` - `animation_builder.gd:61-78` animates `Sprite2D.frame`, but a grep for `sprite_frame` across the writer returns zero emission sites, so the importer branch is reachable only by hand-authored documents and the `mouth_drive` fixture's golden carries only a `bone_transform` track. One is stubbed on both sides: `visibility` - `animation_builder.gd:86` is `push_warning("not implemented yet")` and nothing emits it; no golden in `examples/generated/` carries the track, so retiring it breaks no real file.
- **Interpolation.** `Key.interp` is `linear | constant` (`proscenio.py:217`). The writer sets it only on slot keys (`slot_animations.py:102`, present in the `slot_cycle` / `slot_swap` goldens); the importer never reads it - track-level interpolation is hard-coded (`NEAREST` for frame and slot tracks, `CUBIC` / `CUBIC_ANGLE` upgrade for bone channels at `animation_builder.gd:115-121`). Per-key mixing and Bezier tangents are both absent from the wire.
- **Appearance.** Neither element variant carries modulate, z_index, flip, or blend_mode. The PSD side already knows blend modes: `psd_manifest.py` carries `blend_mode`, and the Blender import maps it onto the material and stamps a `proscenio_blend_mode` Custom Property (`importers/photoshop/planes.py:109-114,406-410`) - the Blender-to-Godot hop is the only place the value dies.
- **Draw order is silently dropped.** The PSD import preserves layer stacking as Blender depth (`planes.py:207`, `cy = z_order * Z_EPSILON`), the writer drops the depth axis by convention (`writer/__init__.py` coordinate notes), and `find_sprite_meshes` sorts elements alphabetically by name (`scene_discovery.py:22-26`). Godot then draws in tree order, so a multi-layer character renders in name order, not authored order. This makes the z_index half of the appearance work a correctness repair for the core flow, not a cosmetic add.
- **Pivot is the third half-built surface.** `SpriteElement.offset` exists in the schema (`proscenio.py:155`) and `sprite_builder.gd:48-49` stamps it; `build_sprite` in `writer/sprites.py` never computes it from the Blender origin, so an authored pivot silently reduces to the `centered` boolean.
- **Cost structure: every wire change is at least four-sided.** A schema field means: the pydantic model plus codegen regeneration (JSON schema artifact, GDScript `schema_bindings/`, TS types), writer emission with headless-bpy units, Godot builder consumption with suite assertions, and fixture goldens (`examples/generated/*.expected.proscenio`) plus the synced `apps/godot/examples` copies. A field that also needs Blender-side authoring state adds rows to the PG/CP mirror (`mirror.py` / `hydrate.py`) - exactly the dual-storage surface the storage-split spec exists to collapse - plus a panel row that becomes recurring manual-GUI surface. Deriving appearance values from native Blender state (object color, negative scale signs, the PSD-stamped depth) avoids both.
- **Migration.** No `migrations/` directory exists anywhere; `importer.gd:136-143` hard-rejects any `format_version != 1`. Every item marked now below is additive-optional (old files keep working on defaults, no bump). The first scheduled breaking change is the storage split, which the execution map already gates behind this spec's migration row.
- **Constraints.** The models carry no `constraints[]`; the writer exports raw pose keyframes only, so any Blender constraint (IK, copy-transform, path-follow, physics) reaches Godot only when baked first. The three constraint rows share one schema shape (a discriminated `constraints[]`), which is the execution map's root-cause collapse for this cluster.
- **Orientation.** The XZ-plane assumption is hardcoded and self-documented in three places (`writer/__init__.py` conventions, `_quat_to_screen_angle` at `animations.py:205-225`, the vertex-Y drop in `sprites.py`). An XY-authored rig or a genuinely 3D mesh exports silently wrong today with no validator warning.
- **Atlas.** `atlas` is one optional string, but the per-element `texture` override already gives each element its own image (the doll multi-PNG convention). The packer grows from `start_size` and returns `None` past `max_size` 4096 (`atlas_packer.py:63-83`) - that `None` is the concrete event that would prove multi-page demand.

Dependency edges found while reading:

- The storage-split spec is explicitly blocked behind the format-migration-path row (see [EXECUTION_MAP.md](../EXECUTION_MAP.md)); gating the migrator on the first scheduled breaking bump preserves that order without building code ahead of its consumer.
- The appearance implementation choice feeds the storage-split surface: new PG fields would enlarge `mirror.py` / `hydrate.py`; deriving from native Blender state keeps that surface frozen.
- The `region_filter_clip` polish row (w4) is a two-line rider on `sprite_builder.gd`, a file the appearance builder chunk already opens - it rides for free.
- Multi-atlas pairs with the exclude-from-atlas flag and per-asset PPU owned by the atlas-packing spec; per-element `texture` is the interim answer.
- Finishing the sprite-frame export path bakes the `drive_from_bone` driver, which flips that feature's badge from blender-only (`core/_shared/feature_status.py:81`) to godot-ready - a small panel-copy and help-topic touch owned by the ui-help-surfaces spec.
- The orientation warnings land in `core/validation`, the surface the export-correctness spec is actively fixing - sequence after its blocking validator rows to avoid collisions.
- Any goldens regeneration here ripples into the mixed-feature fixture and doll-oracle-v2 rows owned by the project-health spec.

### Research notes

- **Spine user guide (Events) + spine-unity events doc + Unity footstep-event tutorials**: event keys for footsteps, audio, and particle cues are a baseline, heavily exercised capability across skeletal runtimes - the Spine editor even previews audio events. The Godot-native consumption is method-call tracks, but a generated scene must keep working without the plugin, so a method-contract design (what node, what method, missing-method behavior on reimport-regenerated scenes) is the real cost, not the schema field.
- **DragonBones docs (Events)**: frame and sound events with custom payloads, dispatched through runtime listeners - a second ecosystem confirming event tracks are table stakes once game wiring matures.
- **Spine 4.2 release blog + Spine user guide (Physics constraints) + PixiJS adoption blog**: physics for hair, cloth, and capes was the headline 4.2 feature and runtimes rushed to support it - demand for secondary motion is real. The decisive detail: Spine ships its own deterministic spring solver inside the runtime and never delegates to engine physics. Mapping Blender constraints onto Godot `Joint2D` scene physics would be non-deterministic, frame-rate coupled, and far heavier than the thing whose popularity motivates the row.
- **Spine user guide (Graph) + Spine curve forum threads**: Spine runtimes flatten Bezier handles into roughly 10 linear segments per curve at playback - even the gold standard ships an approximation. Godot's cubic value-track interpolation (what the importer applies today) already yields smooth splines without handle data, and denser baked sampling is the no-schema fallback when a fidelity complaint actually arrives.
- **Spine user guide (Texture packing) + GameMaker multi-page article + Spine forum threads on character customization**: multi-page atlases serve skin-heavy customization projects and HD rigs; a single bounded character normally fits one page. The format's per-element `texture` override already covers the multiple-image case without pages.
- **Blender manual (NLA) + MoCap Online NLA guide + COA Tools repository**: the game-export norm is one Action per clip and bake-before-export (`Bake Action` with visual keying); COA Tools - the closest Blender 2D-cutout precedent - ships baked animation export. Documenting the native bake as the workflow is standard practice, not a stopgap.
- **Godot class reference (AnimatedTexture deprecation, CanvasItemMaterial, RemoteTransform2D, PathFollow2D) + Godot forum threads on scrolling textures**: Godot users scroll textures with shaders or hand-keyed `region_rect` - shader-first in practice, and outside the character pipeline. `CanvasItemMaterial` covers add / subtract / multiply / premultiplied blends but not screen or overlay, so PSD blend parity needs a documented downgrade. `RemoteTransform2D` and `PathFollow2D` exist as native post-import wiring for constraint-shaped needs.
- **Spine user guide (Transform constraints, Path constraints)**: documented as advanced-rig tools (re-parent simulation, equip / throw, tails and wheels along curves) - adopted by advanced riggers, not a baseline expectation.

### Assessment

Scores: flow-value 5 = core pipeline correctness or productivity; test-burden 5 = recurring manual GUI or cross-app roundtrip (schema rows count all four sides); bug-surface 5 = new modal or stateful surface; under-use risk 5 = speculative.

| Item | Flow value | Test burden | Bug surface | Under-use risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Sprite appearance (light: modulate / z_index / flip) | 4 | 3 | 3 | 2 | now | z_index repairs authored draw order the pipeline silently drops; tint and flip ride the same additive fields. |
| Sprite appearance (heavy: blend_mode) | 3 | 3 | 3 | 3 | defer | Upstream already carries it; `CanvasItemMaterial` maps add / multiply, screen downgrades with a warning - bounded w1 work. |
| Sprite appearance (heavy: mask) | 2 | 5 | 5 | 4 | gate | No single Godot property exists; needs its own masking-strategy study when a character actually needs clipping. |
| Finish the sprite-frame track | 4 | 3 | 2 | 2 | now | The importer half is live and tested; the Blender preview lies (mouth_drive) until the writer emits. |
| Finish the visibility track | 2 | 2 | 1 | 4 | drop | Slot tracks already animate show / hide; retire the enum and the stub instead of building a second mechanism. |
| Bezier curve handles | 2 | 4 | 3 | 4 | gate | Cubic auto-spline approximates well (Spine itself flattens to segments); trigger: a visual-tolerance complaint, answered first with denser baking. |
| Per-key interpolation | 2 | 3 | 3 | 4 | gate | Same fidelity gate as Bezier handles - one design pass decides both. |
| Animation event tracks | 3 | 3 | 3 | 3 | gate | Table stakes across ecosystems, but the Godot method contract needs design; trigger: a game needs a synced cue from an imported animation. |
| Continuous UV animation | 2 | 3 | 3 | 5 | gate | Godot users reach for shaders; trigger stays as written in the backlog entry (water / conveyor / region-resize request). |
| Multiple atlases per character | 2 | 4 | 3 | 4 | gate | Per-element `texture` already splits images; trigger: a real pack overflows the 4096 max page (the packer returns `None`). |
| Sprite pivot offset | 3 | 2 | 2 | 3 | now | Schema and importer shipped; one writer computation closes a logged user confusion. |
| NLA strips to actions | 2 | 3 | 3 | 4 | gate | Native `Bake Action` is the documented norm (COA Tools precedent); trigger: an animator layers strips and hits the gap. |
| Constraint export: transform copy | 3 | 4 | 4 | 4 | gate | `RemoteTransform2D` fits only full-channel mix=1 copies, the rest needs a resolver; bake-at-export covers the motion; backlog trigger stands. |
| Constraint export: path | 2 | 4 | 4 | 4 | gate | Path geometry in the schema plus `PathFollow2D` wiring for a rig style no fixture uses; backlog trigger stands. |
| Constraint export: bone physics | 3 | 5 | 5 | 4 | gate | Real demand (Spine 4.2) but Spine ships its own solver - engine `Joint2D` chains are the heaviest, least deterministic route in the spec. |
| Rig orientation + 2D/3D detection (warn-only) | 4 | 2 | 2 | 3 | now | Stops a silent-wrong export class with pure validation units; warn-only scope, no writer generalization. |
| Full XY-plane rig support | 2 | 4 | 4 | 4 | gate | Generalizing the transform math for a convention no user has asked for; trigger: a real XY-authored rig arrives. |
| Node-name collision polish | 1 | 2 | 2 | 3 | defer | Cosmetic `_001` suffixes; document the convention - prefixing would churn track target lookups. |
| Sprite2D region_filter_clip | 2 | 2 | 1 | 2 | now | Two-line rider on the appearance builder chunk that already opens `sprite_builder.gd`. |

### Verdict summary

Counts across the 19 assessed lines (the 18 backlog rows, with the appearance and orientation rows each split into their halves): **now 5, defer 2, gate 11, drop 1**.

- The blocking day-one pull - sprite appearance light - survives as now, and the study agrees with the tag: the z_index half is a correctness repair (authored stacking currently dies at the Blender-to-Godot hop), and modulate / flip are cheap riders on the same additive fields. One guardrail: derive the values from native Blender state (object color, negative scale, the PSD-stamped depth) and add no new panel properties in the day-one cut, so the manual-GUI surface and the PG/CP mirror stay exactly as large as they are today.
- The other now items are completions of half-built surfaces, not new capability: the sprite-frame export path, the pivot-offset computation, and warn-only orientation guards. Each is writer- or validator-side, unit-testable in existing harnesses, and removes a place where the tool currently lies or fails silently.
- The visibility track drops: retiring the enum, the `Key.visible` field, and the importer stub costs a small diff, breaks no golden, and removes an advertised lie - the slot system already owns show / hide.
- Everything else gates behind written triggers. The expressiveness wave (Bezier, events, UV tracks, atlas pages, NLA, the constraint trio, full XY support, the mask strategy) is where Spine-parity gravity would bloat the tool; every one of those rows has a concrete trigger and a cheaper interim answer (baking, shaders, per-element textures, native Blender workflows). The migrator builds inside the first scheduled breaking bump (the storage split is the known candidate) - a migrator for a v2 that does not exist yet would be speculative scaffolding, and the gate itself preserves the storage-split ordering.
