# SPEC 012 - Quick Armature UX overhaul

Status: **decisions locked**, ready for TODO authoring. D1-D9 closed (see Design decisions section below). Implementation split into Wave 1 (preview + lifecycle hygiene + Front-Ortho snap) and Wave 2 (modifiers + naming + in-modal undo).

## Problem

`PROSCENIO_OT_quick_armature` ([apps/blender/operators/quick_armature.py](../../apps/blender/operators/quick_armature.py)) is the canonical "click-drag a bone" entry point of the Proscenio addon. Today it is the most user-hostile operator the addon ships. Manual testing session 1.14 (10-mai-2026, see [tests/MANUAL_TESTING.md:167-177](../../tests/MANUAL_TESTING.md#L167-L177)) explicitly skipped the remaining checklist after the user concluded the operator was "inviabiliza o operator pro workflow primário" - several UX issues compound to the point that test runs cannot reach completion.

Concrete observed failures:

1. **Zero in-viewport feedback during the drag.** Head is captured on `LEFTMOUSE PRESS`, tail on `LEFTMOUSE RELEASE` ([quick_armature.py:73-83](../../apps/blender/operators/quick_armature.py#L73-L83)). Between press and release there is no preview line, no anchor circle, no tail follower - the user is dragging blind. Result is created only after release, every bone is trial-and-error.
2. **Modal state invisible.** The hint text written via `workspace.status_text_set` ([quick_armature.py:50-53](../../apps/blender/operators/quick_armature.py#L50-L53)) lives in the bottom status bar that 90% of users never look at while their attention is on the viewport. No header overlay, no viewport border highlight, no cursor hint. Users press once, see nothing happen, click again, accidentally start a new bone.
3. **Modal exit is a discoverability dead end.** `Esc` and `RIGHTMOUSE` work ([quick_armature.py:58-59](../../apps/blender/operators/quick_armature.py#L58-L59)) but the only place that documents this is the same status text. There is no in-viewport "Exit" affordance.
4. **Empty `Proscenio.QuickRig` armature leaks on cancel.** `_finish` ([quick_armature.py:145-150](../../apps/blender/operators/quick_armature.py#L145-L150)) clears the drag head and the status text but never removes the QuickRig armature when zero bones were created. Every accidental Esc adds a new orphan armature to the scene.
5. **Single connect/disconnect modifier (`Shift`).** Today `Shift` parents-but-not-connects the new bone to the previous bone. There is no "connect" modifier (Spine `Ctrl`, Spriter `Alt+Shift`), no "pick a different parent than last", no in-modal unparent. Branching skeletons (humanoid arms off a spine) require exiting the operator, manually re-parenting in Edit Mode, and re-entering. Painful loop.
6. **Bone naming is `qbone.NNN` with no rename affordance.** Naming convention from the wider community is `prefix_part_side` (`def_arm_l`, `ctrl_head`). Auto-named `qbone.000` carries zero semantic information; the user must rename in the Outliner after each bone or batch-rename later. SPEC 005 already validated that artists hate post-hoc renaming.
7. **Front-Ortho convention is enforced silently.** Plane projection hardcodes `plane_axis="Y"` ([quick_armature.py:74](../../apps/blender/operators/quick_armature.py#L74)) so bones land on the Y=0 picture plane regardless of view. Correct downstream (the writer assumes XZ), but in Top/Right/Persp the bone lands at Y=0 under a ray cast from the cursor and does not match where the user expected to click. Backlog ["Quick Armature: Front-Ortho UX guard"](../backlog.md#quick-armature-front-ortho-ux-guard) already enumerates the deferred fix - this SPEC absorbs it.
8. **No undo affordance inside the modal.** Each bone is committed via `bpy.ops.object.mode_set` round-trip ([quick_armature.py:125-138](../../apps/blender/operators/quick_armature.py#L125-L138)). User must exit, Ctrl-Z, re-enter to delete the last bone. Spine, Spriter, Adobe Animate all support per-bone undo while the tool is active.

The combination of these is more than the sum of the parts: the user cannot tell where the bone will land, cannot tell if the modal is still active, cannot back out of a single bad bone, and ends up with five `qbone.NNN` bones to rename and one orphan QuickRig armature to delete.

## Reference: 2D rigging tooling survey

Proscenio is the open-source-Godot equivalent of Spine, DragonBones, Spriter, Adobe Animate, and Live2D. The way these tools draw bones is the primary reference surface for SPEC 012 - they all converged on a similar interaction model and the shape of the consensus is informative.

### Spine (industry standard)

The **Create tool** (hotkey `N`) is the canonical bone authoring entry point and lives only in Setup mode. Source: [Spine Tools](http://esotericsoftware.com/spine-tools), [Spine Bones](http://en.esotericsoftware.com/spine-bones).

Interaction model:

- Click for a zero-length bone, click-drag to set initial length.
- Selected bone in the tree is the parent of the next created bone (no separate "select parent" gesture).
- `Shift` held during creation keeps the new bone unselected so the user can rapidly create sibling bones off the same parent (anti-pattern: chaining where you wanted siblings).
- `Alt` clicks/drags re-create the bone in place without affecting children or attachments (common need: fix a mis-placed root).
- `Ctrl`-drag attachments first, release `Ctrl`, then click-drag to create the bone. The bone is auto-named from the first attachment's slot, and the slots reparent under the new bone.
- Tree-side "New Bone" auto-positions the new bone at the parent's tip - saves a click for chain skeletons.

Quality-of-life:

- Mesh wireframe overlay can be enabled so the user can place bones over visible vertices.
- Mode separation (Setup vs Animate) prevents the most common authoring mistake: keyframing topology changes.

### DragonBones (open-source Spine-alike)

Bone tool drag highlights the underlying image with a blue rectangle and auto-attaches that image to the new bone on release. New bones drawn with a parent selected become children automatically. Hierarchy panel supports drag-and-drop re-parenting. Source: [DragonBones tutorial Part I](http://getting-started-dragonbones.blogspot.com/2017/01/dragonbones-tutorial-part-i.html), [Tutorial Ep04](https://www.youtube.com/watch?v=F6TVg6vUxWw).

The image-auto-attach gesture is the most "magic" of all the tools surveyed - one drag does both bone creation and slot binding. Spine requires explicit `Ctrl`-select first.

### Spriter Pro

`Alt + LMB` drag to create. Selected bone at drag time is the parent. `B + click` on a sprite parents the sprite to the selected bone. Source: [creating and assigning bones](https://brashmonkey.com/spriter_manual/creating%20and%20assigning%20bones.htm).

Notably terser than Spine: no separate tool to switch into. The `Alt` modifier is the tool. Trade-off: `Alt` is overloaded with other Spriter shortcuts.

### Adobe Animate

Bone tool click-drags from base to next joint. Each subsequent drag chains automatically off the last bone. Source: [Use the Bone tool animation in Animate](https://helpx.adobe.com/animate/using/bone-tool-animation.html).

Closest model to Proscenio's current design - chained drags in the same modal session. Adobe's win is the auto-chain default with a modifier to break the chain, the inverse of Proscenio's `Shift`-to-chain.

### Live2D Cubism

Different paradigm - deformer-based, no bones. Warp deformers + rotation deformers are nested manually via the deformer panel; rotation deformers can be skinned to ArtMeshes for fluid bending. Source: [Live2D deformer manual](https://docs.live2d.com/en/cubism-editor-manual/deformer/).

Out of scope for direct comparison (Proscenio is bone-based), but worth noting that Live2D users do not have a "draw bone" gesture either - they place deformers via dialog. Proscenio's drag-to-create is closer to Spine/DragonBones than to Live2D.

### Blender native (extrude)

`Add > Armature > Single Bone` then `E` (extrude) is the default Blender bone authoring loop. `E + X|Y|Z` constrains the extrusion axis. `Shift+E` mirror-extrudes when X-Axis Mirror is on (auto `_L`/`_R` suffix). Source: [Extrude - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/extrude.html).

The native model has zero "free draw" - every bone extends from a selected tip. For arbitrary 2D cutout placement (a brow bone that should not chain off the head bone) this forces a manual select-tip-then-extrude-then-deselect cycle. The Quick Armature operator exists exactly to bypass this.

The native model does win on precision: typing `E X 0.5` extrudes a half-unit bone along X with no mouse drift. Proscenio's mouse-driven model loses this. A future "type a length" overlay (numeric input mid-modal) would close the gap.

### COA Tools 2 (direct prior art, GPL Blender addon)

The spiritual model for Proscenio's panel layout (referenced by SPEC 005). README mentions "automatic mesh generation" and a sprite outliner but the public docs do not expose a dedicated bone-drawing operator beyond Blender's native extrude. Source: [Aodaruma/coa_tools2](https://github.com/Aodaruma/coa_tools2).

What COA Tools 2 *does* ship is fast vertex-contour drawing for mesh generation - a click-stroke modal that builds a tessellated polygon. Same interaction shape as Proscenio's quick armature, applied to mesh authoring instead of bone authoring. Worth lifting the modal feedback patterns (preview stroke, cursor hint, undo-during-modal).

### Auto-Rig Pro / Rigify (template-based, not free-draw)

Auto-Rig Pro's "Smart" feature places green markers on a character; on click the addon auto-positions an entire humanoid skeleton. Rigify uses a meta-rig template: pick a humanoid template, edit positions, click Generate. Source: [Auto-Rig Pro doc](https://www.lucky3d.fr/auto-rig-pro/doc/auto_rig.html), [Rigify - Blender Manual](https://docs.blender.org/manual/en/2.81/addons/rigging/rigify.html).

Different category. These solve "rig a humanoid in 30 seconds", not "draw an arbitrary bone where I want". Proscenio's 2D-cutout target audience needs the latter (every character is bespoke; the head-shoulder-arm template does not generalize).

The Auto-Rig Pro UX research (scoring 9 vs Rigify's 5 on user-experience surveys) is still informative: the win is *clear visual hints at every step* (green markers, in-viewport text), not the auto-rig algorithm itself.

### Bone Eyedropper / Bone Gizmos (Blender Studio addons)

Bone Eyedropper modal is a strong reference for in-viewport interaction polish: pre-fetches and caches bone data when the modal starts, compiles draw shaders once on invoke, drops every per-frame scene update that does not move the cursor. Source: [Bone Eyedropper](https://extensions.blender.org/add-ones/bone-eyedropper/).

Bone Gizmos hooks custom operators per bone (auto IK/FK switch, snap). Source: [Bone Gizmos - Blender Studio](https://studio.blender.org/tools/addons/bone_gizmos). Confirms that Blender 3.0+ keeps gizmos drawing during modal operators (relevant if SPEC 012 wants persistent in-viewport handles for the active QuickRig).

## Patterns observed across tools

Categorized so SPEC 012 can pick which patterns to lift. Each row maps to a Proscenio relevance verdict.

| Pattern | Spine | DragonBones | Spriter | Animate | Blender native | **Proscenio relevance** |
| --- | --- | --- | --- | --- | --- | --- |
| Live preview line during drag | yes | yes | yes | yes | yes (extrude follows mouse) | **first cut** |
| Anchor circle at drag origin | yes | yes | yes | yes | (implicit, tip stays selected) | **first cut** |
| In-viewport modal status overlay | yes (header bar) | yes (toolbar hint) | yes (cursor hint) | yes (status panel) | yes (header text + tool settings) | **first cut** |
| Modifier shortcut: chain to previous | (selected = parent) | yes | yes | yes (default) | (extrude is always chain) | **first cut** (already Shift) |
| Modifier shortcut: connect (no gap) | (auto-connect) | (auto-attach) | (auto) | (auto) | yes (extrude is connected) | **first cut** (Ctrl+Shift = connect) |
| Modifier shortcut: pick parent in viewport | yes (click to re-select) | yes | yes | yes | yes (Shift-click bone tip) | **5.1** |
| Modifier shortcut: re-create in place | yes (`Alt`) | (drag to move) | (drag) | (drag) | (re-extrude) | **5.1** |
| Numeric length input mid-modal | (Tab to type) | no | no | no | yes (`E 0.5 Enter`) | **future** |
| Auto-attach underlying image/sprite | (Ctrl gesture) | yes (auto on drag) | (B-key bind) | (auto on overlap) | no | **future** (couples to slot system / atlas) |
| Bone naming default | from attachment slot | from image | sequential | sequential | `Bone.NNN` | **first cut** (configurable prefix) |
| `_L`/`_R` mirror auto-suffix | manual rename | manual | manual | manual | yes (Shift+E with X-Mirror) | **5.1** |
| Per-bone undo inside modal | yes | yes | yes | yes | (Ctrl-Z exits modal) | **first cut** (`Ctrl+Z` in modal) |
| Confirm/Cancel floating buttons | (toolbar) | (toolbar) | (toolbar) | (timeline) | (header text) | **5.1** (in-viewport overlay) |
| Auto-cleanup empty rig on cancel | n/a | n/a | n/a | n/a | n/a (Ctrl-Z covers it) | **first cut** (Proscenio-specific bug) |
| Front-Ortho auto-snap on invoke | (always 2D) | (always 2D) | (always 2D) | (always 2D) | (3D, no snap) | **first cut** (project convention) |
| Mesh wireframe / sprite-bound overlay | yes | yes | yes | yes | (toggle in overlay panel) | **5.1** |
| Mode separation (Setup vs Animate) | yes (modal lock) | yes | yes | yes (pose layers) | yes (Object/Edit/Pose) | **first cut** (already implied by `bpy.types.Mode`) |
| Numeric naming after creation | (rename inline) | (rename) | (rename) | (rename) | (F2 rename) | **first cut** (rename hint or inline) |
| Bone hierarchy editor (re-parent without breaking anim) | yes | yes (drag-drop tree) | yes | (limited) | (manual) | **future** |

The first-cut column is the SPEC 012 minimum viable shape. The "5.1" column is the natural follow-up wave. The "future" column needs its own SPEC.

## Quality-of-life patterns the community praises

Consensus across forum threads, tutorials, and tool documentation. Each is a known win, not speculation.

- **Preview-during-drag is non-negotiable.** Every reviewed tool ships it. The single most-mentioned win in modal-operator reviews ([Bone Eyedropper](https://extensions.blender.org/add-ons/bone-eyedropper/), [boneWidget](https://github.com/waylow/boneWidget)) is "I can see what I'm about to do before I commit." Proscenio's lack of preview is the single biggest user-reported pain.
- **Status hints belong in the header overlay, not the bottom status bar.** Blender 2.8 explicitly moved modal status text from headers to the bottom status bar ([commit reference](https://www.mail-archive.com/bf-blender-cvs@blender.org/msg97049.html)) - and addon UX guides ([CGWire 2026 guide](https://blog.cg-wire.com/blender-addon-ui-scripting-guide/)) acknowledge this is a worse default for modal tools where the user's eyes are on the viewport. The pattern that wins is *both*: status bar for the canonical hint, in-viewport overlay for the loud version.
- **Modifier-key cheatsheet on screen.** Spine and DragonBones print "Shift = sibling, Alt = re-place, Ctrl = bind" in the toolbar while the tool is active. Adobe Animate prints the chord list in the Properties panel. Blender addon best practice: print the modifier list in the header overlay so the user does not have to memorize `bl_description`.
- **Per-bone undo inside the modal.** Every reviewed tool supports it. Blender's modal operators traditionally exit on `Ctrl-Z` because the operator itself does not push undo steps until exit. Custom modal operators that want per-bone undo wrap each commit in `bpy.ops.ed.undo_push(message="qbone.NNN added")`.
- **Naming defaults that carry semantics.** Industry consensus from rigging guides ([Whizzy Studios](https://www.whizzystudios.com/post/why-rig-hierarchy-matters-understanding-bone-parenting-and-constraints-in-blender), [MocapOnline skeleton hierarchy guide](https://mocaponline.com/blogs/mocap-news/skeleton-hierarchy-animation-guide), [Tripo3D clean skeleton hierarchy](https://www.tripo3d.ai/blog/explore/clean-skeleton-hierarchy-standards-for-marketplaces)): `prefix_part_side` (e.g. `def_arm_l`, `ctrl_head`). `qbone.NNN` carries zero semantics.
- **Confirm/Cancel discoverability.** Esc and right-click are conventions but not obvious to new users. Best-in-class addons add a header bar message *or* a floating in-viewport button. The header bar message is cheaper.
- **Cancel cleans up.** Spine, DragonBones, Spriter, Animate all roll back any half-created state on tool exit. Proscenio orphans the QuickRig armature - this is a Proscenio-specific anti-pattern, not a community pattern; fix it.
- **Front-Ortho convention enforcement.** Spine/DragonBones/Spriter/Animate are 2D-only - no view to confuse. Proscenio rides on Blender's 3D viewport, which means the user can be in Top, Right, or Persp when they invoke Quick Armature. Backlog ["Quick Armature: Front-Ortho UX guard"](../backlog.md#quick-armature-front-ortho-ux-guard) already prescribes the soft auto-switch with opt-out toggle - lift it directly.

## Complementary research: Blender native extrude + snap shortcuts

Added after Wave 12.1 manual testing revealed two gaps the first cut did not address: (a) the no-modifier default does not match Blender users' muscle memory for bone authoring, and (b) there is no way to constrain the drag direction or snap to a grid mid-modal. The Proscenio positioning explicitly is *"quick alternative + centralised UI, not reinvention"* - so the right move is to lift Blender's own conventions where they already exist.

### Blender native bone authoring shortcuts (Edit Mode armature)

Sources: [Axis Locking - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/scene_layout/object/editing/transform/control/axis_locking.html), [Extrude - Blender 5.1 Manual](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/extrude.html), [Shortcut Keys for Blender - Katsbits](https://www.katsbits.com/codex/shortcuts/).

| Action | Shortcut | What it does |
| --- | --- | --- |
| Extrude bone | `E` | New bone, head connected to selected tip's tail, tail follows cursor |
| Mirror extrude | `Shift+E` | Same + creates mirrored `_L`/`_R` pair when X-Mirror is on |
| Lock to axis during transform | `X` / `Y` / `Z` | Press once = global axis, press twice = local axis |
| Lock to plane during transform | `Shift+X` / `Shift+Y` / `Shift+Z` | Exclude axis (movement on the other two) |
| Snap to grid | `Ctrl` held during transform | Snap incremental steps (defaults to 1 unit / 10 deg / 0.1 scale) |
| Precision mode | `Shift` held during transform | Slow the transform so small adjustments are easier |
| Typed length | `0.5 Enter` | Type a numeric length after starting transform |
| Enable continuous snap | `Shift+Tab` | Toggle snap on/off without modifier hold |

### Spine bone authoring shortcuts

Sources: [Spine Tools](http://esotericsoftware.com/spine-tools), [Spine Cheat Sheet](http://en.esotericsoftware.com/spine-cheat-sheet).

| Action | Shortcut | What it does |
| --- | --- | --- |
| Create tool | `N` | Enter Create mode |
| Sibling bone | `Shift+drag` | New bone stays unselected so the next drag also siblings off the same parent |
| Re-create in place | `Alt+drag` | Move an existing bone without affecting children |
| Angle snap (during rotate) | `Shift` held while rotating | Snap to 15-degree increments |

Spine does not document a grid snap during bone creation. The 2D canvas + rounded pixel positions make grid snap less common.

### What this means for the Proscenio no-modifier default

Today: LMB drag = unparented bone. Result: every drag starts a new chain. To author a 4-bone arm the user has to drag once unparented, then three times with Shift+drag for chain. That is the *inverse* of Blender's E-key muscle memory (which always chains).

Blender's E semantic is: "the next bone continues the current chain". Spine's no-modifier semantic is similar (selected bone in tree = parent of next). Adobe Animate chains by default too. Only Spriter requires `Alt+drag` for *every* bone - and Spriter community considers that ergonomic, not a default.

Conclusion: invert. Default chain connected matches:

- Blender's E muscle memory (the audience already trained).
- Spine and Animate conventions (the audience cross-trained).
- The most common authoring case: building a chain (spine, arm, leg) is more frequent than starting an isolated bone.

### Snap controls - cost vs benefit

Three patterns dominate, each with cheap-or-free implementation:

- **Axis lock (X / Z keys during drag).** Mid-modal `event.type == "X"` or `"Z"` toggles a flag; next cursor-projection clamps the tail's other axis to the head's axis value. Cost: ~10 lines. Benefit: straight horizontal/vertical bones in one keystroke - matches Blender users' reflex.
- **Grid snap (Ctrl held).** When held, round the projected cursor point to the nearest scene grid increment (`bpy.context.scene.unit_settings.scale_length`-aware). Cost: ~5 lines. Benefit: pixel-accurate bones for cutout rigs aligned to a known grid.
- **Angle snap (Shift held).** Snap the bone direction to 15-degree increments from the head. Conflicts with the press-time `Shift` chord (chain modifier). Either remap (give `Shift` to angle snap, find a different chord for "start new chain") or skip the feature.

Proscenio's authoring target is 2D cutout, often aligned to whole-pixel sprites. Axis lock + grid snap are high value; angle snap is nice-to-have but trades against chord vocabulary clarity.

### Positioning vs Blender native

Quick Armature is **not** a replacement for Edit Mode armature work. It is a fast-path for:

1. **Starting a rig** - first 5-10 bones authored quickly, mode round-trip avoided.
2. **Reaching the picture plane** - Front Ortho lock + Y=0 projection without users having to remember the convention.
3. **Single discoverable entry point** - one button, one modal, no Object Mode / Edit Mode / Pose Mode dance.

It deliberately does **not** ship:

- Numeric length input (`Tab` to type) - Edit Mode E key wins here.
- Per-axis precise constraint chains (`E X X 0.5`) - too keystroke-heavy for the "quick" promise.
- Subdivision, mirror copy, parent re-routing - Edit Mode is the right surface.
- Mirror auto-suffix `_L`/`_R` - deferred to a successor SPEC, not core.

The line: Quick Armature owns the "first-stroke" experience; Edit Mode owns refinement.

## Position of Proscenio today

Mapping observed-pattern coverage to current implementation:

| Pattern | Status today | File / line |
| --- | --- | --- |
| Click-drag to create bone | yes | [quick_armature.py:64-92](../../apps/blender/operators/quick_armature.py#L64-L92) |
| `Shift` to chain (no connect) | yes | [quick_armature.py:74-91](../../apps/blender/operators/quick_armature.py#L74-L91) |
| Status bar hint | yes (bottom bar only) | [quick_armature.py:50-53](../../apps/blender/operators/quick_armature.py#L50-L53) |
| Esc / RMB exit | yes | [quick_armature.py:58-59](../../apps/blender/operators/quick_armature.py#L58-L59) |
| Y=0 plane projection | yes | [quick_armature.py:74,83](../../apps/blender/operators/quick_armature.py#L74) |
| Live preview during drag | **no** | gap |
| In-viewport status overlay | **no** | gap |
| Modifier cheatsheet on screen | **no** | gap |
| `Ctrl+Shift` connect-parent modifier | **no** | gap |
| Per-bone undo in modal | **no** | gap |
| Bone rename hint after commit | **no** (`qbone.NNN` only) | [quick_armature.py:129](../../apps/blender/operators/quick_armature.py#L129) |
| Auto-cleanup empty QuickRig on cancel | **no** | [quick_armature.py:145-150](../../apps/blender/operators/quick_armature.py#L145-L150) |
| Front-Ortho auto-snap on invoke (opt-out) | **no** | [backlog](../backlog.md#quick-armature-front-ortho-ux-guard) |
| Confirm/Cancel viewport affordance | **no** | gap |
| Mirror auto-suffix `_L`/`_R` | **no** | gap |
| Numeric length input | **no** | gap |
| Pick-parent-in-viewport | **no** | gap |
| Auto-attach underlying mesh / sprite | **no** | gap (couples to SPEC 004 / atlas) |

Proscenio today ships the bare drag-to-create primitive and a single chain modifier. Every single quality-of-life pattern from the wider community is missing. The gap is the size of an entire SPEC, which is what justifies SPEC 012.

## Constraints

- **Blender-only.** Operator runs in `bpy.types.Operator`; no GDExtension, no native binding. All work happens in Python at editor time.
- **Strong typing.** Per [`.ai/conventions.md`](../../.ai/conventions.md) static-typing section: every parameter typed, every return typed, `Any` only at the `bpy` boundary. Mypy strict.
- **No new format features.** SPEC 012 is purely authoring UX. The `.proscenio` shape does not change. No schema bump.
- **XZ picture-plane convention is law.** Bones live on Y=0; the writer + Godot importer assume it. SPEC 012 must keep the projection hard-locked, only adding *visual guidance* about it (Front-Ortho auto-snap, in-viewport hint).
- **Reload safety.** Operator must register/unregister cleanly with the addon's reload-scripts loop.
- **No dependency on SPEC 008 (UV animation) or SPEC 004 (slots).** Auto-attach-underlying-sprite is tempting but couples to slot system; defer to a follow-up SPEC.
- **Coexistence with native Blender bone authoring.** A user who exits Quick Armature and continues with native `E` extrude must not have the operator's state corrupt their session. Modal cleanup must be airtight.

## Design surface

The operator is split into three concerns that today live tangled in one class:

1. **Modal feedback** - what the user sees while the modal is active. Preview line, anchor circle, header overlay, modifier-list cheatsheet, viewport border highlight.
2. **Authoring shortcuts** - what the modifier keys do. `Shift` = chain (existing), `Ctrl+Shift` = chain-connected (new), `Alt` = unparent (new), `Ctrl+Z` = undo last bone (new), `Tab` = type length (deferred).
3. **Lifecycle hygiene** - invoke and exit are both broken. Invoke needs Front-Ortho auto-snap with opt-out. Exit needs to remove an empty QuickRig and clear all draw handlers.

### Layout and integration points

The operator stays anchored where it is today: invocable from the Skeleton subpanel button (added in SPEC 005.1.d.3) and from F3 search. SPEC 012 does not move the entry point.

What SPEC 012 adds:

- A `gpu.draw_handler_add` callback on `bpy.types.SpaceView3D` for the preview line + anchor circle, registered in `invoke` and removed in `_finish`.
- A `bpy.types.SpaceView3D.draw_handler_add(POST_PIXEL)` for the in-viewport modifier-list cheatsheet.
- An operator option (`bpy.props.BoolProperty`) `lock_to_front_ortho` defaulting to `True`. When `True` and the active region is not Front-Ortho, `invoke` calls `bpy.ops.view3d.view_axis(type="FRONT")` before `modal_handler_add`. F3 search exposes the toggle so power users can opt out.
- A `bpy.types.AddonPreferences` field for the bone-naming prefix (default `"qbone"`). Power users override to `"def"` or `"ctrl"` once and the rest of the session uses it.
- An undo stack inside the operator (`list[str]`, names of bones added this session). `Ctrl+Z` while modal removes the last bone, `Ctrl+Shift+Z` redoes. On `_finish`, the cumulative bones are wrapped in a single `bpy.ops.ed.undo_push` so that post-modal Ctrl-Z removes the entire session at once (matches user expectation: "I created 5 bones, one undo should remove all 5" or "one Ctrl-Z while modal removes the last bone").
- An empty-QuickRig sweep on `_finish` and on `cancel`: if `len(armature.data.bones) == 0`, unlink and remove the data block.

### Property model

A new `PROSCENIO_OT_quick_armature` operator option group:

```python
class PROSCENIO_OT_quick_armature(bpy.types.Operator):
    bl_idname = "proscenio.quick_armature"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO", "BLOCKING"}

    lock_to_front_ortho: BoolProperty(
        name="Lock to Front Orthographic",
        description="Switch to Front Ortho on invoke; uncheck to author in any view",
        default=True,
    )
```

A new `PROSCENIO_AddonPreferences` field for naming defaults:

```python
quick_armature_name_prefix: StringProperty(
    name="Quick Armature bone prefix",
    description="Prefix for auto-named bones (e.g. 'def' produces 'def.000', 'def.001')",
    default="qbone",
)
```

No new PropertyGroup on Object or Scene - the operator is stateless between invocations except via the QuickRig armature itself.

### Visual feedback strategy

Two parallel draw handlers, both registered in `invoke` and removed in `_finish`:

1. **`POST_VIEW` (3D space)** - draws the preview line in world space. Anchored at `_drag_head` (already captured), tail follows the cursor's projected Y=0 point on every `MOUSEMOVE`. Uses `gpu.shader.from_builtin('UNIFORM_COLOR')` and a `batch_for_shader` with two vertices. Anchor circle is a 12-segment fan at `_drag_head` with the same shader. Color: `(1.0, 0.6, 0.0, 0.9)` (Blender's standard "modal in progress" orange).
2. **`POST_PIXEL` (2D overlay)** - draws the modifier-list cheatsheet in the top-left of the viewport. Text: `"Quick Armature  |  drag = bone  |  Shift = chain  |  Ctrl+Shift = chain connected  |  Alt = no parent  |  Ctrl+Z = undo last  |  Esc = exit"`. Uses `blf` for text rendering, fixed 12-px size. Background: a semi-transparent rect drawn first via the same `UNIFORM_COLOR` shader.

`MOUSEMOVE` events flag the area for redraw via `context.area.tag_redraw()` so the preview line follows the cursor smoothly without polling.

### Modifier semantics

| Modifier | Behavior | Notes |
| --- | --- | --- |
| (none) | Unparented bone | Free-floating root (current default) |
| `Shift` | Parent to last bone, no connect | Current behavior; preserved |
| `Ctrl+Shift` | Parent to last bone, connected (head snaps to parent's tail) | New |
| `Alt` | Unparented bone, do not chain | New (overrides the implicit "if I just dragged, chain" expectation that some users have) |
| `Ctrl+Z` (in modal) | Remove last created bone | New |
| `Ctrl+Shift+Z` (in modal) | Re-create last removed bone | New |

`Alt` is somewhat redundant with the no-modifier default today (since today no-modifier already means unparented). Reserving `Alt` now lets us flip the default in a successor SPEC ("auto-chain like Adobe Animate") without breaking the chord vocabulary.

### Lifecycle hygiene

- `invoke`: snapshot `view_perspective` + `view_matrix` of active region. If `lock_to_front_ortho` is `True` and the snapshot is not Front-Ortho, call `bpy.ops.view3d.view_axis(type="FRONT")`. Save the original view in operator state so `cancel` can restore it (or skip restoration - depends on D3 below).
- `modal`: every event handled today, plus `Ctrl+Z`/`Ctrl+Shift+Z` and `MOUSEMOVE` (for redraw).
- `_finish`: unregister both draw handlers, clear modifier-cheatsheet bg, restore status bar (`workspace.status_text_set(None)` already), wrap session bones in single undo step, sweep empty QuickRig.
- `cancel` (new): explicit cancel path that walks back the entire session - removes every bone added during the modal, then removes the QuickRig if empty. Triggered by `Esc`-with-no-bones-created or by an explicit "Cancel" gesture (TBD in D5 below).

## Design decisions (locked)

| ID | Question | Locked answer | Wave |
| --- | --- | --- | --- |
| D1 | Preview rendering | **A** GPU `draw_handler_add` overlay | 1 |
| D2 | Naming prefix configuration | **E** AddonPref default + F3 redo override | 2 |
| D3 | Front-Ortho snap restore on exit | **A** restore original view | 1 |
| D4 | Empty QuickRig sweep scope | **B** sweep only if operator created it this session | 1 |
| D5 | Confirm/Cancel viewport affordance | **A** header bar text only | 1 |
| D6 | Cheatsheet visibility | **A** always visible while modal active | 1 |
| D7 | Per-bone undo scope | **B** session-local stack + single global push on `_finish` | 2 |
| D8 | Connect-parent modifier chord | **C** `Ctrl+Shift` connect, `Ctrl` reserved | 2 |
| D9 | Shipping shape | **B** Wave 1 (showstoppers) + Wave 2 (productivity polish) | - |
| D10 | No-modifier default behavior | **B** invert: LMB = chain connected, Shift = new root | 2 |
| D11 | Axis lock during drag | **C** X/Z keys + colored axis line overlay | 2 |
| D12 | Grid snap during drag | **B** Ctrl held = snap to 1.0 world-unit grid | 2 |
| D13 | Angle snap during drag | **C** defer to future SPEC | future |
| D14 | `Ctrl` chord re-route | **A** Ctrl = grid snap, re-reserve `Alt` for bone-tip-snap | 2 |
| D15 | Panel exposure for Quick Armature defaults | **C** Scene PG + Skeleton subpanel inline | 2 |

Each section below preserves the option set + rationale for posterity.

### D1 - Preview rendering: GPU module or Edit Mode live update?

Two ways to show the bone-in-progress between drag start and release:

- **D1.A - `gpu.draw_handler_add` overlay.** Add a draw handler that renders a line + circle in the viewport without touching scene data. Cleared on release. Lightweight, no scene state mutation.
- **D1.B - Live update of the Edit Mode bone.** Create the bone immediately on `LEFTMOUSE PRESS` (with head and tail at the same point), then update `edit_bones[name].tail` on every `MOUSEMOVE`. The bone is real and the user sees it via the existing armature draw.
- **D1.C - Both.** GPU overlay shows the preview line (instant feedback), plus Edit Mode bone created on PRESS for "what it will look like" parity.

**Locked: D1.A.** Edit Mode entry/exit is expensive (`bpy.ops.object.mode_set` is the slowest op the modal touches). Mutating the bone tail on every `MOUSEMOVE` is also a real edit-history event - undo/redo bookkeeping gets noisy. GPU overlay is what every reference tool (Spine, DragonBones, Spriter, Animate) does conceptually: a UI hint, not a real bone.

### D2 - Naming prefix: hard-coded, addon pref, or per-invoke?

Today bones are named `qbone.NNN`. Better default and where to configure:

- **D2.A - Hard-code `qbone`.** Status quo.
- **D2.B - Hard-code a better default (e.g. `bone`).** Drop the project-specific prefix; users rename anyway.
- **D2.C - Addon preference.** One value per Blender install.
- **D2.D - Operator option exposed in the F3 redo panel.** Power users can override per-invocation.
- **D2.E - C+D combined.** Addon pref is the default; F3 redo lets you override.

**Locked: D2.E.** Most users set the prefix once (matching their rig naming convention - `def`, `ctrl`, `mch`) and never touch it again. Addon pref carries the default. F3 redo override is essentially free once the operator option exists, and lets a power user temporarily switch to `ctrl` for a control-bones session without a Preferences round-trip.

### D3 - Front-Ortho auto-snap: restore view on exit?

When `lock_to_front_ortho` triggers a `view_axis(type="FRONT")` on invoke, what does cancel/finish do?

- **D3.A - Restore the original view on exit.** User was in Persp, ran Quick Armature, finished, and finds themselves back in Persp. Predictable.
- **D3.B - Stay in Front Ortho after exit.** User was in Persp; after the operator the view is Front Ortho.
- **D3.C - Operator option (`restore_view_on_exit`) defaulting to A.**

**Locked: D3.A.** The operator should not silently change a user's view. The auto-snap is in-modal scaffolding, not a permanent change. Power users who *want* to land in Front Ortho can either uncheck `lock_to_front_ortho` (so no snap happens) or call `view_axis` themselves afterwards. Operator option (D3.C) is YAGNI - no real workflow asks for "snap and stay".

### D4 - Empty QuickRig on cancel: silent sweep or confirm?

When the user invokes the operator, no bones are created (immediate Esc), the empty QuickRig was created in `_ensure_armature`. What happens?

- **D4.A - Silent sweep on `_finish`.** If `len(armature.data.bones) == 0`, unlink and remove. Quiet, no popup.
- **D4.B - Sweep only if QuickRig was created this session.** Track whether `_ensure_armature` instantiated it (vs found an existing one with bones from a prior session). New-and-empty: sweep. Pre-existing-and-emptied (user manually deleted bones during the modal): keep.
- **D4.C - Defer empty-QuickRig sweep entirely; rely on user cleanup.** Status quo.

**Locked: D4.B.** Silent sweep of *anything* the operator finds is over-eager (the user might have a Proscenio.QuickRig from yesterday that they wanted to keep). Sweep only what the operator created this session. Tracked via a single bool on the operator (`self._created_armature_this_session`).

### D5 - Confirm/Cancel viewport affordance

Esc + RMB are the conventional Blender exit gestures but not obvious to new users. What in-viewport affordance to add?

- **D5.A - Header bar message only.** "Quick Armature active - Esc/RMB to exit, Enter to confirm" rendered at the top of the viewport via the same `POST_PIXEL` handler as the cheatsheet.
- **D5.B - Floating buttons.** "Confirm" / "Cancel" buttons drawn in the top-right of the viewport, click-to-trigger via the modal hit-test.
- **D5.C - Both.** Header text plus buttons.
- **D5.D - Header text + a confirmation dialog on Esc when `>=1` bones were created.** "Discard 5 bones?" / "Keep". Prevents accidental discards.

**Locked: D5.A.** Floating buttons in viewport need hit-testing in modal which is non-trivial and visually noisy. Header text is cheap and discoverable. The confirmation dialog (D5.D) is a half-step worth considering if the operator gains an explicit "discard" path - but with Ctrl+Z available inside the modal, a user who regrets their bones can undo them one-by-one without exiting. Defer the confirm dialog.

### D6 - Modifier-list cheatsheet: always visible or toggleable?

The in-viewport overlay listing `Shift = chain | Ctrl+Shift = connected | ...` is a discoverability win. Question is screen real-estate.

- **D6.A - Always visible while modal active.** Simple.
- **D6.B - Toggleable via `H` (hide).** Power users dismiss after they memorize.
- **D6.C - Auto-fade after first successful bone (5 seconds).** Help when you need it, vanish when you don't.

**Locked: D6.A.** Hiding/fading risks the user losing the cheatsheet exactly when they hit a new modifier they hadn't tried. Power users can always uncheck a future "Show modifier hint" addon pref if it gets in the way - but that's a YAGNI until someone asks. First cut: always visible.

### D7 - Per-bone undo: scope inside the modal

`Ctrl+Z` inside the modal removes the last created bone. How does the modal interact with Blender's global undo stack?

- **D7.A - Each bone is a separate undo step on the global stack.** Post-modal Ctrl-Z removes bones one-by-one. Matches in-modal behavior.
- **D7.B - The entire session is one undo step on the global stack.** Post-modal Ctrl-Z removes the entire session. In-modal Ctrl-Z is a separate local stack that does not touch the global one.
- **D7.C - Hybrid: each bone is a separate `undo_push` while the modal runs, but `_finish` collapses them via a single combined push.** Blender API does not directly support stack collapse but a `bpy.ops.ed.undo_history()` walk could approximate it.

**Locked: D7.B.** Cleanest mental model. In-modal Ctrl-Z is a session-local "remove last bone I just made"; post-modal Ctrl-Z is "I changed my mind about the whole authoring session". Two different operations, two different scopes. The implementation: maintain `self._session_bone_names: list[str]` inside the operator; in-modal Ctrl-Z pops the list and removes the named bone via Edit Mode bypass; `_finish` wraps the *cumulative state change* in a single `bpy.ops.ed.undo_push(message="Quick Armature: N bones")`.

### D8 - Connect-parent modifier: `Ctrl+Shift` or alternative?

The new "chain connected" modifier needs a chord that does not collide with Blender defaults inside the 3D viewport during modal.

- **D8.A - `Ctrl+Shift`.** Conventional "extend modifier" chord. Symmetric with native extrude (E vs Shift+E for mirror).
- **D8.B - `Ctrl` alone.** Free in modal; `Shift` already means chain. `Ctrl` alone could mean "connect, no chain" (but then "connect" without a parent makes no sense).
- **D8.C - `Ctrl+Shift` for connect, `Ctrl` alone reserved for future "snap to parent tip" without changing parentage.** Keeps `Ctrl` in vocabulary for a successor.

**Locked: D8.C.** `Ctrl+Shift` covers the immediate need (chain + connect). Reserving `Ctrl` alone for a future use prevents painting ourselves into a corner. Dragonbones-style auto-snap-to-nearby-bone-tip is a clear successor - claim the chord now.

### D9 - Shipping in waves vs single SPEC

SPEC 012 is large. Single drop or multiple commits?

- **D9.A - Single PR with all of D1-D8.** Coherent feature.
- **D9.B - Wave 1 (preview line + cheatsheet + Front-Ortho snap + cleanup), Wave 2 (modifiers + naming prefix + undo).**
- **D9.C - Three waves.** Visual feedback first, then lifecycle hygiene, then modifier expansion.

**Locked: D9.B.** Wave 1 covers the items that make the operator usable at all (the items session 1.14 cited as showstoppers). Wave 2 covers the items that make the operator pleasant for serial use. Wave 1 alone is shippable - a user can author bones today, just inefficiently; Wave 1 closes the "inviabiliza" gap. Wave 2 is the productivity polish.

### D10 - No-modifier default: free root or chain connected? (Wave 12.1 follow-up)

Today (Wave 12.1 default): LMB drag = unparented bone. `Shift+drag` = chained (parent, not connected). User report after first authoring session: "default deveria ser extrusao (parented, connected) porque e o uso mais comum no Blender".

Survey (see complementary research above): Blender's `E` extrude chains connected. Spine's Create tool chains automatically. Adobe Animate chains automatically. Only Spriter requires an explicit `Alt` for every bone, and even Spriter chains the next bone off the previously created one.

- **D10.A - Keep current (no-modifier = unparented root).** Lower surprise for first-use bone (no implicit parent to debug). Cost: every chain authoring needs Shift held continuously.
- **D10.B - Invert (no-modifier = chain connected, Shift = new root).** Matches Blender / Spine / Animate conventions. First bone of any chain is naturally unparented (no previous bone exists); subsequent drags chain. To start a *new* chain mid-session, hold Shift.
- **D10.C - Configurable via AddonPreferences default + per-invoke F3 override.** Choose your audience.

**Locked: D10.B.** Audience reading. Blender users hit `E` reflexively to extrude bones. Spine users expect chain by default. The "I started a new chain by accident" mistake is recoverable via in-modal `Ctrl+Z` (Wave 12.2). The "I have to hold Shift for every bone of a chain" friction is constant. Inverting trades a rare mistake recovery for constant ergonomic wins.

D10.C is over-engineered; the audience consensus is strong enough to lock a default. If a user really wants free-root default, they can wrap the operator in a custom keymap with `lock_to_front_ortho=True` and a hypothetical `default_chain=False` option - but the consensus does not require shipping the option in Wave 12.2.

### D11 - Axis lock during drag (X / Z keys)

Blender users press `X` or `Z` mid-transform to lock the active drag to that axis. Adopting the same chord costs almost nothing and pays off for "straight bones" use cases (vertical spine, horizontal limbs).

- **D11.A - No axis lock.** Status quo. Power users can drop into Edit Mode and use native E if they need precision.
- **D11.B - X / Z keys during drag = lock to axis.** Press once = global axis (clamp the unlocked coord of `tail` to the same value as `head`). Press twice = local axis (would require armature orientation, deferred). `Y` key = no-op (always Y=0).
- **D11.C - X / Z lock + visual indicator.** Same as B plus a colored axis line drawn through the head during the lock (Blender convention - X is red, Z is blue).

**Locked: D11.C.** Free win. The visual indicator turns a hidden state into a visible affordance, which matches Wave 12.1's "no hidden state" principle. Implementation: extend the POST_VIEW draw handler to render an axis line when `self._axis_lock in {"X", "Z"}`.

### D12 - Grid snap during drag (Ctrl held)

Blender's modal transforms snap to grid when `Ctrl` is held. Snap increment defaults to 1.0 world unit, configurable via scene snap settings.

- **D12.A - No grid snap.** Status quo.
- **D12.B - Ctrl held during drag = snap projected cursor to scene grid.** Round each `_cursor_world` coord (X and Z) to the nearest increment.
- **D12.C - Same as B + respect scene snap settings (`scene.tool_settings.snap_elements`, `snap_target`, etc.).** Pro-grade integration with Blender's full snap stack.

**Locked: D12.B.** Minimal scope. Hardcoded 1.0-unit increment for first ship covers the 2D-cutout use case (PPU = 100, so 1 world unit = 100 px; many cutout rigs author at integer-pixel positions). D12.C is YAGNI - scene snap settings are over-configurable; a fixed grid is the right default and a `snap_increment: FloatProperty` can ship later if power users ask. Conflict note: `Ctrl` is reserved by D8 for the future "snap to nearby bone tip" gesture; rename that reservation to `Alt` (no other Alt usage today) - covered in D14 below.

### D13 - Angle snap during drag (Shift held)

Spine snaps bone rotation to 15-degree increments when Shift is held. Useful for symmetric humanoid rigs.

- **D13.A - No angle snap.** Status quo.
- **D13.B - Shift during drag (after PRESS) = snap angle to 15-deg increments.** Conflict: `Shift+LMB PRESS` in D10.B = new chain root. Live `Shift` held after PRESS would have to mean something different. Doable via state machine (track Shift state delta) but adds modal complexity.
- **D13.C - Defer to a future SPEC.** Not enough usage demand observed today.

**Locked: D13.C.** Wave 12.2 is already wide. The chord vocabulary needs to stay clear for the first ship; reusing `Shift` for two meanings within the same drag is a cognitive load multiplier. Revisit if a humanoid rig fixture surfaces the need.

### D14 - `Ctrl` chord reservation re-route (depends on D12)

D8 reserved `Ctrl` alone for a future "snap to nearby bone tip" gesture. D12.B claims `Ctrl` for grid snap. Resolve.

- **D14.A - `Ctrl` = grid snap. Re-reserve `Alt` for the future bone-tip-snap.** Aligns with Blender's `Ctrl`=snap convention everywhere else.
- **D14.B - Keep `Ctrl` reserved for bone-tip-snap. Use `Shift+Ctrl` for grid snap.** Preserves D8.C reservation, costs an extra finger.
- **D14.C - Drop bone-tip-snap reservation entirely; assume a future SPEC will find its own chord.** Don't pre-allocate.

**Locked: D14.A.** Blender convention is `Ctrl`=snap-to-grid universally; users will press it reflexively. Reserving it for a hypothetical future feature wastes the most-discoverable chord. `Alt` is free in this operator today. If/when the bone-tip-snap lands, it can claim `Alt`.

### D15 - Panel exposure for Quick Armature defaults

Wave 12.2 adds several configurable values: `name_prefix` (D2), `lock_to_front_ortho` default, `default_chain` (D10), `snap_increment` (D12). Where do they surface?

- **D15.A - F3 redo panel only.** Each value is an operator property; user tweaks via F3 search > tweak in the redo box at bottom-left of the viewport. Discoverable only after invoke.
- **D15.B - AddonPreferences only.** One value per Blender install, edited from Edit > Preferences > Add-ons > Proscenio. Discoverable from preferences panel.
- **D15.C - Scene PropertyGroup + Proscenio sidebar Skeleton subpanel.** Per-document defaults that ride with the `.blend`. User edits inline next to the "Quick Armature" button. F3 redo override still works for one-off changes.
- **D15.D - AddonPreferences + Scene PG override + F3 redo.** Three layers. Power-user friendly, more code.

**Locked: D15.C.** Authoring is document-centric (matches SPEC 005 D5 - sticky export path lives on Scene PG). Defaults ride with the `.blend`; a complex character `.blend` can ship its preferred `name_prefix`/`snap_increment` without configuring per-user prefs. Adding AddonPreferences (D15.D) is over-engineered for the first ship - no real workflow needs both layers right now. F3 redo still allows per-invocation override.

Concrete layout in the Skeleton subpanel:

```text
N-key sidebar > Proscenio > Skeleton
[Armature info]
[Quick Armature] (button - existing)
  -- Quick Armature defaults --
  [Lock to Front Orthographic   ] [x]
  [Bone name prefix             ] qbone
  [Default chain (Shift = root) ] [x]
  [Snap increment (world units) ] 1.0
[Create Slot]
[...]
```

Settings live under `bpy.types.Scene.proscenio.quick_armature`:

```python
class ProscenioQuickArmatureProps(PropertyGroup):
    lock_to_front_ortho: BoolProperty(default=True)
    name_prefix: StringProperty(default="qbone")
    default_chain: BoolProperty(default=True)
    snap_increment: FloatProperty(default=1.0, min=0.001)
```

Operator reads from `context.scene.proscenio.quick_armature.<field>` in `invoke` when its own option is at sentinel ("inherit"). F3 redo override = explicit operator option value.

**Out of scope for D15:** AddonPreferences (a `.blend`-spanning preference). Revisit if a user opens 5 different rig `.blend`s in a session and wants the same prefix across all of them. Until then, document-centric defaults are simpler. (the items session 1.14 cited as showstoppers). Wave 2 covers the items that make the operator pleasant for serial use. Wave 1 alone is shippable - a user can author bones today, just inefficiently; Wave 1 closes the "inviabiliza" gap. Wave 2 is the productivity polish.

## Architectural patterns + tradeoffs

Captured here so SPEC 012's implementation can lift them without re-deriving.

### Modal draw handler lifecycle

`gpu.draw_handler_add(callback, args, 'WINDOW', 'POST_VIEW')` registers a callback that fires every viewport redraw. It must be unregistered with `gpu.draw_handler_remove(handle, 'WINDOW')` in *every* exit path: `_finish`, `cancel`, error returns. Forgetting one path means the handler keeps firing after the operator ends, eventually crashing Blender when the operator's locals (`_drag_head`, `self`) get garbage-collected.

**Pattern:** wrap the handle in a class attribute (`self._preview_handle`) and define a single `_unregister_handlers` helper called from every exit path. Test: invoke the operator, force-quit Blender from the menu while modal is active. If no crash, the handler is properly cleaned by Blender's atexit; if a Python exception fires in the console, the handler is leaking.

**Tradeoff:** a class attribute means handlers do not survive script reload (the handle becomes stale). Mitigated by an `unregister()`-time sweep that walks all `SpaceView3D.draw_handler_*` registered handlers. Cheap, guards against the addon-reload case.

### Cursor follow + redraw cadence

`MOUSEMOVE` events fire at OS-cursor-event rate (typically 60-120 Hz). Calling `context.area.tag_redraw()` on every `MOUSEMOVE` is fine on modern hardware but the cost compounds on multi-region viewport setups. Bone Eyedropper ships a cached pre-fetch on `invoke` and a single `tag_redraw` per move; same pattern fits here.

### Front-Ortho detection

Detecting whether the active region is in Front Ortho:

```python
rv3d = context.space_data.region_3d
is_ortho = rv3d.view_perspective == 'ORTHO'
is_front = (rv3d.view_matrix.to_3x3() - Matrix.Identity(3)).length < 1e-4
```

The matrix comparison is robust to sign-flipped quadrants (e.g. user rotated 360 degrees). A `view_axis` switch to Front Ortho normalizes the matrix before checking again, so the operator can re-check after `view_axis` to assert the snap took.

### Operator-local undo stack

Per-bone undo inside a modal operator without touching Blender's global stack:

```python
self._session_bone_names: list[str] = []

def _create_bone(self, ...) -> None:
    bone = self._do_create(...)
    self._session_bone_names.append(bone.name)

def _undo_last_bone(self, context) -> None:
    if not self._session_bone_names:
        return
    name = self._session_bone_names.pop()
    self._do_remove(context, name)
```

Each `_create_bone` and `_undo_last_bone` round-trips through Edit Mode internally. No `bpy.ops.ed.undo_push` is called inside the modal - that fires only on `_finish`, wrapping the cumulative state change.

**Tradeoff:** in-modal Ctrl-Z does not interact with Blender's global undo. A user pressing Ctrl-Z thinking they will get the last *non-Quick-Armature* edit will instead remove a Quick Armature bone. Documented in `bl_description` and the in-viewport cheatsheet ("Ctrl+Z = undo last bone").

### Cleanup-on-cancel pattern

If the operator created the QuickRig armature in this invocation, store the reference in `self._created_armature` and in `cancel`:

```python
def cancel(self, context):
    self._unregister_handlers()
    if self._created_armature and not self._created_armature.data.bones:
        bpy.data.armatures.remove(self._created_armature.data, do_unlink=True)
    return {'CANCELLED'}
```

Tied to D4.B - sweep only what the operator created.

### Status text vs in-viewport overlay

Both channels exist; both have value:

- Status bar (`workspace.status_text_set`) is the canonical location Blender users *eventually* learn to glance at. Persisted: keep it.
- In-viewport overlay is the channel that grabs attention while the user's eyes are on the canvas. New: add it.

The `status_text_set` hint should be the *short* form (`"Quick Armature: drag = bone | Shift = chain | Esc = exit"`); the in-viewport cheatsheet is the *full* form with all modifiers. Two channels, two levels of detail.

## Out of scope (deferred to 012.1 or backlog)

- **Auto-attach underlying mesh / sprite to the new bone** (DragonBones-style). Couples to slot system (SPEC 004). Defer to a 012-or-004 follow-up.
- **Pick-parent-in-viewport modifier** (Shift-click an existing bone tip during modal to re-parent the next bone). Useful for branching skeletons but the chord vocabulary (Ctrl/Shift/Alt) is already loaded. Defer to 012.1.
- **Numeric length input** (`Tab` to type "0.5", commit with Enter). Native Blender extrude convention; bigger lift to add a text input field to a modal operator. Defer.
- **Mirror auto-suffix `_L`/`_R`** when X-Mirror is on. Useful for symmetric humanoid rigs but currently no Proscenio fixture exercises it. Defer to 012.1.
- **Floating Confirm/Cancel buttons** in viewport (D5.B). Hit-testing in modal is non-trivial. Defer until D5.A's header bar text proves insufficient in user testing.
- **Per-modifier color-coded preview line** (orange for unparented, green for chain, blue for connect). Cosmetic polish, defer.
- **Undo dialog on Esc with `>=N` bones created** (D5.D). Defer until per-bone undo (D7) ships and we see whether it removes the need.
- **Bone naming patterns with auto-numbering inside a chain** (`spine_01`, `spine_02`). Different from the prefix pref (D2). Defer.
- **Snapshot-and-restore of selected/active object on `_finish`**. Today the operator restores the previous active object ([quick_armature.py:139-140](../../apps/blender/operators/quick_armature.py#L139-L140)) but not the full selection set. Refinement for 012.1.

## Successor considerations

- **SPEC 004 (slots)** can hook into Quick Armature: a `Ctrl+Shift+drag` over an existing sprite could create a bone *and* attach the sprite to it (DragonBones model). Defer until SPEC 004 lands and the slot fixture surfaces a concrete use case.
- **SPEC 008 (UV animation)** is unrelated.
- **A future "Quick Mesh" operator** (COA-Tools-style click-stroke vertex contour drawing) would lift the same modal feedback patterns built here. SPEC 012's GPU-overlay scaffolding is reusable.
- **Addon-wide modal feedback library**. If SPEC 012's draw-handler patterns get repeated in future operators (Quick Mesh, paint-from-rig, etc.), extract into `core/bpy_helpers/modal_overlay.py` with a `ModalOverlay` class managing handle lifecycle. Premature today; revisit after second consumer appears.
- **Localization**. Every cheatsheet / status string is English. If the addon ever localizes (Blender ships full i18n), the in-viewport cheatsheet is one of the largest string surfaces. Use Blender's `bpy.app.translations.pgettext` from day one of SPEC 012 implementation; cost is one decorator per string.
