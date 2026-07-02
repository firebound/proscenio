"""Atlas-file check: every linked atlas image must resolve on disk."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from pathlib import Path

from ..._shared.material_images import iter_material_node_images
from .._shared import abspath_or_none, name_of
from ..issue import Issue


def validate_atlas_files(scene_objects: Sequence[object]) -> list[Issue]:
    """Check that every linked image used as an atlas resolves on disk."""
    issues: list[Issue] = []
    seen: set[str] = set()
    for obj in scene_objects:
        for fp_raw in _iter_object_atlas_filepaths(obj, seen):
            if not _atlas_path_resolves(fp_raw):
                issues.append(_atlas_missing_issue(obj, fp_raw))
    return issues


def _iter_object_atlas_filepaths(obj: object, seen: set[str]) -> Iterator[str]:
    """Yield filepaths for unique TEX_IMAGE images on `obj`'s material slots."""
    for slot in getattr(obj, "material_slots", ()):
        for image in iter_material_node_images(getattr(slot, "material", None)):
            fp_raw = str(getattr(image, "filepath", "") or "")
            if fp_raw and fp_raw not in seen:
                seen.add(fp_raw)
                yield fp_raw


def _atlas_path_resolves(fp_raw: str) -> bool:
    resolved = abspath_or_none(fp_raw)
    return resolved is not None and Path(resolved).exists()


def _atlas_missing_issue(obj: object, fp_raw: str) -> Issue:
    return Issue(
        "warning",
        f"atlas image {fp_raw!r} not found on disk - Godot will warn at import",
        name_of(obj),
    )
