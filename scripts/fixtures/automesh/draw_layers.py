"""Generate automesh PNG layers (SPEC 013 Wave 13.1 fixture).

Run with::

    python scripts/fixtures/automesh/draw_layers.py

Pure Python - no Blender required. Produces 4 PNGs under
``examples/generated/automesh/pillow_layers/`` that
exercise different alpha silhouette shapes the SPEC 013 automesh
operator needs to handle:

- ``hand.png``    - hand silhouette (palm + 5 tapered fingers). The
                    canonical "real character part" smoke target;
                    covers convex + tapered tips that the contour
                    walker has to follow + paired with the 3-bone
                    arm chain in build_blend.py to validate the D15
                    density-under-bones path end-to-end.
- ``blob.png``    - irregular ellipse-ish blob. Simplest smooth
                    convex silhouette; baseline that any future
                    regression should still produce a clean annulus.
- ``lshape.png``  - concave L shape. Stresses the Moore Neighbour
                    walker's ability to follow a concave hull
                    without giving up (Spine `Trace` documents
                    concave support; this is the local regression
                    guard for it).
- ``ring.png``    - donut / ring (alpha hole in the middle). Per
                    Spine docs the addon does NOT support holes;
                    this fixture is included specifically so smoke
                    runs surface how Proscenio degrades when the
                    user violates that contract (outer contour
                    walks the outside; inner contour intersects).

Accompanying ``build_blend.py`` assembles the .blend that wires
these PNGs into 4 sprite planes + a 3-bone arm chain positioned
over the hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, fill  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "automesh"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"

FRAME = 200
BG = (0.0, 0.0, 0.0, 0.0)
HAND_COLOR = (0.95, 0.78, 0.62, 1.0)
BLOB_COLOR = (0.30, 0.65, 0.85, 1.0)
L_COLOR = (0.55, 0.30, 0.80, 1.0)
RING_COLOR = (0.95, 0.55, 0.20, 1.0)


def _to_8bit(color: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return (
        max(0, min(255, int(color[0] * 255 + 0.5))),
        max(0, min(255, int(color[1] * 255 + 0.5))),
        max(0, min(255, int(color[2] * 255 + 0.5))),
        max(0, min(255, int(color[3] * 255 + 0.5))),
    )


def _draw_hand() -> Canvas:
    """Stylized hand silhouette: 3-finger palm + thumb + extended index.

    Tuned so the contour walker has to round 4 distinct finger tips,
    walk the gaps between fingers, and follow the curved palm edge.
    """
    canvas = Canvas.empty(FRAME, FRAME)
    fill(canvas, BG)
    draw = ImageDraw.Draw(canvas.image)
    color = _to_8bit(HAND_COLOR)
    palm_box = (60, 90, 145, 175)
    draw.rounded_rectangle(palm_box, radius=18, fill=color)
    fingers = (
        (72, 30, 90, 110),
        (95, 25, 113, 105),
        (118, 30, 136, 110),
        (135, 65, 165, 130),
    )
    for x0, y0, x1, y1 in fingers:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=10, fill=color)
    return canvas


def _draw_blob() -> Canvas:
    """Smooth convex ellipse - the simplest possible silhouette."""
    canvas = Canvas.empty(FRAME, FRAME)
    fill(canvas, BG)
    draw = ImageDraw.Draw(canvas.image)
    draw.ellipse((25, 40, 175, 160), fill=_to_8bit(BLOB_COLOR))
    return canvas


def _draw_lshape() -> Canvas:
    """Concave L (vertical bar + horizontal foot)."""
    canvas = Canvas.empty(FRAME, FRAME)
    fill(canvas, BG)
    draw = ImageDraw.Draw(canvas.image)
    color = _to_8bit(L_COLOR)
    draw.rectangle((50, 30, 100, 170), fill=color)
    draw.rectangle((50, 130, 170, 170), fill=color)
    return canvas


def _draw_ring() -> Canvas:
    """Donut: outer circle minus inner circle (alpha hole)."""
    canvas = Canvas.empty(FRAME, FRAME)
    fill(canvas, BG)
    draw = ImageDraw.Draw(canvas.image)
    draw.ellipse((20, 20, 180, 180), fill=_to_8bit(RING_COLOR))
    draw.ellipse((75, 75, 125, 125), fill=_to_8bit(BG))
    return canvas


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = (
        ("hand.png", _draw_hand()),
        ("blob.png", _draw_blob()),
        ("lshape.png", _draw_lshape()),
        ("ring.png", _draw_ring()),
    )
    for name, canvas in artifacts:
        canvas.save(LAYERS_DIR / name)
    print(f"[draw_automesh] wrote {len(artifacts)} sprites under {LAYERS_DIR}")


if __name__ == "__main__":
    main()
