# QA Companion

A local tool to walk and curate the Proscenio manual-test checklists. The product surface is large and the audit that seeded it was LLM-generated, so the tool exists to make a human pass over every panel, control, and flow practical: record what works, write notes, paste screenshots, and prune or rewrite the tests themselves as you go.

The checklist `.md` files under [`checklist/`](checklist/) are the source of truth. The tool parses them, serves a local UI, and writes every change straight back to the `.md` - there is no parallel database. The walk record (status, notes, screenshot references) and the curation (edited wording, added or removed tests) all live in those files, reviewable in git.

The surface was mapped by the spec 040 pass (an automatic, code-read audit of the whole product); that spec is retired and its two outputs now live here: the walkable [`checklist/`](checklist/) and the [`findings.md`](findings.md) audit (suspected divergences to verify during the walk, then promote to `specs/backlog/bugs-found.md`).

## Run

```sh
pnpm --dir tools/qa-companion install   # once
pnpm --dir tools/qa-companion walk      # serves http://127.0.0.1:8040
```

Open the URL. The **Tests** tab is the walk: pick a test on the left, the card on the right is where you walk it. The **Feedback** tab is a separate page for panel-level notes (see below).

- `status` answers "does the feature pass": `pending` / `pass` / `fail` / `blocked` / `n/a` / `regressed`. Keys `1`-`5` set it, `0` resets to pending.
- `review` answers "is this test worth keeping": `keep` / `rephrase` / `drop` / `todo`. `drop` archives the block to `checklist/removed.md` with a reason.
- The note field and any pasted/dropped screenshot persist as you type. Prints land in `walk-screenshots/<id>-<n>.png`.
- Panel feedback lives in its own **Feedback** tab, deliberately isolated from the test cards: it is product feedback about a panel (`ui` / `remove` / `bug` / `perf` / `code` / `note` + text), e.g. "the second search field is redundant, remove it", not a test result. Each panel (a checklist group) has one feedback list; the `&#9873;` button on a group header jumps to that panel in the Feedback tab. Entries persist to `checklist/feedback.md` and normalize into the backlog later - separate from a test's `review` (a verdict on the test) and `status` (the feature's result).
- Edit any field inline to rephrase a test. The `+` on a group header adds a new test with an allocated id. Adds and removes use an in-page dialog (the VS Code webview blocks `window.prompt`).

Everything autosaves to the owning `.md` file (the whole file is re-serialized atomically). Review the diff in git before committing.

## Format

Each item is one unified block:

```markdown
### PS-EXPORT-14 · Export manifest + PNGs
- status: pass
- review: keep
- steps:
  1. Pick a folder, open a layered PSD.
  2. Click Export manifest + PNGs.
- observe: green "Wrote N entries"; the JSON and images/*.png appear on disk.
- note: worked; one print attached
- shots:
  - walk-screenshots/PS-EXPORT-14-1.png
```

Scalar fields are single-line; `steps` and `shots` are sublists; `note` is free multiline. No tables means no pipe-escaping, so the parse -> edit -> serialize cycle is byte-stable.

Panel feedback is not part of a test block - it is scoped to a panel (a checklist group), so it lives in `feedback.md`, one section per area:

```markdown
## BL · Outliner panel
- remove: the second (non-native) search field is redundant
- ui: revisit the panel layout
```

Each line is `kind: text` (a line with no kind defaults to `note`); emptying an area's list drops its section. The area header is `<APP> · <group>`, so it round-trips back to the owning checklist file.

## Layout

- `src/format.ts` - the block model and id helpers.
- `src/parse.ts` / `src/serialize.ts` - the test-block round-trip core (pure, idempotent).
- `src/feedback.ts` - the `feedback.md` round-trip core (panel-level feedback, by area).
- `src/store.ts` - the filesystem layer: load, upsert, remove-to-archive, id allocation, panel-feedback load/upsert, screenshot decode.
- `src/server.ts` - the `node:http` server (UI + JSON API, bound to `127.0.0.1`).
- `src/normalize.ts` - one-shot: rewrite every checklist through the serializer to the canonical form.
- `public/` - the static UI (no build step).
- `checklist/` - the test surface (one block per item); `removed.md` archives dropped tests; `feedback.md` holds panel-level feedback by area.
- `findings.md` - the spec 040 code-read audit (suspected divergences) that seeds the walk.
- `walk-screenshots/` - pasted prints, referenced from item `shots` (created on first paste).

## Develop

```sh
pnpm --dir tools/qa-companion test        # vitest: parse / serialize / round-trip / feedback / store
pnpm --dir tools/qa-companion typecheck    # tsc --noEmit
```

The round-trip suite asserts the model survives a serialize cycle on the real checklists, so a parser change that would drop data fails the build.

## Notes

- Screenshots are committed as plain files. A print over ~1 MB will trip the repo's `check-added-large-files` hook; downscale it or keep prints to the relevant panel.
- The tool is local-only and not part of the shipped product; it has its own `package.json` and is not in a pnpm workspace.
