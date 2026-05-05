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

Vertex group weights are read in the inspector but the writer only emits rigid attachment. Phase 2 (SPEC 003) is the planned home for this — see SPEC 000 Q3.

### Atlas region authoring helper

User UV-maps each plane in Blender to a region of the atlas; the writer reads whatever UVs are there. There is no Blender operator to "snap UV to atlas region by name". Could ship as a Phase 2 quality-of-life operator.

### IK constraints export

Out of scope for v1. Godot has built-in `Skeleton2DIK` so the user adds IK in-engine post-import. Future SPEC could detect IK constraints in the armature and round-trip them.

### Auto-detect 2D rig vs 3D mesh

Currently the writer assumes every mesh is a 2D sprite plane. A future check could skip 3D meshes or warn.

### Camera orthographic preview helper

A Blender operator that adds a properly configured ortho camera for pixel-perfect preview, matching the dummy's `pixels_per_unit`.

### Blender 4.3 legacy actions compatibility

`writer._action_fcurves` falls back to `action.fcurves` when present. Untested against Blender 4.2 LTS — may need fixture-based regression once the addon is shipped.

## Godot plugin

### Reimport non-destructive merge

**Resolved by [SPEC 001](001-reimport-merge/STUDY.md)** — adopt full overwrite plus the wrapper-scene pattern (Option A). Marker-based merge (Option B) deferred unless demand emerges.

### Spritesheet support and `Sprite2D` path

**Resolved by [SPEC 002](002-spritesheet-sprite2d/STUDY.md)** — adopt explicit `type` discriminator field per sprite; default `"polygon"` keeps v1 fixtures backwards-compatible. `Sprite2D` ships as the `"sprite_frame"` variant with `hframes`/`vframes`/`frame` and the matching animation track.

### Slot system

Slated for SPEC 004. Sprite-swap groups via `slots` field; importer wires `slot_attachment` tracks.

### Node name collision polish

When a Bone2D and a child Polygon2D share a name (e.g. both called `head`), Godot auto-renames the polygon to `head_001`. Acceptable but ugly. Either prefix sprite names in the importer (`sprite_head`) or document the convention.

### Plugin-uninstall warning UI

Currently the rule "scene must work without the plugin" is enforced by review. A small editor check that opens a generated scene with the plugin disabled and asserts no errors would be a CI-friendly guard.

## Photoshop and Krita

### JSX exporter port from `coa_tools2`

Port `coa_tools2/Photoshop/coa_export.jsx` forward into `photoshop-exporter/proscenio_export.jsx`. Adapt output JSON to the format documented in `.ai/skills/photoshop-jsx-dev.md`.

### Krita exporter

`coa_tools2/Krita/coa_export.py` works in Krita 4.x. Phase 2 port-forward target.

### GIMP exporter

`coa_tools2` has a GIMP path. Lower priority — fewer 2D animation users on GIMP.

## Tests and CI

### Blender headless test — multi-version matrix

A single-version `test-blender` job ships in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) pinned to Blender 5.1.1. Expand to a matrix covering Blender 4.2 LTS and the latest stable so legacy-action regressions are caught.

### Godot importer test — full editor reimport

[`godot-plugin/tests/test_importer.gd`](../godot-plugin/tests/test_importer.gd) exercises the builders directly. A higher-fidelity test would launch the editor headlessly, drop a `.proscenio` into the project, and assert the generated `.scn` opens with the plugin disabled (the no-GDExtension hard rule, automated). Currently verified manually per [SPEC 000 TODO](000-initial-plan/TODO.md).

### CI matrix expansion

The current `test-godot` job pins Godot 4.6.2-stable. Add Godot 4.3 and 4.5 to the matrix once those releases settle. Same for the `test-blender` matrix.

## Repo and packaging

### LICENSE full GPL-3.0 body

`LICENSE` ships the header only with a clear placeholder pointing to gnu.org. Replace with the full text before the first public release.

### Maintainer contact

Resolved — `blender-addon/blender_manifest.toml` now points to `contato@spacewiz.dev`.

### Final repo URL

Resolved — canonical URL is `https://github.com/Space-Wizard-Studios/firebound-proscenio`.

### Issue and PR templates

`.github/` lacks templates. Low priority until the project is open to outside contributors.

### Statusline / dev-loop polish

The dev junction setup for the Blender addon is a manual `New-Item -ItemType Junction`. A `scripts/install-dev.ps1` would automate it. Same for copying the dummy fixture into `godot-plugin/test_dummy/`.

## Architecture revisits

These items intentionally violate or expand on a current hard rule. They are **not slated** — listed only so that if the trigger condition appears in a future SPEC discussion, we have prior art on the alternatives we already considered.

### GDExtension / C# escape hatch

**Current rule:** [`AGENTS.md`](../AGENTS.md) hard rule #3 — no GDExtension, no native runtime; the Godot plugin is GDScript-only and runs only at editor import time. See [`.ai/skills/architecture.md`](../.ai/skills/architecture.md) for the rationale.

**Why this entry exists:** the maintainer prefers strong typing, nullables, and a real compiler over GDScript's dynamic feel ("magia e reza braba"). Firebound itself is C# (mono build). Continuing in GDScript is a deliberate trade for plugin reach in the broader 2D community, not an endorsement of GDScript's ergonomics.

**Triggers that would justify reopening the rule:**

- **Deep Firebound integration** — Firebound exposes a runtime API (signals, services, custom nodes) that the imported character must talk to natively, and surfacing that contract through GDScript adapters becomes the bottleneck.
- **Performance ceiling hit** — `Polygon2D` skinning with high bone counts measured against a real game scene exceeds frame budget; compute-shader skinning via GDExtension becomes the cheapest path.
- **Live link Blender ↔ Godot** — pose/animation/sprite delta streaming over a socket needs sustained throughput that GDScript's dictionary parsing cannot hit.
- **Binary `.proscenio` format** — JSON parse time becomes import-loop pain on large projects; binary format reader benefits from native code.
- **Editor authoring tools that need round-trip serialization back to `.proscenio`** — writing the format from inside Godot at interactive speed.

**What that future SPEC would look like:**

- Likely targets a *separate optional component* (`godot-plugin-csharp/`) that ships alongside the GDScript plugin, gated behind a feature flag, so non-mono users still have the GDScript path.
- Mono-only audience cut would be **documented openly** as the price of the feature; this is acceptable for Firebound users (already on mono) but acknowledged as a regression for general OSS reach.
- Anything moved to native must remain **import-time only** unless the SPEC explicitly relaxes the runtime side. Generated `.scn` keeps using built-in nodes.

**See also:** [`.ai/skills/architecture.md`](../.ai/skills/architecture.md), [`.ai/conventions.md`](../.ai/conventions.md), the language-decision discussion in this backlog's revision history.
