# Blender addon help, docs, and i18n system

Status: **scope sketched, not started**. Successor to spec 022 (UI restructure). 022 ships the structural shell - every panel and subpanel carries a status badge and a `?`, using the existing Blender icons. This spec gives those affordances their behaviour: brief tooltips everywhere, a `?` popup that links out to the Proscenio docs, a custom Godot badge icon, and the single-source string isolation that makes a later translation pass possible.

This is the second spec of the `apps/blender` UI/UX review series (019 naming, 022 structure, 023 help/docs/i18n, 024 preferences).

## Problem

After 022 the sidebar reads well structurally, but the help layer is thin and inconsistent: the `?` popups show inline text only, the see-also references render as plain labels that look clickable but are not, there is no link to any external documentation, the godot/blender distinction rides on a generic checkmark instead of a distinct mark, and every user-facing string is inlined at its draw site, so there is no path to translation.

## Scope (sketch)

- **Brief tooltip on every panel and subpanel.** A one-line hover description (the panel/field description), distinct from the `?` popup. Tooltips are plain strings - the doc link lives in the `?`, not the tooltip (a Blender constraint: tooltips cannot hold clickable links).
- **`?` popup upgrade.** Keep the inline explanation (reuse `core/help_topics.py`), make the see-also references clickable (`wm.path_open` for local paths, `wm.url_open` for URLs), and add an "Open online docs" button that appears only when a doc path is registered - so no dead links ship before the docs exist. Closes the standing backlog item about non-clickable see-also refs.
- **Doc-link registry.** One module mapping `feature_id -> {site, path}`. The `?` builds the full URL. Until a page exists the online button stays hidden.
- **Custom Godot badge icon.** Replace the `CHECKMARK` for `GODOT_READY` with a distinct Godot/robot mark loaded via `bpy.utils.previews` (the addon ships a small PNG). The blender-only band keeps its authoring icon.
- **String isolation for i18n.** Move every user-facing string (labels, descriptions/tooltips, doc paths) into one canonical module with stable keys, shaped so `bpy.app.translations` can wrap it later. Build the isolation now; the actual per-locale translation tables are deferred ("translate as we go").
- **Help panel.** Per-operator tooltips drawn from the same isolated descriptions.

## Decisions to lock (when promoted)

- Registry shape and home (a data module vs extending `help_topics.py`).
- The Godot icon art + the `previews` lifecycle (register/unregister hook).
- The string-isolation module layout and key scheme (so 022's labels migrate cleanly).
- Whether the online docs site URL is a constant or itself a preference (ties to spec 024).

## Non-goals

- The actual translations (per-locale tables) - a later pass once the strings are isolated.
- The addon preferences surface - spec 024 (though the docs site URL may land there).
- Any structural panel change - that is spec 022.

## Related

- [`../022-blender-ui-restructure/STUDY.md`](../022-blender-ui-restructure/STUDY.md): the structural shell this spec gives behaviour to (the badge + `?` header convention).
- [`../021-blender-ui-audit/DESIGN-NOTES.md`](../021-blender-ui-audit/DESIGN-NOTES.md): the help/doc-link/i18n decisions captured during the audit (reframe: tooltip is brief, the link lives in the `?`).
- [`../backlog-ui-feedback.md`](../backlog-ui-feedback.md): the "see-also references are not clickable" item this spec closes.
