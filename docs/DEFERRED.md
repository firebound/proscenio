# Deferred / future SPECs

In scope conceptually, not yet shipped. Each becomes a numbered SPEC when work begins; promotion order is not committed. For finer-grained items (single operators, CI matrix, repo polish) see [`specs/backlog.md`](../specs/backlog.md).

## Mesh tessellation from contour

Two related variants under one umbrella, both flagged as future SPEC in [`specs/005-blender-authoring-panel/RESEARCH.md`](../specs/005-blender-authoring-panel/RESEARCH.md):

- **From drawn outline.** User draws an outline in Blender; the operator fills it with a triangulated mesh and auto-UVs against the source texture. Direct port of COA Tools 1's `generate_mesh_from_edges_and_verts`. No external dependency required - Blender's `bmesh` and standard triangulation cover it.
- **From image alpha.** Auto-generates a mesh by walking the source image's alpha channel into a contour. Heavier; CT2 issue #6 is the reference. Avoids external CV2 stack only if the implementation stays inside Blender's own image pipeline.

## Skin coordination (Spine "skins")

Group N slot attachments into a named "skin" so a single setting flips the whole costume / character variant at once. Slots today are per-slot only.

## Bezier curve preservation

Format v1 bakes keyframes as cubic samples. Future v2 transmits per-key Bezier handles (`tangent_in`, `tangent_out`) so Blender curves arrive in Godot byte-for-byte.

## Animation events / method tracks

Sound cues, particle spawns, gameplay hooks. Maps to Godot's `AnimationPlayer` method tracks. Needs an `event` track type in the schema.

## Bone physics, path constraints, transform constraints

Spine-style runtime constraints. Out of v1; needs concrete demand and likely a format extension.

## Multi-atlas per character

Single atlas per character today. Future v2 may carry an `atlas_pages[]` array indexed by sprite.

## Per-key interpolation mixing

Schema's `interp` is per-key but the importer applies one interpolation per track. Mixed `linear` / `constant` / `cubic` keys would need track splitting at import or a Bezier track type.

## Krita / GIMP exporters

Photoshop side proven first. The PSD manifest schema is DCC-agnostic by design; Krita / GIMP exporters become viable once SPEC 006 contract is fully stable.

## Live link Blender ↔ Godot

Hot reload across the DCC boundary. Auto-import on file change works Godot-side today; Blender-side export is manual. Likely triggers the GDExtension reconsideration listed under Architecture revisits in [`specs/backlog.md`](../specs/backlog.md).

## Mid-edit non-destructive re-rig

Today the wrapper scene survives reimport, but weights and keys do not survive a re-rig of the underlying armature. RubberHose-style "adjust mid-animation without losing keys" remains a longer-term goal; partial coverage will likely come with Bezier preservation + key remapping.

## Symmetric / non-destructive weight transfer

Power-user feature for character variants sharing skeleton + mesh shape. Transfers weights between sprites with identical topology via modifiers.

## Mask sprite, blend modes, per-sprite alpha / z / modulate_color

Format extensions covering sprite blending, alpha mask sprites, animatable color modulation. Each adds optional fields to the `Sprite` shape and matching track types.

## Procedural mesh subdivision presets

Quick-rig presets that subdivide a plane into a usable deformable mesh density (low / medium / high) so the user does not start from a 4-vertex quad each time. Pairs naturally with mesh-from-contour.

## Auto-rig templates (humanoid, quadruped, doll)

Preset rigs the user can apply to a sprite group. Less ambitious than DUIK auto-rig; more like "Create biped armature with bone naming the writer expects" so onboarding is one click.
