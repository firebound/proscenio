# Blender addon help, docs, i18n - TODO

Successor to spec 022. STUDY: [STUDY.md](STUDY.md). This pass lands the BASICS that close the help layer; the heavier art + full i18n migration are deferred within the spec (marked below).

## Decisions locked

- **D1 Doc-link registry home:** extend `core/help_topics.py` - `HelpTopic` gains optional `doc_path` (local) + `doc_url` (online). One home for inline content + its links; no separate module.
- **D2 Per-subpanel help topics:** author a distinct topic per subpanel and pass its id in `draw_subpanel_header`. Today every subpanel of a family reuses the parent topic (only `active_element` / `mesh_generation` / `weight_paint` exist), so `?` is generic. Closes the `backlog-ui-feedback.md` "subpanels repeat the parent help topic" item.
- **D3 Clickable see-also:** `help_dispatch` renders each see-also via `wm.path_open` (local path) or `wm.url_open` (http). Closes the standing "see-also not clickable" item.
- **D4 Online-docs button:** appears only when the topic carries a `doc_url` - no dead links before the docs exist.
- **D5 Docs base URL:** a constant in the registry for now (not a preference). Spec 024 may promote it later.
- **D6 Godot badge icon:** DEFERRED this pass - needs a PNG asset + `bpy.utils.previews` lifecycle. The `GODOT_READY` band keeps `CHECKMARK` until the art lands.
- **D7 Full i18n string migration:** DEFERRED - scaffold the canonical strings module + route the help strings through it, but do not migrate every label / description this pass ("translate as we go" per STUDY).

## Gate set (every change)

- [ ] `uvx ruff check apps/blender/`
- [ ] `uvx ruff format --check apps/blender/`
- [ ] `uv run --with mypy mypy --config-file apps/blender/pyproject.toml`
- [ ] `uv run pytest tests/` (repo root)
- [ ] Blender operator suite (`blender --background --python apps/blender/tests/run_operator_tests.py`) + fixture suite
- [ ] Whole-addon import sweep
- [ ] In-editor smoke (every `?` opens a topic-specific popup; see-also entries are clickable)

## Phase 1 - per-subpanel help topics (closes the tooltip-dup gap)

- [ ] `core/help_topics.py`: add topics `active_mesh`, `active_sprite`, `texture_region`, `bind`, `edit_weights`, `snapshot`, `sidecar_io`, `weight_transfer`, `automesh_alpha`, `automesh_interactive`, `debug_pipeline`, plus any slot / skeleton subpanels lacking one. Each = a short, tool-specific What / How (NOT the parent's overview). Cover the features the manual review flagged as unexplained (per-bone Soft / Hard, Snapshot, Sidecar IO, Weight Transfer).
- [ ] `panels/*`: pass each subpanel's own topic id as the `help_topic` arg of `draw_subpanel_header` (today they pass the parent's). Audit every `draw_subpanel_header(...)` + `draw_subbox_header(...)` call.
- [ ] Verify each subpanel `?` opens its own popup.

## Phase 2 - clickable see-also + doc links

- [ ] `core/help_topics.py`: `HelpTopic` gains optional `doc_path` / `doc_url`.
- [ ] `operators/help_dispatch.py`: render see-also refs as `wm.path_open` (local) / `wm.url_open` (http) operators instead of `layout.label`. Add an "Open online docs" button shown only when `doc_url` is set.
- [ ] Doc base URL constant + per-topic relative paths (only where a page exists).

## Phase 3 - tooltips + string-module scaffold (basics; full migration deferred)

- [ ] Ensure every panel / subpanel + operator carries a one-line `bl_description` / tooltip (the brief hover text, distinct from `?`).
- [ ] Scaffold `core/strings.py` (or `core/i18n.py`): a canonical map with stable keys, shaped for `bpy.app.translations`. Route the help-topic strings through it; leave label / description migration as a follow-up.

## Deferred (within 023, follow-up pass)

- Custom Godot badge icon (PNG + `previews` lifecycle) - D6.
- Full label / description i18n migration + per-locale tables - D7.

## Status - shipped (basics) on `feat/spec-023-024-help-prefs`

Phase 1 + Phase 2 shipped (commit 25af912):

- 14 per-subpanel help topics added; every subpanel now opens its own `?` topic instead of the parent's. The features the manual review flagged as unexplained (per-bone Soft / Hard, Snapshot, Sidecar IO, Weight Transfer) get real text.
- `HelpTopic.doc_url` added; see-also URLs render via `wm.url_open`; an "Open online docs" button shows only when a `doc_url` is set (no dead links).

Gates green: ruff, ruff-format, mypy (166 files), `pytest tests/` (613), Blender operator suite (50), fixture suite (7/7).

Deferred (follow-up pass):

- Phase 3 string-isolation module / full i18n migration - D7, "translate as we go".
- Custom Godot badge icon (PNG + `previews` lifecycle) - D6.
- Tooltip audit (most operators / fields already carry `bl_description`; Blender panels have no hover-tooltip slot).
- Migrating the local-path see-also refs (`specs/`, `examples/`) to online `doc_url`s once the docs site exists - they stay plain labels until then, since they do not resolve in an installed addon.
