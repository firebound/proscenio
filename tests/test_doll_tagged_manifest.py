"""SPEC 011 v1 parity oracle (Python side).

Loads the committed `doll_tagged.photoshop_exported.json` from the doll
fixture and asserts the schema + tag coverage. Pairs with the vitest
`tag-smoke` test (which exercises the planner against a synthetic
tree). This file pins the **on-disk artefact** so a regression in the
exporter's serialisation surfaces as a CI failure rather than waiting
for a manual PS round-trip.

Run from the repo root::

    pytest tests/test_doll_tagged_manifest.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

MANIFEST_PATH = (
    REPO_ROOT
    / "examples/authored/doll/02_photoshop_setup/export/doll_tagged.photoshop_exported.json"
)

from core import psd_manifest  # noqa: E402


@pytest.fixture(scope="module")
def manifest_raw() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip(
            f"doll_tagged manifest missing at {MANIFEST_PATH}; re-export from "
            "doll_tagged.psd via the Proscenio Exporter panel."
        )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def manifest(manifest_raw: dict) -> psd_manifest.Manifest:
    return psd_manifest.parse(manifest_raw, source_path=MANIFEST_PATH)


def test_format_version_is_v2(manifest: psd_manifest.Manifest) -> None:
    assert manifest.format_version == 2


def test_canvas_size_matches_doll_psd(manifest: psd_manifest.Manifest) -> None:
    assert manifest.size == (837, 1731)


def test_doc_name(manifest: psd_manifest.Manifest) -> None:
    assert manifest.doc == "doll_tagged.psd"


def test_anchor_is_set_from_guides(manifest: psd_manifest.Manifest) -> None:
    # The artist authored horizontal + vertical guides on the tagged PSD;
    # the planner emits them as the document anchor.
    assert manifest.anchor is not None
    ax, ay = manifest.anchor
    assert 0 < ax < manifest.size[0]
    assert 0 < ay < manifest.size[1]


def test_entry_count_matches_oracle(manifest: psd_manifest.Manifest) -> None:
    # 22 baseline layers + 4 blend-stack duplicates + 1 sprite_frame
    # (brow_states absorbs the nested merge frames into a single entry)
    # - head 2 + Camada 1 skipped during export.
    # See 02_photoshop_setup/README.md::Tags exercised for the breakdown.
    assert len(manifest.layers) == 24


def test_kind_distribution(manifest: psd_manifest.Manifest) -> None:
    kinds = [L.kind for L in manifest.layers]
    assert kinds.count("mesh") == 2  # chest + chest mult
    assert kinds.count("sprite_frame") == 1  # brow_states
    # Rest are polygon (default kind).
    assert kinds.count("polygon") == len(manifest.layers) - 3


def test_blend_modes_round_tripped(manifest: psd_manifest.Manifest) -> None:
    by_name = {L.name: L for L in manifest.layers}
    # Names cascade via joinName when a parent [folder:NAME] tag is
    # present, so the eye blend variants land under the `eyes` prefix.
    assert by_name["chest mult"].blend_mode == "multiply"
    assert by_name["eyes__eye.L scrn"].blend_mode == "screen"
    assert by_name["eyes__eye.R add"].blend_mode == "additive"


def test_subfolders_from_folder_tags(manifest: psd_manifest.Manifest) -> None:
    by_name = {L.name: L for L in manifest.layers}
    assert by_name["chest"].subfolder == "body"
    assert by_name["belly"].subfolder == "body"
    assert by_name["eyes__eye.L"].subfolder == "eyes"
    assert by_name["arm.R"].subfolder == "teste"


def test_origins_from_explicit_and_marker(
    manifest: psd_manifest.Manifest,
) -> None:
    by_name = {L.name: L for L in manifest.layers}
    # Explicit [origin:X,Y]
    assert by_name["arm.R"].origin == (10, 20)
    assert by_name["belly"].origin == (532, 333)
    # Sprite_frame origin from the [origin] marker inside the spritesheet group
    brow_states = by_name["brow_states"]
    assert brow_states.kind == "sprite_frame"
    assert brow_states.origin is not None


def test_path_tag_overrides_filename(manifest: psd_manifest.Manifest) -> None:
    by_name = {L.name: L for L in manifest.layers}
    # arm.R carries [path:test] - the leaf filename becomes `test.png`,
    # not `arm_R.png`.
    arm = by_name["arm.R"]
    assert arm.path is not None
    assert arm.path.endswith("/test.png")


def test_scale_tag_applied_to_size(manifest: psd_manifest.Manifest) -> None:
    by_name = {L.name: L for L in manifest.layers}
    # arm.R: source bbox 145x254, [scale:2.5] -> 362.5x635. The
    # planner rounds the integer part for the manifest (subpixel
    # warning fires); we tolerate the rounding rather than pin the
    # exact rounding direction.
    arm = by_name["arm.R"]
    assert arm.size[0] in (362, 363)
    assert arm.size[1] in (634, 635)


def test_sprite_frame_has_frames(manifest: psd_manifest.Manifest) -> None:
    by_name = {L.name: L for L in manifest.layers}
    brow_states = by_name["brow_states"]
    assert brow_states.kind == "sprite_frame"
    # Nested `1.1 [merge]` inside `1 [merge]` collapses into the parent
    # frame; only `0` and `1` survive as top-level numeric children.
    assert len(brow_states.frames) == 2
    indices = sorted(f.index for f in brow_states.frames)
    assert indices == [0, 1]


def test_no_ignored_layers_present(manifest: psd_manifest.Manifest) -> None:
    names = {L.name for L in manifest.layers}
    # `head 2 [ignore]` and `Camada 1` (empty placeholder) must not appear.
    assert "head 2" not in names
    assert "Camada 1" not in names
