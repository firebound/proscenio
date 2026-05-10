# Status

Live state. For project overview see [README](README.md). For locked decisions see [`docs/DECISIONS.md`](docs/DECISIONS.md). For per-SPEC design see [`specs/`](specs/).

## Current

- **Branch in flight:** `feat/spec-009-modularity` (PR #33 in review).
- **SPEC 009 — code modularity:** waves 9.1 to 9.9 shipping behavior-preserving package splits across writer, panels, operators, validation. No format change.
- **Format:** `format_version=1`. No bump pending.

## Recent waves

| PR | Wave | Branch |
| --- | --- | --- |
| #32 | 5.1.d.6 - README polish | `feat/spec-005.1.d.6-readme-polish` |
| #31 | 5.1.d.4 - sprite-centric outliner + favorites | `feat/spec-005.1.d.4-outliner` |
| #30 | 5.1.d.3 - quick armature (modal click-drag bone draw) | `feat/spec-005.1.d.3-quick-armature` |
| #29 | 5.1.d.2 - pose library shim | `feat/spec-005.1.d.2-pose-library` |
| #28 | 4.4 - SPEC 004 close-out (doll brow promotion + skills) | `feat/spec-004.4-close-out` |

For older history see `git log --oneline`.

## Fixtures in CI

Five Type A fixtures auto-walked by `run_tests.py`: [`doll`](examples/authored/doll/), [`blink_eyes`](examples/blink_eyes/), [`shared_atlas`](examples/shared_atlas/), [`simple_psd`](examples/simple_psd/), [`slot_cycle`](examples/slot_cycle/).

## Open work

- **Manual smoke tests** that do not fit headless CI: see [`MANUAL_TESTS_PENDING.md`](MANUAL_TESTS_PENDING.md) (untracked, local).
- **Plugin-uninstall test** verified manually for SPEC 000; CI automation pending in [`specs/backlog.md`](specs/backlog.md).
- **CI matrix expansion** (Blender 4.2 LTS + Godot 4.3) tracked in `specs/backlog.md`.

## Mocks / placeholders

- **Doll brow** marked as future home for slots; `slot_cycle` covers slot mechanics in isolation.
- **`format-spec.md`** does not exist; schema docstring is the source.

## Next planned work (not committed)

After SPEC 009 lands the planned next slice is **SPEC 008 (UV animation, `texture_region` track)**. Design rough in [`specs/008-uv-animation/STUDY.md`](specs/008-uv-animation/STUDY.md). After that, deferred items are listed in [`docs/DEFERRED.md`](docs/DEFERRED.md); finer-grained backlog is [`specs/backlog.md`](specs/backlog.md).
