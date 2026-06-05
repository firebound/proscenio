"""Cross-cutting infrastructure shared across Blender addon systems.

Modules here belong to no single system: the Custom Property key registry,
the report helper, typed property access, viewport state, geometry math, and
similar plumbing pulled by operators, panels, properties, and exporters alike.
The leading underscore sorts the package above the per-system folders. These
are bpy-free at module top, like every direct child of ``core``; callers
import the submodules directly, e.g. ``from ...core._shared import cp_keys``.
"""
