"""Probe Blender 5.x Action structure."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

OUT = Path(__file__).parent / "inspect_action.out"
lines: list[str] = []


def p(msg: str) -> None:
    lines.append(msg)


for action in bpy.data.actions:
    p(
        f"action='{action.name}'  attrs={[a for a in dir(action) if not a.startswith('_')]}"
    )
    p(f"  has fcurves attr: {hasattr(action, 'fcurves')}")
    p(f"  has layers: {hasattr(action, 'layers')}")
    if hasattr(action, "layers"):
        for li, layer in enumerate(action.layers):
            p(
                f"    layer[{li}]={layer.name}  attrs={[a for a in dir(layer) if not a.startswith('_')]}"
            )
            for si, strip in enumerate(layer.strips):
                p(
                    f"      strip[{si}]={strip.type}  attrs={[a for a in dir(strip) if not a.startswith('_')]}"
                )
                if hasattr(strip, "channelbags"):
                    for ci, cb in enumerate(strip.channelbags):
                        p(
                            f"        channelbag[{ci}] attrs={[a for a in dir(cb) if not a.startswith('_')]}"
                        )
                        if hasattr(cb, "fcurves"):
                            for fc in cb.fcurves:
                                p(
                                    f"          fcurve: data_path='{fc.data_path}' array_index={fc.array_index} keys={len(fc.keyframe_points)}"
                                )
    if hasattr(action, "slots"):
        for slot in action.slots:
            p(
                f"    slot: identifier='{slot.identifier}' attrs={[a for a in dir(slot) if not a.startswith('_')]}"
            )

OUT.write_text("\n".join(lines), encoding="utf-8")
sys.stdout.write(f"wrote {OUT}\n")
