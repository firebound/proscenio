# Backlog

Items that are not in any active spec. Each entry promotes into a numbered spec under `specs/` when work begins. Order within a section is rough priority.

Forward-compatibility items gated on a future Blender release live in a dedicated [`backlog-blender-6.md`](backlog-blender-6.md). Cross-cutting type-safety and lint-enforcement gaps (strict gates configured but not run, trees exempted from type checking) live in [`backlog-code-quality.md`](backlog-code-quality.md).

## Format and schema

### Bezier curve preservation

**What:** the `.proscenio` v1 stores keyframes with track-level interpolation only (`linear`, `constant`); the Godot importer also offers cubic via `INTERPOLATION_CUBIC*` for smooth automatic splines. Blender authors curves with per-key Bezier handles that the format does not transmit.

**Why future-spec:** transmitting Bezier handles requires schema fields (`tangent_in`, `tangent_out`) and a Godot-side custom Bezier track or pre-baking. Cubic auto-spline is good enough for MVP.

**Trigger to revisit:** an animator complains that the imported animation does not match Blender to within visual tolerance.

### Multiple atlases per character

`atlas` is a single string in v1. Multi-atlas characters split into multiple `.proscenio` files. Future v2 may support an `atlas_pages` array indexed by sprite.

### Animation events (method tracks)

`AnimationPlayer` supports method tracks for audio cues, particle spawns, etc. v1 has no `event` track type.

### Per-key interpolation mixing

Schema's `interp` field is per-key but the importer applies a single track-level interpolation. Mixed `linear`/`constant`/`cubic` keys in one track would require splitting into multiple tracks at runtime or adopting a Bezier track type.

### Format detection / migration

Schema validation rejects unknown `format_version`. Once v2 lands, the Blender exporter ships `migrations/v1_to_v2.py` and the Godot importer surfaces a clear migration error pointing to the migrator.

### Bone physics (joint chain export)

`Joint2D` chains driven by physics for cape, hair, tail, dangly weapon ornaments. Requires a schema extension carrying joint type + stiffness / damping per chain, then a Godot-side importer that wires `PinJoint2D` / `DampedSpringJoint2D` / `Joint2D` under the relevant bones. Pairs with the live-link discussion in [Architecture revisits](#architecture-revisits) since runtime physics on hot-reloaded poses gets interesting fast.

**Trigger:** a character design surfaces dangly elements that look stiff under skeletal-only deformation.

### Path constraint export

Bones following a path: tail swish along a curve, eye blink along a Bezier, vehicle wheels rolling along a road. Blender ships path-following constraints today; the schema extension carries the path geometry + per-bone path attachment, and the Godot importer wires `PathFollow2D` (or a custom path resolver) under each follower bone. Requires `format_version=2` bump.

**Trigger:** an animator authors a path constraint in Blender and asks why nothing happens on the Godot side.

### Continuous UV animation (texture region track)

Existing tracks (`bone_transform`, `sprite_frame`, `slot_attachment`, `visibility`) cover skeletal motion, grid-frame swap, attachment swap, and on/off. They do not cover continuous UV animation: animated water flow, conveyor belts, gradient sweeps, mask reveals, region resize.

**Scope when promoted:** add a `texture_region` track that animates `Sprite2D.region_rect.x/y/w/h` on the Godot side. Targets `sprite_frame` sprites in v1; polygon UV animation deferred (would need shader-driven approach). Authoring side reuses the existing `region_x/y/w/h` floats on `Object.proscenio` - already keyframable in Blender via standard right-click flow.

**Open design questions when promoted:** track type name (`texture_region` vs `uv_animation`), scope (sprite_frame only or polygon too), interp options, schema bump path (format v2 with migrator vs additive v1), Blender authoring UX (keyframe-the-floats vs new operator).

**Trigger:** a user asks for animated water, conveyor-belt, or region-resize effects. If the request is "swap whole image" - slot system covers it. If "swap frame in grid" - sprite_frame already covers it.

**Out of scope definitively:** polygon UV animation (Spine-only feature, niche), shader-driven UV scroll (no schema, runtime-only), per-vertex UV animation (free-form deformation territory, separate concern).

### sprite_frame animation track - Blender export path

**What:** the `.proscenio` schema defines a `sprite_frame` track type and the Godot importer (`apps/godot/addons/proscenio/builders/animation_builder.gd`) already consumes it (animates `Sprite2D.frame` over time), but the Blender writer never emits one. `apps/blender/exporters/godot/writer/animations.py` only walks `pose.bones[...]` location / rotation / scale fcurves and emits `bone_transform` tracks (and `slot_animations.py` emits `slot_attachment`); a keyframed or bone-driven `proscenio.frame` channel does not become a `sprite_frame` track. The `drive_from_bone` shortcut is `BLENDER_ONLY` (`core/feature_status.py`), so the mouth_drive fixture's frame swap is a Blender-preview effect that never round-trips - its golden carries only a `bone_transform` track.

**Why:** closes the producer half of an existing importer capability and the mouth_drive UX cliff ("I drove the mouth frame from a bone in Blender, why does Godot not animate it?"). Today the importer branch is reachable only by hand-authored documents; no Blender-produced fixture exercises it.

**Scope sketch:** read keyframes on the sprite's `frame` channel (and/or bake the `drive_from_bone` driver) into a `sprite_frame` track targeting the sprite name; emit `interp: "constant"` keys (frame index is a hard step). Add a fixture with a `.blend` source whose golden carries a `sprite_frame` track so the CI re-export diff covers the path.

**Trigger:** an animator authors a frame swap (blink, mouth phoneme) on the timeline and asks why Godot does not play it.

### visibility animation track - Blender export path

**What:** the schema defines a `visibility` track type, but neither side implements it. The Godot importer stubs it - `animation_builder.gd` matches `"visibility"` and only `push_warning("not implemented yet")` - and nothing on the Blender side emits one. Only the schema enum plus a dead importer branch exist. (Not to be confused with `slot_attachment`, which is fully wired and emits per-attachment `:visible` tracks - that is how slot swaps animate today.)

**Why:** either complete the loop on both sides (a keyframed `hide_render` / `hide_viewport` or a `proscenio.visible` channel becomes a `visibility` track, and the importer builds the value track) or retire the schema enum + importer stub so the format stops advertising an unimplemented track type.

**Trigger:** a feature needs timeline-driven show / hide of a sprite (swap a whole limb on / off), or a code-health pass decides to drop dead importer branches.

### Sprite appearance fields - modulate / draw order / flip / blend-mode passthrough

**What:** the `.proscenio` sprite types (`PolygonSprite`, `SpriteFrameSprite`) carry geometry, skinning, frame metadata and texture, but none of the *appearance* properties that Godot's `Polygon2D` / `Sprite2D` expose and 2D artists routinely use:

- **modulate / colour tint** - no per-sprite colour; a tinted material in Blender is lost. Also absent as an animation track (Godot animates `modulate` freely).
- **draw order / z_index** - draw order is implicit in the `sprites[]` array order only; there is no explicit per-sprite `z_index`. Interleaving sprites across bones (an arm in front of the torso but behind the head) is not expressible.
- **flip_h / flip_v** on the `Sprite2D` path.
- **blend_mode** - the *PSD manifest* already carries `blend_mode` (`PolygonLayer.blend_mode` / `SpriteFrameLayer.blend_mode`, mapped to a Blender material on import), but the `.proscenio` sprite has no `blend_mode` field, so the value is dropped at the Blender → Godot hop. This is a pipeline discontinuity, not just a deferred feature: the upstream schema knows the blend mode and the downstream format throws it away.

**Why:** the format was scoped to geometry + skeleton + skinning + frame swap + slots + TRS animation - enough for a rigged character to deform and play. Appearance fidelity (tint, layering, blend) was outside the MVP. But these are not exotic: blend_mode is already half-plumbed (PSD → Blender), modulate and z_index are first-class 2D rendering knobs, and their absence means an artist's colour / blend / layer choices silently do not reach Godot.

**Scope sketch:** add optional `modulate: [r, g, b, a]`, `z_index: int`, and `blend_mode` (reuse the manifest's `normal | multiply | screen | additive` literal) to both sprite variants; `flip_h` / `flip_v` to `SpriteFrameSprite`. Writer reads them from the Blender material / object; importer stamps the matching node property. For animation, add `modulate` and `z_index` as new track-target properties (or new track types) once the static fields land. Keep every field optional and defaulted so existing v1 goldens round-trip unchanged - additive optionals need no `format_version` bump.

**Out of scope for this entry:** `material` / custom shader references (collides with the GDScript-only, no-GDExtension architecture rule) and method / audio tracks (separate animation-events entry above).

**Trigger:** an artist tints or sets a blend mode on a sprite in Blender / Photoshop and finds it flat / normal in Godot, or a scene needs explicit cross-bone draw layering the array order cannot express.

### Sprite pivot / Sprite2D.offset from the Blender origin

**What:** a `sprite` element (`SpriteElement`) exports only `type / name / bone / hframes / vframes / frame / centered / texture_region` (`writer/sprites.py` `build_sprite_frame`). It does NOT export the quad geometry or any pivot / offset. Unlike a `mesh` element - whose vertices bake in world position, so the Blender origin is honored implicitly - a sprite's authored Blender origin is discarded: positioning comes from the bone attachment, and the only pivot control that ships is the boolean `centered` (Godot `Sprite2D.centered`), which either centers the texture on the node origin or puts its top-left there. Godot's `Sprite2D` also exposes a free `offset: Vector2` that is never used.

**Why:** an artist who sets a deliberate pivot on a sprite quad in Blender (moving the object origin) expects that pivot to reach Godot; today it silently does not - only the centered / top-left toggle does. Deriving `Sprite2D.offset` from the Blender origin relative to the quad bounds would round-trip the authored pivot. Explains the `centered`-vs-origin confusion logged in `backlog-ui-feedback.md`; offset / pivot can ride the same schema bump as the Sprite appearance fields entry above.

**Scope sketch:** add an optional `offset: [x, y]` (or `pivot`) to `SpriteElement`; the writer computes it from the quad's origin-vs-bounds; the importer stamps `Sprite2D.offset` and respects `centered`. Keep it optional + defaulted so existing v1 goldens round-trip unchanged.

**Trigger:** an artist sets a sprite pivot in Blender and finds the Godot Sprite2D ignores it (only centered / top-left honored).

## Blender addon

### Sprite rigid single-bone bind (Weight Paint is mesh-only)

**What:** a `sprite` element (Sprite2D) is rigid - it attaches to a single bone, not deformed by a weight map. The reorganized Weight Paint panel (the `apps/blender` UI restructure, opened by the spec 021 audit) polls `element_type == "mesh"`; a sprite instead gets a one-bone rigid bind control (effective weight 1 on its `parent_bone`).

**Why:** weight paint on a Sprite2D is meaningless; surfacing the weight workflow on sprites invites the user to author weights the exporter ignores. Isolating the rigid-bind path keeps the sprite contract honest and the Weight Paint panel mesh-only.

**Trigger:** lands with the Weight Paint panel in the UI restructure (spec 022); until then sprites are bound via bone-parenting as today.

### Panel helper consolidation (cross-module dupes)

**What:** the spec 022 restructure split the sidebar into 13 panel modules, and small private context accessors recur across them. `_scene_skinning` + `_active_armature` were duplicated in `mesh_generation.py` and `weight_paint.py` (consolidated into `panels/_helpers.py` during the PR #96 review); similar one-liners still live module-local elsewhere (`_active_mesh_props`, `_explicit_target`, `_scene_props`, the per-module `_is_*` predicates). Sweep `panels/` for accessors that are genuinely identical across modules and lift them into `_helpers.py`; leave module-specific ones where they are.

**Why:** CodeRabbit flagged the `_scene_skinning` / `_active_armature` pair on PR #96. Duplicated accessors drift when one copy changes and the other does not, and `panels/_helpers.py` already exists as the home for cross-cutting panel helpers (header drawer, mode predicates, scene accessors).

**Trigger:** low priority - fold in when next touching the panel modules, or when a third copy of any accessor appears.

### Element-type gating: mesh-only tools warn on sprite + sprite stays a quad

**What:** the Mesh Generation panel + the `automesh_from_alpha` operator poll only on `obj.type == "MESH"` (`panels/mesh_generation.py` `_active_is_mesh`, `operators/automesh/automesh.py` `poll`), so they show and run on a `sprite` element too - a sprite is a quad MESH in Blender. Automesh-ing a sprite turns its quad into a deformable annulus with no warning, silently breaking the sprite_frame slicing contract. The Weight Paint panel already gates correctly on `element_type == "mesh"` (`panels/weight_paint.py` `_is_mesh_element`); Mesh Generation does not. Conversely there is no validation that a `sprite` element stays an exact quad (the hframes/vframes grid assumes it).

**Why:** the element-type split (`sprite` = Sprite2D, rigid + sprite_frame grid; `mesh` = Polygon2D, deformable) is a contract. Mesh-only tools (automesh, weight paint, bind) are meaningless on a sprite and should warn or disable; a sprite that stops being a quad breaks slicing downstream. The only thing exclusive to a sprite that a Polygon2D cannot do is the sprite_frame spritesheet grid; everything else (bone deform) is mesh-only.

**Scope sketch:** make Mesh Generation gate on `_is_mesh_element` like Weight Paint (warn-not-hide), or have `automesh_from_alpha` report a warning when `element_type == "sprite"`. Add a validation check that a `sprite` element's mesh is a single quad (4 verts, 1 face) and warn otherwise. Pairs with the sprite rigid single-bone bind entry above.

**Trigger:** a user selects a sprite element and the Automesh from Alpha button runs without warning, or a re-meshed sprite exports a garbled sprite_frame grid.

### Drive slot attachment from a bone (slot analog of Drive-from-Bone)

**What:** the Element panel has Drive from Bone (a bone rotation / translation drives a sprite property via a driver + expression). There is no equivalent for slots: driving which attachment is active (the slot's visible child) from a bone. Today a slot swap animates via keyframed attachment visibility (`slot_attachment` tracks), but there is no driver-based "this bone angle selects this attachment" authoring path.

**Why:** the ergonomics that make Drive-from-Bone useful for sprite_frame (a controller bone picks the frame) apply to slots (a controller bone picks the attachment - hand-pose selector swapping open / fist / point meshes, head turns). Needs a driver target on the slot's active-attachment state plus a panel UX mirroring Drive-from-Bone (range mapping rather than a raw expression - see the Drive-from-Bone UX rework in `backlog-ui-feedback.md`).

**Trigger:** a rig wants a bone to select among slot attachments (hand poses, head turns) without hand-keyframing visibility.

### Spec 016 follow-up: god-module splits + low-risk companions (shipped)

Spec 016 landed the system reorganization (`core/`, `core/bpy_helpers/`, and `operators/` grouped by domain; the `_shared/` infra tier; Custom Property keys consolidated). The three deferred items shipped as the 016 follow-up, behavior-preserving and proven by the headless gate set (ruff + mypy + `uv run pytest tests/` + the Blender fixture and operator suites):

- **Operator god-modules split (done).** `automesh_authoring` projection moved to `core/bpy_helpers/_shared/viewport_math` and its status-bar chords to a sibling `_status_bar.py`. `quick_armature` view-pose / region math moved to `viewport_math`, its chord cheatsheet to `_status_bar.py`, and its GPU preview draw to `_overlay.py`; the bone-length tolerance moved to `core/armature/quick_armature_math`. Registered draw / header callbacks stay in the operators (they bind live class state). The dead `_build_status_bar_text` was dropped.
- **import_photoshop reports through `core.report` (done).** Replaced raw `self.report` + inline `"Proscenio: "` with `report_info` / `report_error`.
- **`scene_has_pre_pack_snapshot` relocated (done).** Now in `core/bpy_helpers/atlas/snapshot.py`; the atlas panel imports it from core instead of reaching into `operators/atlas_pack`.

**Verified:** the moved modal draw / status-bar callbacks run only during the live modal, which the headless gates do not exercise, so this was confirmed by an in-editor smoke test of both the Quick Armature and Automesh Authoring modals (preview overlay, axis-lock guideline, status-bar chords, outside-canvas tooltip) - all intact at runtime.

### Validator internal naming (sprites vs elements)

The element-vocabulary rename (the former spec 019) renamed the wire end-to-end and swept the Blender / Photoshop / Godot / fixtures internals, but `packages/validator` was outside its Phase 1-4 scope and never touched. It still uses the pre-rename internal names `report.sprites` + `SpritePayload` (`measurement.py:177`, `report.py:63`). Internal accumulator names, not the wire field, so nothing breaks. Rename to `report.elements` / `ElementPayload` (and the `test_validator_report.py` import) the next time the validator is touched. Low priority, cosmetic.

### Spec 021 follow-up: unfinished discovery + buckets B/C

The spec 021 UI/UX audit is pruned. Its IA design fed specs 022 (restructure), 023 (help / docs / i18n), and 024 (preferences), and the sprite-rigid-bind + atlas findings were filed elsewhere in this backlog - that purpose is served. Three threads outlived it:

- **Phase A / B discovery (never finished).** The reconciliation against `backlog-ui-feedback.md` was only partly run (~15 areas pending, much now overtaken by spec 022 shipping); the hands-on per-tool audit (GOOD / BAD / MISSING, needs the maintainer in a GUI Blender) never ran. Resume only if a fresh holistic UX pass is wanted.

- **Bucket B - per-asset pixels-per-unit (cross-app).** PPU is a single global value today (one export field, default 100). The audit flagged an end-to-end per-asset PPU so different elements can carry different Blender-world-to-pixel ratios. Spans Blender (a per-element field), the schema (`.proscenio` shape), and the Godot importer. Schema-level, post-launch - a `format_version` concern.
- **Bucket C - per-tool feature gaps.** Bone-collections management inside Proscenio (create / assign / toggle Blender bone collections from the Skeleton panel), and richer bone-hierarchy editing (the read-only connected / relative-parent readout shipped in spec 022; the editing did not). Both are feature work, not IA.

### Spec 022 follow-up: in-editor smoke + guide-doc rename sweep

Spec 022 shipped and verified the 13-panel restructure (2026-06-09: panels renamed, `feature_status` bands updated, the stale `skinning` fallback gone, operator suite green at 50, addon registers headless). It also renamed the operator `proscenio.automesh_from_sprite` -> `automesh_from_alpha` and the Skinning panel -> Mesh Generation. Two deferrals outlive the spec:

- **In-editor visual smoke (workstation).** Headless cannot render panels. At a GUI Blender, confirm the sibling-panel tree (nothing nested under the version line), the accordion subpanels collapsing independently, the warn-not-hide hints, the per-header badge + `?`, and the `debug_mode` preference showing / hiding Diagnostics + the Debug Pipeline subpanel. A layout regression found here is a new bug.
- **Guide-doc rename sweep.** `docs/00-guides/00-basic/02-blender.md` and `docs/00-guides/01-advanced/02-blender.md` still say "Automesh from Sprite" / "Skinning panel"; `backlog-manual-testing.md` references the old names too (a historical log, lower priority). The same two guide pages also carry pre-Element-rename vocabulary - fold this into the spec 019 guide-doc residual for one holistic pass. Verified IA map (while shipping #100): the old "Skinning" panel split into "Mesh Generation" (Automesh from Alpha / Automesh Interactive / Debug Pipeline) and "Weight Paint" (Bind / Edit Weights / Snapshot / Sidecar IO / Weight Transfer); "Active Sprite" persists as a sibling of "Active Mesh" under an "Element" parent (NOT "Active Element"). The workflow prose needs rewriting against this, not find-replace.

**Trigger:** the visual smoke at the next workstation session; the docs sweep follows the review (or sooner - the renames are known).

### Spec 024 follow-up: docs-URL preference (D3) + overrides (D4 - none)

Spec 024 shipped the full preferences surface (2026-06-09: the `errors / info / debug` `log_level` enum gated once in `core/_shared/report`, the `debug` tier now backed by real per-item traces - importer planes, automesh counters, validation issues - so it is not inert; the `debug_mode` bool; all under a Developer box in `addon_prefs.py`). Two locked decisions defer the rest by design:

- **Docs-URL as a preference (D3).** The docs base is the constant `_DOCS_BASE` in `core/help_topics.py`. Promote it to a preference only if a real need surfaces (a self-hosted docs mirror, a version switch).
- **Per-project overrides (D4) - decided NONE.** The scene PropertyGroup already covers per-`.blend` state; preferences stay user-global. Recorded so it is not re-litigated.

**Trigger:** the docs-URL pref lands when a second docs target appears.

### Spec 023 follow-up: i18n tables, see-also URLs, docs depth

Spec 023 shipped and verified the help / docs / i18n layer (2026-06-09: per-subpanel help topics, the `doc_url` + "Open online docs" button, the Godot badge icon via `bpy.utils.previews`, the `bpy.app.translations` isolation mechanism in `core/i18n.py`, and the `docs/02-blender-addon/` reference section). Three deferrals outlive the spec, all by-design:

- **Per-locale translation tables (STUDY non-goal).** The mechanism is wired - English msgids are the source and `bpy.app.translations` auto-translates registered strings - but `TRANSLATIONS` is empty ("translate as we go"). Populate by appending `(locale, {(msgctxt, msgid): msgstr})` rows; no call-site changes.
- **Migrate inline see-also refs to online URLs.** The `specs/` / `examples/` see-also entries render as plain labels because they do not resolve in an installed (zipped) extension; the working clickable link is the per-topic `doc_url` / "Open online docs" button. Convert the local refs to online URLs once the matching pages exist.
- **Expand the addon reference pages.** `docs/02-blender-addon/` is a first cut (one brief page per panel mirroring the `?` help); add screenshots and deeper per-tool detail as the panels settle.

### General rig orientation detection

Writer assumes the 2D plane is Blender XZ (Z up, Y into screen). Some users author on XY (Y up). Future work: detect the dominant plane from the armature's bone axes or expose an export option.

### Multi-polygon mesh meshes

`writer._build_sprite` only emits the **first** polygon of a mesh. A mesh with multiple disjoint polygons (mask cutouts, complex topology) is silently truncated. Multi-polygon support would either:

- emit one Proscenio sprite per polygon (cleanest), or
- use `Polygon2D.polygons` array for multi-island Polygon2D nodes (preserves original mesh structure).

### Atlas region authoring helper

User UV-maps each plane in Blender to a region of the atlas; the writer reads whatever UVs are there. There is no Blender operator to "snap UV to atlas region by name". Could ship as a Phase 2 quality-of-life operator.

### Exclude sprites from the shared atlas pack

`Pack Atlas` is all-or-nothing today: it packs every mesh with a texture - `polygon` and `sprite_frame` alike - into one sheet. This is correct (a packed sprite_frame still slices: Godot divides its `region_rect` by `hframes`/`vframes`, not the whole atlas), but not always wanted - a large spritesheet grid bloats the shared atlas, and an effect sprite may prefer its own texture. Add an opt-out: a per-object `exclude_from_atlas` flag (keeps its own texture, skipping the pack entirely - unlike `material_isolated`, which still uses the atlas image), or auto-isolate `sprite_frame` so spritesheets keep their own composed `_spritesheets/` sheet. Pairs with Multiple atlases per character.

**Trigger:** an artist packs a rig and the atlas balloons to fit a big spritesheet, or wants one effect sheet kept apart.

### Validate sprite_frame UV covers the full sheet

The atlas packer slices each source by its mesh UV bounds. A `sprite_frame` quad is imported with full-sheet UVs (`(0,0)-(1,1)`), so the packer takes the whole sheet as one block and the `hframes`/`vframes` grid survives the round-trip. If a user hand-edits a sprite_frame quad's UVs down to a single cell, the packer would pack just that cell and the grid breaks silently in Godot. Add a Validate check that warns when a `sprite_frame` mesh's UV bounds are not the full sheet.

**Trigger:** a re-UV'd sprite_frame exports a packed atlas whose frames come out garbled in Godot.

### Export bundle: gather the .proscenio and its textures into one folder

The `.proscenio` references its textures by bare filename, and the Godot importer resolves them relative to the document's own folder (same directory, no subfolders). Today the writer drops the `.proscenio` next to the `.blend` and assumes the referenced PNGs (packed atlas, per-sprite, composed spritesheets) are siblings - but PSD-import assets live in `images/` / `_spritesheets/` subfolders, so the user must gather everything into one folder by hand before Godot can import it. Add an export option that writes the `.proscenio` plus copies of every texture it references into a single output folder, named by the user with a sensible default (e.g. `<doc>_proscenio/`), producing a self-contained bundle that drops straight into a Godot project. Keeps the bare-filename contract intact - it just guarantees co-location.

**Trigger:** a user exports, drops only the `.proscenio` into Godot, and the import warns "atlas not found" or sprites render blank because the PNGs stayed behind.

### Weight-preserving PSD re-import

Re-importing a manifest rebuilds every matched plane's mesh - `importers/photoshop/planes.py:_ensure_mesh` runs `clear_geometry()` then stamps a fresh quad - so any Automesh densification and the painted vertex weights are lost on re-import (the weight values live in the vertex data that is cleared; only the vertex-group names, which sit on the object, survive). That makes re-importing PSD art after skinning destructive, and the iteration loop only safe before a sprite is skinned. The Automesh regen path already has a snapshot-and-reproject mechanism (`core/skinning/weight_snapshot`); wiring the same snapshot-before / reproject-after around the manifest re-import (for sprites whose UVs and bounds did not change, at least) would let an artist iterate the PSD after rigging without redoing weights. Pairs with the mid-edit non-destructive re-rig idea in [`docs/01-project/04-deferred.md`](../docs/01-project/04-deferred.md).

**Trigger:** an artist tweaks a PSD layer, re-imports, and finds the rig's weights (and automesh) on every sprite wiped back to a flat quad.

### IK constraints round-trip (Blender -> Godot)

Planned - the project should support IK end to end. Today IK is Blender-only: the writer exports raw bone keyframes, not constraints, so an IK-posed animation reaches Godot only if it is baked to bone keyframes first. Two implementation paths to evaluate: bake the IK-resolved motion into the bone transform tracks at export time (no schema change, motion is flattened), or detect the IK chain and emit Godot's built-in 2D skeleton IK modifiers (`SkeletonModification2D*` on a `SkeletonModificationStack2D`) so it stays live in-engine (needs a schema field for the chain). Until it ships, bake before export or rebuild IK in-engine post-import.

**Trigger:** an animator rigs with IK in Blender and the motion is flat in Godot, or asks to keep IK live in the engine.

### NLA strips to Actions

Planned - the project should support NLA. The writer iterates `bpy.data.actions` and ignores the NLA stack, so motion composed from non-linear strips does not export; the animator must bake to a single Action first. The target is to consume the NLA at export: flatten each object's strips (honouring blend mode and influence) into one baked Action per animation, so a strip-composed timeline round-trips to Godot's `AnimationPlayer` without manual baking.

**Trigger:** an animator layers walk + overlay on the NLA, exports, and Godot plays only the base Action (or nothing).

### Auto-detect 2D rig vs 3D mesh

Currently the writer assumes every mesh is a 2D sprite plane. A future check could skip 3D meshes or warn.

### Camera orthographic preview helper

A Blender operator that adds a properly configured ortho camera for pixel-perfect preview, matching the dummy's `pixels_per_unit`.

### IK chain helper

Blender-side scaffolding that adds an IK constraint stack to a selected bone chain in one click: target bone, pole bone, chain length, defaults. This helper is pure authoring QoL and does not itself touch the `.proscenio` output - exporting IK is tracked separately (see IK constraints round-trip). Pairs with the existing Toggle IK shortcut, which currently flips a per-bone constraint but does not scaffold a whole chain.

**Trigger:** an animator complains about repeatedly walking through the constraint panel to set up arm + leg IK on a fresh rig.

### Joystick / slider authoring

Multi-pose blend widget. The artist authors N corner poses (e.g. mouth shapes); a 2D widget interpolates between them as the artist drags a slider in the viewport. Pairs with Godot's `AnimationTree.BlendSpace2D` so the imported character can blend the same way at runtime. Requires a Blender PG carrying the pose set + corner coordinates, plus an exporter path that emits the blend space.

**Trigger:** the first character with parametric facial expressions (mouth phonemes, eye direction) lands.

### Onion-skin overlay

Viewport draw handler that renders the rest pose plus N keyframes around the current playhead in low-opacity outlines. Authoring shortcut for animators tweaking timing without scrubbing back and forth. Pure GPU overlay; no schema or export impact.

**Trigger:** an animator reports that scrubbing the timeline to compare poses is the slowest part of polishing an action.

### Pose library evolution

The pose-library operator (`PROSCENIO_OT_save_pose_asset`) shipped as a thin shim over Blender's native pose-asset system. Evolutions worth carrying:

- One-click "apply pose to selection" that walks the asset library and lets the artist pick.
- Auto-categorise poses by armature name so the Asset Browser stops mixing rigs.
- Pose-asset thumbnails rendered through the Proscenio preview camera so the swatches are pipeline-flat instead of viewport-shaded.

**Trigger:** the second character ships and the artist hits the asset-browser mixing problem.

### Quick Armature follow-up candidates

Items deferred from the quick-armature spec STUDY out-of-scope after PR #50 shipped. Each is a self-contained refinement of the existing operator; they do not require a new spec, only a follow-up iteration (or a smaller PR) when demand justifies the work.

- **Pick-parent-in-viewport.** `Shift+click` an existing bone tip during the modal to re-target the next bone's parent. Useful for branching skeletons (humanoid second-chain off the spine) without exiting the operator. Medium effort; chord vocabulary already has `Shift+click` available because the press-time `Shift+drag` reads only on PRESS+drag combo. Highest user value on the deferred list.
- **Bone naming chain-aware suffixes.** Today the prefix gives `qbone.000`, `qbone.001`, `qbone.002` flat. A chain-aware mode would emit `spine.01`, `spine.02`, `spine.03` per chain, resetting the counter at every new-root press. Small effort, medium value. Couples to the rigging-guide naming convention from the quick-armature spec's RESEARCH addendum.
- **Mirror auto-suffix `_L`/`_R`** when X-Mirror is enabled in the armature data. Auto-creates the symmetric pair on each press so humanoid rigs save half the work. Small effort but only pays off with a humanoid fixture - currently no Proscenio fixture exercises symmetric rigs end-to-end.
- **Numeric length input.** `Tab` to type `0.5` Enter (Blender E-extrude convention). Bigger lift because it needs a text-input field on a modal operator; precision authoring win when implemented.
- **Local-axis lock.** Today X / Z = global axis only. Pressing the same axis twice could switch to the active armature's local axis (Blender extrude convention). Only relevant when an armature is rotated; small effort but small value for the current XZ-plane-locked workflow.

The remaining quick-armature deferred items are now successor specs (quick-armature STUDY successor-considerations section): auto-attach mesh / sprite to bone (needs slot-system maturity), Quick Mesh operator (sibling tool, would lift `core/bpy_helpers/modal_overlay.py` scaffolding), i18n of the cheatsheet copy, addon-wide modal feedback library extraction.

### Weight-paint productivity follow-up candidates

Items locked as the productivity follow-up tier of the weight-paint-automesh spec Design surface > Out of scope + the productivity polish TODO tier. Each is a self-contained productivity refinement on top of the first cut; they do not require a new spec, only a follow-up iteration when demand justifies the work.

- **Soft vs Hard bone toggle (Adobe Animate lift).** Per-bone enum on the vertex group metadata that flips between proximity-falloff ("soft") and single-nearest ("hard") binding. Rebind operator re-derives weights respecting the mode. First cut covers via `bind_init_mode` at bind time; this adds the runtime per-bone toggle. Trigger: user complains that proximity bleed between adjacent bones is too soft on a specific limb.
- **Bone strength region painting (Moho lift).** Per-bone elliptical / capsule influence widget. Drag a handle along the bone in the viewport to grow / shrink radius. Region drives initial weight map procedurally; weight paint becomes fix-up. Couples to a custom viewport draw + gizmo handle. Highest user-value follow-up candidate by reach. Trigger: feedback that proximity default does not give enough control for long hair, tails, hands.
- **Multi-mesh batch bind.** Bind operator takes selected meshes (not just active) and applies the same algorithm against the picker armature. Trigger: imported-character workflow with N sprites + 1 rig stresses this.
- **Weight transfer between sprites.** `proscenio.copy_weights_to_selected` operator. Active mesh = source; selected meshes = targets; nearest-world-position vertex lookup copies weight dict. Solves COA Tools 2 issues [#18](https://github.com/Aodaruma/coa_tools2/issues/18) + [#73](https://github.com/Aodaruma/coa_tools2/issues/73). Foundational for Live2D-style line / colour / shadow layered sprites.
- **Live pose-mode preview in weight paint.** Scrub bone to posed angle / see deformation / scrub back without leaving Edit Weights modal. Adds pose-scrub overlay + hotkey to toggle rest pose. Trigger: user wants verify weights vs deformed pose without modal exit.
- **Sidecar import / export.** Operator dumps weight sidecar JSON to file + loads from file. Enables version-controlled weight backups outside the `.blend`. Trigger: user asks to back up weight work to git.
- **Brush curve presets dropdown.** Quick-select brush curve presets named for common 2D tasks (Hard edge / Soft falloff / Crease / Smooth blend) via dropdown in the Edit Weights modal status pill. Saves a 6-click trip to the brush curve editor per session.

### Weight-paint aspirational candidates

Heavier lifts than productivity follow-up; each is a candidate for a follow-up spec if the demand surfaces. Listed here so the future reader sees what was considered + why deferred.

- **Auto-Patch joint cover at articulations (Toon Boom Harmony lift).** One-click joint-cover operator: given two child meshes sharing a parent bone, generate the seam geometry + weight blend that hides the inner-elbow hole as the joint bends. Requires both child-mesh detection (which sprites belong to which side of the articulation) and a custom seam generator (boundary-following triangulation). Trigger: humanoid fixture lands + user complains about inner-elbow gap.
- **Cubism Glue equivalent.** Seam-binds overlapping vertices of two meshes with a weight slider biasing which side dominates. Different surface than Auto-Patch (covers any seam, not just articulations). Trigger: layered-sprite use case stresses this.
- **Smart-Bone-style corrective drivers (Moho lift).** Per-bone shape key driven by bone rotation; user records a corrective pose at a specific angle, the addon emits a driver. Belongs in a future animation-system spec not the weight-paint-automesh spec (authoring), but listed here for visibility because the trigger is the same as Auto-Patch.
- **Mirror humanoid binding.** One mesh on one side, click to mirror to other. Couples to symmetric rigs. Trigger: first humanoid fixture lands end-to-end.
- **Bezier brush stroke for alpha-boundary trace.** Adds a free-draw path on top of the one-shot automesh. COA Tools 2 uses straight-segment strokes; Bezier would give higher-control silhouettes for stylised shapes. Requires draw modal with tablet release detection (the gesture helpers are already in place from the first cut).

### Blender 4.3 legacy actions compatibility

`writer._action_fcurves` falls back to `action.fcurves` when present. Untested against Blender 4.2 LTS - may need fixture-based regression once the addon is shipped.

### Split PropertyGroup vs Custom Property storage by intent (target: 1.0.0)

**What:** the current authoring-panel design mirrors every PropertyGroup field on `Object.proscenio` to a sibling raw Custom Property (`obj["proscenio_type"]`, `obj["proscenio_frame"]`, ...) via `update` callbacks, and `core/hydrate.py` rehydrates the PG from CPs on `load_post`. The 11 fields in `OBJECT_PROPS` are mirrored uniformly, which is over-broad: some fields are editor-time only and could live as PG-canonical with no CP at all, while others are animatable / driver targets where the CP is the durable storage and the PG is just a typed widget projection.

**Why:** PropertyGroup data is backed by IDProperty but its visibility depends on the addon's RNA descriptor being registered. Disable → save → reenable cycles can purge orphaned IDProperty data depending on Blender version, so PG is a brittle home for anything that must survive addon-absent file states or be a stable driver target. Raw CPs have none of those constraints, which is why Rigify and similar mature addons keep the *animator-facing* surface (IK/FK switches, layer toggles) on CPs and reserve PGs for *generator-internal* metadata. Mirroring everything pays the cost (doubled write paths, sync risk, undo desync, `deferred_hydrate` timer, dual-key reader fallback in `read_field`) for fields that do not need the resilience. Mirroring nothing loses real resilience for fields that do (`frame` is keyframable into Godot's `AnimationPlayer`; Drive-from-Bone wires drivers onto sprite properties). Blender also cannot keyframe a field nested inside a PropertyGroup ([T48975](https://developer.blender.org/T48975)), so an animatable / driver-target field has to live as a top-level Custom Property regardless.

**Decision (locked):** option **A** - split by intent. Editor-time-only fields become PG-canonical with no CP mirror; animatable / driver-target fields become CP-canonical with PG as a typed widget wrapper. Documented as a deliberate contract, not legacy debt - rewrite the `properties/__init__.py` docstring to call this out instead of describing CPs as "legacy".

**Scope sketch:**

- PG-canonical (drop the CP mirror): `sprite_type`, `region_mode`, `region_x`, `region_y`, `region_w`, `region_h`, `material_isolated`.
- CP-canonical (PG is the typed widget; writer reads CP directly): `frame`, `hframes`, `vframes`, `centered`, `proscenio_slot_index`.
- Drop the mirror entirely (PG-only, pure UI / editor state never exported and never a driver target): `is_outliner_favorite`. It carries a CP mirror today via the blanket `on_any_update` path yet is not even in the `hydrate` map - asymmetric dead weight.
- Reader (`writer/sprites.py`, slot index reads, etc.) drops the `read_field(pg_field=..., cp_key=..., default=...)` dual fallback and reads each field from its canonical home.
- `_update_*` mirror callbacks deleted for the PG-canonical group; retained only as PG → CP one-way for the CP-canonical group (since the PG is the widget the user touches).
- `core/hydrate.py` becomes a one-shot migrator: on `load_post`, hydrate any `.blend` that still has legacy CPs in the PG-canonical group into the PG, then *delete* those CPs so the field has a single source of truth post-migration. Gate behind a `format_version` check on the scene PG so it runs at most once per file.
- `_handlers.py`: keep `load_post` for the one-shot migrator; `save_pre` and `deferred_hydrate` timer can likely be deleted once the mirror is gone (revalidate during the rewrite).
- Drive-from-Bone operator: target the CP path for animatable fields so the driver `data_path` is `pose.bones["X"]["proscenio_frame"]`-style rather than the nested PG path. Reduces driver fragility on linking / append.
- Collapses the duplicate field-mapping tables (code-duplication spec finding N14): today `core/hydrate.py` `OBJECT_PROPS` (11 rows) is a hand-maintained subset of `core/mirror.py` `OBJECT_MIRROR_MAP` (14 rows), so adding a field means editing both in lockstep. After the split each field has a single canonical home and the two tables fold into the per-intent mapping, removing the lockstep hazard. The dedup pass deferred N14 here rather than force-merge the tables, since this redesign reshapes them anyway (merging now would just be re-undone).

**Trigger to revisit:** before 1.0.0 release. Block on this landing so the public surface ships with the final storage contract; post-1.0 schema or storage migrations cost real users.

**Out of scope for this entry:**

- Library-override / linking semantics for the surviving PG fields (separate concern; address only if a user reports issues).
- Schema `format_version` bump - the contract on disk does not change; only the in-`.blend` storage shape does. May still want a `format_version` bump on the *scene PG* to gate the migrator.

## Godot plugin

### Node name collision polish

When a Bone2D and a child Polygon2D share a name (e.g. both called `head`), Godot auto-renames the polygon to `head_001`. Acceptable but ugly. Either prefix sprite names in the importer (`sprite_head`) or document the convention.

### Plugin-uninstall warning UI

Currently the rule "scene must work without the plugin" is enforced by review. A small editor check that opens a generated scene with the plugin disabled and asserts no errors would be a CI-friendly guard.

### `project.godot` warning tuning for JSON boundary

`apps/godot/project.godot` `[debug]` carries only `untyped_declaration=2`, `return_value_discarded=1`, `treat_warnings_as_errors=true`. The `unsafe_property_access` / `unsafe_method_access` / `unsafe_cast` / `unsafe_call_argument` families fire on every line that downcasts `JSON.parse` output, forcing `# warning-ignore` clutter. **Why deferred**: current builders use bare `Dictionary` at the JSON boundary, which compiles cleanly without the pins because the casts are implicit. **Trigger to revisit**: when tightening builders to use `Dictionary[K, V]` typed collections (see entry below), pin the four unsafe-access keys to `0` so the downcasts at the JSON edge stay quiet without per-line ignores.

### Annotate `: Variant` on JSON-boundary lookups in Godot builders

Three lookups currently bind without an explicit type: `polygon_builder.gd:114`, `skeleton_builder.gd:36`, `sprite_frame_builder.gd:74` (each of the shape `var x = dict.get("key", null)`). Conventions explicitly allow bare `Dictionary` at the decode boundary, but the `var x = ...` form trips the "Never `var x = 0`" reading on hover. **Why deferred**: cosmetic, no runtime impact, the surrounding code immediately tests the value for null. **Trigger to revisit**: when refactoring the builders to typed collections, or when a reader confuses these for missing type annotations.

### Sprite2D region_filter_clip for packed sprite_frame

`sprite_frame_builder.gd` sets `region_enabled` + `region_rect` for a sprite_frame packed into an atlas but does not set `region_filter_clip_enabled`. Godot recommends enabling it for atlas usage so a frame does not sample neighbouring atlas pixels at the region edge under linear filtering. The packer's padding mitigates the outer-block edge and nearest filtering sidesteps it entirely, so this is a quality guard, not a correctness fix. Set `region_filter_clip_enabled = true` whenever `region_enabled` is set.

**Trigger:** a packed sprite under linear filtering shows a one-pixel seam from an adjacent atlas region.

## Photoshop and Krita

### Spec 018 follow-up: png-writer findLayerByPath (shipped in #100)

Shipped: `png-writer.ts` now calls the shared `findLayerByPath`, dropping the local `resolveLayer`; the latent non-Array UXP skip/throw and the duplicate fourth walk are closed.

**What (historical):** [`apps/photoshop/src/api/png-writer.ts`](../apps/photoshop/src/api/png-writer.ts) keeps a local `resolveLayer` that walks `doc.layers` / `layer.layers` with a bare `Array.find`. The shared [`api/_layer-find.ts`](../apps/photoshop/src/api/_layer-find.ts) `findLayerByPath` - already used by `layer-rename`, `legacy-migration`, and `ps-selection` - wraps the walk in `toArray()` plus NFC name matching precisely because UXP layer collections are not always real Arrays. The spec 018 TODO ticked "replace png-writer `resolveLayer` with the shared `findLayerByPath`", but the code still carries the local copy.

**Why it matters:** a non-Array UXP layer collection makes the local `Array.find` throw or miss, so an export can silently skip a layer or fail; the duplication also leaves the NFC / robustness fixes protecting only three of the four layer-walk call sites. The gate stays green because the vitest fixtures back layers with real Arrays, so the gap is latent.

**Scope sketch:** import `findLayerByPath` from `./_layer-find`, swap the `resolveLayer(sourceDoc, write.layerPath)` call, delete the local function. `tsc --noEmit` + `eslint src` + `vitest run` should stay green. Same walk as the "Stable layer identity in `PngWrite.layerPath`" item below.

**Trigger to revisit:** before relying on a png export against a deeply nested or programmatically built PS document, or the first wrong-PNG / missing-layer export report.

### JSX exporter port from `coa_tools2`

Port `coa_tools2/Photoshop/coa_export.jsx` forward into `apps/photoshop/proscenio_export.jsx`. Adapt output JSON to the format documented in `.ai/skills/photoshop-jsx-dev.md`.

### Krita exporter

`coa_tools2/Krita/coa_export.py` works in Krita 4.x. Phase 2 port-forward target.

### GIMP exporter

`coa_tools2` has a GIMP path. Lower priority - fewer 2D animation users on GIMP.

### Deferred Photoshop tags (after the photoshop tag system)

Tags evaluated during the photoshop tag system research pass that did not make the v1 taxonomy. Each was deferred for a documented reason. Promote into a future photoshop tag system iteration or a successor spec when a real workflow surfaces the need.

#### `[slice:l,t,r,b]` - Cocos-style 9-slice

Encodes 4 corner insets so a single sprite scales as a 9-slice tile (UI panels, scalable backgrounds). Cocos Creator and Unity ship this. **Why deferred**: Proscenio's current consumer set is rigged characters, not UI; no real workflow surfaces 9-slice today. Trigger to revisit: first UI-focused fixture lands.

#### Head-turner view groups (Adobe Character Animator)

Groups named `Frontal` / `Left Profile` / `Left Quarter` / `Right Quarter` / `Right Profile` collapse into a single mesh with swappable view variants. Specific to face puppetry. **Why deferred**: deep coupling to a face-rig template; harder to generalise across project types than the tag system in the photoshop tag system.

#### Pseudo-keyword auto-tagging (`Head`, `Mouth`, `Eye_Open`, ...)

Layer / group named `Head` automatically gets a face-region tag without an explicit `[head]` bracket. Mirrors Character Animator. **Why deferred**: tight coupling to one rig style (humanoid face puppet); collides with arbitrary artist naming. The bracket-tag explicit path (in the photoshop tag system) is cleaner and ships first.

#### `[isolated]` warp-independent flag (Character Animator's `+` prefix)

Marks a layer as "animated separately from its parent group" so the rig generator emits a dedicated pose key for it. **Why deferred**: Proscenio's rig model has no concept of "warp pose keys"; bones already encode separability. Reserved tag name: `[isolated]` (the `+` prefix from Character Animator is rejected as non-idiomatic for this project). Trigger to revisit: if the authoring-panel or future UV-animation work grows a "per-layer pose channel" concept.

#### Stable layer identity in `PngWrite.layerPath`

`PngWrite.layerPath` (and the parallel `_frameSources` on planned sprite_frame entries) is a chain of layer names. Photoshop allows siblings with duplicate names; if a user authors two children named `arm` inside the same group, the materialiser would resolve whichever appears first in `layer.layers` and silently write the wrong PNG. **Why deferred**: the doll oracle and every shipped fixture have unique names per group; ajv catches name collisions at the sanitize level for manifest entries. **Trigger to revisit**: a user reports a wrong-PNG export, or the photoshop tag system's tag inspector starts addressing layers by stable handle. Implementation hint: replace `string[]` with `Array<{ name: string; index: number }>` so the adapter can tie-break by position when two siblings share a name.

### the photoshop tag system v1 design decisions to revisit

Behaviours that landed as "by design" in the v1 taxonomy. Each is intentional today but worth re-examining once real artist usage stresses the assumption.

#### Nested `[merge]` collapses silently

A `[merge]` group inside another `[merge]` is flattened into the outer entry without a warning. Confirmed end-to-end on the doll oracle: `brow_states [spritesheet]` with `1 [merge]` containing `1.1 [merge]` emits two frames (`0`, `1`) instead of three, because `1.1` collapses into `1`. **Why deferred**: this is the obvious recursive semantics for `[merge]` and the doll authoring run produced no surprise; no warning means no false-positive fatigue. **Trigger to revisit**: an artist reports "I added a sub-layer inside `[merge]` and it vanished" without realising it was deliberate - then we surface a `merge-nested` info-level entry on the Validate tab so the collapse is visible at authoring time.

#### `[name:pre*suf]` parsed but planner does not rewrite

The tag parser accepts `[name:lh_*]` on a parent group, but the v1 planner does not rewrite descendant names against the template. Display names cascade via `joinName` (parent `__` child) unchanged. **Why deferred**: rewrite has subtle interactions with `joinName` (do we rewrite before or after joining? what wins when a child carries its own `[path:NAME]`?) and zero shipped consumer needs it today. **Trigger to revisit**: a fixture or external user wants prefix/suffix templating on a real group; then we design the rewrite order with the actual workflow in hand.

#### `kind: "mesh"` semantically equal to `kind: "polygon"` downstream

`[mesh]` emits `kind: "mesh"` on the manifest and the Blender importer stamps a `proscenio_psd_kind = "mesh"` custom property, but no downstream code branches on it yet (the Godot writer treats both as a single quad). **Why deferred**: the distinction exists so future mesh-deformation work and the continuous-UV-animation entry can tell editable polygons apart from rigid sprites. **Trigger to revisit**: a mesh-deformation feature ships; at that point the importer adds a Subdivision Surface modifier (or equivalent) only to `kind: "mesh"` entries.

#### Waist height drifts -1 px on the PS round-trip

`waist` ships as 173 px tall in the Blender-emitted manifest, returns as 172 px through the Photoshop exporter. Logged in [`backlog-bugs-found.md`](backlog-bugs-found.md). **Why deferred**: cosmetic (0.6 % drift on a 173 px region), and the round-trip oracle accepts it within tolerance. **Trigger to revisit**: an artist reports visible Y-offset on the waist mesh in Godot, or a future Photoshop-roundtrip cycle fixes the underlying off-by-one in the JSX-era PSD reader.

#### `pixels_per_unit` not round-tripped (defaults to 100 on re-export)

The Blender manifest emits `pixels_per_unit = 1000.0`; the PS round-trip emits `100.0` (hardcoded in the JSX exporter, inherited by the UXP port). Logged in [`backlog-bugs-found.md`](backlog-bugs-found.md). **Why deferred**: PPU only affects world-space placement in Blender, and the importer reads the PPU back out of the round-trip manifest correctly (it just lands at a different scale). **Trigger to revisit**: a future Photoshop-roundtrip cycle plumbs PPU through XMP so the round-trip is lossless.

### photoshop tag system follow-ups deferred from the photoshop tag system work

#### Dedicated origin / pivot fixture (a photoshop tag system follow-up)

a photoshop tag system follow-up listed a "small PSD with one `[origin]` marker layer per body part, golden-diffed" as a follow-up. The doll oracle (`02_photoshop_setup/doll_tagged.psd`) covers the planner + writer paths for `[origin]` and `[origin:X,Y]` end-to-end, so the dedicated mini-PSD never materialised. **Why deferred**: tests/test_doll_tagged_manifest.py asserts origin presence on both the explicit-coordinate (`belly`, `arm.R`) and marker (`brow_states`) paths; tag_smoke locks the synthetic case. Coverage redundancy is high. **Trigger to revisit**: a regression where the origin handling diverges between PSD authoring styles - then ship the dedicated fixture so the failure mode has its own named test.

#### Doll-roundtrip oracle re-run against schema v2

The Photoshop UXP migration captured a byte-equal JSX baseline against `doll.psd` for the retirement gate. After the photoshop-tag-system v2 landed, the manifest gained `anchor`, per-entry `origin`, `blend_mode`, `subfolder`, and `kind: "mesh"`. The captured oracle still applies to legacy v1 imports, but a fresh v2 byte-equal capture against `doll_tagged.psd` is open. **Why deferred**: pytest's `test_doll_tagged_manifest.py` already pins the v2 manifest's structural invariants; a byte-equal SHA capture adds little signal beyond locking the exact JSON whitespace and key order. **Trigger to revisit**: the UXP exporter changes its serialisation strategy (key order, indentation, encoding) - then byte-equal capture catches the change before users notice.

#### Spectrum web component shadow-DOM init cost

`sp-action-button` / `sp-textfield` mount with shadow-DOM overhead noticeable on first paint of the Tags / Validate panels. Acceptable on the doll-sized PSD (22 layers). **Why deferred**: panels are not interaction-heavy, and the doll fixture is the largest known consumer today. **Trigger to revisit**: an artist reports lag opening the Tags tab on a >100-layer PSD; first response is to switch the hot widgets to plain HTML elements (the SRP audit already retired several Spectrum components for this reason - see `5c6bef2`).

#### Migrating flat fixtures into `psd_to_blender/` and `blender_to_godot/`

The new categorization buckets at `examples/generated/{psd_to_blender,blender_to_godot}/` accept new fixtures directly. The pre-existing flat fixtures (`atlas_pack/`, `blink_eyes/`, `mouth_drive/`, `shared_atlas/`, `simple_psd/`, `slot_cycle/`, `slot_swap/`) stay where they are because moving them ripples through every spec TODO, the `packages/fixtures/` index, and several wrapper-scene paths. **Why deferred**: refactor cost > current confusion cost. **Trigger to revisit**: the next time one of those fixtures needs editing for an unrelated reason; piggyback the move onto the same commit.

### Tags advanced-fields form cannot clear a set tag

**What:** in the Tags panel's advanced-fields expander, clearing a previously-set field (emptying `[folder:...]`, `[path:...]`, `[scale:...]`, `[origin:...]`, `[name:...]`, or un-checking the origin marker) does not remove the tag. The value stays on the layer name. Setting and changing values works; only clearing is broken.

**Why:** `lib/tag-form.ts` `computeChanges` signals a cleared field by returning `undefined` from the `diff*` helper, but `applyDiff` then does `delete changes[key]` instead of writing the key. `applyTagChanges` (`lib/tag-writer.ts`) clears a tag only when the key is *present* with value `undefined`; an absent key is a no-op. The `delete` was an `exactOptionalPropertyTypes` workaround (assigning `undefined` to an optional field is a type error) that silently dropped the clear signal. Pre-existing; surfaced during the web-app-layout extraction of this logic out of `Details.tsx` (it was moved verbatim, not introduced).

**Scope sketch:** carry cleared keys explicitly - e.g. `computeChanges` returns `{ set: Partial<TagBag>; clear: (keyof TagBag)[] }`, or the changes object uses a branded "clear" marker - so the rename path passes `undefined` through to `applyTagChanges` for each cleared field. Extend `tag-form.test.ts` with the clear cases (currently it asserts only the set / unchanged / validation paths, deliberately not locking in the broken clear behaviour).

**Trigger:** an artist sets a folder / scale / origin via the advanced fields, empties it, applies, and the tag is still on the layer.

## Tests and CI

### Spec 020 follow-up: coverage deferrals

Spec 020 lifted coverage 36% -> 88.8% (Sonar gate green at merge, PR #95) and shipped the test suites, the UXP host mock, the in-Blender `coverage.py` instrumentation (`apps/blender/tests/run_coverage.py`), and the exclusion policy (recipe in the `sonar-project.properties` header). Three follow-ups were deferred by design:

- **Wire `run_coverage.py` + combine into CI.** Today Sonar runs only on the local Docker instance, so the two-interpreter combine is a documented local pre-scan step. Wire it into the `test-blender` job, and set `REFERENCE_BRANCH=main` for new-code, once Sonar moves into CI (Community Edition ignores `REFERENCE_BRANCH` on a single-branch project, so `NUMBER_OF_DAYS=30` stands in locally).
- **Drop the bpy-bound coverage exclusions when in-Blender unit coverage is comprehensive.** `operators/`, `panels/`, `properties/`, `core/bpy_helpers/` stay excluded because the headless suites are scenario integration tests (measured 23-29%), not units; dropping the exclusions would add ~6900 lines at ~25% and tank the number. The instrumentation makes them measurable; the value is not there until real unit coverage exists.
- **Edge-polish ~8 pure modules at 89-93%.** One to six uncovered edge lines each; diminishing returns, not chased.

Related enforcement gaps (ESLint not in CI, `packages/{models,codegen}` without a mypy gate, the bpy-bound mypy `ignore_errors` override) live in [`backlog-code-quality.md`](backlog-code-quality.md).

### Blender headless test - multi-version matrix

A single-version `test-blender` job ships in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) pinned to Blender 5.1.1. Expand to a matrix covering Blender 4.2 LTS and the latest stable so legacy-action regressions are caught.

### Godot importer test - full editor reimport

[`apps/godot/tests/test_importer.gd`](../apps/godot/tests/test_importer.gd) exercises the builders directly. A higher-fidelity test would launch the editor headlessly, drop a `.proscenio` into the project, and assert the generated `.scn` opens with the plugin disabled (the no-GDExtension hard rule, automated). Currently verified manually as part of the smoke checklist.

### CI matrix expansion

The current `test-godot` job pins Godot 4.6.2-stable. Add Godot 4.3 and 4.5 to the matrix once those releases settle. Same for the `test-blender` matrix.

### End-to-end mixed-feature fixture

Existing fixtures isolate single features (`blink_eyes` = sprite_frame, `shared_atlas` = sliced atlas, `slot_cycle` = slots). There is no generated golden exercising a realistic rig with many features at once: a skinned `polygon` body, a `sprite_frame` mouth, a slot swapping several attachments (mixed `polygon` + `sprite_frame`), a packed atlas, Drive-from-Bone, and an animation - carried from a `.psd` through Blender to a Godot `.scn`. Add such a fixture and run it through the full generated pipeline (Photoshop manifest -> Blender import -> `.proscenio` -> Godot `.scn`) as a CI golden, so cross-feature interactions are covered - especially atlas pack + sprite_frame + slots stacked in one character, the exact combination this backlog round surfaced as untested.

**Trigger:** a feature combination that each isolated fixture passes still breaks when stacked in one character.

## Repo and packaging

### LICENSE full GPL-3.0 body

`LICENSE` ships the header only with a clear placeholder pointing to gnu.org. Replace with the full text before the first public release.

### Issue and PR templates

`.github/` lacks templates. Low priority until the project is open to outside contributors.

### Statusline / dev-loop polish

The dev junction setup for the Blender addon is a manual `New-Item -ItemType Junction`. A `scripts/install-dev.ps1` would automate it. Same for copying the dummy fixture into `apps/godot/test_dummy/`.

### Release workflow Photoshop job stale (`.jsx` → UXP `dist/`)

`.github/workflows/release.yml` line 39 still runs `cp apps/photoshop/proscenio_export.jsx "dist/proscenio-photoshop-${version}.jsx"`. The legacy JSX exporter is gone; the plugin is now a UXP bundle that webpack emits into `apps/photoshop/dist/` (`index.html`, `index.js`, `manifest.json`, `icons/`). A `photoshop-v*` tag would fail at this step. **Why deferred**: no release has been cut yet on the UXP branch; current development uses `pnpm uxp:load` from the dev folder. **Trigger to revisit**: before cutting the first `photoshop-v*` tag. Replace the `cp` with `(cd apps/photoshop/dist && zip -r "../../../dist/proscenio-photoshop-${version}.ccx" .)` (or `.zip` if `.ccx` packaging is out of scope), and adjust the release artifact pattern in the same job.

## Typed-models migration follow-ups

The typed-models codegen migration is complete: pydantic is the source of truth, the writer builders construct model instances (`PolygonSprite()` / `Skeleton()` / `Animation()`), both manifest readers parse through the typed models (Blender `psd_manifest.py` → `PsdManifest`, Photoshop `manifest-reader.ts` → `parseManifest`), no `as unknown` casts remain in the typed surface, and the strictness flags all landed (`exactOptionalPropertyTypes`, ESLint `strictTypeChecked`, the mypy `disallow_any_*` trio). Committed-match tests reproduce the JSON Schema, TypeScript, and GDScript artifacts from the models and fail on drift (`tests/codegen/test_schema_roundtrip.py`, `test_ts_emit.py`, `test_godot_emit.py`); the docs emitter is the one artifact left ungated (see below). Only optional tooling / docs follow-ups remain.

### bpy stubs via fake-bpy-module / bpy-stubgen

The mypy `disallow_any_*` trio landed with per-module overrides that relax the `bpy` / `mathutils` / `bmesh` boundary (no stubs ship for those modules). A frozen per-release stub snapshot would let those overrides drop so the boundary is fully typed. Both `fake-bpy-module` and `bpy-stubgen` exist; both are fragile across Blender releases, so pinning a snapshot per release matrix is the realistic path.

**Trigger to revisit:** the next Blender LTS jump that breaks an existing typed surface, or a push to remove the remaining bpy-boundary mypy overrides.

### Docusaurus wiring of generated docs

`docs/content/api/schemas/*.md` is regenerable via `python -m proscenio_codegen docs` but no docs site reads it, and the committed markdown has drifted from a fresh emit - it is the one codegen artifact without a committed-match staleness test, because it depends on the npx `jsonschema2md` output rather than pure-Python emit. The typed-models codegen deferred the site itself as a separate chore; regenerating (or deleting) the stale markdown rides along with wiring or dropping the site.

**Trigger to revisit:** the first time someone wants to ship public schema documentation, or a code-health pass decides to drop the unconsumed markdown.

## Quick Armature follow-ups (deferred polish)

Three small items deferred from the quick-armature TODO at ship time. None are blocking; listed so the next quick-armature touch can clean them up.

- **Help-topic for `quick_armature_defaults`** - panel already self-describes via field tooltips; a dedicated topic page would help discoverability but is not required.
- **Headless undo / axis-lock interaction tests** - the helper-level math is covered by `tests/test_quick_armature_math.py`; the ClassVar dance is hard to test without booting Blender, so manual smoke covers it.
- **Add the ClassVar mutation rule to `.ai/conventions/code.md` Static typing section + `.ai/skills/blender-dev.md`** - the rule lives in [`backlog-bugs-found.md`](backlog-bugs-found.md); promoting it to the conventions doc is low-priority because the bug is rare enough.

## Architecture revisits

These items intentionally violate or expand on a current hard rule. They are **not slated** - listed only so that if the trigger condition appears in a future spec discussion, we have prior art on the alternatives we already considered.

### GDExtension / C# escape hatch

**Current rule:** [`AGENTS.md`](../AGENTS.md) hard rule #3 - no GDExtension, no native runtime; the Godot plugin is GDScript-only and runs only at editor import time. See [`.ai/skills/architecture.md`](../.ai/skills/architecture.md) for the rationale.

**Why this entry exists:** the maintainer prefers strong typing, nullables, and a real compiler over GDScript's dynamic feel ("magia e reza braba"). Firebound itself is C# (mono build). Continuing in GDScript is a deliberate trade for plugin reach in the broader 2D community, not an endorsement of GDScript's ergonomics.

**Triggers that would justify reopening the rule:**

- **Deep Firebound integration** - Firebound exposes a runtime API (signals, services, custom nodes) that the imported character must talk to natively, and surfacing that contract through GDScript adapters becomes the bottleneck.
- **Performance ceiling hit** - `Polygon2D` skinning with high bone counts measured against a real game scene exceeds frame budget; compute-shader skinning via GDExtension becomes the cheapest path.
- **Live link Blender ↔ Godot** - pose/animation/sprite delta streaming over a socket needs sustained throughput that GDScript's dictionary parsing cannot hit.
- **Binary `.proscenio` format** - JSON parse time becomes import-loop pain on large projects; binary format reader benefits from native code.
- **Editor authoring tools that need round-trip serialization back to `.proscenio`** - writing the format from inside Godot at interactive speed.

**What that future spec would look like:**

- Likely targets a *separate optional component* (`apps/godot-csharp/`) that ships alongside the GDScript plugin, gated behind a feature flag, so non-mono users still have the GDScript path.
- Mono-only audience cut would be **documented openly** as the price of the feature; this is acceptable for Firebound users (already on mono) but acknowledged as a regression for general OSS reach.
- Anything moved to native must remain **import-time only** unless the spec explicitly relaxes the runtime side. Generated `.scn` keeps using built-in nodes.

**See also:** [`.ai/skills/architecture.md`](../.ai/skills/architecture.md), [`.ai/README.md`](../.ai/README.md), the language-decision discussion in this backlog's revision history.
