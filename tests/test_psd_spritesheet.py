"""Unit tests for the PSD importer spritesheet composer (SPEC 006 D10).

Pure Pillow; no Blender. Verifies that frames padded to the bbox of
the largest input land at the expected tile slots in the output PNG.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core.psd_spritesheet import compose_spritesheet  # noqa: E402


def _solid_png(path: Path, width: int, height: int, color: tuple[int, int, int, int]) -> None:
    img = Image.new("RGBA", (width, height), color)
    img.save(path, "PNG")


def test_compose_uniform_frames(tmp_path: Path) -> None:
    paths = []
    for i in range(4):
        p = tmp_path / f"frame_{i}.png"
        _solid_png(p, 32, 32, (255, 0, 0, 255))
        paths.append(p)
    out = tmp_path / "out" / "sheet.png"
    result = compose_spritesheet(paths, out)
    assert result.path == out
    assert result.tile_size == (32, 32)
    assert result.hframes == 4
    assert result.vframes == 1

    sheet = Image.open(out)
    assert sheet.size == (128, 32)
    sheet.close()


def test_compose_pads_smaller_frames(tmp_path: Path) -> None:
    """Smaller frames anchor top-left in the larger tile, transparent fill."""
    big = tmp_path / "big.png"
    small = tmp_path / "small.png"
    _solid_png(big, 32, 32, (255, 0, 0, 255))
    _solid_png(small, 16, 16, (0, 255, 0, 255))
    out = tmp_path / "sheet.png"
    result = compose_spritesheet([big, small], out)
    assert result.tile_size == (32, 32)
    assert result.hframes == 2

    sheet = Image.open(out).convert("RGBA")
    # Big frame occupies the first tile fully.
    assert sheet.getpixel((0, 0)) == (255, 0, 0, 255)
    assert sheet.getpixel((31, 31)) == (255, 0, 0, 255)
    # Small frame anchored top-left of second tile (offset 32, 0).
    assert sheet.getpixel((32, 0)) == (0, 255, 0, 255)
    assert sheet.getpixel((47, 15)) == (0, 255, 0, 255)
    # Padding around small frame is transparent.
    assert sheet.getpixel((48, 0)) == (0, 0, 0, 0)
    assert sheet.getpixel((32, 16)) == (0, 0, 0, 0)
    sheet.close()


def test_compose_creates_output_directory(tmp_path: Path) -> None:
    p = tmp_path / "frame_0.png"
    p2 = tmp_path / "frame_1.png"
    _solid_png(p, 8, 8, (0, 0, 255, 255))
    _solid_png(p2, 8, 8, (0, 0, 128, 255))
    out = tmp_path / "deep" / "nested" / "sheet.png"
    compose_spritesheet([p, p2], out)
    assert out.exists()


def test_compose_empty_input_raises() -> None:
    with pytest.raises(ValueError, match="at least one frame"):
        compose_spritesheet([], Path("/tmp/never.png"))


def test_compose_missing_frame_raises(tmp_path: Path) -> None:
    p = tmp_path / "ghost.png"
    with pytest.raises(FileNotFoundError):
        compose_spritesheet([p], tmp_path / "out.png")
