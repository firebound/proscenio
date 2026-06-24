# Spec 068 TODO: Quick Armature root bone

Drives the locked [STUDY](STUDY.md). Three decisions resolved: (1) a pre-modal active-bone seed for the Quick Armature chain, (2) `ROOT_BONE_LENGTH` 0.05 -> 1.0, (3) a threaded `root_bone_length` import-operator property. TDD: each behavior gets a headless test before its implementation.

## 1. Root bone default size 1 unit (decision 2)

- [ ] In [`importers/photoshop/armature.py`](../../apps/blender/importers/photoshop/armature.py), bump `ROOT_BONE_LENGTH = 0.05` to `1.0`. Update the comment to note the spec 055 re-import-reuse caveat: `build_root_armature` reuses an existing root in place, so the new length only sizes a freshly-built root and never retro-resizes an already-imported rig (correct, not a bug).

## 2. Thread a length parameter (decisions 2 + 3)

- [ ] `build_root_armature(name, root_bone_name=..., length: float = ROOT_BONE_LENGTH)` - use `length` for `bone.tail = (0.0, 0.0, length)`.
- [ ] `import_manifest(..., root_bone_length: float = ROOT_BONE_LENGTH)` in [`importers/photoshop/__init__.py`](../../apps/blender/importers/photoshop/__init__.py), passed to `build_root_armature(length=root_bone_length)` (mirror the existing `root_bone_name` thread).
- [ ] Add a `root_bone_length` `FloatProperty` to `PROSCENIO_OT_import_photoshop` in [`operators/import_photoshop.py`](../../apps/blender/operators/import_photoshop.py): default `1.0`, `min` a small positive epsilon (no zero-length root), description noting it sizes the importer root bone (and that a re-import onto an existing rig keeps the old size). Pass `root_bone_length=self.root_bone_length` into `import_manifest`.

## 3. Pre-modal active-bone seed (decision 1)

- [ ] In [`operators/armature/quick_armature.py`](../../apps/blender/operators/armature/quick_armature.py) `invoke`, after `_ensure_armature` resolves the target and `cls._last_bone_name = ""` is set, seed it from the target armature's active bone when present: read the resolved target object (`bpy.data.objects.get(cls._target_armature_name)`), and if its `data.bones.active` is not None, set `cls._last_bone_name = active.name`. Keep it a tiny helper (`_seed_chain_parent_from_active`) so it is testable and documented (zero new chords; additive; `_create_bone` already guards a seed absent from the target edit bones).
- [ ] Confirm no chord/cheatsheet change is needed (the seed is silent; the first connected Draw simply chains from the seeded bone).

## 4. Tests (headless, in-Blender via `run_operator_tests.py`)

- [ ] `armature.py` / importer: `build_root_armature` honors a custom `length` (root bone tail Z == length); `import_manifest(root_bone_length=...)` sizes the fresh root; default is 1.0. Add to an importer/armature test (e.g. a new `test_root_bone_length` or fold into the existing reuse test).
- [ ] Quick Armature seed (in `test_quick_armature_modal.py` or a sibling): with a target armature whose `data.bones.active` is set, `invoke` seeds `_last_bone_name` to that bone; a connected first-bone Draw parents to it. With no active bone, the seed stays `""` (first bone unparented, unchanged behavior). A seeded name absent from the target degrades to unparented (no crash).

## 5. Gates

- [ ] `run_operator_tests.py` (full set) + `run_tests.py` goldens (8/8). The goldens build their own fixtures; if any golden fixture re-imports and asserts the root bone length, update the expectation to 1.0 - otherwise the writer is untouched and goldens stay byte-unchanged (the root bone is not deform-weighted, so it does not reach the Godot export). Verify which.
- [ ] `mypy` strict + `ruff format --check` + `ruff check` on `apps/blender`.

## 6. Post-merge cleanup (ONLY after the maintainer squash-merges the PR - never before)

- [ ] QA Companion: add / update the Quick Armature + import walks (seed-from-active-bone, root-bone-length import field). Use the next free `BL-...` id.
- [ ] Lock the calls in [`decisions.md`](../decisions.md).
- [ ] Prune this spec folder, index in [`_index.md`](../_index.md) with the PR number.
