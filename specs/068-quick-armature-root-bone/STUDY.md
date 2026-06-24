# Spec 068: Quick Armature root bone

Two root-bone gaps in the Quick Armature flow, grouped because both concern the importer-created root bone and the chain authored from it. First, chain retargeting: the Quick Armature modal authors a chain whose bones parent to the previous tail within the session, but there is no way to seed or retarget that chain onto an existing bone - so adding bones starting from the root bone the plugin itself creates is currently impossible. Second, the root bone's initial size: the importer builds the single root bone at a hardcoded 0.05-unit length, which is awkwardly small; this spec sets a sensible default (1 unit) and, preferably, exposes it on the import operator so it is configurable per rig.

Spec 058 already gave the Quick Armature modal a Reparent mode - a viewport pick-parent that resolves the nearest bone tip and makes it the chain parent. The retargeting gap here is the natural extension of that: 058 lets you pick a parent for a click, but seeding a fresh chain from the importer's root bone (or continuing an existing chain off it) is the missing case. The size change is a small, near-shovel-ready constant edit plus an operator property; it is grouped in so the import-config surface and the armature-build constant are touched once, not twice.

## Scope

- **Chain retarget onto an existing bone** - allow the Quick Armature chain being authored to start from / re-parent onto an existing bone, specifically the importer-created root bone, extending spec 058's Reparent mode.
- **Root bone default size 1 unit** - change the importer's hardcoded `ROOT_BONE_LENGTH = 0.05` to a 1-unit default.
- **Expose root bone size on import** - surface the size as a configurable operator property on the Photoshop import, defaulting to the new 1-unit value.

## Open decisions

### 1. Chain retarget: seeding / re-parenting the authored chain onto the root bone

**Code anchors:** `apps/blender/core/armature/quick_armature_math.py` (`resolve_press_mode` / `resolve_press_mode_label` - the connected / unparented / disconnected vocabulary; "no modifier chains the new bone connected to the previous tail; Shift starts a fresh unparented root" - the chain always grows from the previous session tail, with no seam to an existing bone; `nearest_tip` - the screen-radius bone-tip pick spec 058 added for Reparent); `apps/blender/operators/armature/quick_armature.py` (the modal that consumes these; spec 058's Tab-cycles Draw/Reparent mode layer); `apps/blender/tests/operators/test_quick_armature_modal.py`. Locked context: spec 058 `_index.md` / `decisions.md` (Reparent mode is viewport pick-parent, the nearest bone tip within a pixel radius becomes the chain parent; all seven locked Quick Armature promises survive because Draw is additive); the gated `qa-chain-naming-suffixes` ([gated.md](../gated.md)).

**Question:** Spec 058's Reparent mode re-parents to a picked bone tip. The remaining gap is starting a chain whose first bone parents to an existing bone - the importer's root - rather than to a prior session tail or a fresh unparented root. Is that a new modifier in `resolve_press_mode` (a "parent the first bone to the picked / root bone" case), an extension of Reparent mode to cover the chain seed, or a pre-modal "set chain parent" pick?

**Options:** (A) Extend Reparent mode so the picked bone becomes the seed parent for the next-authored chain (closest to 058's existing surface). (B) A new press-mode case in `resolve_press_mode` for "first bone parents to picked bone". (C) A pre-modal active-bone seed: if a bone is active on invoke, the chain's first bone parents to it. (D) ...

**Recommendation:** TBD - lock during STUDY. Lean: (A) or (C) reuse spec 058's pick machinery / the active-bone convention with the least new chord surface, which matters given spec 066 is concurrently fighting chord saturation in the sibling automesh modal. Must preserve the seven locked Quick Armature promises (058) - the seed must be additive, not a reinterpretation of an existing modifier.

**LOCKED (C):** a pre-modal active-bone seed. The chain parent is already `cls._last_bone_name`, which `invoke` resets to `""` (so the first session bone is always unparented today) and which spec 058's Reparent pick already writes when the user clicks an existing bone tip. The new code: in `invoke`, after `_ensure_armature` resolves the target, read that armature's `data.bones.active` and seed `cls._last_bone_name` to it when present, so the first Draw chord (connected) parents the first bone onto the active bone - select the importer root, invoke, draw, and the chain seeds from root with **zero new chords**. Additive by construction: with no active bone the seed is `""` exactly as before, and `_create_bone` already guards a seed that is not in the target's edit bones (`last in edit_bones`), so a stale active bone from another armature degrades to unparented rather than binding to the wrong bone. This composes with spec 058's Reparent for mid-session retargeting; the root becomes a viable Reparent pick once decision 2 bumps its tip away from the origin. Option (A) needs no new code (Reparent already seeds `_last_bone_name`); (B) would add a chord, which the 066 chord-saturation pressure argues against. The seven locked Quick Armature promises hold - Draw is untouched, the seed only changes the first bone's parent and only when a bone was deliberately made active.

### 2. Root bone default size: the new value and the constant's home

**Code anchors:** `apps/blender/importers/photoshop/armature.py` (`ROOT_BONE_LENGTH = 0.05` at line 18; `bone.tail = (0.0, 0.0, ROOT_BONE_LENGTH)` at line 50 - the single hardcoded length; `build_root_armature` reuses an existing armature in place, so a size change only affects fresh builds, not re-imports onto an existing root). Locked context: spec 055 (re-import reuses the existing root armature - a size change will not retro-resize an already-imported rig).

**Question:** Set the default to 1 unit - confirmed. Does the constant stay a module constant defaulted to 1.0, or move to a preference / the import operator property (decision 3 owns the operator side)? And what is the interaction with `build_root_armature` reusing an existing armature - a re-import will not resize the old root, which is correct, but should be documented.

**Options:** (A) Bump the constant to 1.0, keep it as the module-level default that the operator property overrides. (B) Move it to addon preferences. (C) ...

**Recommendation:** TBD - lock during STUDY. Lean: (A) - the constant stays as the default value, the operator property (decision 3) supplies the per-import override; preferences (B) is heavier than the need. Note the re-import-reuse caveat in the change so it is not read as a bug.

**LOCKED (A):** bump `ROOT_BONE_LENGTH` from `0.05` to `1.0` and keep it as the module-level default in `armature.py`; `build_root_armature` gains a `length` parameter defaulted to it, and the operator property (decision 3) supplies the per-import override. Re-import caveat documented in the constant's comment and the import operator help: `build_root_armature` reuses an existing root armature in place (spec 055), so a length change only sizes a freshly-built root, never retro-resizes a rig already imported - which is correct (it must not disturb a grown rig) and not a bug. Preferences (B) rejected as heavier than the need.

### 3. Exposing root bone size on the import operator

**Code anchors:** `apps/blender/importers/photoshop/__init__.py` (`import_manifest(..., root_bone_name=...)` - the existing pattern of a root-bone parameter threaded from the operator; the import operator that calls it); `apps/blender/importers/photoshop/armature.py` (`build_root_armature(name, root_bone_name=...)` - the signature a `length` parameter joins, threaded the same way `root_bone_name` already is). Locked context: spec 037 storage-split (operator-property vs idprop boundaries); the typed-models / operator-property conventions.

**Question:** `root_bone_name` is already a threaded operator property -> `import_manifest` -> `build_root_armature`. Add a root-bone length the same way (a `FloatProperty` on the import operator, threaded to `build_root_armature`), defaulting to the new 1.0? Or is the size purely a constant with no per-import override?

**Options:** (A) Add a `FloatProperty` root-bone-length on the import operator, threaded through `import_manifest` -> `build_root_armature(length=...)`, default 1.0 - mirrors `root_bone_name` exactly. (B) Constant only, no operator exposure (the user marked exposure "preferably", not required). (C) ...

**Recommendation:** TBD - lock during STUDY. Lean: (A) - the threading pattern already exists for `root_bone_name`, so adding a length property is low-cost and matches the user's stated preference for configurability; (B) is the fallback if the operator UI is judged crowded.

**LOCKED (A):** add a `root_bone_length` `FloatProperty` (default `1.0`, `min` a small positive epsilon so a zero-length root cannot be authored) on `PROSCENIO_OT_import_photoshop`, threaded exactly like `root_bone_name`: `import_manifest(..., root_bone_length=self.root_bone_length)` -> `build_root_armature(..., length=root_bone_length)`. Low-cost (the thread already exists for the name) and matches the user's stated preference for per-rig configurability.

## Verdict summary

LOCKED 2026-06-24 - all three decisions resolved. Decision 1 (chain retarget) locked as (C): a pre-modal active-bone seed - `invoke` seeds `cls._last_bone_name` from the resolved target armature's active bone, so selecting the importer root and drawing chains the first bone onto it with zero new chords; additive, guarded, and composing with spec 058's Reparent (which already seeds `_last_bone_name` on a tip pick) once the size bump makes the root a viable pick target. Decision 2 (A): `ROOT_BONE_LENGTH` 0.05 -> 1.0, kept as the module default, with the spec 055 re-import-reuse caveat documented (a re-import never retro-resizes an existing root). Decision 3 (A): a `root_bone_length` `FloatProperty` on the import operator, threaded exactly like `root_bone_name` into `build_root_armature(length=...)`, default 1.0. The design-heavy half (decision 1) lands as a few lines in `invoke` reusing existing state; the sizing half is a constant bump plus one threaded property. Size: S-to-M. See [TODO.md](TODO.md).

## Sources

Extends spec 058 (quick-armature-interaction-redesign - the Reparent pick-parent mode). Related gated items `qa-chain-naming-suffixes` and `sticky-panel` ([gated.md](../gated.md) "Rigging and posing") stay gated. The root-bone sizing is a fresh pre-v1 item, no prior backlog entry; the constant is at `apps/blender/importers/photoshop/armature.py:18`.
