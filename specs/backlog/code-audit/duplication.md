# Duplication (DRY)

Genuine copy-pasted/near-identical logic confirmed by reading the actual function bodies (token-level, not name matching). Phase 1's name-based digest found 2 clusters; the phase-2 body-comparison sweep found 13 more.

## Resolved (spec 074 Phase 3, PR #182)

Fourteen of the fifteen DRY clusters folded, each behind a green guard (goldens stayed byte-identical): `automesh-modal-preamble` (shared `_authoring_preconditions`), `topology-hash-call` (`topology_hash_of`), `writer-rotate-vec2` (`rotate_vec2` in `core/godot_export_math`), `writer-action-length` (`action_length`), `point-to-segment-projection` (`_closest_point_on_segment`), `material-image-node-walk` (routed through `iter_material_image_nodes`), `handlers-sync-index-to-active` (`_sync_index_to_active` + the fast-path guard), `selection-mode-snapshot-dup` (`SelectionModeSnapshot.capture`), `modal-session-skinning-chain` (`scene_skinning`), `tag-redraw-wrapper-dup` (`tag_redraw_view3d_statusbar`), `picture-plane-warning-box` (`draw_picture_plane_warning`), and `writer-image-abspath` (`image_abspath`).

## Open (-> spec 076 Phase B, rides `arc-length-resample-quadratic`)

- **perimeter-length-dup** `[low]` - [geometry.py:76](../../../apps/blender/core/automesh/geometry.py#L76) + [geometry.py:155](../../../apps/blender/core/automesh/geometry.py#L155) - `perimeter_length` and `edge_index_start_distance` share the same cyclic edge-length summation; the latter is just the former with the upper bound capped. Fix: make `_partial_perimeter(contour, end=None)` the general form; both become thin callers. Dissolves when [spec 076](../../076-blender-audit-remainder/TODO.md) Phase B's `arc-length-resample-quadratic` deletes `edge_index_start_distance` (carry `accumulated` incrementally instead).
