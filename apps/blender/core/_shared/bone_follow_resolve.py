"""Pure bone-follow binding resolution (constraint-first, spec 080).

The Proscenio Child Of constraint IS the binding (D5): its ``target`` /
``subtarget`` serialize inside the .blend and read headless with no addon
registered, so the writer, the validators, and the panels all resolve the
followed bone from the constraint first and fall back to the legacy shapes
(the ``slot_bone`` field for slots, a real ``parent_type == "BONE"`` parent
for both kinds). bpy-free: walks plain attributes so pure pytest fakes and
live bpy objects read identically.
"""

from __future__ import annotations

# One home for the constraint names both authoring wrappers use. Distinct per
# kind so shape detection stays per-kind while the machinery is shared; the
# slot name predates spec 080 and is kept to avoid churning existing files.
SLOT_FOLLOW_CONSTRAINT = "Proscenio Slot Follow"
ELEMENT_FOLLOW_CONSTRAINT = "Proscenio Sprite Follow"


def follow_subtarget(obj: object, constraint_name: str) -> str:
    """The bone the named Proscenio follow constraint targets, or "".

    Matches by constraint name AND type (a user re-purposing the name on a
    different constraint kind is not a binding). Iterates rather than using
    ``constraints.get`` so plain-sequence test fakes resolve the same way a
    live ``Object.constraints`` collection does.
    """
    constraints = getattr(obj, "constraints", None)
    if constraints is None:
        return ""
    for con in constraints:
        if getattr(con, "name", "") != constraint_name:
            continue
        if getattr(con, "type", "") != "CHILD_OF":
            return ""
        return str(getattr(con, "subtarget", ""))
    return ""


def bone_parent_name(obj: object) -> str:
    """The bone a real ``parent_type == "BONE"`` parent targets, or ""."""
    if getattr(obj, "parent_type", "") != "BONE":
        return ""
    return str(getattr(obj, "parent_bone", ""))
