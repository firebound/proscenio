# Spec 078: Automesh dense-fill fix + front-ortho snap for the interactive tools

Two independent authoring-correctness fixes for the Blender addon's interactive tools, found while evaluating three reported issues. Both are behaviour fixes, no schema change.

1. **Automesh "Dense" collapses onto "Simple".** With the annulus enabled (`margin_pixels > 0`) the interior-mode toggle produces visually identical meshes.
2. **The interactive tools do not lock to Front Orthographic.** The meshes are 2D (no depth, authored on the Y=0 picture plane), so authoring from an orbited/perspective view is error-prone; only Quick Armature snaps to front ortho today.

## Problem 1: annulus makes Dense == Simple

The automesh builds an ANNULUS when `margin_pixels > 0`: an outer contour plus an inner contour that is the silhouette eroded inward by `margin_pixels` ([contour.py](../../apps/blender/core/automesh/contour.py) `extract_inner_contour`). Two things then conspire:

- The CDT auto-detects the inner ring as a HOLE via `output_type=2` (`CDT_INSIDE_WITH_HOLES`), so the interior of the inner ring is excluded from triangulation ([cdt.py:144-149](../../apps/blender/core/bpy_helpers/automesh/cdt.py#L144-L149), [cdt.py:181](../../apps/blender/core/bpy_helpers/automesh/cdt.py#L181)). The mesh becomes a literal ring with an empty centre.
- The Dense interior Steiner grid is clipped to *outside* the inner ring (`filter_inside_annulus`, [density.py:245-249](../../apps/blender/core/automesh/density.py#L245-L249)), because points inside the ring would otherwise be loose verts in that hole.

Net effect: Dense can only densify the thin `margin_px` perimeter band; the whole centre (the bulk of the mesh) has zero interior points in both Simple and Dense, so they look the same. At the default `margin_pixels = 0` there is no inner ring, so Dense fills the whole silhouette and the two modes do differ - the collapse is specific to the annulus being on.

The inner ring was only ever meant to add "extra edge-loop density at the silhouette for fine border deformation" ([scene_props.py:106-121](../../apps/blender/properties/scene_props.py#L106-L121)); carving it into a hole is the defect. A deformable 2D skin wants a FILLED mesh, not a ring; genuine ring sprites (a bracelet) are handled by real alpha holes (`hole_pixels`), which are separate from the eroded inner ring.

## Problem 2: interactive tools do not lock to front ortho

Survey of the four `modal_handler_add` tools: none requires front ortho, and only Quick Armature snaps to it (its `lock_to_front_ortho`, default ON, captures the view on invoke, snaps via `bpy.ops.view3d.view_axis`, and restores on exit unless the user orbited mid-modal - [view_session.py](../../apps/blender/core/bpy_helpers/armature/view_session.py), [quick_armature.py:243-246](../../apps/blender/operators/armature/quick_armature.py#L243-L246)). Automesh authoring, Manual Mesh, and Edit Weights neither require nor switch. The picture-plane math (`region_event_to_xz`) already projects to Y=0 from any angle, so this is a UX / correctness-of-intent fix, not a math fix: the artist should author on a flat front view by default.

## Decisions

| # | Question | Call |
| --- | --- | --- |
| D1 | Where to fix problem 1 | The automesh assembly (bridge + cdt), NOT the pure density module. `density.py`'s `inner` parameter means "a hole to exclude" and its contract + tests stay intact; the automesh simply stops feeding the eroded inner ring as that hole. |
| D2 | The two-line behaviour change | (a) The interior Steiner grid fills the whole silhouette: pass `inner=[]` to `interior_points_for_annulus` at both call sites ([bridge.py:585](../../apps/blender/core/bpy_helpers/automesh/bridge.py#L585), [authoring_pipeline.py:359](../../apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py#L359)), keeping the inner verts in the min-separation boundary. (b) The CDT stops carving the inner ring: `output_type = 2 if holes else 1` ([cdt.py:181](../../apps/blender/core/bpy_helpers/automesh/cdt.py#L181)). Real alpha holes still carve. |
| D3 | What the inner ring becomes | A border edge-density constraint loop (its stated purpose), not a hole. The centre is filled; Dense densifies the whole interior; Simple stays sparse-filled. `margin_pixels` keeps meaning "extra silhouette edge density"; its doc is corrected to drop "ring / excluded interior". |
| D4 | Front-ortho reuse | Reuse Quick Armature's `ViewSnapshot` rather than reinvent. Move it from `bpy_helpers/armature/` to `bpy_helpers/_shared/view_session.py` (with a per-tool log tag) and add a small `FrontOrthoModalMixin` there that owns the `_view` ClassVar, the `lock_to_front_ortho` property, and the capture/snap/restore lifecycle. |
| D5 | Which tools + default | Apply the mixin to Automesh authoring, Manual Mesh, and Edit Weights. Default ON: snap to front ortho on invoke, restore on exit. The mixin reuses Quick Armature's exact `lock_to_front_ortho` strings, so it adds no new i18n catalog entry. A per-tool opt-out toggle (PG field + panel checkbox) mirroring Quick Armature is deferred: the operator property (default True) already forces front ortho, matching the "only front ortho" intent; the interactive panel toggle is a fast-follow. |
| D6 | Quick Armature | Left functionally unchanged; only its `ViewSnapshot` import path moves to `_shared`. Folding it onto the shared mixin is a low-value follow-on, not done here (avoid churning a working tool). |

## Out of scope / follow-ons

- The third reported issue (leftover preview state cycling automesh <-> manual mesh with reverts) needs a repro disambiguation (Revert-to-Plane vs ESC/cancel) before a fix; tracked separately.
- Folding Quick Armature onto `FrontOrthoModalMixin` (dedup) - follow-on.
- A hard view-lock that prevents orbiting mid-modal (heavier) - not needed; the snap-on-entry default is enough.

## Sources

- Evaluation of the three interactive-tool issues in this session. The annulus mechanism is confirmed in [cdt.py](../../apps/blender/core/bpy_helpers/automesh/cdt.py) + [density.py](../../apps/blender/core/automesh/density.py); the front-ortho survey in the four modal operators under [operators/](../../apps/blender/operators).
- Front-ortho snap precedent: Quick Armature ([view_session.py](../../apps/blender/core/bpy_helpers/armature/view_session.py), spec 012 / 045 lock-to-front-ortho).
