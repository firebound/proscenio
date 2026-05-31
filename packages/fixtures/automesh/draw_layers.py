"""Generate automesh PNG layers (the weight-paint-automesh first cut fixture).

Run with::

    python packages/fixtures/automesh/draw_layers.py

Pure Python - no Blender required. Produces 5 PNGs under
``examples/generated/automesh/pillow_layers/`` that
exercise different alpha silhouette shapes the weight-paint-automesh spec automesh
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
- ``ring.png``    - donut / ring (alpha hole in the middle). Hole
                    support smoke target (the weight-paint-automesh spec D2 amendment,
                    the hole-support amendment). Validates that
                    ``alpha_contour.extract_holes`` detects the
                    centered cutout, the bridge passes it as a
                    CDT constraint loop, and the post-process
                    face-prune drops triangles inside the hole.
                    Proscenio differentiates from Spine + COA
                    Tools 2 by lifting their "no holes" restriction.
- ``swirl.png``   - hi-res anti-aliased S-curve stroke ring (the
                    silhouette is the curve's outline, the curve's
                    interior is a hole). Stresses both the contour
                    walker (smooth curvilinear silhouette, not a
                    primitive shape) AND the hole detector
                    (irregularly-shaped hole, not a perfect circle).
                    Drawn at 4x supersampling + bilinear downsample
                    so the alpha edge fades smoothly instead of
                    pixel-staircasing - exposes any aliasing bias
                    in the downscale + contour pipeline.

Accompanying ``build_blend.py`` assembles the .blend that wires
these PNGs into 5 sprite planes + a 3-bone arm chain positioned
over the hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from _draw import Canvas, fill  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "automesh"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"

FRAME = 200
SWIRL_FRAME = 512  # hi-res AA fixture. 512 picks up the alpha
# gradient across a 128-cell downsampled contour grid (vs 50 cells
# for the 200-pixel sprites) so the boundary reads smooth instead
# of stair-stepped, while keeping the per-pixel validator runtime
# tractable (~250k pixels per swirl pass; 1024 was ~1M and pushed
# validator latency past a minute).
SWIRL_SUPERSAMPLE = 4  # 4x supersample then bilinear downsample
BG = (0.0, 0.0, 0.0, 0.0)
HAND_COLOR = (0.95, 0.78, 0.62, 1.0)
BLOB_COLOR = (0.30, 0.65, 0.85, 1.0)
L_COLOR = (0.55, 0.30, 0.80, 1.0)
RING_COLOR = (0.95, 0.55, 0.20, 1.0)
SWIRL_COLOR = (0.35, 0.75, 0.45, 1.0)


def _to_8bit(color: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    return (
        max(0, min(255, int(color[0] * 255 + 0.5))),
        max(0, min(255, int(color[1] * 255 + 0.5))),
        max(0, min(255, int(color[2] * 255 + 0.5))),
        max(0, min(255, int(color[3] * 255 + 0.5))),
    )


def _draw_hand() -> Canvas:
    """Stylized hand silhouette: palm + 4 fingers + thumb.

    Anatomical layout for a right-hand-facing-viewer pose:
    - Palm: rounded rectangle in the lower-center of the canvas.
    - 4 fingers (index, middle, ring, pinkie) extending up from the
      palm top, decreasing in height pinkie -> middle for the
      typical hand silhouette.
    - Thumb: angled rounded rectangle off the LEFT side of the palm
      mid-height, the classic "T-shape" of a flat hand.
    Tuned so the contour walker has to round 5 distinct fingertips,
    walk 4 inter-finger gaps + 1 thumb-palm seam, and follow the
    curved palm edge.
    """
    canvas = Canvas.empty(FRAME, FRAME)
    fill(canvas, BG)
    draw = ImageDraw.Draw(canvas.image)
    color = _to_8bit(HAND_COLOR)
    # Palm: lower half of the canvas, centered.
    palm_box = (65, 95, 145, 175)
    draw.rounded_rectangle(palm_box, radius=16, fill=color)
    # 4 fingers extending UP from palm top (y=95). Heights vary:
    # middle longest, index + ring slightly shorter, pinkie shortest.
    # Each finger is ~16px wide with 4px gaps between.
    fingers = (
        (68, 35, 84, 100),  # index
        (88, 25, 104, 100),  # middle (tallest)
        (108, 30, 124, 100),  # ring
        (128, 45, 144, 100),  # pinkie (shortest)
    )
    for x0, y0, x1, y1 in fingers:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=8, fill=color)
    # Thumb: slimmer rounded rectangle off the LEFT side of palm at
    # mid-height. Roughly finger-thickness (20px wide, vs 16px
    # finger width) and tall-ish (50px) so silhouette reads as a
    # thumb, not a ball stuck to the palm. Overlaps palm left edge
    # (x=65) by 3px to stay one connected blob.
    draw.rounded_rectangle((48, 100, 68, 150), radius=8, fill=color)
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


def _draw_swirl() -> Canvas:
    """Anti-aliased "8" / double-loop silhouette with a hole in each lobe.

    Two stacked filled ellipses (top + bottom) form the outer
    silhouette - smooth curvilinear shape, not a primitive. A
    smaller knockout ellipse inside EACH lobe produces one alpha
    hole per lobe = 2 holes total. Exercises the hole detector's
    multi-hole path AND the contour walker's smooth-curve handling
    on the same fixture.

    AA via 4x supersample + bilinear downsample. PIL has no native
    AA on ``ellipse`` / ``polygon``; supersample-then-shrink is the
    standard trick (area averaging across the 4x grid fakes the
    fractional coverage at the edge).
    """
    hi = SWIRL_FRAME * SWIRL_SUPERSAMPLE
    hi_image = Image.new("RGBA", (hi, hi), _to_8bit(BG))
    hi_draw = ImageDraw.Draw(hi_image)
    color = _to_8bit(SWIRL_COLOR)

    cx = hi / 2.0
    # Each lobe: ellipse centered at cx, with vertical radius half
    # the canvas minus margin. Lobes overlap by ~10% so the
    # silhouette is one connected blob (single outer contour).
    lobe_rx = hi * 0.22
    lobe_ry = hi * 0.26
    top_cy = hi * 0.32
    bot_cy = hi * 0.68
    hi_draw.ellipse(
        (cx - lobe_rx, top_cy - lobe_ry, cx + lobe_rx, top_cy + lobe_ry),
        fill=color,
    )
    hi_draw.ellipse(
        (cx - lobe_rx, bot_cy - lobe_ry, cx + lobe_rx, bot_cy + lobe_ry),
        fill=color,
    )

    # Two knockout ellipses - one inside each lobe. Each cleanly
    # smaller than the lobe so the alpha hole is fully enclosed
    # (the hole detector requires border-unreachable background).
    hole_rx = hi * 0.10
    hole_ry = hi * 0.12
    hi_draw.ellipse(
        (cx - hole_rx, top_cy - hole_ry, cx + hole_rx, top_cy + hole_ry),
        fill=_to_8bit(BG),
    )
    hi_draw.ellipse(
        (cx - hole_rx, bot_cy - hole_ry, cx + hole_rx, bot_cy + hole_ry),
        fill=_to_8bit(BG),
    )

    final = hi_image.resize((SWIRL_FRAME, SWIRL_FRAME), Image.BILINEAR)
    canvas = Canvas(
        width=SWIRL_FRAME,
        height=SWIRL_FRAME,
        image=final,
        draw=ImageDraw.Draw(final),
    )
    return canvas


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = (
        ("hand.png", _draw_hand()),
        ("blob.png", _draw_blob()),
        ("lshape.png", _draw_lshape()),
        ("ring.png", _draw_ring()),
        ("swirl.png", _draw_swirl()),
    )
    for name, canvas in artifacts:
        canvas.save(LAYERS_DIR / name)
    print(f"[draw_automesh] wrote {len(artifacts)} sprites under {LAYERS_DIR}")


if __name__ == "__main__":
    main()
