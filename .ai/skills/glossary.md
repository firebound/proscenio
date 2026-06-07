---
name: glossary
description: Domain terms used across components
---

# Glossary

| Term | Meaning |
| --- | --- |
| **Element** | Any pipeline object - the umbrella over the two render kinds (mesh and sprite). Authored in Photoshop / Blender, emitted as `elements[]` in `.proscenio`. |
| **Mesh** | Element kind: a deformable cutout - arbitrary vertex count, UV, optional vertex weights. Becomes a Godot `Polygon2D`. Photoshop tag `[mesh]` / `[poly]`; Blender `element_type = mesh`. |
| **Sprite** | Element kind: a rigid textured quad with an optional spritesheet grid (`hframes` x `vframes`). Becomes a Godot `Sprite2D` - one frame is static, N frames animate. Photoshop tag `[sprite]` (single layer) / `[spritesheet]` (group of frames). |
| **Spritesheet** | A sprite element whose frame count is greater than one; the frames tile a grid in the atlas. An attribute of a sprite, not a separate kind. |
| **Bone** | Transform node in a skeleton hierarchy. Drives child elements. |
| **Bone2D** | Godot node type. Always a child (direct or indirect) of `Skeleton2D`. |
| **Skeleton2D** | Godot node holding `Bone2D` children. Computes pose for skinned `Polygon2D` children. |
| **Polygon2D** | Godot node a mesh element becomes - deformable vertices + UV, skinned by `Skeleton2D`. |
| **Sprite2D** | Godot node a sprite element becomes - a quad with an optional `hframes` x `vframes` region grid. |
| **Atlas** | Single packed texture containing multiple elements with UV regions. |
| **Slot** | Named container that can hold one of several elements at a time. Used for swaps (open/closed eyes, weapon variants). |
| **Mesh deformation** | Vertex positions interpolated by bone weights - meshes bend, not just rotate around a pivot. |
| **Weights** | Per-vertex influence values from bones. Sum to 1.0 per vertex. |
| **Cutout animation** | Style where a character is built from rigid elements jointed by bones (vs frame-by-frame). |
| **Track** | Single animated property over time inside an `Animation`. |
| **Keyframe** | Value at a specific time on a track. |
| **Reimport** | Re-running import on a changed source while preserving local edits in the target scene. |
| **PPU** | Pixels per unit - conversion ratio between Blender units and Godot pixels. |
| **`.proscenio`** | The intermediate JSON file that travels from Blender to Godot. |
