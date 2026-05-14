# Comparison

How Proscenio sits next to other 2D cutout / character-animation pipelines and engine-native options.

## Feature matrix

`yes` = shipped, `partial` = incomplete or wrapped, `no` = absent or out of scope, `-` = non-applicable. Parenthetical notes after the status word qualify it.

Standalone authoring tools and engine-native + plugin paths grouped from left to right. "Godot native" / "Unity 2D Animation" sit alongside the popular plugin add-ons available on each engine (Souperior on Godot; Puppet2D and AnyPortrait on Unity).

| Capability | Proscenio | Spine | COA Tools 2 | Live2D | DragonBones | Godot native | Souperior (Godot plugin) | Unity 2D Animation | Puppet2D (Unity plugin) | AnyPortrait (Unity plugin) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **License** | GPL-3.0 | paid | GPL | paid (free tier) | open | open | MIT | proprietary | paid (Asset Store) | paid (Asset Store) |
| **Target engine** | Godot 4 only | multi (40+ runtimes) | Godot (broken), generic | Cubism viewer + AE/Unity SDK | multi (Cocos, Unity, Phaser…) | Godot 4 | Godot 4 (extends Skeleton2D) | Unity | Unity | Unity |
| **Output is engine-native scene** | yes (`.scn` with core nodes) | no (runtime required) | no (runtime required) | no (SDK required) | no (runtime required) | yes | yes (uses Skeleton2D modifications) | yes | yes (Unity GameObjects) | partial (AnyPortrait runtime component) |
| **Plugin-uninstall safe** | yes | no | no | no | no | - | no (IK nodes ARE the plugin) | - | no (runtime scripts required) | no (AnyPortrait runtime required) |
| **Authoring tool** | Blender + Photoshop | Spine editor | Blender + PSD/GIMP/Krita | Cubism + PSD | DragonBones Pro + PSD | Godot editor | Godot editor | Unity editor + PSD Importer | Unity editor + Puppet2D windows | Unity editor + AnyPortrait window (in-engine) |
| **PSD ingestion** | yes (JSX + manifest schema) | yes | yes (multi-DCC) | yes | yes | no | no (rigging only) | yes (2D PSD Importer) | no (Unity sprites) | yes (layered PSD import) |
| **Skeleton + bones** | yes | yes | yes | - | yes | yes (Skeleton2D) | yes (extends Skeleton2D) | yes (Sprite Skinning) | yes | yes |
| **Polygon mesh + per-vertex weights** | yes | yes (FFD) | yes | partial (deformer-based) | yes | yes (Polygon2D) | no (bone-side only) | yes | yes (control-point mesh deform) | yes (mesh deform) |
| **Spritesheet cells (`hframes` / `vframes`)** | yes (Sprite2D) | yes | yes | - | yes | yes (AnimatedSprite2D) | no | yes | no | yes |
| **Slot / sprite-swap system** | yes | yes | yes | - | yes | no | no | partial (Sprite Library / Resolver) | partial | yes |
| **Skin coordination (group of slots)** | no (candidate post-008) | yes | no | - | yes | no | no | partial (Sprite Library categories) | no | partial |
| **Inverse Kinematics** | partial (wrap of Blender native) | yes (pose tool) | partial | - | yes | yes (Skeleton2D modifications) | yes (IK + LookAt, primary feature) | yes (IK Manager 2D) | yes (IK chains) | yes |
| **Path constraints** | no | yes | no | - | no | partial (PathFollow2D) | no | partial | no | yes (motion paths) |
| **Bone physics** | no (backlog) | yes | no | yes | partial | no | no | partial (community) | no | yes (jiggle / dynamics) |
| **Animation events / method tracks** | no (backlog) | yes | no | partial | partial | yes (AnimationPlayer) | yes (inherits Godot AnimationPlayer) | yes (Animation Events) | yes (Unity AnimationClip) | yes |
| **Bezier curve preservation in export** | no (format v2) | yes | yes (via Blender) | - | yes | yes | yes (inherits Godot) | yes | yes (Unity native) | yes |
| **Atlas packing (rotation, slicing)** | partial (no rotation) | yes | yes | yes | yes | partial (manual) | no | yes (Sprite Atlas) | yes (Unity) | yes |
| **Multi-atlas per character** | no (format v2) | yes | yes | yes | yes | - | - | yes | yes (Unity) | yes |
| **Mid-edit re-rig non-destructive** | partial (wrapper survives, weights/keys do not) | partial (skins help) | partial | yes | partial | - | yes (lives in Godot) | partial | partial | partial |
| **Preview = runtime parity** | no (Blender ≠ Godot) | yes (runtime in editor) | no | yes (Cubism viewer) | yes | yes (same engine) | yes (same engine) | yes (same engine) | yes (same engine) | yes (same engine) |
| **Hot reload on save** | partial (Godot side only) | yes | partial | yes | yes | yes | yes | yes | yes | yes |
| **Auto-rig / templates / presets** | no | partial (pose tool) | partial | yes (physics presets) | partial | no | no | partial (community) | no | partial (templates) |
| **Mesh-from-contour (automesh)** | no | yes | yes | - | partial | no | no | no | no (manual control points) | yes (auto-mesh from sprite) |
| **Strong typing across pipeline** | yes (mypy strict + GDScript typed + TypeScript strict) | - | no | - | - | - | - | - | - | - |
| **Versioned export schema (open)** | yes (JSON Schema 2020-12, 5 gates) | proprietary | no | proprietary | proprietary | - | - | - | proprietary | proprietary |

## Positioning summary

- **Against Spine.** Proscenio gives up multi-runtime, bone physics, path constraints, and a polished in-editor preview in exchange for being free, open, native to Godot, and plugin-uninstall safe. Wins on contract transparency and engine-native output. Loses on iteration loop tightness.
- **Against COA Tools 2.** Proscenio is more conservative on authoring acceleration (no automesh, only PSD bridge today) and more rigorous on schema and CI (mypy strict, `format_version`, golden fixtures). The Godot output is the differentiator: CT2's Godot importer is broken; Proscenio generates plain `.scn` that any Godot 4 project can open.
- **Against Live2D.** Different paradigm. Live2D wins on illustration-first deformer rigs and parameter-driven facial animation. Proscenio wins on game-runtime fit and skeleton-based cutout. Not direct competitors; the two cover different art forms.
- **Against DragonBones.** Both open. DragonBones wins on multi-runtime breadth and a community editor. Proscenio wins on Blender-as-editor (no proprietary DCC) and on Godot scene-native output without a runtime layer.
- **Against Godot native (no plugin).** Godot's `Skeleton2D` + `Polygon2D` + `AnimationPlayer` are exactly what Proscenio outputs. The gap Proscenio fills is the **authoring** side: rig and animate in Blender's mature toolset rather than in Godot's editor, with PSD ingestion and schema validation along the way.
- **Against Souperior 2D Skeleton Modifications (Godot plugin).** Souperior is complementary, not competitive: it adds IK and LookAt nodes on top of Godot's Skeleton2D modification system. A Proscenio-imported scene can use Souperior nodes for in-engine IK polish; the two stack rather than replace each other. Souperior alone does not author cutout characters (no PSD ingestion, no mesh, no slots).
- **Against Unity 2D Animation + PSD Importer.** Unity 2D is the closest analog feature-set on the Unity side. Unity's pitch is "stay in Unity"; Proscenio's pitch is "stay in Blender, ship to Godot." Apples-to-oranges across engines, but a useful checkpoint for parity expectations.
- **Against Puppet2D (Unity plugin).** Paid Unity Asset Store plugin focused on skeletal rigging with control-point mesh deform. No PSD ingestion path, no spritesheet variant, no slot system. Proscenio targets Godot, so direct competition is null; on paradigm, Puppet2D is closer to a lighter Spine-on-Unity than to Proscenio's full Photoshop→Blender→engine chain.
- **Against AnyPortrait (Unity plugin).** Paid Unity Asset Store asset that is the most feature-comparable Unity-side counterpart: PSD layered import, mesh deform with weights, bones, IK, motion paths, bone physics, blend modes, automesh from sprite. Authoring lives in a Unity-internal editor window and play-time uses an AnyPortrait runtime component (not engine-native scenes). Proscenio's differentiation is engine-native output and an open contract; AnyPortrait's differentiation is a richer single-tool authoring surface.

## Paradigms

Cross-tool QoL paradigms the community celebrates, and where Proscenio sits on each axis.

### Adopted

- **Source-art preservation.** PSD layers survive into Blender via the manifest; Blender data survives into Godot via the wrapper-scene pattern. Reimport never destroys user-authored wrappers. (Live2D, Spine, COA all sell this.)
- **Engine-native output.** Generated `.scn` uses only Godot core nodes. Plugin uninstall is a hard test, not a hope. (Differentiator vs Spine, DragonBones, CT2 Godot importer.)
- **Direct manipulation in the DCC.** Authoring inherits Blender's existing weight paint, dopesheet, NLA, drivers. Proscenio adds shortcuts (Quick Armature, Drive from Bone), not proprietary modes. (CT2 markets this as "no proprietary modes.")
- **Versioned contract as single source of truth.** Schema bumps are explicit, validated in 5 gates, and force migration. (Inherited from data-engineering practice; rare among DCC pipelines.)
- **Strong typing end-to-end.** Python `mypy --strict`, GDScript `untyped_declaration=2`, TypeScript `strict`. (Paradigm absent from prior art.)

### Partially adopted

- **Non-destructive iteration.** Wrapper survives; weights and keys do not survive a re-rig today. (RubberHose and Spine skins set the bar higher.)
- **Sketch-speed authoring.** Quick Armature and Create Slot reduce friction; export still costs three clicks (Validate → Export → copy). (COA's bone-draw is the reference target.)
- **Atlas efficiency.** Atlas packer ships, no rotation packing yet, no multi-atlas. (Spine and DragonBones lead here.)
- **Onboarding investment.** In-panel `?` popups and topic help land. Tutorials, reference characters, and showcase fixtures are still light. (Live2D's investment in samples and lessons is the high-water mark.)

### Not adopted (and why)

- **Preview = runtime parity.** Blender preview ≠ Godot runtime today. Workbench mode ignores the slot preview shader. Closing this gap likely requires a Godot live-link, which would reopen the GDExtension decision. Currently a known cost.
- **Auto-rig / parameter-driven templates.** Proscenio leaves rig topology to the user. No humanoid template, no quadruped preset, no parameter binder. Rationale: scope discipline; Blender's existing rig presets are reachable from the user side.
- **Parameter-driven deformer rigs (Live2D paradigm).** Out of scope; different art form.
- **Mid-animation re-rig (RubberHose paradigm).** Format v1 bakes the rig into tracks; re-rigging mid-flight would need bezier preservation (format v2) plus key remapping logic.
