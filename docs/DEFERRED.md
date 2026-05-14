# Deferred - long-term direction

The big picture. Each item below is an *umbrella initiative* that conceptually fits Proscenio but is not committed to a roadmap. When work begins, the umbrella breaks down into one or more numbered SPECs.

This file is intentionally coarse. Finer-grained items (single operators, CI matrix entries, repo polish, follow-ups deferred from shipped SPECs) live in `specs/backlog.md` with their own trigger conditions.

## Authoring acceleration

Lift the artist out of "start from a 4-vertex quad" mode and toward "draw a shape, get a riggable mesh".

- **Mesh tessellation from contour.** From a drawn outline (Blender `bmesh` + triangulation) or from the source image's alpha channel.
- **Procedural mesh subdivision presets.** Low / medium / high density quad subdivision so the user does not start from scratch.
- **Auto-rig templates.** Humanoid, quadruped, doll presets - "create armature with the bone naming the writer expects". Less ambitious than full auto-rig; more of a one-click onboarding step.

## Animation expressiveness

Match what the established cutout tools (Spine, DragonBones, CT2) deliver out of the box.

- **Bezier curve preservation.** Per-key in / out tangent handles in the schema so Blender's curve fidelity arrives byte-for-byte in Godot.
- **Per-key interpolation mixing.** Mixed `linear` / `constant` / `cubic` keys on the same track.
- **Animation events / method tracks.** Sound cues, particle spawns, gameplay hooks - maps to Godot's `AnimationPlayer` method tracks. Removes the mirror-`AnimationPlayer` workaround.
- **Mid-edit non-destructive re-rig.** Today the wrapper survives reimport, but weights and keys do not survive a re-rig of the underlying armature. Partial coverage likely arrives with Bezier preservation + key remapping.

## Rig topology and physics

The runtime side of "what a character can do".

- **Skin coordination.** Spine-style "skin" that groups N slot attachments under a named variant; one switch flips the whole costume.
- **Bone physics, path constraints, transform constraints.** Spine-style runtime constraints. Requires a format extension and concrete demand.
- **Symmetric / non-destructive weight transfer.** Transfer weights between sprites with identical topology for character variants sharing skeleton + mesh.

## Format extensions

Each adds optional fields to the schemas and matching consumer logic.

- **Multi-atlas per character.** Single atlas today; future `atlas_pages[]` indexed by sprite.
- **Mask sprite, blend modes, animatable color modulation.** Per-sprite alpha mask, animatable `modulate` color, animatable `z_index`.

## Cross-DCC reach

The PSD manifest schema is DCC-agnostic by design.

- **Krita / GIMP exporters.** Emit a conforming manifest from another DCC; Blender importer needs no changes.
- **Live link Blender ↔ Godot.** Hot reload across the DCC boundary. Likely triggers the GDExtension reconsideration.
