# Execution map

Status: active. The backlog aggregated into thematic specs.

The 027-035 wave shipped (PRs #104-#113) and those nine spec folders are pruned (see [_index.md](_index.md)). Their resolved rows left the backlogs; the not-now rows moved to [DEFERRED.md](DEFERRED.md), [GATED.md](GATED.md), and [DROPPED.md](DROPPED.md); the GUI-retest rows ride the Verification session below. What stays active here is the three not-yet-started thematic specs (ui-help-surfaces, storage-split, reach) plus that verification session. The operational companion is [PLAN.md](PLAN.md).

Tags: `[blocking]` clears before the tag; `[w1]`..`[w5]` post-release wave; `[retest]` a GUI re-check folded into the verification session; `[pf]` a first-impression pull-forward candidate.

## Shipped wave (027-035, pruned)

The 2026-06-11 effort evaluation scored every item now / defer / gate / drop; the **now** items shipped and were code-verified against each PR (not the spec checkboxes, which proved unreliable). Per-spec carve-out (counts approximate; a few rows split into halves, so totals run slightly above the row count):

| Spec | Shipped (now) | -> GATED | -> DEFERRED | -> DROPPED | PR |
| --- | --- | --- | --- | --- | --- |
| 027 export-correctness | 5 | 0 | 0 | 0 | #104 |
| 028 schema-expressiveness | 5 | 12 | 2 | 1 (visibility, retired in-code) | #105 |
| 029 mesh-authoring | 7 | 1 | 0 | 1 | #106 |
| 030 skinning-weight-paint | 12 | 1 (+2 extensions) | 0 | 6 | #107 |
| 031 rigging-and-posing | 8 | 9 | 0 | 10 | #108 |
| 032 slot-attachments | 5 | 1 | 2 | 0 | #109 |
| 033 atlas-packing | 9 | 3 | 1 | 3 | #110 |
| 034 photoshop-plugin | 1 (+1 retest) | 6 | 0 | 3 | #111 |
| 035 project-health | 6 | 9 | 0 | 5 | #112 / #113 |

Retests (code shipped, GUI smoke pending) ride the Verification session: 027 `slot-transform-keys`, 029 `automesh-interactive-extend-cut`, 031 `skeleton-row-click-select` + `pose-save-library-precheck`, 034 `waist-1px-drift`.

The locked design calls from this wave are in [decisions.md](decisions.md). The per-item reasoning is in each pruned spec's STUDY.md (recover from git history via `git log --all --diff-filter=A -- 'specs/NNN-*/STUDY.md'`).

## Active thematic specs

### 036 - ui-help-surfaces

Editor UI not tied to a single tool domain: help/docs, small panel polish, and the new panels.
Surface: `panels/*`, help system, `docs/`, `outliner.py`, `object_props.py`, `uv_authoring.py`.

- `[blocking]` sprite-frame-preview-help-orphan - `draw_subbox_header` regressed to zero callers.
- `[w4]` active-sprite: reproject-uv-orientation (replace `smart_project`; perf retest), header-mesh-name, clamp-initial-frame, rename-initial-frame, centered-vs-origin-help.
- `[w4] [pf]` outliner left-align-names, validation frame-unhide-on-click.
- `[w4]` outliner indented-tree; validation validator-element-rename.
- `[w4]` help/docs: see-also-clickable, help-panel-popup-button, merge-diagnostics-help, i18n-locale-tables, see-also-online-urls, addon-docs-screenshots, docs-url-preference, guide-doc-rename-sweep.
- `[w4]` cross-panel: panel-helper-consolidation, subpanel-drag-reorder (subpanel half upstream-limited).
- `[w4]` new surfaces: materials-panel, onion-skin-overlay, joystick-slider-blend.

### 037 - storage-split

Collapse the dual-fallback PG-vs-CP storage by intent. Architecturally distinct, 1.0.0-gated, breaking.
Surface: `mirror.py`, `hydrate.py`, writer `read_field`.

- `[w3]` pg-cp-storage-split - lands behind the schema-expressiveness migration path (the `format-migration-path` gate); blocks 1.0.0, not the first tag.

### 038 - reach

New surfaces with the lowest gain-per-effort right now.
Surface: new `apps/`.

- `[w5]` krita-exporter (Phase 2), gimp-exporter, gdextension-escape-hatch (gated on triggers; see [GATED.md](GATED.md) / [backlog.md](backlog.md)).

## Verification session (not a spec)

One GUI pass closes the `[retest]` rows from the shipped wave (slot-transform-keys, automesh-interactive-extend-cut, skeleton-row-click, pose-save-precheck, waist-1px-drift) plus the 036 reproject-uv perf retest, plus the cross-app roundtrip bar: doll PS->Blender->Godot end to end, `slot_swap`, `slot_cycle`. Known waivers re-measured here: waist 1px, PPU=100. The hands-on checklist lives in [manual-testing.md](manual-testing.md) (being repopulated; the open retest slugs carry `needs-retest` in [BACKLOGS_SUMMARY.md](BACKLOGS_SUMMARY.md)).

## Upstream-watch (no spec)

- qa-gizmo-crash - Blender/AMD internals; defensive try/except shipped; watch only.
