"""Pure-Python helpers for the Quick Armature operator.

bpy-free. Lives under ``core/`` so unit tests can exercise the
chord-resolution / axis-lock / grid-snap math without booting Blender.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, TypeAlias

from .._shared.nearest import nearest_index

AxisLock: TypeAlias = Literal["X", "Z"] | None

DEFAULT_NAME_PREFIX = "qbone"

# Minimum head->tail world distance for a bone to be created. A release
# closer than this to the press point is rejected as a stray click
# ("bone too short, skipped"); the live preview also uses it to decide
# whether to surface the snapped-away press marker.
BONE_TOO_SHORT_TOLERANCE = 1e-4


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
    return "disconnected" if shift_held else "unparented"


def resolve_press_mode(
    *,
    shift_held: bool,
    alt_held: bool = False,
    default_chain: bool,
) -> tuple[bool, bool]:
    """Decide ``(parent_to_last, connect)`` for a left-mouse PRESS.

    ``default_chain=True``: no modifier chains the new bone connected
    to the previous tail; Shift starts a fresh unparented root; Alt
    gives a parented + disconnected bone (head free, parent set). When
    ``default_chain=False``, Shift means chain-disconnected.
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
    """Round X and Z to the nearest ``increment``; Y (picture plane) is left as-is.

    ``increment`` of zero or below is a no-op so callers can pass a
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


def resolve_pick(
    cursor_xz: tuple[float, float],
    tips: Sequence[tuple[str, tuple[float, float]]],
    radius: float,
) -> str | None:
    """Return the bone whose tail is nearest ``cursor_xz`` within ``radius``.

    ``tips`` pairs each candidate bone name with its tail projected to the
    Y=0 XZ plane (the picture-plane the whole modal commits to). Resolution
    is the pure :func:`nearest_index` scan, so the pick tolerance is whatever
    world ``radius`` the caller derived from a screen-constant pixel distance.

    Returns ``None`` when ``tips`` is empty or every tail lies beyond
    ``radius`` - the caller treats that as "no bone tip near cursor" and keeps
    the current parent (a miss is a no-op with feedback, never a silent state
    change). Ties keep the first-listed bone (``nearest_index`` uses strict
    ``<``).
    """
    points = [tail for _name, tail in tips]
    idx = nearest_index(cursor_xz, points, max_distance=radius)
    if idx < 0:
        return None
    return tips[idx][0]


def sanitize_prefix(raw: str | None) -> str:
    """Strip whitespace; empty string falls back to the default prefix."""
    cleaned = (raw or "").strip()
    return cleaned or DEFAULT_NAME_PREFIX


def format_bone_name(prefix: str, index: int) -> str:
    """Compose ``f'{prefix}.{index:03d}'`` with the convention's padding."""
    return f"{prefix}.{index:03d}"


# Bone drag-preview colors keyed by drag validity + parent-connection state.
PREVIEW_COLOR = (1.0, 0.6, 0.0, 0.9)  # connected (Blender modal-progress orange)
PREVIEW_COLOR_UNPARENTED = (0.4, 0.8, 1.0, 0.9)  # cyan = no parent
PREVIEW_COLOR_DISCONNECTED = (1.0, 0.85, 0.2, 0.9)  # yellow = parent + free head
PREVIEW_COLOR_INVALID = (0.9, 0.25, 0.25, 0.85)  # red = cursor off the canvas

Rgba: TypeAlias = tuple[float, float, float, float]
Point3: TypeAlias = tuple[float, float, float]


def preview_color_for(cursor_in_canvas: bool, press_mode: PressMode) -> Rgba:
    """Pick the bone drag-preview color from validity + parent-connection state.

    Off-canvas is invalid (red); otherwise the color encodes whether the bone
    would land unparented (cyan) or parent-connected / disconnected.
    """
    if not cursor_in_canvas:
        return PREVIEW_COLOR_INVALID
    if press_mode == "unparented":
        return PREVIEW_COLOR_UNPARENTED
    if press_mode == "disconnected":
        return PREVIEW_COLOR_DISCONNECTED
    return PREVIEW_COLOR


def axis_guideline_endpoints(
    head: Point3, axis: AxisLock, half_length: float
) -> tuple[Point3, Point3] | None:
    """Endpoints of the infinite-looking axis guideline through ``head``.

    Only X and Z lock (the authoring plane is Y=0), so the line extends
    +/- ``half_length`` along that axis; returns None for any other axis value.
    """
    if axis == "X":
        return (
            (head[0] - half_length, head[1], head[2]),
            (head[0] + half_length, head[1], head[2]),
        )
    if axis == "Z":
        return (
            (head[0], head[1], head[2] - half_length),
            (head[0], head[1], head[2] + half_length),
        )
    return None
