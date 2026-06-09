# Skeleton

The project-wide armature picker and presence checks. The picker is the single source of truth the bind and automesh steps target; the body splits into subpanels.

## Armature

A read-only list of every bone the writer would export, indented by depth with connected / relative flags. Click a bone to select it in the viewport. Inspection only - it never changes the `.proscenio`.

## Pose Mode

Pose-only authoring shortcuts, all **blender-only**: *Bake Current Pose* keys every bone at the playhead (those keys do export), *Toggle IK* adds or removes a test IK constraint, and *Save Pose to Library* stores the pose as a Blender asset.

## Quick Armature

A modal viewport tool that draws bones one press-drag at a time onto the Y=0 picture plane, without entering Edit Mode. The options box sets the front-ortho lock, chain default, name prefix, and grid snap. See the [walkthrough](../00-guides/00-basic/02-blender.md#build-the-skeleton) for the full chord cheatsheet.
