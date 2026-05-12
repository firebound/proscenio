"""Headless Proscenio fixture test runner.

Invoke from the repository root:

    blender --background --python apps/blender/tests/run_tests.py

Walks every fixture under ``examples/*/`` that owns a paired
``<name>.blend`` + ``<name>.expected.proscenio``. For each pair, opens
the ``.blend``, runs the addon writer, validates the JSON against
``schemas/proscenio.schema.json`` (when ``jsonschema`` is available in
Blender's bundled Python), and diffs the actual output against the
golden. Exits non-zero on the first failure.

Output is normalized via ``json.dumps(sort_keys=True, indent=2)`` before
comparison so dict ordering and trailing whitespace do not flap.
"""

from __future__ import annotations

import difflib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
ADDON_PATH = REPO_ROOT / "apps" / "blender"
ADDON_PACKAGE = "proscenio"
EXAMPLES_DIR = REPO_ROOT / "examples"
SCHEMA_PATH = REPO_ROOT / "schemas" / "proscenio.schema.json"


def _load_addon_as_package() -> None:
    """Register ``apps/blender/`` under sys.modules as ``proscenio``.

    The addon's submodules use relative imports rooted at the package
    name declared in its manifest (``proscenio``). The folder on disk
    is named ``blender`` - valid as identifier, but mounting it under
    the manifest name keeps the package path identical to what the
    extension loader produces.
    """
    if ADDON_PACKAGE in sys.modules:
        return
    init_path = ADDON_PATH / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        ADDON_PACKAGE,
        init_path,
        submodule_search_locations=[str(ADDON_PATH)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not build import spec for {init_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[ADDON_PACKAGE] = module
    spec.loader.exec_module(module)


def _normalize(doc: dict[str, Any]) -> str:
    return json.dumps(doc, sort_keys=True, indent=2)


def _validate_against_schema(doc: dict[str, Any]) -> list[str]:
    """Return schema violations for ``doc``, empty if valid.

    Falls back gracefully if ``jsonschema`` is not in Blender's bundled
    Python (it usually is not). Returns ``[]`` with a stderr note in
    that case so the test still proves the writer round-trip - schema
    enforcement happens in the dedicated ``validate-schema`` CI job.
    """
    try:
        import jsonschema  # type: ignore[import-untyped]
    except ImportError:
        return []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'.'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in validator.iter_errors(doc)
    ]


def _discover_fixtures() -> list[tuple[Path, Path]]:
    """Find every ``*.expected.proscenio`` under ``examples/`` paired with a golden.

    Recursive walk so the tier-0 hand-authored fixtures under
    ``examples/authored/<name>/`` are discovered alongside the
    procedural ones at the root (``examples/<name>/``). A single
    fixture dir may host multiple ``(blend, golden)`` pairs (e.g.
    a baseline + a derived variant) - one pair per golden.

    Returns a sorted list of ``(blend_path, expected_path)`` tuples.
    """
    pairs: list[tuple[Path, Path]] = []
    orphans: list[Path] = []
    for expected in sorted(EXAMPLES_DIR.rglob("*.expected.proscenio")):
        name = expected.name[: -len(".expected.proscenio")]
        blend = expected.parent / f"{name}.blend"
        if blend.exists():
            pairs.append((blend, expected))
        else:
            orphans.append(expected)
    if orphans:
        listing = "\n".join(f"  - {p}" for p in orphans)
        raise RuntimeError("orphan golden(s) with no matching .blend sibling:\n" + listing)
    return pairs


def _run_one(blend: Path, expected: Path, writer_module: Any) -> bool:
    """Open ``blend``, re-export, validate + diff. Return True on pass."""
    label = f"{blend.parent.name}/{blend.stem}"
    print(f"--- {label}", flush=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    actual_path = expected.with_name(expected.stem + ".actual.proscenio")
    writer_module.export(actual_path, pixels_per_unit=100.0)
    actual = json.loads(actual_path.read_text(encoding="utf-8"))
    expected_doc = json.loads(expected.read_text(encoding="utf-8"))

    schema_errors = _validate_against_schema(actual)
    if schema_errors:
        print(f"FAIL ({label}): writer output is not schema-valid", file=sys.stderr)
        for err in schema_errors:
            print(f"  - {err}", file=sys.stderr)
        return False

    actual_s = _normalize(actual)
    expected_s = _normalize(expected_doc)
    if actual_s == expected_s:
        actual_path.unlink()
        print(f"PASS ({label})")
        return True

    diff = difflib.unified_diff(
        expected_s.splitlines(),
        actual_s.splitlines(),
        fromfile=expected.name,
        tofile=actual_path.name,
        lineterm="",
    )
    print(f"FAIL ({label}): writer output differs from golden", file=sys.stderr)
    for line in diff:
        print(line, file=sys.stderr)
    print(f"\nactual written to: {actual_path}", file=sys.stderr)
    return False


def main() -> int:
    _load_addon_as_package()
    from proscenio.exporters.godot import writer  # type: ignore[import-not-found]

    fixtures = _discover_fixtures()
    if not fixtures:
        print("FAIL: no fixtures found under examples/", file=sys.stderr)
        return 1

    failures = 0
    for blend, expected in fixtures:
        if not _run_one(blend, expected, writer):
            failures += 1

    total = len(fixtures)
    passed = total - failures
    print(f"\n{passed}/{total} fixture(s) passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
