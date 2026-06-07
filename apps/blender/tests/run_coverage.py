"""Run the headless Blender test suites under coverage.py.

Invoke from the repository root:

    blender --background --python apps/blender/tests/run_coverage.py -- <suite>

where ``<suite>`` is ``fixtures`` (default; runs ``run_tests.py``) or
``operators`` (runs ``run_operator_tests.py``). coverage.py must be
installed in Blender's bundled Python (``<blender-python> -m pip install
coverage``); pytest is needed for the operators suite.

Writes a parallel data file (``.coverage.blender.*``) at the repo root
with ``relative_files`` paths (from ``pyproject.toml``) so the host-side
``coverage combine`` can merge it with the pure-pytest run into one
``coverage.xml`` the Sonar scan consumes.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import coverage

REPO_ROOT = Path(__file__).resolve().parents[3]
ADDON_DIR = REPO_ROOT / "apps" / "blender"
SUITES = {
    "fixtures": ADDON_DIR / "tests" / "run_tests.py",
    "operators": ADDON_DIR / "tests" / "run_operator_tests.py",
}


def _selected_suite() -> str:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return args[0] if args else "fixtures"


def _run_suite(path: Path) -> int:
    spec = importlib.util.spec_from_file_location("_proscenio_suite", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load suite {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return int(module.main())


def main() -> int:
    suite = _selected_suite()
    runner = SUITES.get(suite)
    if runner is None:
        print(f"unknown suite {suite!r}; expected one of {sorted(SUITES)}", file=sys.stderr)
        return 2

    cov = coverage.Coverage(
        source=[str(ADDON_DIR)],
        data_file=str(REPO_ROOT / ".coverage.blender"),
        config_file=str(REPO_ROOT / "pyproject.toml"),
        data_suffix=suite,
    )
    cov.start()
    try:
        rc = _run_suite(runner)
    finally:
        cov.stop()
        cov.save()

    measured = [f for f in cov.get_data().measured_files() if "blender" in f.replace("\\", "/")]
    print(f"BLENDER_COV_FILES {len(measured)}")
    print(f"SUITE_RC {rc}")
    return rc


if __name__ == "__main__":
    # Exit 0 regardless of suite rc: the spike / CI cares about the
    # coverage data, and suite pass/fail is reported separately by the
    # plain (non-coverage) test jobs.
    main()
    sys.exit(0)
