"""Generate every PNG layer for the doll fixture (SPEC 007 step 3, Pillow only).

Run with::

    python scripts/fixtures/draw_doll.py

Pure Python — no Blender required. Produces all of the body-part PNGs
under ``examples/doll/layers/`` plus the eye spritesheet. Geometric
primitives (circles, rectangles, triangles, trapezoids) colored
regionally for instant visual debugging.

The companion ``build_doll.py`` runs in headless Blender, loads these
PNGs from disk, and assembles the ``.blend`` (37-bone armature, ~25
sprite meshes, multi-bone weights, 4 actions).

Pillow coordinates are top-down (``y = 0`` at top of canvas). The
saved PNG preserves that orientation; Blender reads the PNG and shows
it the same way in the UV editor.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import (  # noqa: E402
    Canvas,
    border,
    circle,
    fill,
    rect,
    trapezoid,
    triangle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYERS_DIR = REPO_ROOT / "examples" / "doll" / "layers"

# Eye spritesheet specs (must match build_doll.py).
EYE_FRAME_W = 32
EYE_FRAME_H = 32
EYE_HFRAMES = 4
EYE_VFRAMES = 1
EYE_SHEET_W = EYE_FRAME_W * EYE_HFRAMES
EYE_SHEET_H = EYE_FRAME_H * EYE_VFRAMES

# Color palette
BEIGE = (0.93, 0.78, 0.68, 1.0)
DARK_BROWN = (0.30, 0.20, 0.15, 1.0)
WHITE = (0.95, 0.95, 0.95, 1.0)
PUPIL = (0.10, 0.10, 0.10, 1.0)
RED = (0.85, 0.20, 0.20, 1.0)
NAVY = (0.10, 0.18, 0.45, 1.0)
BLUE = (0.20, 0.40, 0.85, 1.0)
LIGHT_BLUE = (0.40, 0.60, 0.95, 1.0)
GREEN = (0.20, 0.65, 0.30, 1.0)
GREEN_PALE = (0.55, 0.78, 0.55, 1.0)
GOLD = (0.85, 0.65, 0.20, 1.0)
BROWN = (0.50, 0.30, 0.15, 1.0)
BORDER = (0.0, 0.0, 0.0, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)

# (sprite_name, w_px, h_px, draw_kind)
# Same list as referenced by _doll_meshes.py. Keep in sync when editing.
SPRITES: tuple[tuple[str, int, int, str], ...] = (
    ("head_base", 96, 96, "head"),
    ("brow.L", 24, 6, "brow"),
    ("brow.R", 24, 6, "brow"),
    ("ear.L", 16, 24, "ear"),
    ("ear.R", 16, 24, "ear"),
    ("jaw", 48, 16, "jaw"),
    ("lip.T", 32, 6, "lip"),
    ("lip.B", 32, 6, "lip"),
    ("neck", 32, 24, "neck"),
    ("spine_block", 80, 144, "torso"),
    ("breast.L", 36, 36, "breast"),
    ("breast.R", 36, 36, "breast"),
    ("pelvis_block", 96, 64, "pelvis"),
    ("shoulder.L", 32, 32, "shoulder"),
    ("shoulder.R", 32, 32, "shoulder"),
    ("upper_arm.L", 24, 80, "limb"),
    ("upper_arm.R", 24, 80, "limb"),
    ("forearm.L", 22, 72, "limb"),
    ("forearm.R", 22, 72, "limb"),
    ("hand.L", 24, 24, "hand"),
    ("hand.R", 24, 24, "hand"),
    ("finger.001.L", 8, 16, "finger"),
    ("finger.001.R", 8, 16, "finger"),
    ("finger.002.L", 8, 12, "finger"),
    ("finger.002.R", 8, 12, "finger"),
    ("thigh.L", 28, 96, "limb_gold"),
    ("thigh.R", 28, 96, "limb_gold"),
    ("shin.L", 26, 96, "limb_gold"),
    ("shin.R", 26, 96, "limb_gold"),
    ("foot.L", 32, 16, "foot"),
    ("foot.R", 32, 16, "foot"),
)

# Eye spritesheet frames: (frame_index, eye_open_height_ratio).
EYE_FRAMES: tuple[tuple[int, float], ...] = (
    (0, 1.0),
    (1, 0.6),
    (2, 0.2),
    (3, 0.0),
)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    for name, w, h, kind in SPRITES:
        canvas = Canvas.empty(w, h)
        _draw_region(kind, canvas)
        canvas.save(LAYERS_DIR / f"{name}.png")
    _draw_eye_spritesheet()
    print(f"[draw_doll] wrote {len(SPRITES)} body PNG(s) under {LAYERS_DIR}")
    print(f"[draw_doll] wrote eye spritesheet {LAYERS_DIR / 'eye_spritesheet.png'}")


def _draw_region(kind: str, canvas: Canvas) -> None:
    """Dispatch to the geometric primitive matching the body region."""
    w, h = canvas.width, canvas.height
    fill(canvas, TRANSPARENT)
    if kind == "head":
        circle(canvas, w / 2.0, h / 2.0, w / 2.0 - 1, BEIGE)
    elif kind == "brow":
        rect(canvas, 0, 0, w, h, DARK_BROWN)
    elif kind == "ear":
        # Triangle pointing right (Pillow top-down: y grows down).
        triangle(canvas, (0, 0), (w, h / 2.0), (0, h), BEIGE)
    elif kind == "jaw":
        rect(canvas, 0, 0, w, h, BEIGE)
    elif kind == "lip":
        rect(canvas, 0, 0, w, h, RED)
    elif kind == "neck":
        rect(canvas, 0, 0, w, h, BEIGE)
    elif kind == "torso":
        rect(canvas, 0, 0, w, h, BLUE)
    elif kind == "breast":
        circle(canvas, w / 2.0, h / 2.0, w / 2.0 - 1, LIGHT_BLUE)
    elif kind == "pelvis":
        # Trapezoid: narrower at top (waist), wider at bottom (hips).
        trapezoid(canvas, 0, 0, w * 0.6, w, h, NAVY)
    elif kind == "shoulder":
        circle(canvas, w / 2.0, h / 2.0, w / 2.0 - 1, GREEN)
    elif kind == "limb":
        rect(canvas, 0, 0, w, h, GREEN)
    elif kind == "limb_gold":
        rect(canvas, 0, 0, w, h, GOLD)
    elif kind == "hand":
        rect(canvas, 0, 0, w, h, GREEN_PALE)
    elif kind == "finger":
        rect(canvas, 0, 0, w, h, GREEN_PALE)
    elif kind == "foot":
        # Trapezoid: narrower at top (ankle), wider at bottom (foot).
        trapezoid(canvas, 0, 0, w * 0.7, w, h, BROWN)
    border(canvas, BORDER)


def _draw_eye_frame(canvas: Canvas, open_ratio: float) -> None:
    """White iris + dark pupil, vertically clipped by ``open_ratio``."""
    cx = canvas.width / 2.0
    cy = canvas.height / 2.0
    iris_r = canvas.width / 2.0 - 2
    pupil_r = iris_r * 0.4
    open_h = (canvas.height * open_ratio) / 2.0
    circle(canvas, cx, cy, iris_r, WHITE)
    circle(canvas, cx, cy, pupil_r, PUPIL)
    if open_h < canvas.height / 2.0:
        clip = max(0, int(cy - open_h))
        rect(canvas, 0, 0, canvas.width, clip, TRANSPARENT)
        rect(canvas, 0, canvas.height - clip, canvas.width, clip, TRANSPARENT)


def _draw_eye_spritesheet() -> None:
    """Generate the 4-frame eye spritesheet inside layers/."""
    sheet = Canvas.empty(EYE_SHEET_W, EYE_SHEET_H)
    for idx, open_ratio in EYE_FRAMES:
        sub = Canvas.empty(EYE_FRAME_W, EYE_FRAME_H)
        _draw_eye_frame(sub, open_ratio)
        sheet.image.paste(sub.image, (idx * EYE_FRAME_W, 0))
        # Per-frame PNGs follow the <name>_<index> SPEC 006 convention.
        sub.save(LAYERS_DIR / f"eye_{idx}.png")
    sheet.save(LAYERS_DIR / "eye_spritesheet.png")


if __name__ == "__main__":
    main()
