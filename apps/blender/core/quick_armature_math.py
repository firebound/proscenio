"""Pure-Python helpers for the Quick Armature operator (SPEC 012.2).

bpy-free. Lives under ``core/`` so unit tests can exercise the
chord-resolution / axis-lock / grid-snap math without booting
Blender. The operator imports these from
``apps/blender/operators/quick_armature.py``.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

AxisLock: TypeAlias = Literal["X", "Z"] | None

DEFAULT_NAME_PREFIX = "qbone"


PressMode = Literal["connected", "unparented", "disconnected"]


def resolve_press_mode_label(
    *,
    shift_held: bool,
    alt_held: bool,
    default_chain: bool,
) -> PressMode:
    """Return the press-time chord category as a Blender-aligned label.

    ``connected`` = parented + ``use_connect=True`` (head snaps to the
    parent's tail; Blender E extrude convention).
    ``unparented`` = bone has no parent at all.
    ``disconnected`` = parented + ``use_connect=False`` (head stays
    where the user pressed; useful for branching chains starting at
    an offset from the tip).

    ``alt_held`` always means disconnected, regardless of
    ``default_chain``. ``shift_held`` flips the no-modifier vocabulary
    between connected and unparented per ``default_chain``.
    """
    if alt_held:
        return "disconnected"
    if default_chain:
        return "unparented" if shift_held else "connected"
    # Legacy SPEC 012.1 vocabulary: no modifier = unparented root,
    # Shift = parented but disconnected (head free, parent set).
    return "disconnected" if shift_held else "unparented"


def resolve_press_mode(
    *,
    shift_held: bool,
    alt_held: bool = False,
    default_chain: bool,
) -> tuple[bool, bool]:
    """Decide ``(parent_to_last, connect)`` for a left-mouse PRESS.

    ``default_chain=True`` (D10 recommendation) matches Blender's E
    extrude reflex: no modifier chains the new bone connected to the
    previous tail; Shift starts a fresh unparented root. Hold Alt for
    a parented + disconnected bone (head free, parent set). When
    ``default_chain=False`` the SPEC 012.1 vocabulary applies and
    Shift means chain-disconnected.
    """
    label = resolve_press_mode_label(
        shift_held=shift_held, alt_held=alt_held, default_chain=default_chain
    )
    if label == "connected":
        return (True, True)
    if label == "disconnected":
        return (True, False)
    return (False, False)


def snap_world_point_xz(
    point: tuple[float, float, float],
    increment: float,
) -> tuple[float, float, float]:
    """Round X and Z to the nearest ``increment``; Y is unchanged.

    Y is the picture-plane axis (Y=0 by Proscenio contract); rounding
    it would amplify floating-point noise without UX gain. ``increment``
    of zero or below is treated as a no-op so callers can pass a
    snap_increment field directly without guarding.
    """
    if increment <= 0.0:
        return point
    return (
        round(point[0] / increment) * increment,
        point[1],
        round(point[2] / increment) * increment,
    )


def apply_axis_lock(
    head: tuple[float, float, float],
    tail: tuple[float, float, float],
    axis: AxisLock,
) -> tuple[float, float, float]:
    """Clamp the non-locked component of ``tail`` to match ``head``.

    Locking ``X`` keeps tail X free and forces Y / Z to head's values
    so the bone runs purely along the X axis. Locking ``Z`` mirrors
    that for the vertical axis. ``None`` is a no-op.
    """
    if axis == "X":
        return (tail[0], head[1], head[2])
    if axis == "Z":
        return (head[0], head[1], tail[2])
    return tail


def sanitize_prefix(raw: str | None) -> str:
    """Strip whitespace; empty string falls back to the default prefix."""
    cleaned = (raw or "").strip()
    return cleaned or DEFAULT_NAME_PREFIX


def format_bone_name(prefix: str, index: int) -> str:
    """Compose ``f'{prefix}.{index:03d}'`` with the convention's padding."""
    return f"{prefix}.{index:03d}"
