"""Generate slot_swap PNG layers (Pillow only).

Run with::

    py scripts/fixtures/slot_swap/draw_layers.py

Pure Python -- no Blender required. Produces:

- ``examples/slot_swap/pillow_layers/arm.png``    32x8  -- horizontal forearm
- ``examples/slot_swap/pillow_layers/club.png``   32x32 -- club attachment
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

ARM_W = 32
ARM_H = 8
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
    _draw_club()
    _draw_sword()
    print(f"[draw_slot_swap] wrote 3 attachments under {LAYERS_DIR}")


def _draw_arm() -> None:
    """Horizontal pixel-art arm: skin rectangle + dark outline.

    32 px wide x 16 px tall -- a forearm extending sideways from the
    body. The slot Empty sits at the bone tip (right side after the
    swing rotation) so the weapon attachment naturally comes out of
    the wrist.
    """
    canvas = Canvas.empty(ARM_W, ARM_H)
    rect(canvas, 0, 0, ARM_W, ARM_H, OUTLINE)
    rect(canvas, 1, 1, ARM_W - 2, ARM_H - 2, SKIN_OUTLINE)
    rect(canvas, 2, 2, ARM_W - 4, ARM_H - 4, SKIN)
    canvas.save(LAYERS_DIR / "arm.png")


def _draw_club() -> None:
    """Upright wooden club: thicker head on top, narrower grip below.

    Two solid wood rectangles stacked: the head (broader) and the
    grip (narrower). Same vertical layout as the sword so both
    attachments read as 'weapon held upright'. Coordinate system has
    Y=0 at the TOP.

    - Y 0..18   club head: 14 px wide brown rectangle with outline,
                slightly darker shading on the left edge.
    - Y 18..29  grip: 6 px wide brown column.
    - Y 29..32  pommel cap.
    """
    canvas = Canvas.empty(WEAPON_W, WEAPON_H)

    # Club head (top, broader).
    head_x = 9
    head_w = 14
    head_y = 1
    head_h = 17
    rect(canvas, head_x - 1, head_y - 1, head_w + 2, head_h + 2, OUTLINE)
    rect(canvas, head_x, head_y, head_w, head_h, WOOD)
    rect(canvas, head_x, head_y, 2, head_h, WOOD_DARK)

    # Grip (narrower, below head).
    grip_x = 13
    grip_w = 6
    grip_y = 18
    grip_h = 11
    rect(canvas, grip_x - 1, grip_y, grip_w + 2, grip_h, OUTLINE)
    rect(canvas, grip_x, grip_y, grip_w, grip_h, WOOD)
    rect(canvas, grip_x, grip_y, 1, grip_h, WOOD_DARK)

    # Pommel cap (small steel ring at the very bottom).
    rect(canvas, grip_x - 2, 28, grip_w + 4, 4, OUTLINE)
    rect(canvas, grip_x - 1, 29, grip_w + 2, 2, STEEL)
    rect(canvas, grip_x - 1, 29, grip_w + 2, 1, STEEL_DARK)

    canvas.save(LAYERS_DIR / "club.png")


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
