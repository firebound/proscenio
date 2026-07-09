# Slots

A slot presents one of N attachment meshes at a time - use it for hard swaps like sword / staff / empty, brow up / down, or an expression change. The parent panel lists every slot in the scene with its attachment count (each row selects it) and hosts **Create Slot**. With meshes selected, Create Slot wraps them into a new slot; in Pose Mode with an active bone, it anchors an empty slot at that bone (a tip box in the panel spells out both).

A slot is kind-agnostic: one slot can hold both mesh attachments (weight-painted) and sprite attachments (texture-sliced) - each row shows its kind. In Godot each slot becomes a `Node2D` under the bone with its attachments as sibling children; the default attachment starts visible (or nothing shows, when the default names none), and a `slot_attachment` animation track flips visibility per key. For a continuous, driven change instead of an either/or swap, use [Drive from Bone](02-element.md#drive-from-bone).

## Active Slot

Shown when a slot Empty is the active object (the parent Slots panel stays visible regardless, so its list and Create Slot never vanish). It shows how the slot follows its bone, lists the attachments, and adds new ones.

Each attachment row carries a SOLO star (filled on the one shown at scene load - click another to change the default), the attachment name and a mesh/sprite kind icon, and a `Show Only` button that authors the swap (below). Two buttons add attachments: `Attach Mesh` picks a mesh by name (the path that works when only the slot is selected), and `Add Selected` promotes the already-selected mesh. Validation issues for the slot render at the foot of the panel.

### Authoring a swap: show-only visibility keyframes

A swap is authored as direct visibility keyframes on the attachment meshes - there is no index to track. `Show Only` on an attachment row keys that attachment visible and every sibling hidden at the current frame (`hide_render` and `hide_viewport` in lockstep, hard-cut), so exactly one attachment shows from that frame on. The `(none) / Hide All` button below the list keys every attachment hidden - the no-attachment-visible state, for an idle pose that carries no weapon. Because the keys live on the meshes' own visibility, a swap previews natively in the Blender viewport as you scrub the timeline: there is no separate preview mode, and what the viewport shows is what the Godot runtime plays.

Swaps are per-animation. A swap follows the active animation by default - the one selected in the [Animation](07-animation.md) panel - so `idle` (no weapon), `attack_chicken`, and `attack_staff` each carry their own attachment timeline; you pick which animation a swap belongs to simply by making that animation active before you key. The `Target anim` dropdown in this panel overrides that when you want a swap to land on a specific animation instead of the active one - leave it empty to follow the active animation. The Animation panel lists each exported animation once by name, deduped across the rig's motion and the per-mesh visibility datablocks.

Export is unchanged in shape: a swap still emits a `slot_attachment` track, a `none` key names no attachment, and a slot can also rest blank when its default names none, so it starts with nothing shown. To carry over a slot authored under the older index model, run the one-shot `Convert Slot Index to Visibility` operator on the slot Empty; it re-keys each stored index as a show-only visibility keyframe on the attachments and clears the legacy track.

On Blender 4.4+ a slot's attachment visibility and the rig motion co-locate in one action per animation; on 4.2 they live in same-named separate actions that export merges by name. The minimum supported version stays 4.2 either way - only the datablock tidiness differs.

There are two ways to make a slot follow a bone, and both export the same and rebuild identically in Godot.

**Bind to Bone** is the safe route: it keeps the Empty object-parented (so the flat attachment quads stay in the picture plane) and adds a `Child Of` constraint whose inverse cancels the bone rest, so the slot rides only the bone's pose delta. It stays flat for any bone orientation.

**Hand bone-parenting** the Empty (Ctrl+P > Bone) is also supported and exports fine, but only for bones pointing into the screen. An in-plane bone (one lying in the picture plane) inherits its rest orientation and tilts the flat quads edge-on, collapsing them - the panel warns when a bone-parented slot's bone would do this and points you to Bind to Bone instead.

The panel shows how each slot follows - a Proscenio constraint, a bone parent, or a `slot_bone` that is set but inert (bound but not yet following in Blender; Bind to Bone wires the live follow) - and names its parent. **Unbind** stops the follow, removing whichever relation is live and leaving the Empty object-parented and inert. Binding refuses when a slot already follows, so to rebind after moving a slot you Unbind then Bind.
