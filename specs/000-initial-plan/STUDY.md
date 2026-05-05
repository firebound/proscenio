# SPEC 000 — Initial plan

Status: **draft**, in active discussion. This is the planning spec that drives Phase 0 → Phase 1 work.

## Purpose

Capture the current understanding of what Proscenio is, why it exists, what is settled, what is open, and what the simplest current answer is for each open question. Once Phase 1 begins implementation, this spec is frozen and follow-up SPECs reopen specific scopes.

## Context

Firebound (the user's 2D framework on Godot) needs a 2D cutout-animation pipeline that does not depend on a paid runtime, a custom Godot build, or a third-party-of-third-party support story. Spine2D fails on those constraints. The COA Tools ecosystem could fill the gap but the Godot side has been broken or absent for years.

The decision is to build a fresh tool — Proscenio — instead of forking COA Tools. The Photoshop and Krita exporter scripts from `coa_tools2` work and can be ported forward; everything else is rewritten.

## Components

| Component | Language | Target |
| --- | --- | --- |
| `photoshop-exporter/` | ExtendScript (`.jsx`) | Photoshop CC 2015+ |
| `blender-addon/` | Python 3.11 | Blender 4.2 LTS, tested through 5.x |
| `godot-plugin/` | GDScript 2.0 | Godot 4.3+ |
| `schemas/proscenio.schema.json` | JSON Schema (draft 2020-12) | shared contract |

Strict dependency direction: Photoshop knows nothing of Blender; Blender knows nothing of Godot internals; Godot reads only `.proscenio`. The schema is the only shared artifact.

## Why no GDExtension

This is the single most important architectural decision. Spine ships a GDExtension because their `.skel` is a binary format, interpreted by their proprietary code at runtime, frame by frame, while the game runs. The engine needs native code to do that with acceptable performance.

Proscenio does the conversion **once, at editor import time**. The output is a `.tscn` made of built-in nodes — `Skeleton2D`, `Bone2D`, `Polygon2D`, `Sprite2D`, `AnimationPlayer`, `AnimationLibrary` — all of which are already C++ in Godot core. At runtime the game uses Godot's own animation system. There is nothing for our plugin to do.

| Dimension | Spine GDExtension | Proscenio EditorImportPlugin |
| --- | --- | --- |
| Runtime cost | non-zero, native call per frame | zero — built-in nodes |
| Per-platform compilation | yes | no |
| Update cadence vs Godot | breaks on engine API drift | only Skeleton2D API matters |
| End-user install | runtime + plugin | nothing — scene is portable |
| Maintenance | high | low |

The only case where GDExtension would be worth the cost is if we wanted to add a custom node type (e.g. `ProscenioCharacter` with proprietary tools). That is explicitly **out of scope**. Pure GDScript stays.

A consequence to enforce in code review: a generated `.tscn` must open and play in a Godot project that does **not** have the Proscenio plugin installed. The plugin is an editor-time tool only.

## Prior art investigation

### Godot 2D Bridge — Tor-Kai/Godot-2d-Bridge-1.0.0

Closest existing prior art. A Blender addon that exports 2D meshes and armatures to a Godot scene as `Polygon2D` and `Skeleton2D` nodes. Stuck on Godot 4.0, no animation support. Useful patterns from `gd2db_scene_parsing.py`:

- **Vertex ordering via BMesh boundary-first.** Boundary vertices come first, then internal vertices, to match Godot's polygon winding expectation. Worth replicating.
- **UV extraction.** Reads active render layer, scales by image dimensions, flips Y.
- **Bone weights from Blender vertex groups.** Mapped directly to Godot's `bones = [name, PoolRealArray(...)]` syntax.
- **Skeleton2D rest + pose.** Each bone gets a `Transform2D` for rest, plus current pose values.
- **Single armature per mesh.** Hard limit — Godot can't link more than one armature to a `Polygon2D`. Document and enforce.

What we deliberately do differently:

- They write `.tscn` text directly. We use `PackedScene.pack()` + `ResourceSaver.save()` inside an `EditorImportPlugin`. The Godot way, more robust against `.tscn` syntax drift across versions, and lets the engine canonicalize the output.
- They support multiple Godot major versions in one codebase (1.x / 2.x / 3.x). We target 4.3+ only.
- They have no animation pipeline. We do — the entire reason Proscenio exists.

### coa_tools2 — Aodaruma/coa_tools2

Forked from `ndee85/coa_tools` in 2023, alive on Blender 3.4 → 5.x. The Godot side is **not just broken — the export button is missing from the UI entirely** ([issue #28](https://github.com/Aodaruma/coa_tools2/issues/28), open since 2023, in-progress).

What `issue #28` reveals:

- The original `export_json.py` script still ships in `coa_tools2/operators/export_json.py` but is unreachable from the UI.
- The script is incompatible with Blender 2.8+ (Aodaruma's own assessment).
- A community contributor (EvgeneKuklin) patched it enough to run on Blender 3.6 in 2023 and reported that the JSON output had broken bone structure and broken animations even with the fix. The PR was never merged.
- The companion Godot importer was last compatible with Godot **2.1.4**.

What this tells us:

- We inherit nothing useful from `coa_tools2`'s Godot export. Start fresh.
- The community wants a generic JSON format with engine-specific importers (tozpeak comment on #28). That is exactly what Proscenio is. The interest is real.
- Photoshop/Krita exporters in `coa_tools2` work and can be ported forward to feed our `.proscenio` format.

### Original ndee85/coa_tools

Dead since 2019. JSON export was being actively removed by the maintainer at the time. The Godot importer (`coa_importer/`) was Godot 2.x only. Worth reading the GDScript source for the **reimport-with-merge algorithm** — that is the one piece of design we want to recover and modernize for Phase 2.

## Format `.proscenio` v1 — what is settled

Captured in [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json) and [`.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md).

- Top-level: `format_version`, `name`, `pixels_per_unit`, optional `atlas`, `skeleton`, `sprites`, optional `slots`, optional `animations`.
- Coordinates: Blender Y-up flipped to Godot Y-down by the exporter. Rotations negated CCW → CW. The Godot importer trusts the file.
- Bones: name, optional parent (null for root), position, rotation, scale, length.
- Sprites: name, optional bone, texture region in atlas pixels, polygon, UV, optional weights.
- Animations: name, length, optional loop, tracks of type `bone_transform`, `sprite_frame`, `slot_attachment`, `visibility`.

## Open questions and simplest current answers

For each open question, the simplest path is documented as the **current decision**. The decision is provisional — a follow-up SPEC can revisit any of these after MVP feedback.

### Q1 — `Sprite2D` vs `Polygon2D` for non-deformed sprites

`Polygon2D` is required for skinning. `Sprite2D` is required for spritesheet `frame` animation. A simple un-skinned quad could be either.

**Current decision:** MVP emits **`Polygon2D` everywhere**. A simple quad is `polygon = [4 corners], uv = [(0,0),(1,0),(1,1),(0,1)]`. No special-case for `Sprite2D` until Phase 2 spritesheets. The schema does not need a `type` discriminator yet.

### Q2 — Cubic interpolation

The schema currently lists `cubic` as a valid `interp` value, but cubic Bézier needs in/out tangent handles per key, which the schema does not define. Latent bug.

**Current decision:** **drop `cubic` from v1**. Keep `linear` and `constant`. Cubic with proper handle fields lands in a future format bump if real demand arises. Update schema and `format-spec.md` accordingly (TODO).

### Q3 — Bone weights and skinning wiring

Schema models `weights` as optional per sprite. The Godot importer scaffold does not yet wire `Polygon2D.skeleton` and `set_bones()`.

**Current decision:** MVP supports **rigid attachment only** — a sprite without `weights` becomes a child of its target `Bone2D` and rides the bone transform. Sprites with `weights` are accepted in the schema but ignored at import in MVP, with a console warning. Full skinning lands in Phase 2.

### Q4 — Atlas packing

Who packs the atlas?

**Current decision:** **external pre-pack**. The artist runs TexturePacker (or similar) and the Blender addon consumes the resulting atlas + per-sprite `texture_region` metadata. The `atlas` field is a path. Phase 2 may add an in-Blender packer, but it is not required.

### Q5 — Animation events

Spine has trigger events (audio cues, particle spawns) embedded in the animation format. Godot's `AnimationPlayer` supports method tracks for the same purpose.

**Current decision:** **out of scope for v1**. No `event` track type. Add in v2 if real demand surfaces.

### Q6 — Multiple `AnimationLibrary` instances per character

`AnimationPlayer` in Godot 4 can hold multiple named libraries.

**Current decision:** **single default library** (`""`). Animations grouped under one library named after the character. Sufficient for one character one set of animations. Phase 2 may revisit if multi-character scenes benefit from grouping.

### Q7 — Multiple atlases per character

`atlas` field is a single string.

**Current decision:** **one atlas per `.proscenio` file**. If a character genuinely needs more textures than fit in one atlas, split into multiple `.proscenio` files. Revisit in v2.

### Q8 — Material, blend modes, shaders

`Polygon2D` exposes `modulate`, `texture`, `texture_offset`, etc. Nothing for normal maps or custom shaders.

**Current decision:** **out of scope for v1**. The user can attach a custom material to the imported `Polygon2D` post-import; non-destructive reimport (Phase 2) preserves it.

### Q9 — Coordinate origin of the character root

Where is `(0, 0)` for the character?

**Current decision:** the **scene-root `Node2D`** is the character origin. The `Skeleton2D` lives at `(0, 0)` relative to it. The `root` bone (if any) carries any offset. Consistent with how artists think about anchor points.

## Risks

- **Reimport-merge complexity (Phase 2).** The scene tree diff/merge algorithm is non-trivial and has no clean prior art for Godot 4. Expect a dedicated SPEC before implementation.
- **Blender API drift across 4.x/5.x.** `coa_tools2` has been chasing this constantly (issues #92, #93, #95, #107, #109, #110, #111). Use only stable `bpy` APIs; pin to documented LTS surface.
- **`PackedScene.pack()` round-trip.** Untested at scale for our specific node mix. Validate early with the dummy fixture.
- **Y-flip and rotation negation.** Easy to get wrong. The dummy fixture must include at least one bone with a non-zero rotation and a sprite offset from origin to catch sign errors.

## Out of scope (explicit no)

- Custom Godot node types via GDExtension.
- IK constraint export — Godot's built-in `Skeleton2DIK` is added in-engine post-import.
- DragonBones export (the original ndee85 path).
- Spine `.skel` interop.
- A Blender modal edit mode like the COA Tools "edit mode" — already correctly abandoned by `coa_tools2`.
- Krita exporter rewrite — port from `coa_tools2` in Phase 2 if needed.

## References

- Repo: <https://github.com/Tor-Kai/Godot-2d-Bridge-1.0.0>
- Repo: <https://github.com/Aodaruma/coa_tools2>
- Repo: <https://github.com/ndee85/coa_tools>
- Issue: <https://github.com/Aodaruma/coa_tools2/issues/28> — confirms the Godot export gap
- Godot docs: `EditorImportPlugin`, `PackedScene`, `ResourceSaver`, `AnimationLibrary`, `Skeleton2D`, `Bone2D`, `Polygon2D`
- Spine Godot integration story: <https://github.com/EsotericSoftware/spine-runtimes/tree/4.2/spine-godot> (cited as the anti-pattern we avoid)

## Successor SPECs to expect

| Number | Topic |
| --- | --- |
| 001 | Reimport with non-destructive merge |
| 002 | Spritesheet support (introduces `Sprite2D` path) |
| 003 | Skinning weights and `Polygon2D.skeleton` wiring |
| 004 | Slot system |
| 005 | Blender authoring panel (COA Tools-style ergonomics) |

> Phase 1 MVP (originally penciled as SPEC 001) shipped under SPEC 000's TODO since the scope was small enough to absorb. SPECs are renumbered from 001 onward to keep the catalog dense.
