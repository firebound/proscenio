# Spec 071: Revert a mesh element to its original plane

A one-click revert that undoes everything Proscenio did to a mesh element and restores the original imported textured plane - the plain quad with its image material, no automesh geometry, no weights. The escape hatch for "start this element's mesh over".

Logged as `mesh-revert-to-plane` in [backlog/ui-feedback.md](../backlog/ui-feedback.md). It is distinct from per-element PSD re-import (spec 067), which re-runs automesh and reprojects weights: revert deliberately goes *back to the bare quad* and drops the deformation, where re-import rebuilds a deformed mesh from source.

## Scope

- **In:** a mesh-element operator that rebuilds the original quad, drops the automesh geometry and the skinning data, and leaves a clean textured plane ready to re-author; a button on the Element (or Mesh Generation) panel.
- **Out:** sprite elements (already a quad - nothing to revert); reverting the *element* itself back to a raw non-Proscenio mesh (revert keeps `element_type`); touching user-added drivers / modifiers / shape keys Proscenio never stamped.

## Open decisions

### 1. Restore strategy: rebuild from the import placement, or snapshot the pre-automesh quad?

**Code anchors:** `apps/blender/importers/photoshop/planes.py` (`_build_quad` ~332-360 - 4 verts, 1 face, UV (0..1); `_ensure_mesh` ~276-307 reuses-or-rebuilds keyed on `_placement_unchanged` ~362; the `PROSCENIO_IMPORT_PLACEMENT` Custom Property `[width, height, offset_x, offset_z]` stamped at import and never touched by automesh; `_attach_material` ~405 - the image material is a mesh property independent of geometry); `apps/blender/core/bpy_helpers/automesh/base_sprite.py` (`initialize_base_sprite_group` ~24, `delete_non_base_geometry` ~49, `remove_base_sprite_verts` ~59 - automesh flags the original 4 verts then deletes them unless `preserve_base_quad`, so the original quad is normally gone after meshing); `apps/blender/operators/atlas_pack/unpack.py` (`PROSCENIO_OT_unpack_atlas` ~36, `_restore_object` ~79 - the snapshot-restore precedent: reads `PROSCENIO_PRE_PACK`, restores UVs + material + region, survives .blend reload, Ctrl+Z does not). Locked context: `decisions.md` "Schemas are the contract" is irrelevant here (authoring-only); the re-import contract (spec 055/067) is the sibling operation.

**Question:** Automesh deletes the original quad (the base-sprite verts are dropped at regen unless `preserve_base_quad`), so the 4-vert plane is not sitting on the object to restore. Two ways to get it back: rebuild it deterministically from the placement tag the import stamped, or restore a snapshot the addon takes before the first automesh. Which?

**Options:**
- (A) Rebuild from `PROSCENIO_IMPORT_PLACEMENT` + the existing material: call `_build_quad(obj, (width, height), (offset_x, offset_z))` to recreate the exact original quad and UVs; the image material is already on the object, untouched. No new storage - the placement tag survives every automesh run, and this mirrors the re-import quad-rebuild path. Fails only for an element with no placement tag (see decision 3).
- (B) Snapshot the pre-automesh state into a Custom Property (e.g. `PROSCENIO_PRE_AUTOMESH`: verts / faces / UVs / material) the first time automesh runs, and restore it on revert - the `unpack_atlas` pattern exactly. Exact recovery even for hand-edited or incorporated meshes, at the cost of new write-on-first-automesh plumbing and stale-snapshot risk if the quad was manually edited before meshing.
- (C) Re-import from the stamped manifest (`PROSCENIO_IMPORT_MANIFEST`) and stop before automesh. Reuses import, but re-import's whole contract is to *produce a mesh*, and it needs the manifest file present - heavier and more fragile than rebuilding a quad we can fully describe from one tag.

**Recommendation:** **(A).** The placement tag is a complete description of the original quad (size + offset + the fixed (0..1) UV), it is never mutated by automesh, and the material rides along independently - so a rebuild is exact with zero new snapshot infrastructure, and it reuses `_build_quad`, the proven path re-import already calls. (B) buys recovery for the no-placement case (incorporated meshes) but pays for it on every element forever; better to handle that case as a narrow fallback (decision 3) than to carry a snapshot for all. (C) misuses re-import and adds a file dependency. **Lock (A) as the primary, with the no-placement fallback decided in 3.** Size **M** (the operator: rebuild quad + the data-wipe of decision 2 + guards + a headless test that an automeshed element reverts to 4 verts / 1 face with the material intact).

### 2. What a revert wipes versus keeps

**Code anchors:** `apps/blender/core/_shared/cp_keys.py` (`PROSCENIO_WEIGHT_SIDECAR`, `PROSCENIO_BONE_MODES`, `PROSCENIO_ENVELOPE_RADIUS`, `PROSCENIO_MIRROR_X` ~83-86 - skinning state; `PROSCENIO_USER_STROKES` / `_OUTER_STROKES` / `_USER_STEINERS` ~88-93 - automesh authoring state; `PROSCENIO_IMPORT_PLACEMENT` / `_ORIGIN` / `_MANIFEST` ~105-109 - import identity; `PROSCENIO_TYPE` ~53 - element kind); `apps/blender/core/bpy_helpers/skinning/sidecar_io.py` (`apply_sidecar` ~91 - wipes non-base groups + recreates deform groups, the inverse of what a wipe needs); `apps/blender/operators/skinning/restore_weight_snapshot.py` (`PROSCENIO_OT_restore_weight_snapshot` ~29 - the topology-hash guard precedent); the object's `vertex_groups` (deform-bone groups + `proscenio_base_sprite`). Locked context: `decisions.md` "Photoshop manifest re-import PRESERVES painted weights via the sidecar reproject" - revert is the opposite intent (drop the weights).

**Question:** A reverted plain quad has no deformation, so the skinning data is meaningless on it. The import identity (placement, origin, manifest, element_type) must stay so the element is still a Proscenio element and a *re-import or re-author* still works. The grey area is the automesh authoring state (the user's strokes / interior points): wiping gives a truly blank plane; keeping lets a later re-automesh reproduce the user's edits. Which fields are cleared, which survive?

**Options:**
- (A) Wipe skinning (every deform vertex group + `proscenio_base_sprite`, the `PROSCENIO_WEIGHT_SIDECAR` and the bone-mode / envelope / mirror keys) and the automesh authoring strokes (`PROSCENIO_USER_*`); keep import identity (placement / origin / manifest), `element_type`, and the material. A true blank original plane.
- (B) Wipe skinning, but KEEP the authoring strokes so a subsequent automesh re-creates the user's hand-edits. Convenient for "revert then re-mesh with new params", but the reverted plane silently carries invisible authoring state, which is surprising and is exactly the "hidden state" trap the spec 069 export-toggle review flagged.
- (C) Wipe everything Proscenio-authored including `element_type` (revert all the way to a raw mesh). Cleanest object, but it stops being a Proscenio element, breaking the Outliner listing and the panels - and the user said "back to the imported plane", which is still an element.

**Recommendation:** **(A).** "Back to the original imported plane" means the plane as it was right after import: an element with its image and placement, no weights, no automesh edits. Keeping invisible strokes (B) reads as a bug the first time a revert-then-remesh resurrects deleted geometry; if "re-mesh preserving my edits" is wanted, that is re-running automesh *without* reverting, not a revert. (C) over-reverts past what the user asked and breaks the element contract. **Lock (A); decide whether revert reports a summary of what it cleared (recommended - weights / N strokes / vgroups) so the destructive scope is visible.** Size **S-M** (the wipe is a handful of `cp_keys` deletes + vertex-group removal; the test asserts the keys and groups are gone and identity survives).

### 3. Eligibility and the no-placement fallback (incorporated / hand-built elements)

**Code anchors:** `apps/blender/operators/incorporate.py` (`PROSCENIO_OT_incorporate_element` ~49-119 - makes a hand-authored mesh an element by stamping `element_type`; it does NOT stamp `PROSCENIO_IMPORT_PLACEMENT`, so an incorporated element has no original quad to rebuild from); `apps/blender/panels/_helpers.py` (`_is_mesh_element` ~62 - the mesh-element gate the panel buttons use); `apps/blender/importers/photoshop/planes.py` (`_placement_unchanged` ~362 - reads the placement tag). Locked context: spec 067 per-element re-import resolves an element by `proscenio_import_origin` and degrades to a warn-and-no-op when it cannot.

**Question:** Decision-1A rebuilds from `PROSCENIO_IMPORT_PLACEMENT`, which only PSD-imported elements carry. An incorporated or hand-built mesh element has no placement (and no original quad), and a sprite element is already a quad. What is eligible, and what happens to an element with no placement?

**Options:**
- (A) Restrict revert to PSD-imported mesh elements (those with `PROSCENIO_IMPORT_PLACEMENT`); on a no-placement element, warn-and-no-op ("no original plane recorded for this element") - the spec 067 degrade posture. Honest and simple; an incorporated mesh never had an "original imported plane" to revert to.
- (B) Add a bounds fallback: when there is no placement, rebuild the quad from the current mesh's bounding box (and the material's image), so any mesh element reverts to *a* quad fitting its extent. Broader coverage, but it invents an "original" that never existed and can mis-size if the mesh was scaled.
- (C) Pair revert with the decision-1B snapshot so incorporated meshes get an exact pre-automesh snapshot too. Universal, but pulls in the snapshot infrastructure (A) avoided.

**Recommendation:** **(A) for v1, with (B) as a flagged follow-on.** The feature the user described is "revert the generated mesh to the original imported plane with texture" - that is the PSD-import case by definition, and restricting to it keeps the rebuild exact and the semantics honest (an incorporated mesh has no imported plane). (B)'s bounding-box quad is a plausible later convenience but it fabricates an original; gate it behind a real request. (C) is only worth it if incorporated-mesh revert becomes a hard requirement. **Lock (A); log (B) as the extension.** Guard the operator behind `_is_mesh_element` + a placement check, and warn-no-op otherwise. Size **S** (a poll/guard + the warn path; the bulk of the work is decisions 1-2).

## Verdict summary

Revert rebuilds the original quad from the `PROSCENIO_IMPORT_PLACEMENT` tag plus the element's existing image material (decision 1A) - exact, no new snapshot storage, reusing `_build_quad` the way re-import already does. It wipes the skinning data (vertex groups, weight sidecar, bone-mode keys) and the automesh authoring strokes, while keeping the import identity, `element_type`, and material, leaving a clean textured plane (decision 2A). v1 is restricted to PSD-imported mesh elements; a no-placement (incorporated) element warns-and-no-ops, with a bounding-box rebuild logged as a follow-on (decision 3A). Open locks for the user: report-cleared-summary or silent (2), and whether the incorporated-mesh fallback (3B) is wanted now. Total size **M**, mostly the operator + the data-wipe + guards; the quad rebuild is an existing function.

## Sources

- `backlog/ui-feedback.md` - the `mesh-revert-to-plane` entry this STUDY drives.
- Spec 067 (element-individual-reimport) and 055 (reimport-contract) - the sibling re-import path; see `decisions.md` "Element individual reimport" and "Photoshop manifest re-import PRESERVES painted weights".
- `PROSCENIO_OT_unpack_atlas` (`operators/atlas_pack/unpack.py`) - the snapshot-restore precedent weighed in decision 1.
- Code anchors above, current as of 2026-06-27 (`apps/blender/importers/photoshop/planes.py`, `core/bpy_helpers/automesh/base_sprite.py`, `core/_shared/cp_keys.py`, `operators/incorporate.py`, `operators/skinning/`, `operators/atlas_pack/`).
