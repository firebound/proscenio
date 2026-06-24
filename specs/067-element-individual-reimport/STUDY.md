# Spec 067: Element individual reimport

Re-import a single Element - one PSD layer / one manifest entry - from the Element panel, instead of re-running the whole manifest. Today the only re-import path walks every layer in the manifest and re-stamps all of them; an artist who fixed one layer's art in Photoshop has to re-import the entire document to pick up that one change, which churns every other Element (and risks the per-Element work they grew on the others). This spec adds a per-Element reimport surfaced where the Element already lives - the Element panel - reusing the per-entry stamping the orchestrator already isolates.

The re-import contract this rides on is already settled (spec 055): a same-bounds re-import preserves painted weights and density, a changed-bounds re-import reprojects from the surviving sidecar, and the importer reuses the existing root armature rather than orphaning it. The single-Element case must honor the same contract, scoped to one entry: re-stamp this Element's mesh / sprite, preserve its weights when the bounds hold, and leave every sibling Element untouched. The open work is identifying the Element-to-manifest-entry mapping at re-import time and deciding what happens when the source layer has moved, been renamed, or vanished from the PSD since the first import.

## Scope

- **Per-Element reimport entry point** - a button / operator in the Element panel that re-imports only the active Element from its source manifest entry.
- **Honor the 055 contract, scoped to one entry** - preserve painted weights / density on same-bounds, reproject from the sidecar on changed-bounds, touch no sibling Element.
- **Resolve the Element-to-entry mapping** - map the active Blender object back to its manifest layer, and define behavior when that layer is renamed, moved, or gone.

## Open decisions

### 1. Element-to-manifest-entry resolution at reimport time

**Code anchors:** `apps/blender/importers/photoshop/__init__.py` (`import_manifest` - iterates `manifest.layers`, dispatches each to `stamp_mesh` / `stamp_sprite`; the whole-manifest loop a single-Element path must factor out of; `_anchor_meshes_at_feet` builds `layer_by_name = {layer.name: layer for layer in manifest.layers}` - the same name-keyed lookup a single-Element reimport needs, including its fallback `.get(obj.name) or layer_by_name.get(...)`); `apps/blender/importers/photoshop/planes.py` (`stamp_mesh` / `stamp_sprite` and `_find_existing` - the per-entry re-stamp + find-by-tag reuse the single path calls); `apps/blender/panels/element.py` (`PROSCENIO_PT_element`, the per-kind subpanels `_draw_mesh` / `_draw_sprite` - where the reimport control lands); `apps/blender/core/validation/active_element.py` (active-Element resolution). Locked context: spec 055 re-import contract (`_index.md`, `decisions.md`); spec 037 storage-split (the `proscenio_*` idprops that identify an Element).

**Question:** Re-importing one Element means mapping the active Blender object back to exactly one manifest entry. Is that mapping by layer name (the existing `layer_by_name` key), by a stable stamped identity (a `proscenio_*` idprop / stable layer id), or by the find-by-tag the importer already uses for reuse? Name is what the code keys on today but breaks on rename; stable identity is robust but may not be stamped yet.

**Options:** (A) Reuse the name-keyed `layer_by_name` lookup (matches current behavior, breaks on layer rename). (B) Stamp and resolve by a stable layer id (robust to rename; depends on the gated `stable-layer-identity`). (C) Find-by-tag like `_find_existing`. (D) ...

**Recommendation:** TBD - lock during STUDY. Tension: name-keying ships now with no new stamping but silently fails a renamed layer; stable-id is correct but reaches into the gated `stable-layer-identity` ([gated.md](../gated.md) "Photoshop plugin"). Likely answer: name-key first with an explicit not-found warning, note stable-id as the later hardening.

**LOCKED (A, via the stamped origin):** resolve through the already-stamped `PROSCENIO_IMPORT_ORIGIN` idprop (`"psd:<layer>"`, strip the prefix) into `layer_by_name`, falling back to `obj.name` when the object carries no origin tag (a freshly-authored mesh adopted under the layer's name). This is name-keyed - it ships now with no new identity stamping and is robust to a Blender-side object rename (the stamp survives) - but a PSD-side layer rename misses and degrades to an explicit not-found warning (decision 2). Stable-id resolution stays the later hardening behind the gated `stable-layer-identity`. Mirrors the existing reverse lookup in `_anchor_meshes_at_feet` and the reuse key in `planes._find_existing`.

### 2. Behavior when the source layer changed, moved, or vanished

**Code anchors:** `apps/blender/importers/photoshop/__init__.py` (`ImportResult` with `.skipped` / warnings - the per-entry degrade-to-warning pattern spec 053 established); `apps/blender/importers/photoshop/planes.py` (`stamp_mesh` returning `None` on a skip); the changed-bounds reproject path from spec 055. Locked context: spec 053 import resilience (one rejected entry degrades to a per-entry warning, prior progress survives); spec 055 changed-bounds reprojection.

**Question:** The single source layer may have changed bounds (reproject weights per 055), been renamed (mapping miss per decision 1), or been deleted from the PSD entirely (no entry to re-stamp). What is the deterministic outcome in each case - reproject, warn-and-no-op, or offer a remap?

**Options:** (A) Same-bounds -> re-stamp preserving weights; changed-bounds -> reproject from sidecar; missing -> warn-and-no-op leaving the Element intact. (B) Add an explicit remap-to-different-layer affordance for the renamed case. (C) ...

**Recommendation:** TBD - lock during STUDY. Lean: (A) as the deterministic baseline (it is the 055 contract scoped to one entry plus the 053 warn-don't-destroy posture); a manual remap (B) is a later convenience, not the first cut.

**LOCKED (A):** the 055 contract scoped to one entry, inherited for free from `planes._ensure_mesh` (same-bounds short-circuits and keeps the mesh + weights + automesh density; changed-bounds rebuilds the quad and reprojects from the surviving `proscenio_weight_sidecar`); a layer that no longer resolves (renamed or deleted in the PSD) is a warn-and-no-op that leaves the Element fully intact (053 posture); a missing PNG for a resolved layer degrades to a per-entry skip warning. The single-Element path deliberately does NOT call `_anchor_meshes_at_feet` - that is a whole-figure Z-shift, and re-anchoring on one Element would move it relative to every untouched sibling, breaking the "touch no sibling" requirement. A manual remap (B) stays a later convenience.

### 3. Where the manifest path comes from for a single-Element reimport

**Code anchors:** `apps/blender/importers/photoshop/__init__.py` (`import_manifest` takes the loaded manifest; the operator that loads it from a chosen path); `apps/blender/panels/element.py` (the panel has the active object but not necessarily the originating manifest path). Locked context: spec 053 import path resolution and the busy-before-picker flow; spec 055 same-bounds re-import.

**Question:** The whole-manifest reimport starts from a file picker. A per-Element reimport from the Element panel needs the source manifest - is the originating manifest path stored on the object / scene at first import and reused silently, or does the per-Element reimport also prompt for the manifest?

**Options:** (A) Persist the manifest path at first import (scene or object idprop) and reuse it silently, prompt only if missing / stale. (B) Always prompt. (C) ...

**Recommendation:** TBD - lock during STUDY. Lean: (A) - a per-Element reimport should be one click, so the path should be remembered; falling back to a picker only when the stored path is gone matches the spec 053 stale-folder re-pick pattern.

**LOCKED (A, object-scoped):** stamp the absolute manifest source path on each imported object at first import via a new `PROSCENIO_IMPORT_MANIFEST` Custom Property; the per-Element reimport reads it off the active object and runs silently, falling back to the file picker only when the idprop is absent or the file is gone (the 053 stale-folder re-pick). Per-object rather than scene-level so two manifests imported into one scene each resolve their own source - the Element knows its own origin file the same way it already knows its origin layer (`PROSCENIO_IMPORT_ORIGIN`).

## Verdict summary

LOCKED 2026-06-24 - all three decisions resolved, all (A). The feature is additive and rides a settled contract: spec 055 defines what survives a re-import, so the work is scoping that contract to a single manifest entry and wiring the entry point into the Element panel. Decision 1: resolve the Element through its stamped `PROSCENIO_IMPORT_ORIGIN` (name-keyed, robust to a Blender-side rename, warn on a PSD-side rename), stable-id deferred to the gated `stable-layer-identity`. Decision 2: the 055 contract per entry, inherited from `planes._ensure_mesh` (same-bounds keep / changed-bounds reproject), warn-and-no-op on an unresolvable layer, and crucially NO `_anchor_meshes_at_feet` (a whole-figure shift would move the one Element relative to its untouched siblings). Decision 3: a new per-object `PROSCENIO_IMPORT_MANIFEST` idprop remembers the source path, reused silently with a picker fallback. Size M: a per-entry dispatch factored out of the manifest loop (shared by `import_manifest` and a new `reimport_element`), the manifest-path stamp, the Element-panel button + operator, and headless tests; clean reuse of `stamp_mesh` / `stamp_sprite` / `_find_existing` / `build_root_armature`. See [TODO.md](TODO.md).

## Sources

Builds on spec 055 (reimport-contract - what survives a re-import) and spec 053 (import resilience - per-entry warn-don't-destroy). Touches the gated `stable-layer-identity` ([gated.md](../gated.md) "Photoshop plugin") if decision 1 chooses stable-id resolution. No existing backlog entry - new pre-v1 scope.
