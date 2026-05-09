"""Proscenio core helpers (SPEC 009 wave 9.6 split).

This package hosts the small, focused modules the operators / panels /
writer share. The contract is:

- Direct children of ``core/`` are bpy-free (or import bpy lazily
  inside one function and accept ``Any``-typed inputs from tests).
  Pytest can exercise them with ``SimpleNamespace`` mocks.
- ``core/bpy_helpers/`` hosts every module that imports ``bpy`` at the
  module top. Tests that touch these patch ``bpy`` first, or skip
  when running outside Blender.
- ``core/validation/`` is a subpackage of bpy-free validators (SPEC
  009 wave 9.5).

Top-level modules (bpy-free):

- ``cp_keys.py``         Custom Property string constants registry
- ``feature_status.py``  Feature-readiness dispatch table (5.1.d.5)
- ``help_topics.py``     In-panel help topic registry (5.1.d.5)
- ``hydrate.py``         CP -> PG hydration logic
- ``mirror.py``          PG -> CP mirror logic
- ``pg_cp_fallback.py``  PG-first / CP-fallback reader
- ``props_access.py``    typed accessors for scene/object PGs
- ``psd_manifest.py``    Photoshop manifest dataclass + reader
- ``psd_naming.py``      PSD layer-name parsing
- ``region.py``          texture region resolver
- ``report.py``          operator report helpers (Proscenio: prefix)
- ``slot_emit.py``       slot dict projection
- ``uv_bounds.py``       UV-bounds rect computation
- ``atlas_packer.py``    pure-Python MaxRects packer

Subpackages:

- ``bpy_helpers/``  bpy-bound helpers (atlas_io, psd_spritesheet,
                    sprite_frame_shader, select, viewport_math)
- ``validation/``   per-validator submodules (active_sprite,
                    active_slot, export, issue, _shared)

Adding new code: pick the subdirectory by its bpy dependency. A pure
Python helper goes at the top level. A helper that calls
``bpy.data`` / ``bpy.ops`` / etc. goes under ``bpy_helpers/``.
"""
