# Slots

A slot presents one of N attachment meshes at a time - use it for hard swaps like sword / staff / empty, brow up / down, or an expression change. The parent panel lists every slot in the scene with its attachment count (each row selects it) and hosts **Create Slot**. With meshes selected, Create Slot wraps them into a new slot; in Pose Mode with an active bone, it anchors an empty slot at that bone (a tip box in the panel spells out both).

A slot is kind-agnostic: one slot can hold both mesh attachments (weight-painted) and sprite attachments (texture-sliced) - each row shows its kind. In Godot each slot becomes a `Node2D` under the bone with its attachments as sibling children; the default starts visible, and a `slot_attachment` animation track flips visibility per key. For a continuous, driven change instead of an either/or swap, use [Drive from Bone](02-element.md#drive-from-bone).

## Active Slot

Shown when a slot Empty is the active object (the parent Slots panel stays visible regardless, so its list and Create Slot never vanish). It shows how the slot follows its bone, lists the attachments, and adds new ones.

Each attachment row carries a SOLO star (filled on the one shown at scene load - click another to change the default), the attachment name and a mesh/sprite kind icon, and a keyframe button that keys this attachment's visibility on the slot's `slot_attachment` track at the playhead. Two buttons add attachments: `Attach Mesh` picks a mesh by name (the path that works when only the slot is selected), and `Add Selected` promotes the already-selected mesh. Validation issues for the slot render at the foot of the panel.

There are two ways to make a slot follow a bone, and both export the same and rebuild identically in Godot.

**Bind to Bone** is the safe route: it keeps the Empty object-parented (so the flat attachment quads stay in the picture plane) and adds a `Child Of` constraint whose inverse cancels the bone rest, so the slot rides only the bone's pose delta. It stays flat for any bone orientation.

**Hand bone-parenting** the Empty (Ctrl+P > Bone) is also supported and exports fine, but only for bones pointing into the screen. An in-plane bone (one lying in the picture plane) inherits its rest orientation and tilts the flat quads edge-on, collapsing them - the panel warns when a bone-parented slot's bone would do this and points you to Bind to Bone instead.

The panel shows how each slot follows - a Proscenio constraint, a bone parent, or a `slot_bone` that is set but inert (bound but not yet following in Blender; Bind to Bone wires the live follow) - and names its parent. **Unbind** stops the follow, removing whichever relation is live and leaving the Empty object-parented and inert. Binding refuses when a slot already follows, so to rebind after moving a slot you Unbind then Bind.
