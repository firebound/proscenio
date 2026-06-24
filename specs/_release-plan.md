# Release plan - beta to 1.0 (disposable)

Throwaway working doc: not a spec, not the source of truth. The durable versioning convention lives in [`../.ai/conventions/layout.md`](../.ai/conventions/layout.md) "Versioning", [`../.ai/skills/release.md`](../.ai/skills/release.md), and the locked decision in [`decisions.md`](decisions.md). Delete this file once the beta to 1.0 funnel closes and the implementation follow-ups below are done.

## Version scheme (consolidated - see the convention)

Lockstep single product version `vX.Y.Z` across the three apps; `format_version` stays independent (frozen at v2 on the wire). Bump by highest severity across components; unchanged apps re-stamp and ride along. Pre-1.0 is `0.MINOR.PATCH` with `-beta` on the beta channel. The wire/disk `.proscenio` format is already v2 and the sprint does not touch it - that is what makes a beta-now safe.

## The funnel

### Beta gate -> `0.9.0-beta`

The full polish sprint closes first (decided: beta ships polished, not raw):

- 036 ui-help-surfaces - shipped + pruned 2026-06-18
- 043 outliner-selection - shipped + pruned 2026-06-18
- 044 weight-paint-mode-sync - shipped + pruned 2026-06-18
- 045 skeleton-quick-armature - shipped + pruned 2026-06-18
- 046 slots-list-ux - shipped + pruned 2026-06-18
- 047 godot-import-verify - shipped + pruned 2026-06-18
- 048 photoshop-read-perf - shipped (PR #133) + pruned 2026-06-18

The beta gate is closed. 036 and the 043-048 sprint shipped, and the post-036 polish (049-065) shipped on top (see [`_index.md`](_index.md)). `v0.9.0-beta` ships 2026-06-21. Exit criteria met: the Blender gate set is green on the 5.x dev target (207 operator tests + 8/8 goldens, 855 pytest, mypy clean), there are no open crashers (`backlog/bugs-found.md` is empty), and `CHANGELOG.md` is started.

### Beta window -> `0.9.x-beta`

- Collect feedback + real `.blend` files from testers.
- 037 storage-split SHIPPED 2026-06-24 (pruned, see [`_index.md`](_index.md)). The internal PG-vs-CP dual storage collapsed to one home per field; the disk `.proscenio` format did NOT move. No migrator ships: pre-release, there are no `.blend` in the wild, so the original 1.0.0 gate (field-validate a once-per-file migrator) dissolved and the split landed now rather than waiting on the beta. The GUI-only risks (undo through the proxies, disable -> save -> enable, Drive-from-Bone on the idprop path) are pinned by an in-Blender `test_storage_proxy`; a final manual GUI pass in the beta is still worthwhile but no longer gating.
- Beta bugfixes ship as `0.9.x`.

### 1.0.0 gate

- 037 landed (no migrator: pre-release, fixtures regenerate). DONE.
- `.proscenio` format declared stable (v2 frozen; freeze documented in `format-spec.md`).
- Polish complete, zero known crashers.
- 038 reach is OUT of 1.0 scope: Krita gated on demand, GIMP dropped, GDExtension gated on a measured trigger.

## Disciplines after the split (the storage contract is now load-bearing)

- New per-Object fields pick one home by the read boundary: export/headless-read or animatable -> a `proscenio_*` idprop behind a `get`/`set` proxy; pure-GUI -> a plain PropertyGroup field. Never a third hybrid state.
- Every export-side field read routes through `read_field` - keeps the one-home contract mechanical.

## Post-1.0

- Model-expanding features (proscenio-y-depth-layers, skin-coordination) ship as additive MINOR when they do not break the disk format; each STUDY decides whether it touches the schema. MAJOR (2.0) only if the disk format breaks.
- Spec-sized backlog (materials-panel, element-driver-management, incorporate-blender-mesh-as-element, qa-rotation-mode, qa-quickarm-interaction-revision) is post-1.0, demand-ordered.

## Implementation follow-ups (make lockstep real - NOT done by the convention edit)

- [x] Retarget `.github/workflows/release.yml` tag trigger to a single `v*` and build all three zips per tag (done 2026-06-21; the retired `blender-v*` / `godot-v*` / `photoshop-v*` prefixes are gone).
- [x] One version source of truth: a root `VERSION` (`0.9.1-beta`) sits beside the three manifests, which carry the numeric `0.9.1` (the Blender and UXP version fields are strict `x.y.z`, so the `-beta` channel lives on the git tag and `VERSION`). Auto-stamping the manifests from `VERSION` at build time stays a follow-up; the git tag is the effective source of truth for the artifact names.
- [x] Single `CHANGELOG.md` with per-app sub-bullets per release (started at `0.9.0-beta`).
- [x] `blender-multi-version-matrix` (see [`gated.md`](gated.md)): the `.blend` fixtures were rebuilt under Blender 4.2 (they open on 4.2 and 5.x) and the full headless suite now passes on 4.2 LTS (201 operator tests + 8/8 goldens) and on 5.x (207 + 8/8); a 4.2-only registration bug (the brush-preset operator's annotation) was fixed in passing. `blender_version_min 4.2.0` is verified, shipped in `v0.9.1-beta`.
- [ ] Walk the QA Companion checklist ([`tools/qa-companion/checklist/`](../tools/qa-companion/checklist/)) for any `pending` / `regressed` item in the changed areas - **deferred to the beta window** (10 `regressed` rows outstanding). This is the GUI-smoke gate; the retests are walkable items in the checklist, the locked owner of the manual-test surface.
