"""Facade: the atlas manifest parser moved to the pure ``core/atlas`` home.

Re-exports ``Placement`` + ``read_manifest`` so the bpy-bound atlas-pack
operators keep importing them from here while the parser itself is bpy-free.
"""

from __future__ import annotations

from ...atlas.atlas_manifest import Placement, read_manifest

__all__ = ["Placement", "read_manifest"]
