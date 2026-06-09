# Blender addon preferences - TODO

Successor to spec 022 (which landed the minimal `ProscenioAddonPreferences` + `debug_mode`). STUDY: [STUDY.md](STUDY.md). This pass grows it into the basic preferences surface.

## Decisions locked

- **D1 Log-level:** a `debug / info / errors` `EnumProperty` on `ProscenioAddonPreferences`, gated in ONE place in `core/_shared/report` (the report helpers consult the pref before echoing to the console). Not per-call-site.
- **D2 debug_mode:** keep the existing bare bool (022's gating of Diagnostics + Debug Pipeline must keep working); group it visually with the log-level under a "Developer" section in the prefs draw.
- **D3 Docs URL pref:** NOT a preference this pass - stays a constant in spec 023's registry. Revisit if a real need surfaces.
- **D4 Per-project overrides:** none - the scene PG already covers per-`.blend` state; preferences are user-global only.

## Gate set (every change)

- [ ] `uvx ruff check apps/blender/`
- [ ] `uvx ruff format --check apps/blender/`
- [ ] `uv run --with mypy mypy --config-file apps/blender/pyproject.toml`
- [ ] `uv run pytest tests/` (repo root)
- [ ] Blender operator suite (`blender --background --python apps/blender/tests/run_operator_tests.py`) + fixture suite
- [ ] Whole-addon import sweep
- [ ] In-editor smoke (prefs draw shows log-level + debug_mode; changing log-level changes console verbosity)

## Phase 1 - log-level preference

- [ ] `addon_prefs.py`: add `log_level: EnumProperty(items=[debug / info / errors], default=info)`.
- [ ] `core/_shared/report.py`: read the pref in `report_info` / `report_warn` / `report_error` (single gate) so INFO is suppressed below the chosen level; ERROR always shows. Keep the bpy `self.report` UI path intact; gate the console echo.
- [ ] Draw `log_level` in the preferences UI.

## Phase 2 - own debug_mode + Developer group

- [ ] `addon_prefs.py`: keep `debug_mode` bool; draw it + `log_level` under a "Developer" labelled box.
- [ ] Confirm the Diagnostics panel + Debug Pipeline subpanel still gate on `debug_mode_enabled(context)` unchanged.

## Deferred (within 024, follow-up)

- Cross-tool global defaults (e.g. a configurable docs URL) - only if 023 needs it.
- Any per-project override surface.

## Status

- [ ] not started
