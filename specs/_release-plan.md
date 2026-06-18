# Release plan - beta to 1.0 (disposable)

Throwaway working doc: not a spec, not the source of truth. The durable versioning convention lives in [`../.ai/conventions/layout.md`](../.ai/conventions/layout.md) "Versioning", [`../.ai/skills/release.md`](../.ai/skills/release.md), and the locked decision in [`decisions.md`](decisions.md). Delete this file once the beta to 1.0 funnel closes and the implementation follow-ups below are done.

## Version scheme (consolidated - see the convention)

Lockstep single product version `vX.Y.Z` across the three apps; `format_version` stays independent (frozen at v2 on the wire). Bump by highest severity across components; unchanged apps re-stamp and ride along. Pre-1.0 is `0.MINOR.PATCH` with `-beta` on the beta channel. The wire/disk `.proscenio` format is already v2 and the sprint does not touch it - that is what makes a beta-now safe.

## The funnel

### Beta gate -> `0.9.0-beta`

The full polish sprint closes first (decided: beta ships polished, not raw):

- 036 ui-help-surfaces (still open)
- 043 outliner-selection - shipped + pruned 2026-06-18
- 044 weight-paint-mode-sync - shipped + pruned 2026-06-18
- 045 skeleton-quick-armature - shipped + pruned 2026-06-18
- 046 slots-list-ux - shipped + pruned 2026-06-18
- 047 godot-import-verify - shipped + pruned 2026-06-18
- 048 photoshop-read-perf - shipped (PR #133) + pruned 2026-06-18

Only 036 remains before the beta gate closes (043-048 audited done; see [`_index.md`](_index.md)). Exit criteria: full Blender gate set green, zero known crashers, `CHANGELOG.md` started.

### Beta window -> `0.9.x-beta`

- Collect feedback + real `.blend` files from testers.
- Land 037 storage-split here. It is the one breaking change, but internal only: the disk `.proscenio` format does NOT move. Validate the one-shot migrator against real pre-split `.blend` files - undo through the proxy widgets, the disable -> save -> enable cycle, and Drive-from-Bone retargeted onto CP paths. The beta tester population is exactly the GUI coverage 037's STUDY says it needs and that headless tests cannot give.
- Beta bugfixes ship as `0.9.x`.

### 1.0.0 gate

- 037 landed + migrator validated in the field.
- `.proscenio` format declared stable (v2 frozen; freeze documented in `format-spec.md`).
- Polish complete, zero known crashers.
- 038 reach is OUT of 1.0 scope: Krita gated on demand, GIMP dropped, GDExtension gated on a measured trigger.

## Disciplines during the beta (from 037's STUDY, to protect the split diff)

- New fields keep the uniform-mirror convention - never a third hybrid storage state.
- Every new field read routes through `read_field` - keeps the eventual mirror retirement one-home mechanical.

## Post-1.0

- Model-expanding features (proscenio-y-depth-layers, skin-coordination) ship as additive MINOR when they do not break the disk format; each STUDY decides whether it touches the schema. MAJOR (2.0) only if the disk format breaks.
- Spec-sized backlog (materials-panel, element-driver-management, incorporate-blender-mesh-as-element, qa-rotation-mode, qa-quickarm-interaction-revision) is post-1.0, demand-ordered.

## Implementation follow-ups (make lockstep real - NOT done by the convention edit)

- [ ] Retarget `.github/workflows/release.yml` tag trigger from `blender-v*` / `godot-v*` / `photoshop-v*` to a single `v*`, and build all three zips per tag.
- [ ] One version source of truth (a root `VERSION` or the git tag) stamped into `blender_manifest.toml`, the Godot `plugin.cfg`, and the Photoshop `manifest.json` at release.
- [ ] Single `CHANGELOG.md` with per-app sub-bullets per release.
- [ ] Re-run the gated `blender-multi-version-matrix` check before the first public `v*` tag (its trigger was keyed to `blender-v*`; see [`gated.md`](gated.md)).
