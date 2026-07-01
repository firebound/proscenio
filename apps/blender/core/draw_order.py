"""Draw-order -> viewport Y layout math (pure, bpy-free)."""

from __future__ import annotations


def y_location_from_draw_order(order: int, spacing: float) -> float:
    """Viewport Y offset that fans a stacked plane apart by its draw order.

    The integer draw order is authoritative (the writer negates it into
    ``z_index``); this Y offset only spreads stacked planes so they do not
    z-fight in the viewport and never affects the export. Isolated from the
    bpy-bound ``set=`` callback (which supplies ``spacing`` from the addon
    preference and reads ``bpy.context``) so the math is unit-testable without
    Blender.
    """
    return order * spacing
