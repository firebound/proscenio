"""Generate the slot_cycle PNG attachments (SPEC 004 Wave 4.3, Pillow only).

Run with::

    python scripts/fixtures/slot_cycle/draw_layers.py

Pure Python - no Blender required. Produces three 32x32 PNGs under
``examples/generated/slot_cycle/pillow_layers/``: a red square, a green square,
and a blue square. The accompanying ``build_blend.py`` runs in
headless Blender, builds an armature with one bone, wraps the three
quads as slot attachments under a single Empty, and adds an action
that cycles the active attachment per keyframe.

Smallest possible slot fixture - mirrors the simple_psd / blink_eyes
shape (SPEC 007 layout, Pillow + bpy two-stage).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, fill  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "slot_cycle"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"

SIZE = 32

ATTACHMENTS: tuple[tuple[str, tuple[float, float, float, float]], ...] = (
    ("attachment_red", (0.85, 0.20, 0.20, 1.0)),
    ("attachment_green", (0.25, 0.75, 0.30, 1.0)),
    ("attachment_blue", (0.20, 0.40, 0.85, 1.0)),
)


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    for name, color in ATTACHMENTS:
        canvas = Canvas.empty(SIZE, SIZE)
        fill(canvas, color)
        canvas.save(LAYERS_DIR / f"{name}.png")
    print(f"[draw_slot_cycle] wrote {len(ATTACHMENTS)} attachment(s) under {LAYERS_DIR}")


if __name__ == "__main__":
    main()
