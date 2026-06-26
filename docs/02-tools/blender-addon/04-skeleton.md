# Skeleton

The project-wide armature picker and presence checks. The picker is the single source of truth the bind and automesh steps target; the body splits into subpanels. The header reads `Skeleton: <name>` while there is room and drops to `Skeleton` on a narrow panel. The panel shows only in Object, Pose, or Edit-armature mode.

The picker is a read-only field (Blender forbids writing scene data during a draw, so the addon fills it from load handlers). With no armature in the scene it points you at Quick Armature below; with armatures present but none picked, it warns that skeleton ops will create a new `Proscenio.QuickRig` and offers a button per existing armature to pick one instead.

## Active Armature

A list of every bone the writer would export. The `Display As` dropdown at the top sets the whole rig's viewport draw style (Octahedral / Stick / B-Bone / Envelope / Wire) - the native armature display type, surfaced here so it is one click away while authoring. The bone list indents by hierarchy depth and reads as the parenting tree by default; the native A-Z toggle flattens it to a plain alphabetical order and drops the indent (mirroring the Outliner). Each row carries connectivity icons on the right: a chain (`connected`, the head is locked to the parent's tail) or a broken chain (`disconnected`, a child whose head moves freely), each a hover tooltip rather than text. Connect / disconnect itself stays in Blender's native Edit mode, since it snaps the head and is a geometry edit. The child-of icon is a live toggle for Relative Parenting (a pose-inheritance flag, no geometry change). The star pins a bone; the `Favorites` toggle in the count row hides every non-pinned bone. Per-bone favorites live on `bone.proscenio.is_favorite`, persisted in the .blend.

Click a bone to select it in the viewport; Shift / Ctrl extend or toggle the selection (the per-row marker shows in Pose and Edit mode). Below the list, `Active to Euler` and `All to Euler` convert bone rotation mode to XYZ Euler. This is the one-click fix for the export validator's warning that a bone driving a sprite is not in the XYZ Euler mode the driver reads.

## Rig UI

Per-collection select buttons and visibility toggles built from the picked armature's native bone collections, all **blender-only** (it selects and shows bones, it never exports). The layout honors the 4.1+ collection nesting: a top-level collection with children renders as a labelled row of per-child select buttons (the Rigify-style "Arm.L: IK | FK | Tweak" grouping), a childless collection renders as a single-button row. Each row's button selects that collection's bones in the viewport, the eye toggles the collection's visibility (a hidden parent hides its children, the native inheritance), and the swatch opens a color dialog that applies a bone color to every bone in the collection at once - Blender has no per-collection color, so this batches over the bones. The color operator also turns on the armature's Bone Colors viewport display, so a rig that had it off still shows the result (pick the `Default` palette to clear). Assign bones to collections in Blender's native Bone Collections panel; this subpanel only consumes what is there, so with no collections it stays hidden.

## Bone Display

Assign a generated 2D outline as a bone's custom shape, **blender-only**. The grid offers a flat primitive set (circle, square, diamond, line, triangle, arrow); the meshes are generated on demand as `WGT-proscenio-<shape>` data-blocks and kept out of the scene. Clicking a shape assigns it to the active bone's `custom_shape` through the native mechanism (the same Rigify uses). Custom shapes show only in Pose mode. `Clear Shape` removes it (natively, you clear a custom shape by emptying the Custom Object field in Bone Properties). The operator's redo panel switches the scope to the selected bones or a whole bone collection and sets the scale and offset. Proscenio is a 2D pipeline, so the outlines lie in the bone's local X-Y plane, which faces the front-ortho camera for bones drawn into the picture plane; 3D widgets are out of scope.

## Pose Mode

Pose-only authoring shortcuts, all **blender-only** (enter Pose mode to reach them): `Bake Current Pose` keys every bone at the playhead (those keys do export), `Toggle IK` adds or removes a test IK constraint, `Bake IK to Keyframes` writes the IK-solved pose onto the chain bones as keyframes (the fix for the validator's animated-IK-without-keyframes error), and `Save Pose to Library` stores the pose as a Blender asset (covered below).

### Save Pose to Library

`Save Pose to Library` is a one-click shim over Blender's native `poselib.create_pose_asset`. Set the pose, click it, and the pose lands in the Asset Browser named `<action>.<frame>` (or `<armature>.<frame>` when no action is active). Pose assets are **blender-only** - they never reach the `.proscenio`; use them to reuse a pose across animations, characters, or projects. Assets land in the active asset library, set under Preferences > File Paths > Asset Libraries, and you re-apply them from Window > Asset Browser.

## Quick Armature

A modal viewport tool that draws bones one press-drag at a time onto the Y=0 picture plane, without entering Edit Mode. It is reachable even with no armature in the scene. The options box sets the front-ortho lock, chain default, name prefix, and grid snap increment. See the [walkthrough](../../00-guides/01-basic/02-blender.md#build-the-skeleton) for the full chord cheatsheet.
