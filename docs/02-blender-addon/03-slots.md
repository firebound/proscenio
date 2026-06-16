# Slots

A slot presents one of N attachment meshes at a time - use it for hard swaps like sword / staff / empty, brow up / down, or an expression change. The parent panel lists every slot in the scene (each row selects it) and hosts **Create Slot**.

In Godot each slot becomes a `Node2D` under the bone with its attachments as sibling children; the default starts visible, and a `slot_attachment` animation track flips visibility per key. For a continuous, driven change instead of an either/or swap, use [Drive from Bone](02-element.md#drive-from-bone).

## Active Slot

Shown when a slot Empty is the active object. Lists the slot's child attachments, lets you mark which one is visible at scene load (the SOLO star), and adds the selected mesh as a new attachment.

**Bind to Bone** makes the slot follow a bone inside Blender the way the Godot importer already makes it follow at runtime: it keeps the Empty object-parented (so the flat attachment quads stay in the picture plane) and adds a `Child Of` constraint whose inverse cancels the bone rest, so the slot rides only the bone's pose delta. The bone line and the unparented warning reflect the bound bone once set. **Unbind** removes the follow. Because the inverse is baked when you bind, rebind after moving the slot.
