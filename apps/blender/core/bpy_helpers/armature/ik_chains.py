"""Scan an armature's pose bones for Proscenio IK chains.

bpy-bound. The Skeleton panel surfaces IK chains two ways - a per-row marker on
a bone that is a chain tip or some chain's control, and an "IK chains" section
listing tip / chain length / control. Both read from this single scan over
``armature.pose.bones`` so the panel cannot drift from the rig: the constraint
is the only source of truth, never stored chain state.

The scan does attribute access only, so it is exercised with SimpleNamespace
fakes in ``tests/test_ik_chains.py`` without a live Blender.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import bpy

_IK_CONSTRAINT_NAME = "Proscenio IK"


@dataclass(frozen=True)
class IkChain:
    """One Proscenio IK chain as the panel shows it: tip bone, chain length, control."""

    tip: str
    chain_count: int
    control: str


@dataclass(frozen=True)
class IkChainScan:
    """Result of one pass over ``armature.pose.bones``.

    ``chains`` is the inventory (sorted by tip). ``_tips`` / ``_controls`` back
    the per-row predicates so a UIList draw_item is an O(1) set lookup rather
    than a re-scan per row.
    """

    chains: list[IkChain]
    _tips: frozenset[str] = field(default_factory=frozenset)
    _controls: frozenset[str] = field(default_factory=frozenset)

    def is_tip(self, bone_name: str) -> bool:
        """True when ``bone_name`` carries a ``Proscenio IK`` constraint."""
        return bone_name in self._tips

    def is_control(self, bone_name: str) -> bool:
        """True when ``bone_name`` is the control (subtarget) of some chain."""
        return bone_name in self._controls

    def __bool__(self) -> bool:
        return bool(self.chains)


def scan_ik_chains(armature_obj: bpy.types.Object) -> IkChainScan:
    """Collect every ``Proscenio IK`` chain on ``armature_obj``'s pose bones.

    Empty (rather than raising) when the object has no pose, so a panel draw in
    a mode without an evaluated pose stays safe.
    """
    pose = getattr(armature_obj, "pose", None)
    if pose is None:
        return IkChainScan(chains=[])

    chains: list[IkChain] = []
    tips: set[str] = set()
    controls: set[str] = set()
    for pose_bone in pose.bones:
        constraint = next((c for c in pose_bone.constraints if c.name == _IK_CONSTRAINT_NAME), None)
        if constraint is None:
            continue
        tips.add(pose_bone.name)
        subtarget = constraint.subtarget or ""
        if subtarget:
            controls.add(subtarget)
        chains.append(
            IkChain(
                tip=pose_bone.name,
                chain_count=int(constraint.chain_count),
                control=subtarget,
            )
        )

    chains.sort(key=lambda chain: chain.tip)
    return IkChainScan(chains=chains, _tips=frozenset(tips), _controls=frozenset(controls))
