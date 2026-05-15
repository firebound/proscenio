# Backlog

Items that are not in any active SPEC. Each entry promotes into a numbered SPEC when work begins. Order within a section is rough priority.

## Format and schema

### Bezier curve preservation

**What:** the `.proscenio` v1 stores keyframes with track-level interpolation only (`linear`, `constant`); the Godot importer also offers cubic via `INTERPOLATION_CUBIC*` for smooth automatic splines. Blender authors curves with per-key Bezier handles that the format does not transmit.

**Why future-SPEC:** transmitting Bezier handles requires schema fields (`tangent_in`, `tangent_out`) and a Godot-side custom Bezier track or pre-baking. Cubic auto-spline is good enough for MVP.

**Trigger to revisit:** an animator complains that the imported animation does not match Blender to within visual tolerance.

### Multiple atlases per character

`atlas` is a single string in v1. Multi-atlas characters split into multiple `.proscenio` files. Future v2 may support an `atlas_pages` array indexed by sprite.

### Animation events (method tracks)

`AnimationPlayer` supports method tracks for audio cues, particle spawns, etc. v1 has no `event` track type.

### Per-key interpolation mixing

Schema's `interp` field is per-key but the importer applies a single track-level interpolation. Mixed `linear`/`constant`/`cubic` keys in one track would require splitting into multiple tracks at runtime or adopting a Bezier track type.

### Format detection / migration

Schema validation rejects unknown `format_version`. Once v2 lands, the Blender exporter ships `migrations/v1_to_v2.py` and the Godot importer surfaces a clear migration error pointing to the migrator.

## Blender addon

### General rig orientation detection

Writer assumes the 2D plane is Blender XZ (Z up, Y into screen). Some users author on XY (Y up). Future work: detect the dominant plane from the armature's bone axes or expose an export option.

### Multi-polygon mesh meshes

`writer._build_sprite` only emits the **first** polygon of a mesh. A mesh with multiple disjoint polygons (mask cutouts, complex topology) is silently truncated. Multi-polygon support would either:

- emit one Proscenio sprite per polygon (cleanest), or
- use `Polygon2D.polygons` array for multi-island Polygon2D nodes (preserves original mesh structure).

### Skinning weights export

Vertex group weights are read in the inspector but the writer only emits rigid attachment. Phase 2 (SPEC 003) is the planned home for this - see SPEC 000 Q3.

### Atlas region authoring helper

User UV-maps each plane in Blender to a region of the atlas; the writer reads whatever UVs are there. There is no Blender operator to "snap UV to atlas region by name". Could ship as a Phase 2 quality-of-life operator.

### IK constraints export

Out of scope for v1. Godot has built-in `Skeleton2DIK` so the user adds IK in-engine post-import. Future SPEC could detect IK constraints in the armature and round-trip them.

### Auto-detect 2D rig vs 3D mesh

Currently the writer assumes every mesh is a 2D sprite plane. A future check could skip 3D meshes or warn.

### Camera orthographic preview helper

A Blender operator that adds a properly configured ortho camera for pixel-perfect preview, matching the dummy's `pixels_per_unit`.

### Quick Armature: Front-Ortho UX guard

**Resolved by [SPEC 012](012-quick-armature-ux/STUDY.md)** Wave 12.1 - `lock_to_front_ortho` operator option (default `True`) auto-snaps to Front Orthographic on `invoke` and restores the original view on exit. Opt-out via F3 redo for legitimate persp-view authoring. Status hint + in-viewport cheatsheet ship in the same wave.

### Blender 4.3 legacy actions compatibility

`writer._action_fcurves` falls back to `action.fcurves` when present. Untested against Blender 4.2 LTS - may need fixture-based regression once the addon is shipped.

### Split PropertyGroup vs Custom Property storage by intent (target: 1.0.0)

**What:** the current SPEC 005 design mirrors every PropertyGroup field on `Object.proscenio` to a sibling raw Custom Property (`obj["proscenio_type"]`, `obj["proscenio_frame"]`, ...) via `update` callbacks, and `core/hydrate.py` rehydrates the PG from CPs on `load_post`. The 11 fields in `OBJECT_PROPS` are mirrored uniformly, which is over-broad: some fields are editor-time only and could live as PG-canonical with no CP at all, while others are animatable / driver targets where the CP is the durable storage and the PG is just a typed widget projection.

**Why:** PropertyGroup data is backed by IDProperty but its visibility depends on the addon's RNA descriptor being registered. Disable -> save -> reenable cycles can purge orphaned IDProperty data depending on Blender version, so PG is a brittle home for anything that must survive addon-absent file states or be a stable driver target. Raw CPs have none of those constraints, which is why Rigify and similar mature addons keep the *animator-facing* surface (IK/FK switches, layer toggles) on CPs and reserve PGs for *generator-internal* metadata. Mirroring everything pays the cost (doubled write paths, sync risk, undo desync, `deferred_hydrate` timer, dual-key reader fallback in `read_field`) for fields that do not need the resilience. Mirroring nothing loses real resilience for fields that do (`frame` is keyframable into Godot's `AnimationPlayer`; Drive-from-Bone wires drivers onto sprite properties).

**Decision (locked):** option **A** - split by intent. Editor-time-only fields become PG-canonical with no CP mirror; animatable / driver-target fields become CP-canonical with PG as a typed widget wrapper. Documented as a deliberate contract, not legacy debt - rewrite the `properties/__init__.py` docstring to call this out instead of describing CPs as "legacy".

**Scope sketch:**

- PG-canonical (drop the CP mirror): `sprite_type`, `region_mode`, `region_x`, `region_y`, `region_w`, `region_h`, `material_isolated`.
- CP-canonical (PG is the typed widget; writer reads CP directly): `frame`, `hframes`, `vframes`, `centered`, `proscenio_slot_index`.
- Reader (`writer/sprites.py`, slot index reads, etc.) drops the `read_field(pg_field=..., cp_key=..., default=...)` dual fallback and reads each field from its canonical home.
- `_update_*` mirror callbacks deleted for the PG-canonical group; retained only as PG -> CP one-way for the CP-canonical group (since the PG is the widget the user touches).
- `core/hydrate.py` becomes a one-shot migrator: on `load_post`, hydrate any `.blend` that still has legacy CPs in the PG-canonical group into the PG, then *delete* those CPs so the field has a single source of truth post-migration. Gate behind a `format_version` check on the scene PG so it runs at most once per file.
- `_handlers.py`: keep `load_post` for the one-shot migrator; `save_pre` and `deferred_hydrate` timer can likely be deleted once the mirror is gone (revalidate during the rewrite).
- Drive-from-Bone operator: target the CP path for animatable fields so the driver `data_path` is `pose.bones["X"]["proscenio_frame"]`-style rather than the nested PG path. Reduces driver fragility on linking / append.

**Trigger to revisit:** before 1.0.0 release. Block on this landing so the public surface ships with the final storage contract; post-1.0 schema or storage migrations cost real users.

**Out of scope for this entry:**

- Library-override / linking semantics for the surviving PG fields (separate concern; address only if a user reports issues).
- Schema `format_version` bump - the contract on disk does not change; only the in-`.blend` storage shape does. May still want a `format_version` bump on the *scene PG* to gate the migrator.

## Godot plugin

### Reimport non-destructive merge

**Resolved by [SPEC 001](001-reimport-merge/STUDY.md)** - adopt full overwrite plus the wrapper-scene pattern (Option A). Marker-based merge (Option B) deferred unless demand emerges.

### Spritesheet support and `Sprite2D` path

**Resolved by [SPEC 002](002-spritesheet-sprite2d/STUDY.md)** - adopt explicit `type` discriminator field per sprite; default `"polygon"` keeps v1 fixtures backwards-compatible. `Sprite2D` ships as the `"sprite_frame"` variant with `hframes`/`vframes`/`frame` and the matching animation track.

### Slot system

Slated for SPEC 004. Sprite-swap groups via `slots` field; importer wires `slot_attachment` tracks.

### Node name collision polish

When a Bone2D and a child Polygon2D share a name (e.g. both called `head`), Godot auto-renames the polygon to `head_001`. Acceptable but ugly. Either prefix sprite names in the importer (`sprite_head`) or document the convention.

### Plugin-uninstall warning UI

Currently the rule "scene must work without the plugin" is enforced by review. A small editor check that opens a generated scene with the plugin disabled and asserts no errors would be a CI-friendly guard.

### `project.godot` warning tuning for JSON boundary

`apps/godot/project.godot` `[debug]` carries only `untyped_declaration=2`, `return_value_discarded=1`, `treat_warnings_as_errors=true`. The `unsafe_property_access` / `unsafe_method_access` / `unsafe_cast` / `unsafe_call_argument` families fire on every line that downcasts `JSON.parse` output, forcing `# warning-ignore` clutter. **Why deferred**: current builders use bare `Dictionary` at the JSON boundary, which compiles cleanly without the pins because the casts are implicit. **Trigger to revisit**: when tightening builders to use `Dictionary[K, V]` typed collections (see entry below), pin the four unsafe-access keys to `0` so the downcasts at the JSON edge stay quiet without per-line ignores.

### Annotate `: Variant` on JSON-boundary lookups in Godot builders

Three lookups currently bind without an explicit type: `polygon_builder.gd:114`, `skeleton_builder.gd:36`, `sprite_frame_builder.gd:74` (each of the shape `var x = dict.get("key", null)`). Conventions explicitly allow bare `Dictionary` at the decode boundary, but the `var x = ...` form trips the "Never `var x = 0`" reading on hover. **Why deferred**: cosmetic, no runtime impact, the surrounding code immediately tests the value for null. **Trigger to revisit**: when refactoring the builders to typed collections, or when a reader confuses these for missing type annotations.

## Photoshop and Krita

### JSX exporter port from `coa_tools2`

Port `coa_tools2/Photoshop/coa_export.jsx` forward into `apps/photoshop/proscenio_export.jsx`. Adapt output JSON to the format documented in `.ai/skills/photoshop-jsx-dev.md`.

### Krita exporter

`coa_tools2/Krita/coa_export.py` works in Krita 4.x. Phase 2 port-forward target.

### GIMP exporter

`coa_tools2` has a GIMP path. Lower priority - fewer 2D animation users on GIMP.

### Deferred Photoshop tags (post SPEC 011)

Tags evaluated during the SPEC 011 research pass that did not make the v1 taxonomy. Each was deferred for a documented reason. Promote into SPEC 011.x or a successor SPEC when a real workflow surfaces the need.

#### `[slice:l,t,r,b]` - Cocos-style 9-slice

Encodes 4 corner insets so a single sprite scales as a 9-slice tile (UI panels, scalable backgrounds). Cocos Creator and Unity ship this. **Why deferred**: Proscenio's current consumer set is rigged characters, not UI; no real workflow surfaces 9-slice today. Trigger to revisit: first UI-focused fixture lands.

#### Head-turner view groups (Adobe Character Animator)

Groups named `Frontal` / `Left Profile` / `Left Quarter` / `Right Quarter` / `Right Profile` collapse into a single mesh with swappable view variants. Specific to face puppetry. **Why deferred**: deep coupling to a face-rig template; harder to generalise across project types than the tag system in SPEC 011.

#### Pseudo-keyword auto-tagging (`Head`, `Mouth`, `Eye_Open`, ...)

Layer / group named `Head` automatically gets a face-region tag without an explicit `[head]` bracket. Mirrors Character Animator. **Why deferred**: tight coupling to one rig style (humanoid face puppet); collides with arbitrary artist naming. The bracket-tag explicit path (SPEC 011 D1) is cleaner and ships first.

#### `[isolated]` warp-independent flag (Character Animator's `+` prefix)

Marks a layer as "animated separately from its parent group" so the rig generator emits a dedicated pose key for it. **Why deferred**: Proscenio's rig model has no concept of "warp pose keys"; bones already encode separability. Reserved tag name: `[isolated]` (the `+` prefix from Character Animator is rejected as non-idiomatic for this project). Trigger to revisit: if SPEC 005 / 008 grow a "per-layer pose channel" concept.

#### Stable layer identity in `PngWrite.layerPath`

`PngWrite.layerPath` (and the parallel `_frameSources` on planned sprite_frame entries) is a chain of layer names. Photoshop allows siblings with duplicate names; if a user authors two children named `arm` inside the same group, the materialiser would resolve whichever appears first in `layer.layers` and silently write the wrong PNG. **Why deferred**: the doll oracle and every shipped fixture have unique names per group; ajv catches name collisions at the sanitize level for manifest entries. **Trigger to revisit**: a user reports a wrong-PNG export, or SPEC 011's tag inspector starts addressing layers by stable handle. Implementation hint: replace `string[]` with `Array<{ name: string; index: number }>` so the adapter can tie-break by position when two siblings share a name.

### SPEC 011 v1 design decisions to revisit

Behaviours that landed as "by design" in the v1 taxonomy. Each is intentional today but worth re-examining once real artist usage stresses the assumption.

#### Nested `[merge]` collapses silently

A `[merge]` group inside another `[merge]` is flattened into the outer entry without a warning. Confirmed end-to-end on the doll oracle: `brow_states [spritesheet]` with `1 [merge]` containing `1.1 [merge]` emits two frames (`0`, `1`) instead of three, because `1.1` collapses into `1`. **Why deferred**: this is the obvious recursive semantics for `[merge]` and the doll authoring run produced no surprise; no warning means no false-positive fatigue. **Trigger to revisit**: an artist reports "I added a sub-layer inside [merge] and it vanished" without realising it was deliberate - then we surface a `merge-nested` info-level entry on the Validate tab so the collapse is visible at authoring time.

#### `[name:pre*suf]` parsed but planner does not rewrite

The tag parser accepts `[name:lh_*]` on a parent group, but the v1 planner does not rewrite descendant names against the template. Display names cascade via `joinName` (parent `__` child) unchanged. **Why deferred**: rewrite has subtle interactions with `joinName` (do we rewrite before or after joining? what wins when a child carries its own `[path:NAME]`?) and zero shipped consumer needs it today. **Trigger to revisit**: a fixture or external user wants prefix/suffix templating on a real group - then we design the rewrite order with the actual workflow in hand.

#### `kind: "mesh"` semantically equal to `kind: "polygon"` downstream

`[mesh]` emits `kind: "mesh"` on the manifest and the Blender importer stamps a `proscenio_psd_kind = "mesh"` custom property, but no downstream code branches on it yet (the Godot writer treats both as a single quad). **Why deferred**: the distinction exists so SPEC 002 (mesh deformation) and SPEC 008 (UV animation) can tell editable polygons apart from rigid sprites. **Trigger to revisit**: SPEC 002 ships; at that point the importer adds a Subdivision Surface modifier (or equivalent) only to `kind: "mesh"` entries.

#### Waist height drifts -1 px on the PS round-trip

`waist` ships as 173 px tall in the Blender-emitted manifest, returns as 172 px through the Photoshop exporter. Logged in [`tests/BUGS_FOUND.md`](../tests/BUGS_FOUND.md). **Why deferred**: cosmetic (0.6 % drift on a 173 px region), and the round-trip oracle accepts it within tolerance. **Trigger to revisit**: an artist reports visible Y-offset on the waist mesh in Godot, or a SPEC 010.5 cycle fixes the underlying off-by-one in the JSX-era PSD reader.

#### `pixels_per_unit` not round-tripped (defaults to 100 on re-export)

The Blender manifest emits `pixels_per_unit = 1000.0`; the PS round-trip emits `100.0` (hardcoded in the JSX exporter, inherited by the UXP port). Logged in [`tests/BUGS_FOUND.md`](../tests/BUGS_FOUND.md). **Why deferred**: PPU only affects world-space placement in Blender, and the importer reads the PPU back out of the round-trip manifest correctly (it just lands at a different scale). **Trigger to revisit**: SPEC 010.5 plumbs PPU through XMP so the round-trip is lossless.

### SPEC 011 follow-ups deferred from Waves 11.x

#### Dedicated origin / pivot fixture (Wave 11.2)

Wave 11.2 listed a "small PSD with one `[origin]` marker layer per body part, golden-diffed" as a follow-up. The doll oracle (`02_photoshop_setup/doll_tagged.psd`) covers the planner + writer paths for `[origin]` and `[origin:X,Y]` end-to-end, so the dedicated mini-PSD never materialised. **Why deferred**: tests/test_doll_tagged_manifest.py asserts origin presence on both the explicit-coordinate (`belly`, `arm.R`) and marker (`brow_states`) paths; tag_smoke locks the synthetic case. Coverage redundancy is high. **Trigger to revisit**: a regression where the origin handling diverges between PSD authoring styles - then ship the dedicated fixture so the failure mode has its own named test.

#### SPEC 010 doll-roundtrip oracle re-run against schema v2

Wave 10.3 captured a byte-equal JSX baseline against `doll.psd` for the SPEC 010 retirement gate. After SPEC 011 v2 landed, the manifest gained `anchor`, per-entry `origin`, `blend_mode`, `subfolder`, and `kind: "mesh"`. The captured oracle still applies to legacy v1 imports, but a fresh v2 byte-equal capture against `doll_tagged.psd` is open. **Why deferred**: pytest's `test_doll_tagged_manifest.py` already pins the v2 manifest's structural invariants; a byte-equal SHA capture adds little signal beyond locking the exact JSON whitespace and key order. **Trigger to revisit**: the UXP exporter changes its serialisation strategy (key order, indentation, encoding) - then byte-equal capture catches the change before users notice.

#### Spectrum web component shadow-DOM init cost

`sp-action-button` / `sp-textfield` mount with shadow-DOM overhead noticeable on first paint of the Tags / Validate panels. Acceptable on the doll-sized PSD (22 layers). **Why deferred**: panels are not interaction-heavy, and the doll fixture is the largest known consumer today. **Trigger to revisit**: an artist reports lag opening the Tags tab on a >100-layer PSD; first response is to switch the hot widgets to plain HTML elements (the SRP audit already retired several Spectrum components for this reason - see `5c6bef2`).

#### Migrating flat fixtures into `psd_to_blender/` and `blender_to_godot/`

The new categorization buckets at `examples/generated/{psd_to_blender,blender_to_godot}/` accept new fixtures directly. The pre-existing flat fixtures (`atlas_pack/`, `blink_eyes/`, `mouth_drive/`, `shared_atlas/`, `simple_psd/`, `slot_cycle/`, `slot_swap/`) stay where they are because moving them ripples through every SPEC TODO, the `scripts/fixtures/` index, and several wrapper-scene paths. **Why deferred**: refactor cost > current confusion cost. **Trigger to revisit**: the next time one of those fixtures needs editing for an unrelated reason; piggyback the move onto the same commit.

## Tests and CI

### Blender headless test - multi-version matrix

A single-version `test-blender` job ships in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) pinned to Blender 5.1.1. Expand to a matrix covering Blender 4.2 LTS and the latest stable so legacy-action regressions are caught.

### Godot importer test - full editor reimport

[`apps/godot/tests/test_importer.gd`](../apps/godot/tests/test_importer.gd) exercises the builders directly. A higher-fidelity test would launch the editor headlessly, drop a `.proscenio` into the project, and assert the generated `.scn` opens with the plugin disabled (the no-GDExtension hard rule, automated). Currently verified manually per [SPEC 000 TODO](000-initial-plan/TODO.md).

### CI matrix expansion

The current `test-godot` job pins Godot 4.6.2-stable. Add Godot 4.3 and 4.5 to the matrix once those releases settle. Same for the `test-blender` matrix.

## Repo and packaging

### LICENSE full GPL-3.0 body

`LICENSE` ships the header only with a clear placeholder pointing to gnu.org. Replace with the full text before the first public release.

### Maintainer contact

Resolved - `apps/blender/blender_manifest.toml` now points to `contato@spacewiz.dev`.

### Final repo URL

Resolved - canonical URL is `https://github.com/Space-Wizard-Studios/firebound-proscenio`.

### Issue and PR templates

`.github/` lacks templates. Low priority until the project is open to outside contributors.

### Statusline / dev-loop polish

The dev junction setup for the Blender addon is a manual `New-Item -ItemType Junction`. A `scripts/install-dev.ps1` would automate it. Same for copying the dummy fixture into `apps/godot/test_dummy/`.

### Release workflow Photoshop job stale (`.jsx` -> UXP `dist/`)

`.github/workflows/release.yml` line 39 still runs `cp apps/photoshop/proscenio_export.jsx "dist/proscenio-photoshop-${version}.jsx"`. The legacy JSX exporter is gone; the plugin is now a UXP bundle that webpack emits into `apps/photoshop/dist/` (`index.html`, `index.js`, `manifest.json`, `icons/`). A `photoshop-v*` tag would fail at this step. **Why deferred**: no release has been cut yet on the UXP branch; current development uses `pnpm uxp:load` from the dev folder. **Trigger to revisit**: before cutting the first `photoshop-v*` tag. Replace the `cp` with `(cd apps/photoshop/dist && zip -r "../../../dist/proscenio-photoshop-${version}.ccx" .)` (or `.zip` if `.ccx` packaging is out of scope), and adjust the release artifact pattern in the same job.

## Architecture revisits

These items intentionally violate or expand on a current hard rule. They are **not slated** - listed only so that if the trigger condition appears in a future SPEC discussion, we have prior art on the alternatives we already considered.

### GDExtension / C# escape hatch

**Current rule:** [`AGENTS.md`](../AGENTS.md) hard rule #3 - no GDExtension, no native runtime; the Godot plugin is GDScript-only and runs only at editor import time. See [`.ai/skills/architecture.md`](../.ai/skills/architecture.md) for the rationale.

**Why this entry exists:** the maintainer prefers strong typing, nullables, and a real compiler over GDScript's dynamic feel ("magia e reza braba"). Firebound itself is C# (mono build). Continuing in GDScript is a deliberate trade for plugin reach in the broader 2D community, not an endorsement of GDScript's ergonomics.

**Triggers that would justify reopening the rule:**

- **Deep Firebound integration** - Firebound exposes a runtime API (signals, services, custom nodes) that the imported character must talk to natively, and surfacing that contract through GDScript adapters becomes the bottleneck.
- **Performance ceiling hit** - `Polygon2D` skinning with high bone counts measured against a real game scene exceeds frame budget; compute-shader skinning via GDExtension becomes the cheapest path.
- **Live link Blender ↔ Godot** - pose/animation/sprite delta streaming over a socket needs sustained throughput that GDScript's dictionary parsing cannot hit.
- **Binary `.proscenio` format** - JSON parse time becomes import-loop pain on large projects; binary format reader benefits from native code.
- **Editor authoring tools that need round-trip serialization back to `.proscenio`** - writing the format from inside Godot at interactive speed.

**What that future SPEC would look like:**

- Likely targets a *separate optional component* (`apps/godot-csharp/`) that ships alongside the GDScript plugin, gated behind a feature flag, so non-mono users still have the GDScript path.
- Mono-only audience cut would be **documented openly** as the price of the feature; this is acceptable for Firebound users (already on mono) but acknowledged as a regression for general OSS reach.
- Anything moved to native must remain **import-time only** unless the SPEC explicitly relaxes the runtime side. Generated `.scn` keeps using built-in nodes.

**See also:** [`.ai/skills/architecture.md`](../.ai/skills/architecture.md), [`.ai/conventions.md`](../.ai/conventions.md), the language-decision discussion in this backlog's revision history.
