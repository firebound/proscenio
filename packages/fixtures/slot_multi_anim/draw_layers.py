"""Generate slot_multi_anim PNG layers (the slot system, Pillow only).

Run with::

    python packages/fixtures/slot_multi_anim/draw_layers.py

Pure Python - no Blender required. Produces three PNGs under
``examples/generated/slot_multi_anim/pillow_layers/``:

- ``arm.png``   32x8  - horizontal forearm (the slot rides its bone tip)
- ``club.png``  32x32 - a wooden club attachment
- ``torch.png`` 32x32 - a lit torch attachment

The companion ``build_blend.py`` wires a slot Empty with the two attachments
and authors TWO animations - ``idle`` (both attachments hidden -> "(none)") and
``attack`` (club shown) - so the writer's per-animation slot export has a
multi-animation blend to read. Minimal pixel-art so the club/torch difference
is unambiguous in CI screenshots.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, rect  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
LAYERS_DIR = REPO_ROOT / "examples" / "generated" / "slot_multi_anim" / "pillow_layers"

ARM_W = 32
ARM_H = 8
WEAPON_W = 32
WEAPON_H = 32

SKIN = (0.85, 0.65, 0.50, 1.0)
SKIN_OUTLINE = (0.20, 0.10, 0.05, 1.0)
WOOD = (0.40, 0.25, 0.10, 1.0)
WOOD_DARK = (0.25, 0.15, 0.05, 1.0)
FLAME = (0.95, 0.55, 0.10, 1.0)
FLAME_CORE = (0.98, 0.85, 0.30, 1.0)
OUTLINE = (0.05, 0.05, 0.05, 1.0)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _draw_arm()
    _draw_club()
    _draw_torch()
    print(f"[draw_slot_multi_anim] wrote 3 attachments under {LAYERS_DIR}")


def _draw_arm() -> None:
    """Horizontal pixel-art forearm: skin rectangle + dark outline."""
    canvas = Canvas.empty(ARM_W, ARM_H)
    rect(canvas, 0, 0, ARM_W, ARM_H, OUTLINE)
    rect(canvas, 1, 1, ARM_W - 2, ARM_H - 2, SKIN_OUTLINE)
    rect(canvas, 2, 2, ARM_W - 4, ARM_H - 4, SKIN)
    canvas.save(LAYERS_DIR / "arm.png")


def _draw_club() -> None:
    """Upright wooden club: broad head on top, narrow grip below. Y=0 is TOP."""
    canvas = Canvas.empty(WEAPON_W, WEAPON_H)
    head_x, head_w, head_y, head_h = 9, 14, 1, 17
    rect(canvas, head_x - 1, head_y - 1, head_w + 2, head_h + 2, OUTLINE)
    rect(canvas, head_x, head_y, head_w, head_h, WOOD)
    rect(canvas, head_x, head_y, 2, head_h, WOOD_DARK)
    grip_x, grip_w, grip_y, grip_h = 14, 3, 18, 12
    rect(canvas, grip_x - 1, grip_y, grip_w + 2, grip_h, OUTLINE)
    rect(canvas, grip_x, grip_y, grip_w, grip_h, WOOD)
    canvas.save(LAYERS_DIR / "club.png")


def _draw_torch() -> None:
    """Lit torch: wooden handle below, a flame on top. Y=0 is TOP."""
    canvas = Canvas.empty(WEAPON_W, WEAPON_H)
    # Flame (top).
    rect(canvas, 12, 1, 8, 12, OUTLINE)
    rect(canvas, 13, 2, 6, 10, FLAME)
    rect(canvas, 14, 4, 4, 6, FLAME_CORE)
    # Handle (bottom).
    handle_x, handle_w, handle_y, handle_h = 14, 4, 13, 18
    rect(canvas, handle_x - 1, handle_y, handle_w + 2, handle_h, OUTLINE)
    rect(canvas, handle_x, handle_y, handle_w, handle_h, WOOD)
    rect(canvas, handle_x, handle_y, 1, handle_h, WOOD_DARK)
    canvas.save(LAYERS_DIR / "torch.png")


if __name__ == "__main__":
    main()
