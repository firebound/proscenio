"""Smoke tests for the Markdown docs emitter.

The npm tool's own coverage owns the docs content; these tests focus
on the Python wrapper's contract: the call hits the right
directories, both schemas surface at the top level, the sweep step
removes stale artifacts.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from proscenio_codegen.docs_emit import emit_docs


def _node_available() -> bool:
    return shutil.which("npx") is not None or shutil.which("npx.cmd") is not None


@pytest.mark.skipif(
    not _node_available(),
    reason="docs emit requires Node + npx on PATH; skipped on host without it",
)
def test_emit_writes_a_file_per_schema(tmp_path: Path) -> None:
    """A real run lands one top-level Markdown per schema dump."""
    written = emit_docs(docs_dir=tmp_path)
    names = {p.name for p in written}
    assert "proscenio.md" in names
    assert "psd_manifest.md" in names


@pytest.mark.skipif(
    not _node_available(),
    reason="docs emit requires Node + npx on PATH; skipped on host without it",
)
def test_sweep_removes_stale_markdown(tmp_path: Path) -> None:
    """The pre-emit sweep clears any leftover .md from earlier runs."""
    stale = tmp_path / "ghost-from-an-old-schema.md"
    stale.write_text("stale content", encoding="utf-8")
    assert stale.is_file()

    emit_docs(docs_dir=tmp_path)
    assert not stale.exists(), "sweep step should have removed the stale file"
