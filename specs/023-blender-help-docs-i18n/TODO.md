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

Addon reference docs shipped on `feat/spec-023-help-docs`:

- New Docusaurus section "Blender addon" (sidebar + navbar) under `docs/02-blender-addon/` - an index + one page per sidebar panel, with brief per-panel / per-subpanel text mirroring the `?` help.
- `topic_for` fills each topic's `doc_url` from a central map pointing at the matching reference page + anchor, so the "Open online docs" button now lands somewhere real. Docusaurus build is clean.

Spec 023 finalized on `feat/spec-023-help-docs`:

- Custom Godot badge icon (D6): the official Godot mark loads via `bpy.utils.previews` and renders for the godot-ready band, falling back to `CHECKMARK` on a missing / headless load.
- i18n isolation (D7): `core/i18n.py` wires `bpy.app.translations` the idiomatic way - English stays inline as the msgid and Blender auto-translates registered strings, so no call-site rewrite. Per-locale tables are deferred (the STUDY non-goal), added by appending rows to `TRANSLATIONS`.
- Tooltip / help pass verified: 41/41 operators carry a tooltip (40 `bl_description` + the dynamic status-badge `description`), properties carry descriptions, and panel headers expose a hover tooltip (the status badge) plus the `?` detail popup. Blender panels have no hover-tooltip slot, so that is the complete surface.
- Help panel disposition (decided 2026-06-08): per-operator tooltips are satisfied in each operator's home panel - every operator carries a `bl_description` that shows on hover where the operator is a button. The Help panel stays the F3 idname cheat-sheet rather than duplicating those as runnable operator buttons (which would turn it into a launcher with an accidental-run foot-gun).
- See-also disposition: the inline `specs/` / `examples/` see-also refs stay plain labels because they do not resolve in an installed (zipped) extension; the working clickable docs link is the per-topic `doc_url` / "Open online docs" button. Migrating those refs to online URLs is the follow-up below.

With that, the 023 scope is concluded - the only open items are the explicit STUDY non-goal (per-locale translation tables) and one documented follow-up (migrating the local see-also refs to online URLs).

Deferred (STUDY non-goals + follow-ups):

- Per-locale translation tables - the actual `pt_BR` / other-language strings ("translate as we go").
- Migrating the inline see-also refs (`specs/`, `examples/`) to online links - the per-topic `doc_url` now points at the new reference, but the see-also entries themselves still render as plain labels (they do not resolve in an installed addon).
- Expanding the addon reference pages beyond the first-cut placeholders (screenshots, deeper per-tool detail) as the panels settle.
