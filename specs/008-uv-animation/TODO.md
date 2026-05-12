# SPEC 008 - TODO

Stub. Greenlit only when a concrete use case appears. See [STUDY.md](STUDY.md).

## Trigger to activate this SPEC

A user (or internal need) asks for one of:

- Animated water / fire / energy effects with continuous UV scroll.
- Conveyor-belt / treadmill style continuous-loop sprite.
- Region resize animation.

If the use case is "swap whole image" → SPEC 004 (slots) covers it. If "swap frame in grid" → SPEC 002 (sprite_frame) covers it. SPEC 008 is **only** for continuous region animation.

## Decisions to lock when SPEC opens

- [ ] D1 - track type name: `texture_region` vs `uv_animation`
- [ ] D2 - scope: sprite_frame only or polygon too
- [ ] D3 - interp options
- [ ] D4 - schema bump path (format v2 vs additive v1)
- [ ] D5 - authoring UX

## Implementation (pending greenlight)

- [ ] Schema: add `texture_region` track type to `schemas/proscenio.schema.json`
- [ ] Writer: walk action fcurves on `region_x/y/w/h`, emit track
- [ ] Importer: per-sprite-kind animation track building
- [ ] `tests/test_texture_region_track.py`
- [ ] Validation: warn (or error) on polygon target if scope-locked
- [ ] Fixture `flow_water/` (extends SPEC 007)

## Risk

Schema bump cascades. If v2 ships with this + Bezier preservation + animation events, migration becomes a single coordinated effort. Track that on `specs/backlog.md` "Format and schema".
