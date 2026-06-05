"""Proscenio core helpers.

This package hosts the small, focused modules the operators / panels /
writer share. The contract is:

- Direct children of ``core/`` are bpy-free (or import bpy lazily
  inside one function and accept ``Any``-typed inputs from tests).
  Pytest can exercise them with ``SimpleNamespace`` mocks.
- ``core/bpy_helpers/`` hosts every module that imports ``bpy`` at the
  module top. Tests that touch these patch ``bpy`` first, or skip
  when running outside Blender.
- ``core/validation/`` is a subpackage of bpy-free validators.

Top-level modules (bpy-free, single-file features not yet grouped):

- ``help_topics.py``       In-panel help topic registry
- ``mirror.py``            PG -> CP mirror logic
- ``uv_bounds.py``         UV-bounds rect computation

Subpackages:

- ``_shared/``      cross-cutting infra (cp_keys, report, props_access,
                    pg_cp_fallback, feature_status, hydrate, geometry_2d,
                    region, viewport_state, modal_overlay_geometry)
- ``armature/``     quick-armature math + target resolver
- ``atlas/``        pure MaxRects packer (``atlas_packer``)
- ``psd/``          PSD manifest reader + layer-name parsing
- ``slot/``         pure slot[] projection (``slot_emit``)
- ``sprite_frame/`` pure UV-cell math (``sprite_frame_math``)
- ``automesh/`` / ``skinning/`` / ``validation/``  per-feature domain packages
- ``bpy_helpers/``  bpy-bound helpers (``_shared/``, ``atlas/``, ``psd/``,
                    ``automesh/``, ``skinning/``, ``sprite_frame/``)

Adding new code: pick the subdirectory by its bpy dependency. A pure
Python helper goes at the top level. A helper that calls
``bpy.data`` / ``bpy.ops`` / etc. goes under ``bpy_helpers/``.
"""
