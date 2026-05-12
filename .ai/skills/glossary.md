---
name: glossary
description: Domain terms used across components
---

# Glossary

| Term | Meaning |
| --- | --- |
| **Bone** | Transform node in a skeleton hierarchy. Drives child sprites and meshes. |
| **Bone2D** | Godot node type. Always a child (direct or indirect) of `Skeleton2D`. |
| **Skeleton2D** | Godot node holding `Bone2D` children. Computes pose for skinned `Polygon2D` children. |
| **Sprite** | Textured 2D shape. In Proscenio, may be a single quad or an arbitrary mesh. |
| **Atlas** | Single packed texture containing multiple sprites with UV regions. |
| **Slot** | Named container that can hold one of several sprites at a time. Used for swaps (open/closed eyes, weapon variants). |
| **Mesh deformation** | Vertex positions interpolated by bone weights - sprites bend, not just rotate around a pivot. |
| **Weights** | Per-vertex influence values from bones. Sum to 1.0 per vertex. |
| **Cutout animation** | Style where a character is built from rigid sprites jointed by bones (vs frame-by-frame). |
| **Track** | Single animated property over time inside an `Animation`. |
| **Keyframe** | Value at a specific time on a track. |
| **Reimport** | Re-running import on a changed source while preserving local edits in the target scene. |
| **PPU** | Pixels per unit - conversion ratio between Blender units and Godot pixels. |
| **`.proscenio`** | The intermediate JSON file that travels from Blender to Godot. |
