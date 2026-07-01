# Dead code

Symbols with no live references, grep-verified repo-wide (apps/blender + repo-root tests/) including `__all__`, dynamic dispatch, and string lookups. One phase-1 "dead" claim was refuted (`known_topic_ids` - see [refuted.md](refuted.md)).

## Resolved (spec 074 Phase 3, PR #182)

The four safe deletes shipped: `Rect.area`, `VertexPen.dragging`, the two `_bpy_compat` shims (`iter_action_layers` / `iter_action_strips`), and `HOLE_SAFETY_DILATE_CELLS` (+ its `core/automesh/__init__.py` re-export) - all grep-confirmed zero callers, guarded by the existing suites.

## Open (-> spec 076 Phase D)

- **psd-naming-module-orphaned** `[low/small]` `[confirmed]` `DECIDIR (STUDY): resolved -> delete` - [psd_naming.py:71](../../../apps/blender/core/psd/psd_naming.py#L71) (`is_uniform_indexed_group`) and [psd_naming.py:103](../../../apps/blender/core/psd/psd_naming.py#L103) (`group_by_index_suffix`) - both are tested-only public API with no production caller anywhere in apps/; the **entire `psd_naming` module is unconsumed by apps/**. O2 resolved to delete: spritesheet frames are authored in Photoshop (`[spritesheet]` tag -> `planner.ts` -> explicit manifest `frames` list) and Blender consumes the manifest, so the Blender-side guess-from-layer-names module is the wrong layer. Delete `psd_naming.py` + `tests/test_psd_naming.py`. Owned by [spec 076](../../076-blender-audit-remainder/TODO.md) Phase D.
