"""Unit tests for action classification + Animation-panel dedup (spec 079 D2).

Pure pytest, no Blender. A slot swap authored as direct visibility keyframes
creates a visibility-only action (``hide_render`` / ``hide_viewport`` fcurves).
The Animation panel must dedup those against the same-named rig action so the
panel lists one row per exported animation, and ``set_active_action`` must refuse
to graft a visibility-only action onto the armature - both share the helpers
exercised here. Actions are duck-typed ``SimpleNamespace`` stubs exposing the
``fcurves`` / ``name`` the classifier reads.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.action_kind import (  # noqa: E402
    animation_representatives,
    is_visibility_only_action,
)


def _fcurve(data_path: str) -> SimpleNamespace:
    return SimpleNamespace(data_path=data_path)


def _action(name: str, *data_paths: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, fcurves=tuple(_fcurve(p) for p in data_paths))


def test_visibility_only_action_is_detected() -> None:
    action = _action("idle", "hide_render", "hide_viewport")
    assert is_visibility_only_action(action) is True


def test_action_with_bone_transform_is_not_visibility_only() -> None:
    action = _action("idle", 'pose.bones["root"].location', "hide_render")
    assert is_visibility_only_action(action) is False


def test_empty_action_is_not_visibility_only() -> None:
    # An action with no fcurves has nothing to graft or dedup on; treating it as
    # visibility-only would wrongly hide it from the rig panel.
    assert is_visibility_only_action(_action("empty")) is False


def test_dedup_collapses_same_named_rig_and_visibility_actions() -> None:
    actions = [
        _action("idle", 'pose.bones["root"].rotation_euler'),
        _action("idle", "hide_render", "hide_viewport"),
        _action("attack", 'pose.bones["arm"].location'),
    ]
    reps = animation_representatives(actions)
    # One representative per name: idle + attack.
    assert len(reps) == 2
    names = {actions[i].name for i in reps}
    assert names == {"idle", "attack"}


def test_dedup_prefers_the_rig_action_as_representative() -> None:
    # Visibility action first, rig action second: the rig datablock must win the
    # row so selecting it grafts a playable action, not a refused swap.
    actions = [
        _action("idle", "hide_render", "hide_viewport"),
        _action("idle", 'pose.bones["root"].rotation_euler'),
    ]
    reps = animation_representatives(actions)
    assert reps == {1}
    assert not is_visibility_only_action(actions[next(iter(reps))])


def test_dedup_keeps_a_lone_visibility_action() -> None:
    # A visibility-only swap with no rig action of that name still shows as its
    # own animation row.
    actions = [_action("swap_only", "hide_render", "hide_viewport")]
    assert animation_representatives(actions) == {0}
