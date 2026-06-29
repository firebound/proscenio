# Dead code

Symbols with no live references, grep-verified repo-wide (apps/blender + repo-root tests/) including `__all__`, dynamic dispatch, and string lookups. Two are safe immediate deletes; the rest are wire-or-remove decisions for a STUDY. One phase-1 "dead" claim was refuted (`known_topic_ids` - see [refuted.md](refuted.md)).

## Safe deletes (quick wins)

- **rect-area-dead** `[low/trivial]` `[confirmed]` `[quick win]` - [atlas_packer.py:45-47](../../../apps/blender/core/atlas/atlas_packer.py#L45) - `Rect.area` property is never read anywhere. Fix: remove lines 45-47; keep `right`/`bottom` (used by the packer).
- **vertexpen-dragging-dead** `[low/trivial]` `[confirmed]` `[quick win]` - [vertex_pen.py:114-116](../../../apps/blender/core/bpy_helpers/automesh/vertex_pen.py#L114) - `VertexPen.dragging` property is never read; callers use `self._drag_index` directly. Fix: delete lines 114-116. (Phase-1 cited line 106 - the property is at 114-116.)
- **bpy-compat-dead-shims** `[low/trivial]` `[confirmed]` `[quick win]` - [_bpy_compat.py](../../../apps/blender/core/bpy_helpers/_shared/_bpy_compat.py) - `iter_action_layers` and `iter_action_strips` have zero call sites. Fix: delete both, or wire `iter_action_layers` into the animations writer if it was meant to be. (Cross-listed in [god-modules-and-srp.md](god-modules-and-srp.md).)

## Wire-or-remove decisions

- **hole-safety-dilate** `[low/trivial]` `[confirmed]` `DECIDIR (STUDY):` - [contour.py:46-50](../../../apps/blender/core/automesh/contour.py#L46) - `HOLE_SAFETY_DILATE_CELLS` is a deprecated, functionally-unused constant kept alive only by the `core/automesh/__init__.py` re-export + `__all__`; its docstring documents it as retained for backward compat of direct importers. Grep shows zero current importers of the symbol. Since this is an internal addon package (no external consumers), the safe action is removal: delete contour.py:46-50, the import (__init__.py:19), and the `__all__` entry (__init__.py:57) - no call site breaks. Keep one release if a deprecation window is wanted.
- **psd-naming-module-orphaned** `[low/small]` `[confirmed]` `DECIDIR (STUDY):` - [psd_naming.py:71](../../../apps/blender/core/psd/psd_naming.py#L71) (`is_uniform_indexed_group`) and [psd_naming.py:103](../../../apps/blender/core/psd/psd_naming.py#L103) (`group_by_index_suffix`) - both are tested-only public API with no production caller anywhere in apps/. The verification notes the **entire `psd_naming` module is currently unconsumed by apps/**, so the decision likely applies module-wide. Fix: in the PSD-import STUDY, decide wire-or-remove - either wire `psd_naming` into the PSD import path that classifies indexed frame groups, or delete `psd_naming.py` + `tests/test_psd_naming.py`.
