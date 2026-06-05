# Tools Comparison

How Proscenio sits next to other 2D cutout / character-animation pipelines and engine-native options.

## Feature matrix

`yes` = shipped, `partial` = incomplete or wrapped, `no` = absent or out of scope, `-` = non-applicable. Parenthetical notes after the status word qualify it.

Columns are ordered by how directly each compares to Proscenio: the headline rivals first - Spine, Godot's built-in 2D, Unity's first-party 2D Animation, and Moho - then the other suites and engine plugins. Moho's live-skeleton game export (glTF) is recent (Moho 14.4, late 2025); earlier versions bake only sprite sheets or video.

| Capability | Proscenio | Spine | Godot native | Unity 2D Animation | Moho | COA Tools 2 | Live2D | DragonBones | Souperior (Godot plugin) | Puppet2D (Unity plugin) | AnyPortrait (Unity plugin) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **License** | GPL-3.0 | paid | open | proprietary | paid (Debut / Pro) | GPL | paid (free tier) | open | MIT | paid (Asset Store) | paid (Asset Store) |
| **Target engine** | Godot 4 only | multi (~20 runtimes) | Godot 4 | Unity | multi via glTF (14.4+) | Godot (broken), generic | Cubism viewer + AE/Unity SDK | multi (Cocos, Unity, Phaser…) | Godot 4 (Skeleton2D modifier nodes) | Unity | Unity |
| **Output is engine-native scene** | yes (`.scn` with core nodes) | no (runtime required) | yes | yes | no (glTF interchange) | no (runtime required) | no (SDK required) | no (runtime required) | yes (uses Skeleton2D modifications) | yes (Unity GameObjects) | partial (AnyPortrait runtime component) |
| **Plugin-uninstall safe** | yes | no | - | - | - | no | no | no | no (IK nodes ARE the plugin) | no (runtime scripts required) | no (AnyPortrait runtime required) |
| **Authoring tool** | Blender + Photoshop | Spine editor | Godot editor | Unity editor + PSD Importer | Moho editor + PSD | Blender + PSD/GIMP/Krita | Cubism + PSD | DragonBones Pro + PSD | Godot editor | Unity editor + Puppet2D windows | Unity editor + AnyPortrait window (in-engine) |
| **PSD ingestion** | yes (UXP + manifest schema) | yes | no | yes (2D PSD Importer) | yes (Pro) | yes (multi-DCC) | yes | yes | no (rigging only) | no (Unity sprites) | yes (layered PSD import) |
| **Skeleton + bones** | yes | yes | yes (Skeleton2D) | yes (Sprite Skinning) | yes (Smart Bones) | yes | - | yes | yes (operates on Skeleton2D) | yes | yes |
| **Polygon mesh + per-vertex weights** | yes | yes (FFD) | yes (Polygon2D) | yes | partial (bone binding, vector-first) | yes | partial (deformer-based) | yes | no (bone-side only) | yes (control-point mesh deform) | yes (mesh deform) |
| **Spritesheet cells (`hframes` / `vframes`)** | yes (Sprite2D) | yes | yes (Sprite2D) | yes | no (PNG sequence only) | yes | - | yes | no | no | partial (export only) |
| **Slot / sprite-swap system** | yes | yes | no | partial (Sprite Library / Resolver) | yes (Switch Layers) | yes | - | yes | no | partial | yes |
| **Skin coordination (group of slots)** | no (candidate follow-up) | yes | no | partial (Sprite Library categories) | partial | no | - | yes | no | no | partial |
| **Inverse Kinematics** | partial (wrap of Blender native) | yes (pose tool) | yes (SkeletonModification2D, experimental) | yes (IK Manager 2D) | yes | partial | - | yes | yes (IK + LookAt, primary feature) | yes (IK chains) | yes |
| **Path constraints** | no | yes | partial (PathFollow2D) | no | partial (Follow Path) | no | - | no | no | no | no |
| **Bone physics** | no (backlog) | yes | no | no (community only) | yes (Bone Dynamics, Pro) | no | yes (pendulum, not bone-based) | no | yes (jiggle) | no | yes (jiggle / dynamics) |
| **Animation events / method tracks** | no (backlog) | yes | yes (AnimationPlayer) | yes (Animation Events) | no | no | partial | yes | yes (inherits Godot AnimationPlayer) | yes (Unity AnimationClip) | yes |
| **Bezier curve preservation in export** | no (format v2) | yes | yes | yes | no (baked on export) | yes (via Blender) | - | yes | yes (inherits Godot) | yes (Unity native) | yes |
| **Atlas packing (rotation, slicing)** | partial (no rotation) | yes | partial (manual) | yes (Sprite Atlas) | no | yes | yes | yes | no | yes (Unity) | yes |
| **Multi-atlas per character** | no (format v2) | yes | - | yes | no | yes | yes | yes | - | yes (Unity) | yes |
| **Mid-edit re-rig non-destructive** | partial (wrapper survives, weights/keys do not) | partial (skins help) | - | partial | partial | partial | yes | partial | yes (lives in Godot) | partial | partial |
| **Preview = runtime parity** | no (Blender ≠ Godot) | yes (runtime in editor) | yes (same engine) | yes (same engine) | partial (glTF) | no | yes (Cubism viewer) | yes | yes (same engine) | yes (same engine) | yes (same engine) |
| **Hot reload on save** | partial (Godot side only) | yes | yes | yes | - | partial | yes | yes | yes | yes | yes |
| **Auto-rig / templates / presets** | no | partial (pose tool) | no | partial (community) | yes (Character Wizard) | partial | yes (physics presets) | partial | no | yes (auto-rig biped) | partial (templates) |
| **Mesh-from-contour (automesh)** | yes (alpha trace) | yes | no | yes (Auto Geometry) | no (manual) | yes | yes (auto mesh gen) | partial | no | no (manual control points) | yes (auto-mesh from sprite) |
| **Strong typing across pipeline** | yes (mypy strict + GDScript typed + TypeScript strict) | - | - | - | - | no | - | - | - | - | - |
| **Versioned export schema (open)** | yes (JSON Schema 2020-12, 5 gates) | proprietary | - | - | partial (glTF) | no | proprietary | proprietary | - | - | proprietary |

## Positioning summary

Each tool below reads from Proscenio's side: *Win* where Proscenio aims to be better, *Loss* where it is worse, *Tie* where they match.

- **Spine**
  - *Win:* free and open (GPL); engine-native `.scn` with no runtime library; plugin-uninstall safe; an open, strongly-typed export contract (Spine's format is proprietary).
  - *Loss:* multi-runtime export; bone physics, path constraints, skin coordination; bezier preserved through export; runtime-accurate in-editor preview; tighter iteration loop.
  - *Tie:* skeleton, mesh + weights, slots, spritesheets, automesh - both cover the cutout core.

- **Godot native (no plugin)**
  - *Win:* the entire authoring layer - PSD ingestion, Blender rigging, automesh, slots - plus a typed export contract; with bare Godot you hand-build all of it in-editor.
  - *Loss:* no export hop, same-engine preview parity, native `AnimationPlayer` events and bezier curves.
  - *Tie:* the output is identical - Proscenio emits exactly Godot's `Skeleton2D` + `Polygon2D` + `AnimationPlayer`.

- **Unity 2D Animation + PSD Importer**
  - *Win:* open and free vs Unity's proprietary stack; Blender's mature rig + animation toolset; typed open contract.
  - *Loss:* single-engine workflow (no export hop), same-engine preview, runtime IK, full atlas packing, animation events, and a broad ecosystem.
  - *Tie:* near feature-match on the cutout core - PSD rig, Auto Geometry automesh, mesh + weights, skeleton - across a different engine. (Proscenio's slot system is fuller than Unity's partial Sprite Library.)

- **Moho**
  - *Win:* engine-native Godot scene + typed contract; automesh (Moho dropped auto-trace in v13); a plugin-free runtime; free and open.
  - *Loss:* Moho's authoring depth - Smart Bones, bone-dynamics physics, mature IK, Character Wizard, content library - a full app versus a thin plugin.
  - *Tie:* PSD-to-rig, skeleton + bone-driven deform, slot / switch-layer swaps.
  - Note: Moho's live-skeleton game export (glTF) only arrived in 14.4 (late 2025) and is generic + lossy; older versions bake sprite sheets or video only.

- **COA Tools 2**
  - *Win:* a working, typed Godot export (COA's importer is unmaintained); pure-Python automesh with no `cv2` install blocker; schema + CI rigor.
  - *Loss:* multi-DCC ingestion - COA reads PSD, GIMP, and Krita; Proscenio is PSD-only today.
  - *Tie:* Blender as the authoring host, automesh, skeleton + mesh + slots.

- **Live2D**
  - *Win:* game-runtime fit, skeleton-based cutout, engine-native and open output.
  - *Loss:* illustration-first deformer rigs, parameter-driven facial animation, mature physics and presets.
  - Note: a different art form, not a direct rival - the two barely overlap.

- **DragonBones**
  - *Win:* engine-native Godot output (no runtime lib); typed open schema; stronger automesh (DragonBones' is rough); actively maintained (the DragonBones editor has been stale since ~2021).
  - *Loss:* multi-runtime breadth; skin coordination; richer exported animation (runtime IK, events, bezier).
  - *Tie:* open and free, skeleton + mesh + weights, slots.

- **Souperior (Godot plugin)**
  - *Win:* Proscenio authors the whole character - PSD, mesh, slots - which Souperior cannot.
  - *Loss:* Souperior adds richer in-engine IK / LookAt / jiggle than Proscenio, which exports no constraints.
  - Note: complementary, not competing - import with Proscenio, polish with Souperior; the two stack.

- **Puppet2D (Unity plugin)**
  - *Win:* PSD ingestion, spritesheet variants, a slot system, automesh, engine-native + open output - Puppet2D (paid Unity) has none of these.
  - *Loss:* Puppet2D's auto-rig biped and runtime IK; the Unity ecosystem.
  - *Tie:* skeletal rigging with mesh deform - across a different engine.

- **AnyPortrait (Unity plugin)**
  - *Win:* engine-native scene + open contract (AnyPortrait needs its runtime component at play time); free and open.
  - *Loss:* AnyPortrait's richer single-tool authoring - bone physics, blend modes, mature IK.
  - *Tie:* PSD import, mesh + weights, bones, automesh, slots - a feature-comparable core, across a different engine.

## Paradigms

Cross-tool QoL paradigms the community celebrates, and where Proscenio sits on each axis.

### Adopted

- **Source-art preservation.** PSD layers survive into Blender via the manifest; Blender data survives into Godot via the wrapper-scene pattern. Reimport never destroys user-authored wrappers. (Live2D, Spine, COA all sell this.)

- **Engine-native output.** Generated `.scn` uses only Godot core nodes. Plugin uninstall is a hard test, not a hope. (Differentiator vs Spine, DragonBones, CT2 Godot importer.)

- **Direct manipulation in the DCC.** Authoring inherits Blender's existing weight paint, dopesheet, NLA, drivers. Proscenio adds shortcuts (Quick Armature, Drive from Bone), not proprietary modes. (CT2 markets this as "no proprietary modes.")

- **Versioned contract as single source of truth.** Schema bumps are explicit, validated in 5 gates, and force migration. (Inherited from data-engineering practice; rare among DCC pipelines.)

- **Strong typing end-to-end.** Python `mypy --strict`, GDScript `untyped_declaration=2`, TypeScript `strict`. (Paradigm absent from prior art.)

- **No dependency friction.** Each plugin runs on what already ships - a UXP panel, a Blender addon with bundled pydantic wheels, a GDScript importer - with no `cv2` / numpy install and no PyPI reachability needed. (COA Tools 2's OpenCV requirement is the cautionary tale.)

### Partially adopted

- **Non-destructive iteration.** Wrapper survives; weights and keys do not survive a re-rig today. (RubberHose and Spine skins set the bar higher.)

- **Sketch-speed authoring.** Automesh, Quick Armature, and Create Slot reduce friction; export still costs three clicks (Validate → Export → copy). (COA's bone-draw is the reference target.)

- **Atlas efficiency.** Atlas packer ships, no rotation packing yet, no multi-atlas. (Spine and DragonBones lead here.)

- **Onboarding investment.** In-panel `?` popups and topic help land. Tutorials, reference characters, and showcase fixtures are still light. (Live2D's investment in samples and lessons is the high-water mark.)

### Not adopted

Paradigms deliberately outside Proscenio's lane (the roadmap rationale for these lives in [Deferred](04-deferred.md)):

- **Runtime-parity preview** - the Blender preview is not the Godot runtime; closing the gap likely needs a live link.

- **Auto-rig / parameter-driven templates** - rig topology is left to the user.

- **Parameter-driven deformer rigs (Live2D paradigm)** - a different art form, not a roadmap gap.

- **Mid-animation re-rig (RubberHose paradigm)** - the format bakes the rig into tracks today.
