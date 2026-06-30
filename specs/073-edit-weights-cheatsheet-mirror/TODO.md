# Spec 073 TODO: Edit Weights panel cheatsheet mirror

Drives [STUDY](STUDY.md). One quick-win: give Edit Weights the panel cheatsheet mirror every other interactive tool already has. Decisions LOCKED.

## 1. Chord vocabulary

- [x] New `operators/skinning/_status_bar.py` with `emit_edit_weights_chords(layout)` on the shared `chord` primitive (ESC exit + mirror-source read-out).
- [x] `edit_weights.py` `_draw_statusbar_edit_weights` keeps the title row, delegates the chords to `emit_edit_weights_chords`.

## 2. Panel mirror

- [x] `weight_paint.py` `_draw_edit_weights_shortcuts(layout)` - collapsible `layout.panel("proscenio_edit_weights_shortcuts", default_closed=True)`, gated on `PROSCENIO_OT_edit_weights_modal._statusbar_appended`, emits the chords into the body.
- [x] Call it from `PROSCENIO_PT_edit_weights.draw`.

## 3. Docs + backlog

- [x] `.ai/conventions/code.md` "Interactive-tool gesture cheatsheet" - list all four tools; drop the "not yet" note.
- [x] Remove `interactive-cheatsheet-cross-tool` from [`backlog/ui-feedback.md`](../backlog/ui-feedback.md).

## 4. Gates

- [ ] ruff + mypy (`--config-file apps/blender/pyproject.toml`) + repo-root `uv run pytest tests/` + `run_operator_tests.py` + `run_tests.py` goldens (8/8 - no writer surface touched).

## 5. Post-merge cleanup (ONLY after squash-merge)

- [ ] Prune this spec folder; index in [`_index.md`](../_index.md) with the PR number (073 -> pruned).
