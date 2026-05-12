# Status

Live state. For project overview see [README](README.md). For locked decisions see [`docs/DECISIONS.md`](docs/DECISIONS.md). For per-SPEC design see [`specs/`](specs/).

## Current

- **Branch in flight:** `refactor/photoshop` (PR #46 in review).
- **SPEC 010 - Photoshop UXP migration:** shipped through Wave 10.8. Legacy JSX exporter / importer retired; UXP plugin owns both directions of the manifest roundtrip. Doll oracle confirmed pixel-byte parity vs the captured JSX baseline.
- **Format:** `format_version=1`. SPEC 011 will bump to v2 once tag taxonomy lands.

## Recent waves

| PR | Wave | Branch |
| --- | --- | --- |
| #46 | SPEC 010 (10.1 - 10.8) - Photoshop UXP migration | `refactor/photoshop` |
| #32 | 5.1.d.6 - README polish | `feat/spec-005.1.d.6-readme-polish` |
| #31 | 5.1.d.4 - sprite-centric outliner + favorites | `feat/spec-005.1.d.4-outliner` |
| #30 | 5.1.d.3 - quick armature (modal click-drag bone draw) | `feat/spec-005.1.d.3-quick-armature` |
| #29 | 5.1.d.2 - pose library shim | `feat/spec-005.1.d.2-pose-library` |

For older history see `git log --oneline`.

## Fixtures in CI

Five Type A fixtures auto-walked by `run_tests.py`: [`doll`](examples/authored/doll/), [`blink_eyes`](examples/generated/blink_eyes/), [`shared_atlas`](examples/generated/shared_atlas/), [`simple_psd`](examples/generated/simple_psd/), [`slot_cycle`](examples/generated/slot_cycle/).

## Open work

- **Manual smoke tests** that do not fit headless CI: see [`MANUAL_TESTS_PENDING.md`](MANUAL_TESTS_PENDING.md) (untracked, local).
- **Plugin-uninstall test** verified manually for SPEC 000; CI automation pending in [`specs/backlog.md`](specs/backlog.md).
- **CI matrix expansion** (Blender 4.2 LTS + Godot 4.3) tracked in `specs/backlog.md`.

## Mocks / placeholders

- **Doll brow** marked as future home for slots; `slot_cycle` covers slot mechanics in isolation.
- **`format-spec.md`** does not exist; schema docstring is the source.

## Next planned work (not committed)

After PR #46 merges, the next slice is **SPEC 011 (Photoshop tag system + plugin UI mini-app)**. Design locked in [`specs/011-photoshop-tag-system/STUDY.md`](specs/011-photoshop-tag-system/STUDY.md); bracket-tag taxonomy, schema v2 bump, in-panel tagging UI. **SPEC 008 (UV animation, `texture_region` track)** queues behind that - design rough in [`specs/008-uv-animation/STUDY.md`](specs/008-uv-animation/STUDY.md). Deferred items in [`docs/DEFERRED.md`](docs/DEFERRED.md); finer-grained backlog in [`specs/backlog.md`](specs/backlog.md).
