"""Markdown documentation emitter.

Invokes ``@adobe/jsonschema2md`` (npm) via ``npx --yes`` against every
schema dumped under ``packages/models/schemas/`` and writes the result
to ``docs/content/api/schemas/``. The output is a per-schema folder
plus a top-level index that Docusaurus (or any other Markdown reader)
can consume directly.

The Docusaurus integration itself is out of scope for this emitter -
the typed-models codegen P5 ships the regenerable artifacts; wiring the docs site to
read them lands as a follow-up chore.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from proscenio_codegen._io import REPO_ROOT

_MULTI_BLANK = re.compile(r"\n{3,}")


def postprocess_markdown(text: str) -> str:
    """Normalise jsonschema2md output so it is well-formed Markdown.

    The generator emits runs of 2-3 blank lines (markdownlint MD012) and
    repeats a top-level ``#`` heading per referenced definition
    (markdownlint MD025). Collapse blank runs to a single blank line and
    demote every heading after the first ``#`` to ``##`` so the committed
    reference is clean without a lint-ignore over the whole tree.
    """
    text = _MULTI_BLANK.sub("\n\n", text)
    out: list[str] = []
    seen_h1 = False
    for line in text.split("\n"):
        if line.startswith("# "):
            if seen_h1:
                line = "#" + line
            else:
                seen_h1 = True
        out.append(line)
    return "\n".join(out)

SCHEMAS_DIR = REPO_ROOT / "packages" / "models" / "schemas"
DOCS_DIR = REPO_ROOT / "docs" / "content" / "api" / "schemas"

# Pinned to keep the generated Markdown reproducible across machines.
JSONSCHEMA2MD_VERSION = "8.0.2"


def _npx_executable() -> str:
    """Return the npx binary name; raise if Node is not installed."""
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if npx is None:
        raise RuntimeError(
            "docs_emit needs `npx` on PATH (Node.js + npm). Install Node, "
            "then re-run `python -m proscenio_codegen docs`."
        )
    return npx


def emit_docs(
    schemas_dir: Path = SCHEMAS_DIR,
    docs_dir: Path = DOCS_DIR,
) -> list[Path]:
    """Run jsonschema2md across every schema and return the written files.

    jsonschema2md writes a flat set of ``.md`` files plus an ``index.md``
    rollup; the caller can wire those into the docs site or post-process
    them further. The output directory is cleaned of any previous emit
    so stale artifacts from a removed schema do not linger.
    """
    npx = _npx_executable()
    docs_dir.mkdir(parents=True, exist_ok=True)
    # Sweep stale files so a renamed or removed schema does not leave a
    # ghost markdown behind.
    for stale in docs_dir.glob("*.md"):
        stale.unlink()

    subprocess.run(
        [
            npx,
            "--yes",
            f"@adobe/jsonschema2md@{JSONSCHEMA2MD_VERSION}",
            "--input",
            str(schemas_dir),
            "--out",
            str(docs_dir),
            "--schema-out",
            "-",
            "--no-readme",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    # jsonschema2md output carries MD012 (blank runs) + MD025 (repeated
    # top-level headings); normalise each file in place so the committed
    # docs are clean Markdown.
    written = sorted(docs_dir.glob("*.md"))
    for md in written:
        original = md.read_text(encoding="utf-8")
        normalised = postprocess_markdown(original)
        if normalised != original:
            md.write_text(normalised, encoding="utf-8")

    return written
