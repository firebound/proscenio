"""Atlas manifest read (SPEC 009 wave 9.10 split of atlas_io).

Pure JSON parser, but lives under ``bpy_helpers/`` because the typed
``Rect`` it returns is shared with ``compose_atlas`` and the
``read_manifest`` consumer (``operators/atlas_pack/apply.py``) is bpy-bound.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..atlas_packer import Rect


@dataclass(frozen=True)
class Placement:
    """Manifest entry: slot rect in atlas + slice rect in source image."""

    slot: Rect
    source_w: int
    source_h: int
    slice: Rect


def read_manifest(manifest_path: Path) -> tuple[int, int, int, dict[str, Placement]]:
    """Inverse of ``compose.write_manifest``. Tolerates the v1 (no slice) format.

    Returns ``(atlas_w, atlas_h, padding, placements)``. Entries from v1
    manifests get ``slice == slot`` and ``source_w/h == slot.w/h`` so
    the apply operator's slice-aware code path stays correct.
    """
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    placements: dict[str, Placement] = {}
    for name, r in payload["placements"].items():
        slot = Rect(int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]))
        slice_rect = Rect(
            int(r.get("slice_x", 0)),
            int(r.get("slice_y", 0)),
            int(r.get("slice_w", slot.w)),
            int(r.get("slice_h", slot.h)),
        )
        placements[name] = Placement(
            slot=slot,
            source_w=int(r.get("source_w", slot.w)),
            source_h=int(r.get("source_h", slot.h)),
            slice=slice_rect,
        )
    return (
        int(payload["atlas_w"]),
        int(payload["atlas_h"]),
        int(payload.get("padding", 0)),
        placements,
    )
