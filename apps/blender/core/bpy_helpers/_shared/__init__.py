"""Cross-cutting bpy-bound infrastructure shared across systems.

The bpy-bound counterparts to ``core._shared``: viewport math, modal overlay
drawing, selection helpers, and the bpy iteration shims. Modules here import
``bpy`` at module top, unlike the bpy-free ``core._shared``.
"""
