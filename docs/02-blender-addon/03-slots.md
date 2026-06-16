# Slots

A slot presents one of N attachment meshes at a time - use it for hard swaps like sword / staff / empty, brow up / down, or an expression change. The parent panel lists every slot in the scene (each row selects it) and hosts **Create Slot**.

In Godot each slot becomes a `Node2D` under the bone with its attachments as sibling children; the default starts visible, and a `slot_attachment` animation track flips visibility per key. For a continuous, driven change instead of an either/or swap, use [Drive from Bone](02-element.md#drive-from-bone).

## Active Slot

Shown when a slot Empty is the active object. Lists the slot's child attachments, lets you mark which one is visible at scene load (the SOLO star), and adds the selected mesh as a new attachment.

There are two ways to make a slot follow a bone, and both export the same and rebuild identically in Godot.

**Bind to Bone** is the safe route: it keeps the Empty object-parented (so the flat attachment quads stay in the picture plane) and adds a `Child Of` constraint whose inverse cancels the bone rest, so the slot rides only the bone's pose delta. It stays flat for any bone orientation.

**Hand bone-parenting** the Empty (Ctrl+P > Bone) is also supported and exports fine, but only for bones pointing into the screen. An in-plane bone (one lying in the picture plane) inherits its rest orientation and tilts the flat quads edge-on, collapsing them - the panel warns when a bone-parented slot's bone would do this and points you to Bind to Bone instead.

The panel shows how each slot follows (a Proscenio constraint or a bone parent) and names its parent. **Unbind** stops the follow, removing whichever relation is live and leaving the Empty object-parented and inert. Binding refuses when a slot already follows, so to rebind after moving a slot you Unbind then Bind.
