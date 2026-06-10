"""bpy-bound selection helpers.

Replaces the 5+ inline copies of the deselect-all-then-select-one
idiom across operators (select_issue_object, select_outliner_object,
create_ortho_camera, reproject_sprite_uv, create_slot, etc).

Lives in ``core/`` for now; will move to ``core/bpy_helpers/`` once
the code-modularity split lands. The bpy import here is intentional and acknowledged
via the file docstring rather than the package-level "bpy-free"
contract.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator

import bpy

from ..._shared.report import report_warn


def select_only(context: bpy.types.Context, obj: bpy.types.Object) -> None:
    """Deselect everything in the scene, then select + activate ``obj``.

    Mirrors the pattern Blender's UI uses for Outliner-driven
    activation: a single click selects exactly one object and makes it
    active. Suitable for operator paths that want the post-selection
    state to be unambiguous (the selected object is always the active
    one).
    """
    for other in context.scene.objects:
        other.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj


def restore_selection(
    context: bpy.types.Context,
    prior_selected_names: list[str],
    prior_active: bpy.types.Object | None,
) -> None:
    """Restore a captured selection: deselect the current selection, reselect
    ``prior_selected_names`` by name, then restore ``prior_active``.

    Each step suppresses the ``RuntimeError`` / ``ReferenceError`` a stale
    (undo-recreated or deleted) datablock raises, so a partial restore never
    aborts a modal operator's ``finally`` cleanup. Object lookups go by name
    so undo-driven recreation does not strand the restore on a dead pointer.
    """
    for obj in list(context.selected_objects):
        with contextlib.suppress(RuntimeError, ReferenceError):
            obj.select_set(False)
    for name in prior_selected_names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            with contextlib.suppress(RuntimeError):
                obj.select_set(True)
    if prior_active is not None:
        with contextlib.suppress(RuntimeError, ReferenceError):
            context.view_layer.objects.active = prior_active


@contextlib.contextmanager
def preserve_selection(context: bpy.types.Context) -> Iterator[None]:
    """Snapshot the current selection + active object, restore on exit.

    Captures the selected object names + the active object on entry and
    restores them via :func:`restore_selection` when the block exits, even
    if the body raises. Selection is captured by name so undo-driven
    recreation inside the body does not strand the restore on a dead
    datablock. Wrap an operator step that has to commandeer the selection
    (``parent_set``, a mode toggle, a ``bpy.ops`` call) and hand it back
    untouched.
    """
    prior_selected_names = [obj.name for obj in context.selected_objects]
    prior_active = context.view_layer.objects.active
    try:
        yield
    finally:
        restore_selection(context, prior_selected_names, prior_active)


def select_named_or_warn(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    name: str,
    *,
    not_found_message: str | None = None,
    predicate: Callable[[bpy.types.Object], bool] | None = None,
) -> bpy.types.Object | None:
    """Look up ``name`` in ``bpy.data.objects`` and make it the sole selection.

    Returns the object after selecting + activating it via
    :func:`select_only`, or ``None`` after reporting a warning when the
    name is absent (or ``predicate`` rejects the match - evaluated before
    anything is selected, so a rejected object is never selected).

    ``not_found_message`` overrides the default ``object '<name>' not
    found`` so slot / issue callers phrase the miss in their own terms.
    ``predicate`` adds a type / flag gate (e.g. the slot-Empty check);
    it is only called when the object exists.

    The empty-``name`` short-circuit is left to callers: some want a
    distinct message, some stay silent, and ``bpy.data.objects.get("")``
    already returns ``None`` here regardless.
    """
    obj = bpy.data.objects.get(name)
    if obj is None or (predicate is not None and not predicate(obj)):
        report_warn(operator, not_found_message or f"object '{name}' not found")
        return None
    select_only(context, obj)
    return obj
