# Refuted findings (false positives)

Phase-1 findings the adversarial verification pass **disproved** by reading the real code. Recorded so nobody re-flags them - each is a sanctioned convention or a factual error in the original claim. Do NOT act on these.

## God-module claims left un-split by spec 075 (2026-07-02)

When spec 075 (PR #184) drained the god-modules / SRP theme, two of its items shipped no split - one refuted as a god-module, one already decomposed. Recorded here (`god-modules-and-srp.md` was deleted on the prune) so nobody re-flags them.

- **authoring-ik-module** (claimed: a god-module to split by operator) - **REFUTED as a god-module.** [authoring_ik.py](../../../apps/blender/operators/armature/authoring_ik.py) is a single cohesive Proscenio IK feature whose four operators share low-level helpers; splitting by operator would fracture those shared helpers. A size-only smell, not an unrelated bundle. Left intact by design.
- **build-automesh-debug-stages** (claimed: `build_automesh` interleaves debug-stage early-returns that should move to a stage table) - **NO ACTION (already decomposed).** [bridge.py](../../../apps/blender/core/bpy_helpers/automesh/bridge.py) `build_automesh` is already broken into named helpers; its six debug early-returns each snapshot an intermediate only available at that point and cannot cleanly move to a stage table without re-threading the same state. Leave as-is unless a future change opens it.

## Already-correct at HEAD by the time spec 076 implemented them (2026-07-01)

Two bug findings the audit CONFIRMED on 2026-06-28 were, when spec 076 (PR #183) went to implement them, already correct in the code (fixed by intervening work / never actually broken). No change shipped for either; recorded so nobody re-flags them.

- **driver-source-bone-enum-remap** (claimed: the `driver_source_bone` EnumProperty stores a positional index that a bone rename/reorder silently remaps) - **ALREADY CORRECT.** [_dynamic_items.py:57](../../../apps/blender/properties/_dynamic_items.py#L57) - `driver_bone_items` already emits `(bone.name, bone.name, "")` items, so the selection stores the bone NAME (the identifier is the first element), not a positional index; the module-level `_DRIVER_BONE_ITEMS_CACHE` also already pins the list against the EnumProperty GC bug. Nothing to fix.
- **feet-landing-name-over-tag** (claimed: a mesh resolves to a PSD layer by name before tag) - **ALREADY CORRECT.** Every layer/mesh resolution in the photoshop importer is already tag-first / name-fallback: [`_layer_for_object`](../../../apps/blender/importers/photoshop/__init__.py#L216) resolves the stamped `proscenio_import_origin` before the object name, and [`_find_existing`](../../../apps/blender/importers/photoshop/planes.py#L315) checks the origin tag before a name match. No name-first path remains.

- **bone-modes-cp-io** (claimed: misplaced - bpy custom-property IO in a bpy-free package) - **REFUTED.** [bone_modes.py](../../../apps/blender/core/skinning/bone_modes.py) imports bpy only under `TYPE_CHECKING`; there is no runtime bpy. Custom-property access is dict-style (`obj[...]` / `obj.get`), which is the **documented package-wide convention** (cp_keys.py:8-13, json_cp.py:10-13 state the runtime stays bpy-free precisely by using dict-style access that the headless writer and pytest satisfy without registering the addon). 11 of ~13 core/skinning modules do this. Moving the functions would break the existing bpy-free test and invert layering (bpy_helpers depend on core, not the reverse).

- **validation-abspath-bpy** (claimed: misplaced - `abspath_or_none` imports bpy inside core/) - **REFUTED.** [_shared.py:50-56](../../../apps/blender/core/validation/_shared.py#L50) imports bpy **lazily inside the function body**, wrapped in try/except ImportError with a bpy-free fallback. The core/ contract (core/__init__.py:6-8) explicitly permits "import bpy lazily inside one function". Sanctioned pattern.

- **apply-atlas-snapshot** (claimed: SRP - operator owns a full snapshot/restore state machine) - **REFUTED.** [apply.py:99-157](../../../apps/blender/operators/atlas_pack/apply.py#L99) holds two private methods used only inside this operator; the reusable primitives are **already extracted** into `operators/atlas_pack/_paths.py` and shared with unpack.py. What remains in apply.py is operator-specific orchestration, correctly placed.

- **slot-attachment-keyframe** (claimed: SRP - four unrelated operators bundled) - **REFUTED.** [attachment.py](../../../apps/blender/operators/slot/attachment.py) holds four operators that are all slot-attachment-themed and share the same `proscenio.is_slot` poll on the active Empty - they are tightly related, not unrelated. The "four unrelated parenting operators" framing is factually wrong.

- **known-topic-ids-dead** (claimed: dead code - zero references) - **REFUTED.** [help_topics.py:696-698](../../../apps/blender/core/help_topics.py#L696) - `known_topic_ids()` has a **live reference and a dedicated test**: `tests/test_help_topics.py:31` (import) and `:238` (`test_known_topic_ids_returns_registration_order`). Phase 1's grep missed the repo-root test. Not dead.

- **weight-transfer-test-docs** (claimed: test-org - bare docstring + generic names) - **REFUTED.** [test_weight_transfer.py](../../../apps/blender/tests/operators/test_weight_transfer.py) - both test functions already have behavior-describing docstrings (line 9, line 46) and behavior-descriptive names. The "bare one-liner / generic names" claim is false. (The separate `weight-transfer-cancel-partial-write` coverage gap in [test-quality.md](test-quality.md) is real and stands.)
