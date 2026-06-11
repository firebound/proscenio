# Spec 031: Rigging and posing

Round out rig authoring and animation setup - bone creation, skeleton management, drivers, IK, and the pose library.

## Scope

- **Retest skeleton row-click** selecting the bone in the viewport.
- **Retest Save Pose** failing without a writable asset library.
- **Skeleton names the armature** the writer uses.
- **Quick Armature: clamp/color the preview line** under panel overlays.
- **Quick Armature: rotation-mode choice** (Euler-Y vs quaternion) with a safe swap.
- **Quick Armature: pick the parent bone** in the viewport during the modal.
- **Quick Armature: chain-aware name suffixes**.
- **Quick Armature: auto _L/_R suffix** with X-Mirror.
- **Quick Armature: numeric length entry** (Tab to type).
- **Quick Armature: local-axis lock** (press the axis twice).
- **Quick Armature: help topic** for its defaults.
- **Quick Armature: headless undo / axis-lock tests**.
- **Skeleton: inline bone rename**.
- **Skeleton: bone-collection management** from the panel.
- **Skeleton: richer hierarchy editing** beyond the read-only readout.
- **Drive from Bone: two editable ranges** instead of a raw expression.
- **Drive from Bone: inline value readout** plus Inspect/Reset buttons.
- **Drive from Bone: a sticky panel** while editing a pose bone.
- **Drive a slot attachment from a bone**.
- **IK: wire a target/subtarget** when toggling the constraint.
- **IK: a bake-action gate** before export.
- **IK: a runtime IK/FK switch**.
- **IK: a one-click chain helper** (target + pole scaffolding).
- **IK round-trip** Blender to Godot.
- **Pose library: one-click apply** pose to selection.
- **Pose library: auto-categorise** poses by armature.
- **Pose library: thumbnails** via the preview camera.

## Study

### Surface notes

- The Quick Armature operator (`operators/armature/quick_armature.py`, 960 lines) is the heaviest modal in the addon: ~35 ClassVar state fields, an in-modal undo/redo stack of `_BoneRecord`s, view + selection snapshot/restore, double-invoke handler sweeping, per-event region filtering, two GPU draw handlers plus STATUSBAR and VIEW3D header appends. The chord vocabulary is already saturated - <kbd>Shift</kbd> flips chain mode, <kbd>Alt</kbd> means disconnected, <kbd>Ctrl</kbd> is grid snap and undo, <kbd>X</kbd>/<kbd>Z</kbd> toggle axis lock - and the code comments document the collisions (`_is_axis_lock_event` skips Shift to protect the chain modifier). Every follow-up in the cluster (parent picking, text entry, mirrored creation, per-chain counters) lands inside this state machine and widens the chord surface.
- Bone naming is a flat counter: `format_bone_name(prefix, len(edit_bones))` emits `qbone.000`, `qbone.001` across chains (`quick_armature.py:547`, `core/armature/quick_armature_math.py:116-118`). Chain-aware naming needs per-chain counters plus new-root detection in modal state.
- Axis lock is global X/Z only and a second press clears it (`quick_armature.py:266-275`). Authoring is hard-locked to the world XZ picture plane (Y=0) and QuickRig is created unrotated at the origin, so the local-vs-global distinction the double-press proposal targets has no reachable case in this pipeline.
- The preview-line fix shipped as option B: the line turns red and an "outside canvas" tooltip renders when the cursor crosses a panel overlay (`_overlay.py:36,114-115,144-167`). The clamp (option A) is unimplemented and the tradeoff is documented in the backlog as accepted.
- Headless infrastructure exists for an operator suite: `tests/test_quick_armature_math.py` covers the pure helpers, and `apps/blender/tests/operators/` (driven by `run_operator_tests.py` inside real headless Blender) holds suites for automesh and weights but none for Quick Armature. `_create_bone`, `_undo_last_bone`, `_redo_last_bone`, and `_post_process_world_point` are callable without the modal event loop, so the undo/redo stack and snap-then-lock ordering are testable today.
- The **Skeleton** bone list rows are `emboss=False` operator buttons wired to `proscenio.select_bone_by_name` (`panels/skeleton.py:51-57`, `operators/selection.py:79-93`, fix `dcd08f6`) - only the GUI retest is open. An inline-rename prop field would fight the row-click operator for the same click; row-click already makes the bone active, and <kbd>F2</kbd> renames the active bone natively.
- The armature picker shipped (`properties/scene_props.py:473-486`) and its tooltip claims "the writer exports it", but `writer/scene_discovery.py:find_armature` still returns the first ARMATURE in the scene - the export-correctness spec owns that blocking fix ([writer-ignores-picker](../027-export-correctness/STUDY.md)). Naming the export target in the panel before that fix lands would advertise a lie; this item sequences strictly after it.
- Drive-from-Bone is a 29-line box (`panels/_draw_driver_shortcut.py`) exposing the raw `driver_expression` string. The operator (`operators/driver.py`) is idempotent - re-running replaces the driver and purges stale siblings - prefills from the PG, and already normalizes rotation reads to XYZ Euler radians in world space. A two-range linear map is a contained addition: four float fields, a pure expression builder, panel rows, with the raw string demoted to an Advanced fallback. Re-clicking `Drive from Bone` already is the reset.
- The default expression is an active hazard: `var` maps radians (about -3.14..3.14) straight onto a frame range of 0..N-1, so negative rotation clamps to 0 and the flagship driver looks broken on first contact - the ui-feedback log records exactly this experience.
- `Toggle IK` (`operators/armature/authoring_ik.py:49-55`) inserts a `Proscenio IK` constraint with `chain_count` only - no `target`/`subtarget`. A targetless IK constraint solves only while grabbing the constrained bone, so the shipped toggle half-delivers and the INFO bar punts the user to the Properties editor.
- The IK export hole is silent: the writer reads raw fcurves, so an animation keyed only on an IK target exports flat intermediate bones; nothing in `core/validation` detects an active-influence IK chain without keyframes and no `nla.bake` wrapper exists. This is a wrong `.proscenio` with no warning - the exact failure class this project exists to prevent.
- The pose library operator (`operators/pose_library.py:68-85`) carries the writable-library pre-check, the actionable error, and the `asset_library_reference` argument (fix `7d10f69`) - only the GUI retest is open. `bake_current_pose` keys every pose bone at the playhead.
- Rotation mode is authoring clarity, not export correctness: the writer collapses both representations through `_quat_to_screen_angle` (`writer/animations.py:188-205`), so quaternion-default bones export correctly when rotated in-plane. The gap is four opaque quaternion channels in the Graph Editor and a clumsier Drive-from-Bone target; the backlog scope sketch spans three surfaces including a keyframe-guarded safe-swap operator that can silently break animations if wrong.

### Research notes

- **Godot docs, SkeletonModification2D (4.6 stable):** the entire 2D modification stack - `SkeletonModification2DTwoBoneIK`, `CCDIK`, `FABRIK` - is flagged "Experimental: may be changed or removed in future versions". 3D got the `SkeletonModifier3D` rework in 4.3; 2D never received the equivalent and still ships the 4.0-era experimental API.
- **godotengine/godot issues #79960, #75224:** the 2D IK stack throws confusing setup errors in plain configurations and breaks under negative X scale - it is unreliable in exactly the flipped-rig cases 2D games hit. Emitting live IK into imported scenes would stand on this.
- **Esoteric Software, Spine IK constraints + In Depth:** IK is a 2D-cutout authoring staple (legs are near-universally IK-rigged) and Spine keeps constraints live through its runtimes. Proscenio's import-time-only, built-in-nodes contract has no runtime, so baking IK into bone keyframes at export is the structural equivalent, not a compromise.
- **Esoteric Software, Spine keys guide + forums:** Spine has no pose library; animators copy/paste bone transforms (<kbd>Ctrl+C</kbd>/<kbd>Ctrl+V</kbd>) or stash poses in spare animations. A pose library is a Blender-native bonus on top of genre expectations, not a gap to close.
- **Blender manual, Pose Library (5.1):** pose assets are native - applying from the Asset Shelf affects selected bones, flipped apply is built in, <kbd>Ctrl</kbd> blends, catalogs organize per rig, and `create_pose_asset` auto-generates a viewport preview. The pose-library evolution items mostly re-wrap shipped Blender features.
- **Blender manual, bone Naming + Editing Bones:** the L/R suffix convention exists to power native X-Axis Mirror on bilaterally symmetric rigs; <kbd>E</kbd> extrude in Edit Mode already provides chained creation, axis locking with the double-tap local variant, and typed numeric length - the precision ergonomics the Quick Armature follow-ups propose to clone. Quick Armature's documented value is the rough-sketch phase before refining in Edit Mode; precision lives one <kbd>Tab</kbd> away.
- **AVG Guild / Animation Salvation, FK vs IK:** IK/FK switching with match tools is a mid-shot control-handoff technique from 3D film and game rigs (the ladder-grab case). In an export-baked 2D pipeline the animator toggles IK between takes; a runtime switch has no consumer.
- **cgtyphoon / MotionBuilder naming conventions:** symmetric naming pays off on bilaterally symmetric rigs; 2D cutout characters are commonly authored asymmetric from a single 3/4 view (different sprites per side), and no Proscenio fixture exercises a symmetric rig end-to-end.

### Assessment

Scores: flow value (5 = protects the core PSD -> Blender -> export -> Godot flow), test burden (5 = recurring manual GUI), bug surface (5 = new modal/stateful surface), underuse risk (5 = speculative demand).

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| skeleton-row-click-select (retest) | 4 | 2 | 1 | 1 | now | Fix `dcd08f6` in code; one GUI smoke confirms. |
| pose-save-library-precheck (retest) | 3 | 2 | 1 | 1 | now | Fix `7d10f69` in code; one GUI smoke confirms. |
| skeleton-armature-picker | 5 | 2 | 2 | 1 | now | Export-target trust; sequences after the 027 writer-picker fix. |
| qa-preview-clamp-color (clamp half) | 1 | 4 | 3 | 4 | drop | Red-line + tooltip shipped; clamp is cosmetic geometry on a modal. |
| qa-rotation-mode | 3 | 4 | 4 | 3 | gate | Export already correct; three-surface sketch with a risky safe-swap. |
| qa-pick-parent-viewport | 2 | 5 | 5 | 4 | gate | Bone-tip hit-testing inside a saturated chord vocabulary. |
| qa-chain-naming-suffixes | 2 | 3 | 3 | 3 | gate | Flat counter works; batch rename covers after the fact. |
| qa-mirror-suffix | 2 | 4 | 4 | 5 | gate | No symmetric fixture; mirrored create entangles the undo stack. |
| qa-numeric-length | 2 | 5 | 5 | 4 | drop | Text-entry state machine in the modal; Edit Mode <kbd>E</kbd> + type covers precision. |
| qa-local-axis-lock | 1 | 4 | 3 | 5 | drop | Local == global in the XZ-locked, origin-anchored workflow. |
| qa-defaults-help-topic | 1 | 1 | 1 | 4 | drop | Field tooltips self-describe; the quick_armature topic is the home. |
| qa-headless-undo-axis-tests | 3 | 1 | 1 | 1 | now | Locks the undo/redo + snap-lock machine; cuts future manual smoke. |
| skeleton-inline-rename | 2 | 4 | 3 | 3 | drop | Row-click owns the click; row-click + <kbd>F2</kbd> is the native path. |
| skeleton-bone-collections | 2 | 4 | 4 | 4 | drop | Duplicates the native Bone Collections panel one editor away. |
| skeleton-hierarchy-editing | 2 | 5 | 4 | 4 | drop | Edit Mode is the hierarchy editor; readout is read-only by design. |
| expression-two-ranges | 5 | 3 | 3 | 2 | now | Default `var` makes the flagship driver look broken; map is pure math. |
| driver-readout-inspect-reset | 4 | 3 | 2 | 2 | now | Readout rides the two-ranges PR; idempotent re-run already resets; Inspect popup dropped. |
| sticky-panel | 3 | 4 | 4 | 3 | gate | Real swap pain but a poll-architecture change; re-measure after the driver rework. |
| drive-slot-from-bone | 3 | 5 | 4 | 4 | gate | New driver target + roundtrip burden; no rig has asked. |
| ik-toggle-no-target | 4 | 3 | 2 | 2 | now | Shipped toggle half-works; wiring a target makes it deliver. |
| ik-bake-gate | 5 | 2 | 2 | 2 | now | Unkeyed IK chains export silently wrong; check is headless-testable. |
| ik-fk-switch | 1 | 5 | 5 | 5 | drop | Film-rig technique; export is baked, toggle covers authoring. |
| ik-chain-helper | 3 | 4 | 3 | 3 | gate | Target wiring absorbs most of it; scaffold on demand. |
| ik-round-trip (live half) | 2 | 5 | 5 | 4 | gate | Godot 2D IK is experimental and buggy; the bake gate covers the need. |
| pose-apply-to-selection | 2 | 3 | 2 | 4 | drop | Native Asset Shelf apply already targets selected bones. |
| pose-auto-categorise | 2 | 3 | 2 | 4 | gate | Native catalogs exist; auto-assign waits for a second character. |
| pose-thumbnails | 1 | 4 | 3 | 5 | drop | Native auto-preview ships; flat-render swatches are cosmetic. |

### Verdict summary

- **Now: 8** - two GUI retests, the headless Quick Armature suite, the picker export-target display (after 027), the Drive-from-Bone two-ranges rework with its inline readout, and the two IK items that protect the export (`target` wiring, bake gate).
- **Gate: 9** - every postponed item carries a written trigger; none proceeds on imagination.
- **Drop: 10** - the Quick Armature precision cluster (numeric length, local-axis lock, clamp, help topic), the Skeleton items that duplicate native Blender (inline rename, bone collections, hierarchy editing), the IK/FK runtime switch, and the two pose-library items native Blender already ships (apply-to-selection, thumbnails).
- **Defer (untriggered): 0.**

The spec's real payload is small: keep the flagship Drive-from-Bone from looking broken and close the one silent-wrong-export hole (unbaked IK). The 27-row count is inflated by a follow-up cluster around an operator that already works - Quick Armature is a rough-sketch tool and Blender Edit Mode is its precision tier, so cloning Edit Mode ergonomics into the modal buys test burden, chord conflicts, and imagined demand. The pose library is a thin shim over a native system that already does most of what the evolution items ask.
