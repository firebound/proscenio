# SPEC 001 - Reimport without losing user work

Status: **draft**, design phase. No implementation until the questions below are settled.

## Problem

The Godot importer ([`apps/godot/addons/proscenio/importer.gd`](../../apps/godot/addons/proscenio/importer.gd)) regenerates a packed scene from each `.proscenio` on every reimport. A re-export from Blender therefore clobbers any work the user did *to the imported scene itself*: attached scripts, child nodes added in the editor, animations authored in Godot, exported property values.

This is fine for first import but punishes iteration. The user authors a character in Blender, imports, attaches a `dummy.gd` to the root, adds a `CollisionShape2D` under the `torso` bone, then re-exports a fixed-up animation from Blender - and loses the script and the collision.

The decision: pick the merge strategy and document it.

## Constraints

- **No GDExtension** ([`.ai/skills/architecture.md`](../../.ai/skills/architecture.md)). Whatever merge logic ships runs in GDScript at editor-import time only.
- **`.proscenio` is the source of truth** for everything authored in the DCC (bones, sprite shapes, atlas regions, DCC-authored animations).
- **The plugin must remain optional at runtime** ([SPEC 000 plugin-uninstall test](../000-initial-plan/TODO.md)). The merged scene must still open and play with the plugin disabled.
- **Reimport must be deterministic.** Re-running the importer on the same `.proscenio` with no editor edits in between must produce a byte-identical scene (or at least a semantically identical one - explicit goal: no flapping diffs in version control).

## Design options

### Option A - Full overwrite (current behavior)

The importer rebuilds the scene from scratch and overwrites the previous output. The user wraps the generated scene in their own scene and customizes there.

**How it works.** The user creates `Dummy.tscn` that *instances* the imported `dummy.scn` (or *inherits* from it). Scripts and extra nodes live on the wrapping scene, not on the generated one. Reimport touches only `dummy.scn`; `Dummy.tscn` is untouched.

**Pros.**

- Zero merge logic in the importer.
- Aligns with Godot's idiomatic instance/inherit pattern.
- Plugin-uninstall guarantee survives trivially: the generated scene is just nodes and resources, the user's wrapper is a normal `.tscn`.

**Cons.**

- The user cannot attach a script to a *bone inside* the generated scene (Godot doesn't let you add scripts to nodes inside an instanced sub-scene unless you make them editable children, which is fragile).
- Per-bone customization (a script on `head`, an extra `Particles2D` parented to `hand`) requires "Editable Children" or a node-replacement workflow at runtime.
- Animations authored in the editor cannot extend the imported `AnimationLibrary` - they live in a sibling `AnimationPlayer` on the wrapping scene, which is awkward but not broken.

### Option B - Marker-based merge

Reimport reads the previous output `.scn` (via `ResourceLoader`), walks both trees, and preserves any node tagged with metadata `_proscenio_user = true`. User-added nodes carry that flag; auto-generated nodes don't. Animations follow the same rule via `AnimationLibrary` metadata.

**How it works.**

1. The importer loads the existing `.scn` if present.
2. It builds the fresh scene from the `.proscenio`.
3. It walks the existing scene's tree, finds nodes flagged `_proscenio_user = true` (and their entire subtree), and re-parents them onto the matching bone or sprite in the fresh scene by **node-name match**.
4. Scripts and exported properties on root, sprites, and bones come from the existing scene if those targets are matched by name.
5. The merged scene replaces the existing `.scn`.

**Pros.**

- The user can attach scripts to *any* node and add children to *any* bone. The generated scene is the canonical scene.
- Iteration story matches Spine/COA expectations: edit in DCC, re-export, keep working.

**Cons.**

- Bone renames in Blender break the match. Without stable IDs in the schema (and there are none in v1), a rename looks like *delete old + add new*, and user work attached to the old name is dropped.
- "Editable children" semantics: scripts on a node that came from the generated scene will be reset when that node is regenerated, unless the importer reads them off the old scene and reapplies them.
- Significant new code in the importer; significant new test surface.
- Plugin-uninstall guarantee still holds because the *output* is still a regular `.scn`, but the *import-time logic* now reads-modifies-writes - first-class debugging of merge state becomes a real workflow.

### Option C - Hybrid: A by default, B opt-in

The importer's default behavior is full overwrite (Option A). The user opts into merge per-asset via an import option `preserve_user_edits = true` exposed on the importer. When enabled, the importer runs Option B's merge logic.

**Pros.**

- Lets the simple case stay simple.
- Lets users with deep per-bone customization needs opt in.
- Encourages the instance/inherit pattern (A) as the documented default.

**Cons.**

- Two code paths.
- Users will not realize the option exists until they lose work once.

## Recommendation

**Adopt Option A as the default and document the instance/inherit pattern as the canonical workflow.** Defer Option B unless and until concrete user demand emerges that the wrapper-scene pattern cannot serve.

Reasons:

- The instance/inherit pattern is what Godot does for every other complex resource (`Skeleton3D`-driven characters, GLTF imports, etc.). Adopting it here makes Proscenio feel native to the engine.
- Option B is a moving target: bone renames, sprite renames, atlas region rebakes, animation track rewrites all change identity, and without schema-level stable IDs, name-matching is the only available strategy and is fragile.
- The plugin-uninstall constraint cuts harder against Option B: every merge bug is a potential bug in the *output*, not just the importer.
- Option A unblocks the user today with zero new code. If demand for B emerges, B can be added later as Option C without changing default behavior.

## Open questions

- **Q1.** Where in `apps/godot/` should the canonical "wrapper scene" example live, and how should it be documented? Tentative: `examples/dummy/Dummy.tscn` instancing `dummy.scn`, with a one-paragraph note in [`.ai/skills/godot-dev.md`](../../.ai/skills/godot-dev.md).
- **Q2.** Is "Editable Children" workflow good enough for users who want to attach a script to a single bone inside the imported scene, or do we need to ship a small helper that scripts a Bone2D safely? Default: don't ship anything until someone asks.
- **Q3.** Animations authored in Godot - should the wrapper scene's `AnimationPlayer` *merge* the imported `AnimationLibrary` plus user-authored animations into a single named library (so playback is one call), or is it acceptable to have two libraries side by side? Tentative: document that the wrapper can call `AnimationPlayer.add_animation_library("user", user_lib)` alongside the imported `""` library and play across both.
- **Q4.** If a user re-exports the `.proscenio` with a renamed bone, the generated `.scn` changes structurally. Wrapper scenes that referenced the old bone name (`$Skeleton2D/torso`) break. Acceptable cost? Tentative: yes, document it as the price of a cross-DCC rename. A rename in Blender is a rename in Godot - same as renaming a node in any other engine workflow.

## Out of scope

- Anything that requires a stable-ID extension to the `.proscenio` schema. That's a v2 conversation and would force SPEC 001 to wait on a format bump.
- Diffing animations key-by-key. Animations are owned by the DCC in v1; user-authored animations belong to the wrapping scene.
- Live link / hot reload - separate concern, not in this spec.
