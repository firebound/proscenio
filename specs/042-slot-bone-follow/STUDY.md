# Spec 042: Slot bone-follow authoring parity

Make a Proscenio slot visibly follow its bone inside Blender, the way the Godot importer already makes it follow at runtime. Today a slot bound to a bone exports correctly and follows the bone in Godot, but in Blender the slot Empty sits inert: nothing inside it tracks the bone, so the authoring view diverges from the shipped scene. The trigger was the mixed-feature fixture: making the face follow the `head` bone, or the slot_swap weapon follow the arm, required hand-adding a `Child Of` constraint that no operator authors and the panel does not recognize.

## Scope

- A `Bind Slot to Bone` operator that wires the Blender-side follow (a `Child Of` constraint with the inverse baked) and writes the `slot_bone` field the writer already reads.
- An `Unbind` path that reverses it.
- The `create_slot` bone path migrated off real bone-parenting onto the same convention, so new bone-anchored slots are born following their bone without tilting their flat quads out of the picture plane.
- The bone resolver (`slot_parent_bone`) taught to recognize the `slot_bone` field, so the Active Slot panel and the slot validators stop reporting a correctly-bound slot as unparented.
- The two slot fixtures (`mixed_feature`, `slot_swap`) authored with the constraint so they open in Blender already following their bone.

Surface: [create.py](../../apps/blender/operators/slot/create.py), the slot operators package [operators/slot/](../../apps/blender/operators/slot/), [panels/slots.py](../../apps/blender/panels/slots.py), [active_slot.py](../../apps/blender/core/validation/active_slot.py), the writer's [slots.py](../../apps/blender/exporters/godot/writer/slots.py), the Godot [slot_builder.gd](../../apps/godot/addons/proscenio/builders/slot_builder.gd), and the fixtures [mixed_feature/build_blend.py](../../packages/fixtures/mixed_feature/build_blend.py) + [slot_swap/build_blend.py](../../packages/fixtures/slot_swap/build_blend.py).

## Study

### Surface notes

**1. The data path that carries bone-follow already exists; nothing authors it in Blender.** The writer prefers an explicit `slot_bone` field and only falls back to `parent_bone` for the old bone-parented shape ([slots.py:28-33](../../apps/blender/exporters/godot/writer/slots.py#L28-L33)). The `slot_bone` PropertyGroup field exists (`object_props.py`) and the mixed-feature fixture sets it. But there is no UI affordance or operator that sets the field, and crucially no Blender-side transform that makes the slot move with the bone. The author has to know the convention and hand-edit a Custom Property, then separately hand-add a constraint. The intent is supported end to end in data but unsupported in authoring.

**2. `create_slot` bone-parents the Empty, which tilts the flat attachment quads out of the picture plane.** When a pose bone is active, [create.py:79-82](../../apps/blender/operators/slot/create.py#L79-L82) sets `parent_type = "BONE"` and `parent_bone`. A real bone parent anchors the child at the bone tail and inherits the bone's full rest orientation. For an in-plane `+Z` bone, that rotates the slot (and its child attachment quads) about the depth axis, collapsing the flat quads edge-on - the same failure the slot_cycle convention avoids by object-parenting. So the one operator that anchors a slot to a bone produces the visually wrong result, and its export rides the `parent_bone` fallback rather than the preferred `slot_bone` field.

**3. The panel and validators only recognize a real bone parent, so a correctly-bound slot reads as unparented.** `slot_parent_bone` returns "" unless `parent_type == "BONE"` ([active_slot.py:63-73](../../apps/blender/core/validation/active_slot.py#L63-L73)). The Active Slot panel uses it for the `bone:` line and the "no parent bone - attachments will not follow any bone" warning ([panels/slots.py](../../apps/blender/panels/slots.py)). A slot on the new convention (object-parent + `slot_bone` field, which exports and follows in Godot) therefore shows `bone: (unparented)` and trips a false error. The resolver has one definition shared by the panel and the validators, so a single fix corrects both - but it must read the same `slot_bone`-then-`parent_bone` order the writer uses, or the panel and the export will disagree about which bone the slot follows.

**4. Godot already reconstructs the follow with the inverse the constraint needs.** The importer parents the slot Node2D under the `Bone2D` and cancels the bone rest: `node.transform = follow_bone.get_skeleton_rest().affine_inverse()` ([slot_builder.gd:64-69](../../apps/godot/addons/proscenio/builders/slot_builder.gd#L64-L69)). The slot then rides only the bone's pose delta, with attachments baked in absolute screen space. The Blender twin of that is a `Child Of` constraint targeting the bone with `inverse_matrix = (armature.matrix_world @ pose_bone.matrix).inverted()` - the headless equivalent of the `Set Inverse` button, identical to the Godot cancel when bound at the rest pose. So the operator is not inventing behavior; it is mirroring in Blender what the importer builds in Godot, which is exactly the parity this spec is about.

### Assessment

Scores 1-5. Flow value: size x likelihood of the breakage the work removes. Test burden: cost to build plus recurring cost. Bug surface: complexity the change itself adds. Underuse risk: 5 = the fix protects nothing real.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| bind-slot-to-bone operator | 4 | 2 | 2 | 1 | now | The core gap: no way to author bone-follow so the Blender view matches Godot. The constraint + field write is well-scoped and mirrors a behavior Godot already ships. |
| migrate create_slot bone path | 4 | 2 | 2 | 1 | now | The existing bone path produces the visually wrong result (tilted quads) and rides the fallback field; moving it to the new convention fixes both at the source so new slots are born correct. |
| resolver reads slot_bone | 5 | 1 | 1 | 1 | now | A correctly-bound slot currently reads as unparented and trips a false error; the panel and export disagree until the shared resolver matches the writer's field order. Near-free. |
| fixtures author the constraint | 3 | 1 | 1 | 1 | now | mixed_feature + slot_swap should open in Blender already following their bone, so the examples demonstrate the parity rather than needing the hand-add this spec removes. |

### Verdict summary

Counts: **4 now, 0 gate, 0 drop**. The work is a single coherent slice: author the follow (operator + create_slot), recognize it (resolver), and demonstrate it (fixtures). No part is gated; the convention choice the bone-orientation gate in spec 039 worried about does not recur here, because the slot follow is object-parent plus a constraint that cancels rest, so the attachment quads never inherit the bone orientation that would tilt them.

### Decisions (locked)

- **Preferred follow convention: object-parent + `Child Of` constraint + `slot_bone` field.** Keeps the attachment quads in the picture plane and mirrors the Godot cancel-rest exactly. Chosen over keep-transform bone-parenting (which is math-equivalent at the rest pose) because the bind lives in a separate, removable constraint layer instead of a baked parent-inverse: unbinding returns the Empty to its clean authored transform rather than stranding it with the bone's rest baked into local. Preferred and reinforced - but not the only supported shape (see below).
- **Both authoring shapes stay supported; the constraint shape is the facilitated default.** The writer, the resolver, the validators, and the panel each recognize *either* a `slot_bone`-bound slot (object-parent + constraint) *or* a real bone-parented Empty (`parent_type == "BONE"` + `parent_bone`); both export to the same bone name and Godot rebuilds them identically. Real bone-parenting is a permanently supported hand-authored shape, not a deprecation - the operator and `create_slot` only *default to* the constraint shape, they never forbid or strip the other.
- **Set-inverse covers location, rotation, and scale (full).** Godot cancels the whole rest via `get_skeleton_rest().affine_inverse()`, so the Blender inverse matches the full rest, not a location-only subset.
- **`create_slot` defaults to the constraint convention.** Its pose-bone path stops *auto* bone-parenting and instead object-parents plus binds via the new operator's shared helper, so new bone-anchored slots are born flat and already following. A user who deliberately bone-parents an Empty by hand still gets a recognized, exportable slot (dual-support above).
- **The shared resolver reads `slot_bone` first, then `parent_bone`.** Same order as the writer, so the panel, the validators, and the export never disagree about the followed bone.
- **Unbind is reversible.** Removes the `Child Of` constraint and clears `slot_bone`, leaving the Empty object-parented and inert (the pre-bind state).

### Open question for the implementation pass

- Re-binding after the slot has moved: the inverse is baked at bind time, so moving the slot afterward needs a re-bind to stay put (the same caveat as Blender's `Set Inverse`). The operator should make re-binding cheap (run it again on an already-bound slot to recompute the inverse) rather than refuse. Confirmed as the intended behavior; the TODO carries it as an explicit acceptance check.
