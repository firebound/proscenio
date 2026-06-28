"""Bone export-gate predicate: is a bone emitted to the Godot document?

Bpy-free. Reads only duck-typed bone attributes (``use_deform`` and the
Proscenio per-bone ``exclude_from_export`` flag), so the Godot writer, the
export validator, and the Skeleton panel's "won't export" cue all read one
definition instead of re-deriving the rule.

Two reasons a bone stays out of the export:

- ``use_deform`` is off - a control/scaffolding bone (the ``.IK`` / ``.pole``
  goals the IK authoring creates with ``use_deform=False``). The deform
  skeleton Godot skins with never carries these.
- the rigger marked it ``exclude_from_export`` - a rig helper that only makes
  sense in Blender (a Drive-from-Bone source bone, a tweak handle), which the
  user pins off the export with the bone-list toggle even though it deforms.

A bone with no ``proscenio`` group (the addon's PropertyGroup unregistered, or
a pre-existing datablock) reads as not-excluded, so the gate degrades to the
plain ``use_deform`` rule the export used before this flag existed.
"""

from __future__ import annotations


def bone_is_exported(bone: object) -> bool:
    """True when ``bone`` should reach the exported Godot skeleton / animation.

    The single export gate: a bone exports when it deforms (``use_deform``) and
    the rigger has not pinned it off the export (``proscenio.exclude_from_export``).
    Duck-typed so the pure pytest suite can drive it with ``SimpleNamespace``.
    """
    if not getattr(bone, "use_deform", False):
        return False
    props = getattr(bone, "proscenio", None)
    return not bool(getattr(props, "exclude_from_export", False))
