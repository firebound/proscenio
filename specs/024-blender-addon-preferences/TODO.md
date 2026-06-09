# Blender addon preferences - TODO

Successor to spec 022 (which landed the minimal `ProscenioAddonPreferences` + `debug_mode`). STUDY: [STUDY.md](STUDY.md). This pass grows it into the basic preferences surface.

## Decisions locked

- **D1 Log-level:** an `errors / info / debug` `EnumProperty` on `ProscenioAddonPreferences`, gated in ONE place in `core/_shared/report` (the report helpers consult the pref before echoing to the console). Not per-call-site. The `debug` tier is backed by real per-item traces (`report_debug` in the importer / automesh / validation operators) so it is never an inert option.
- **D2 debug_mode:** keep the existing bare bool (022's gating of Diagnostics + Debug Pipeline must keep working); group it visually with the log-level under a "Developer" section in the prefs draw.
- **D3 Docs URL pref:** NOT a preference this pass - stays a constant in spec 023's registry. Revisit if a real need surfaces.
- **D4 Per-project overrides:** none - the scene PG already covers per-`.blend` state; preferences are user-global only.

## Gate set (every change)

- [x] `uvx ruff check apps/blender/`
- [x] `uvx ruff format --check apps/blender/`
- [x] `uv run --with mypy mypy --config-file apps/blender/pyproject.toml`
- [x] `uv run pytest tests/` (repo root)
- [x] Blender operator suite (`blender --background --python apps/blender/tests/run_operator_tests.py`) + fixture suite
- [x] Whole-addon import sweep
- [x] In-editor smoke (prefs draw shows log-level + debug_mode; changing log-level changes console verbosity)

## Phase 1 - log-level preference

- [x] `addon_prefs.py`: add `log_level: EnumProperty(items=[errors / info / debug], default=info)`.
- [x] `core/_shared/report.py`: read the pref in `report_info` / `report_warn` / `report_error` (single gate) so INFO is suppressed below the chosen level; ERROR always shows. Keep the bpy `self.report` UI path intact; gate the console echo.
- [x] Draw `log_level` in the preferences UI.

## Phase 2 - own debug_mode + Developer group

- [x] `addon_prefs.py`: keep `debug_mode` bool; draw it + `log_level` under a "Developer" labelled box.
- [x] Confirm the Diagnostics panel + Debug Pipeline subpanel still gate on `debug_mode_enabled(context)` unchanged.

## Phase 3 - the debug tier (finalized 2026-06-09)

- [x] `core/_shared/report.py`: `_LEVELS` gains `debug: 2`; add `_DEBUG_LEVEL` + a `report_debug(op, msg)` helper gated `>= _DEBUG_LEVEL`, emitted as an INFO report (Blender filters its native DEBUG severity out of every visible channel - verified by probe) under a distinct `[Proscenio debug]` tag so dev traces read apart from the plain `Proscenio:` info lines.
- [x] `addon_prefs.py`: add the `debug` item to the `log_level` enum + its help text.
- [x] Wire genuine `report_debug` call sites so the tier is not inert: per-plane import trace (`operators/import_photoshop.py`), the full automesh counter dump (`operators/automesh/automesh.py`), per-issue validation trace (`operators/export_flow.py`, shared by validate + the export gate via `_report_issue_traces`).
- [x] `tests/test_report_gate.py`: pure unit test proving the gate (errors -> error only; info -> info/warning surface, debug held back; debug -> all four, the trace emitted as INFO; unknown -> info fallback).

## Deferred (decided; recorded in ../backlog.md "Spec 024 follow-up: docs-URL preference (D3) + overrides (D4 - none)")

- Docs-URL as a preference (D3) - the docs base stays the `_DOCS_BASE` constant; promote only if a second docs target appears.
- Per-project overrides (D4) - decided NONE; the scene PG covers per-`.blend` state.

## Status - complete 2026-06-09

Phase 1 + Phase 2 shipped earlier (commit 3a2fe48: the `errors / info` `log_level` gated once in `core/_shared/report`, `debug_mode` + `log_level` under a Developer box). Phase 3 finalizes the spec: the real `debug` tier now ships with `report_debug` + three genuine call sites (importer planes, automesh counters, validation issues), so the option is not the inert level CodeRabbit removed on PR #97. Gates green: ruff, ruff-format, mypy (168 files), `pytest tests/` (618, incl. the new report-gate unit), Blender operator suite (50), fixture suite (7/7), headless prefs-RNA smoke (the enum exposes errors / info / debug; a trace surfaces at debug, is suppressed at info). D3 (docs-URL) + D4 (overrides = none) recorded in the backlog as the surviving by-design deferments.
