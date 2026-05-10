"""Generate slot_swap PNG layers (Pillow only).

Run with::

    py scripts/fixtures/slot_swap/draw_layers.py

Pure Python -- no Blender required. Produces:

- ``examples/slot_swap/pillow_layers/arm.png``    16x32 -- pseudo-arm
- ``examples/slot_swap/pillow_layers/axe.png``    32x32 -- axe attachment
- ``examples/slot_swap/pillow_layers/sword.png``  32x32 -- sword attachment

Each attachment is a separate PNG (no spritesheet) -- the slot system
swaps **discrete meshes**, not cells of a shared texture. Visual style
is intentionally minimal pixel-art so the diff between attachments
during a swap is unambiguous in CI screenshots.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
LAYERS_DIR = REPO_ROOT / "examples" / "slot_swap" / "pillow_layers"

ARM_W = 16
ARM_H = 32
WEAPON_W = 32
WEAPON_H = 32

# Solid pixel-art swatches.
SKIN = (0.85, 0.65, 0.50, 1.0)
SKIN_OUTLINE = (0.20, 0.10, 0.05, 1.0)

WOOD = (0.40, 0.25, 0.10, 1.0)
WOOD_DARK = (0.25, 0.15, 0.05, 1.0)
STEEL = (0.80, 0.80, 0.85, 1.0)
STEEL_DARK = (0.50, 0.50, 0.55, 1.0)
GOLD = (0.90, 0.75, 0.20, 1.0)
GOLD_DARK = (0.55, 0.45, 0.10, 1.0)
OUTLINE = (0.05, 0.05, 0.05, 1.0)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _draw_arm()
    _draw_axe()
    _draw_sword()
    print(f"[draw_slot_swap] wrote 3 attachments under {LAYERS_DIR}")


def _draw_arm() -> None:
    """Tall thin pixel-art arm: skin fill + dark outline."""
    canvas = Canvas.empty(ARM_W, ARM_H)
    rect(canvas, 0, 0, ARM_W, ARM_H, OUTLINE)
    rect(canvas, 1, 1, ARM_W - 2, ARM_H - 2, SKIN_OUTLINE)
    rect(canvas, 2, 2, ARM_W - 4, ARM_H - 4, SKIN)
    canvas.save(LAYERS_DIR / "arm.png")


def _draw_axe() -> None:
    """Single-bladed axe: vertical wood handle with steel head on the right."""
    canvas = Canvas.empty(WEAPON_W, WEAPON_H)

    # Wood handle (vertical center column).
    handle_x = 14
    rect(canvas, handle_x, 4, 4, WEAPON_H - 8, OUTLINE)
    rect(canvas, handle_x + 1, 5, 2, WEAPON_H - 10, WOOD)
    rect(canvas, handle_x + 1, 5, 1, WEAPON_H - 10, WOOD_DARK)

    # Pommel ring at top + bottom.
    rect(canvas, handle_x - 1, 3, 6, 2, OUTLINE)
    rect(canvas, handle_x, 4, 4, 1, STEEL)
    rect(canvas, handle_x - 1, WEAPON_H - 5, 6, 2, OUTLINE)
    rect(canvas, handle_x, WEAPON_H - 4, 4, 1, STEEL)

    # Axe head: trapezoid bulge to the right of the handle.
    head_x0 = handle_x + 4
    rect(canvas, head_x0, 8, 12, 16, OUTLINE)
    rect(canvas, head_x0, 10, 10, 12, STEEL)
    rect(canvas, head_x0, 10, 10, 1, STEEL_DARK)


    canvas.save(LAYERS_DIR / "axe.png")


def _draw_sword() -> None:
    """Straight sword: tall steel blade with gold cross-guard, pointing up."""
    canvas = Canvas.empty(WEAPON_W, WEAPON_H)

    # Blade (vertical center column, 4 wide).
    blade_x = 14
    rect(canvas, blade_x, 1, 4, 22, OUTLINE)
    rect(canvas, blade_x + 1, 2, 2, 20, STEEL)
    rect(canvas, blade_x + 1, 2, 1, 20, STEEL_DARK)

    # Pointed tip.
    rect(canvas, blade_x + 1, 0, 2, 2, OUTLINE)

    # Cross-guard (wide horizontal gold bar at y=22).
    rect(canvas, blade_x - 5, 22, 14, 3, OUTLINE)
    rect(canvas, blade_x - 4, 23, 12, 1, GOLD)
    rect(canvas, blade_x - 4, 23, 12, 1, GOLD_DARK)

    # Grip (short vertical wood column).
    rect(canvas, blade_x, 25, 4, 5, OUTLINE)
    rect(canvas, blade_x + 1, 26, 2, 3, WOOD)

    # Pommel.
    rect(canvas, blade_x - 1, 30, 6, 2, OUTLINE)
    rect(canvas, blade_x, 31, 4, 1, GOLD)

    canvas.save(LAYERS_DIR / "sword.png")


if __name__ == "__main__":
    main()
