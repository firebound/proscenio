"""Unit tests for the IK chain scan that drives the Skeleton panel cues.

Pure pytest - ik_chains imports bpy at module top (the bpy_helpers contract),
so a MagicMock stands in before the import, the same way
``tests/test_slot_bone_follow.py`` does. The scan does attribute access only, so
SimpleNamespace mocks exercise the logic without Blender.

The constraint is the single source of truth (no stored chain state): a row
marker reads "is this bone a chain tip or some chain's control", and the
chains list reads tip / chain_count / control off each ``Proscenio IK``
constraint.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

# ik_chains does a top-level ``import bpy``; stub it before importing.
sys.modules["bpy"] = MagicMock()

from pathlib import Path  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.armature.ik_chains import (  # noqa: E402
    IkChain,
    IkChainScan,
    scan_ik_chains,
)


def _constraint(
    name: str, subtarget: str = "", chain_count: int = 2
) -> SimpleNamespace:
    return SimpleNamespace(name=name, subtarget=subtarget, chain_count=chain_count)


def _pose_bone(
    name: str, constraints: list[SimpleNamespace] | None = None
) -> SimpleNamespace:
    return SimpleNamespace(name=name, constraints=constraints or [])


def _armature(pose_bones: list[SimpleNamespace]) -> SimpleNamespace:
    pose = SimpleNamespace(bones=pose_bones)
    return SimpleNamespace(pose=pose)


def test_scan_finds_a_chain_keyed_by_tip() -> None:
    tip = _pose_bone(
        "hand", [_constraint("Proscenio IK", subtarget="hand.IK", chain_count=3)]
    )
    control = _pose_bone("hand.IK")
    scan = scan_ik_chains(_armature([tip, control]))
    assert scan.chains == [IkChain(tip="hand", chain_count=3, control="hand.IK")]


def test_scan_marks_tip_and_control_bones() -> None:
    tip = _pose_bone("hand", [_constraint("Proscenio IK", subtarget="hand.IK")])
    control = _pose_bone("hand.IK")
    plain = _pose_bone("spine")
    scan = scan_ik_chains(_armature([tip, control, plain]))
    assert scan.is_tip("hand") is True
    assert scan.is_tip("hand.IK") is False
    assert scan.is_control("hand.IK") is True
    assert scan.is_control("hand") is False
    assert scan.is_tip("spine") is False
    assert scan.is_control("spine") is False


def test_scan_ignores_non_proscenio_constraints() -> None:
    # A hand-added IK constraint (different name) is not a Proscenio chain.
    tip = _pose_bone(
        "hand", [_constraint("IK", subtarget="other"), _constraint("Copy Location")]
    )
    scan = scan_ik_chains(_armature([tip]))
    assert scan.chains == []
    assert scan.is_tip("hand") is False


def test_scan_handles_empty_subtarget() -> None:
    # A Proscenio IK whose control was deleted by hand: still a chain (tip known),
    # but nothing is marked as its control.
    tip = _pose_bone("hand", [_constraint("Proscenio IK", subtarget="")])
    scan = scan_ik_chains(_armature([tip]))
    assert scan.chains == [IkChain(tip="hand", chain_count=2, control="")]
    assert scan.is_control("") is False


def test_scan_sorts_chains_by_tip_name() -> None:
    a = _pose_bone("zeta", [_constraint("Proscenio IK", subtarget="zeta.IK")])
    b = _pose_bone("alpha", [_constraint("Proscenio IK", subtarget="alpha.IK")])
    scan = scan_ik_chains(_armature([a, b]))
    assert [c.tip for c in scan.chains] == ["alpha", "zeta"]


def test_scan_of_armature_without_pose_is_empty() -> None:
    # An armature in a mode with no pose (or a bad handle) yields an empty scan
    # rather than raising in the panel draw.
    scan = scan_ik_chains(SimpleNamespace(pose=None))
    assert scan == IkChainScan(chains=[], _tips=frozenset(), _controls=frozenset())
    assert scan.chains == []
