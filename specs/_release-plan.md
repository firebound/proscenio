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

- [x] Retarget `.github/workflows/release.yml` tag trigger to a single `v*` and build all three zips per tag (done 2026-06-21; the retired `blender-v*` / `godot-v*` / `photoshop-v*` prefixes are gone).
- [x] One version source of truth: a root `VERSION` (`0.9.0-beta`) sits beside the three manifests, which carry the numeric `0.9.0` (the Blender and UXP version fields are strict `x.y.z`, so the `-beta` channel lives on the git tag and `VERSION`). Auto-stamping the manifests from `VERSION` at build time stays a follow-up; the git tag is the effective source of truth for the artifact names.
- [x] Single `CHANGELOG.md` with per-app sub-bullets per release (started at `0.9.0-beta`).
- [~] `blender-multi-version-matrix` (see [`gated.md`](gated.md)): Blender 4.2 LTS loads and registers the addon, runs the fixture-free operator tests, and passes `extension validate` on the manifest, but the committed `.blend` fixtures were saved in Blender 5.x and 4.2 cannot open them, so the full headless suite cannot run on 4.2 yet. Rebuilding the fixtures under 4.2 (they then open in both) to run the full matrix is a beta-window task. `blender_version_min` stays `4.2.0`.
- [ ] Walk the QA Companion checklist ([`tools/qa-companion/checklist/`](../tools/qa-companion/checklist/)) for any `pending` / `regressed` item in the changed areas - **deferred to the beta window** (10 `regressed` rows outstanding). This is the GUI-smoke gate; the retests are walkable items in the checklist, the locked owner of the manual-test surface.
