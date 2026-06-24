# Skeleton

The project-wide armature picker and presence checks. The picker is the single source of truth the bind and automesh steps target; the body splits into subpanels. The header reads `Skeleton: <name>` while there is room and drops to `Skeleton` on a narrow panel. The panel shows only in Object, Pose, or Edit-armature mode.

The picker is a read-only field (Blender forbids writing scene data during a draw, so the addon fills it from load handlers). With no armature in the scene it points you at Quick Armature below; with armatures present but none picked, it warns that skeleton ops will create a new `Proscenio.QuickRig` and offers a button per existing armature to pick one instead.

## Active Armature

A read-only list of every bone the writer would export, indented by depth, with `connected` / `disconnected` / `relative` flags. Click a bone to select it in the viewport; Shift / Ctrl extend or toggle the selection (the per-row marker shows in Pose and Edit mode). Inspection only - it never changes the `.proscenio`.

Below the list, `Active to Euler` and `All to Euler` convert bone rotation mode to XYZ Euler. This is the one-click fix for the export validator's warning that a bone driving a sprite is not in the XYZ Euler mode the driver reads.

## Pose Mode

Pose-only authoring shortcuts, all **blender-only** (enter Pose mode to reach them): `Bake Current Pose` keys every bone at the playhead (those keys do export), `Toggle IK` adds or removes a test IK constraint, `Bake IK to Keyframes` writes the IK-solved pose onto the chain bones as keyframes (the fix for the validator's animated-IK-without-keyframes error), and `Save Pose to Library` stores the pose as a Blender asset (covered below).

### Save Pose to Library

`Save Pose to Library` is a one-click shim over Blender's native `poselib.create_pose_asset`. Set the pose, click it, and the pose lands in the Asset Browser named `<action>.<frame>` (or `<armature>.<frame>` when no action is active). Pose assets are **blender-only** - they never reach the `.proscenio`; use them to reuse a pose across animations, characters, or projects. Assets land in the active asset library, set under Preferences > File Paths > Asset Libraries, and you re-apply them from Window > Asset Browser.

## Quick Armature

A modal viewport tool that draws bones one press-drag at a time onto the Y=0 picture plane, without entering Edit Mode. It is reachable even with no armature in the scene. The options box sets the front-ortho lock, chain default, name prefix, and grid snap increment. See the [walkthrough](../../00-guides/01-basic/02-blender.md#build-the-skeleton) for the full chord cheatsheet.
