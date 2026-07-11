"""Classify an action by what it drives (spec 079).

A slot swap is now authored as direct visibility keyframes on attachment meshes
(``hide_render`` / ``hide_viewport``), which creates its own action datablock. The
Animation panel dedups those against the rig actions, and ``set_active_action``
must refuse to graft a pure-visibility action onto the armature - both need to
tell a visibility-only action apart from a rig (bone-transform) action. This is
the single home for that test.

Duck-typed (plain ``getattr`` / iteration through :func:`action_fcurves`, no
``bpy``) so the panel + operator logic stays importable without Blender and the
pytest suite can drive it with ``SimpleNamespace`` stubs.
"""

from __future__ import annotations

from collections.abc import Sequence

from .action_fcurves import action_fcurves

# The two data paths a visibility swap keys (spec 079 R1). A slotted 4.4+ action
# that co-locates the rig's bone tracks alongside these is NOT visibility-only -
# it carries bone transforms too, so grafting it onto the armature is valid.
_VISIBILITY_PATHS = frozenset({"hide_render", "hide_viewport"})


def is_visibility_only_action(action: object) -> bool:
    """True when every fcurve on ``action`` drives object visibility only.

    A visibility-only action carries at least one fcurve and every fcurve's data
    path is ``hide_render`` or ``hide_viewport`` - the shape a slot swap keyed
    with no rig animation to co-locate into takes (spec 079). An action with no
    fcurves is not visibility-only: there is nothing to graft or dedup on, and
    treating an empty action as visibility-only would wrongly hide it from the
    rig panel.

    Reads through :func:`action_fcurves`, so a 4.4+ slotted action that
    co-locates bone-transform tracks with visibility tracks reads as NOT
    visibility-only (it has bone curves), which is the correct rig classification.
    """
    seen = False
    for fcurve in action_fcurves(action):
        path = str(getattr(fcurve, "data_path", ""))
        if path not in _VISIBILITY_PATHS:
            return False
        seen = True
    return seen


def animation_representatives(actions: Sequence[object]) -> set[int]:
    """Indices of the one action datablock to show per exported animation name.

    The writer emits one Godot animation per action NAME and merges by name, so
    ``idle`` composed of a rig action plus a per-mesh visibility action is one
    exported animation, not two (spec 079 D2). This keeps a single index per name
    and prefers a rig (bone-transform) datablock as the representative, so
    selecting that row assigns a playable action to the armature rather than a
    visibility-only swap ``set_active_action`` would refuse.

    Duck-typed over ``actions`` (only ``.name`` is read, plus the fcurve shape
    :func:`is_visibility_only_action` needs) so the Animation panel + the pytest
    suite share one implementation.
    """
    best_by_name: dict[str, int] = {}
    for index, action in enumerate(actions):
        name = str(getattr(action, "name", ""))
        current = best_by_name.get(name)
        if current is None:
            best_by_name[name] = index
            continue
        # A rig action wins the row over a same-named visibility-only swap.
        if is_visibility_only_action(actions[current]) and not is_visibility_only_action(action):
            best_by_name[name] = index
    return set(best_by_name.values())
