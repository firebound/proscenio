# tag_smoke fixture (SPEC 011 v1)

Synthetic layer tree that exercises every bracket tag in the SPEC 011 v1 taxonomy in one shot. No PSD file on disk - the input is a TypeScript object literal in [`apps/photoshop/uxp-plugin-tests/tag-smoke.test.ts`](../../../../apps/photoshop/uxp-plugin-tests/tag-smoke.test.ts); the planner runs against it and the emitted manifest is snapshot-diffed against [`tag_smoke.expected.json`](tag_smoke.expected.json).

## Why no PSD?

The full doll round-trip oracle (`examples/authored/doll/02_photoshop_setup/doll_tagged.psd`) already proves the PS-DOM side - export from a real PSD, every PNG written, XMP round-tripped. `tag_smoke` exists to lock the **planner-side semantics** of every tag into CI: the algorithm that turns a tag bag into a `format_version: 2` manifest entry. Pure logic. Mocking the layer tree in TypeScript is enough; spinning up Photoshop is not.

## Tag coverage

| Tag | Where in the synthetic tree | Asserted in test |
| --- | --- | --- |
| `[ignore]` | `ignored_layer [ignore]` | excluded from manifest |
| `[merge]` | `hair [merge]` group with multi-child | one polygon entry, children flattened |
| `[folder:NAME]` | `body [folder:body]` parent group | `subfolder = "body"` on descendants |
| `[polygon]` (explicit) | `torso [polygon]` | `kind = "polygon"` (no inference change) |
| `[mesh]` | `chest [mesh]` | `kind = "mesh"` |
| `[spritesheet]` | `eyes [spritesheet]` group | one sprite_frame entry with frames[] |
| `[origin]` marker | `pivot [origin]` child of `eyes [spritesheet]` | sprite_frame `origin` = marker centre |
| `[origin:X,Y]` | `arm [origin:10,20]` | `origin = [10, 20]` |
| `[scale:N]` | `arm [scale:2.0]` | bbox dimensions multiplied by 2 |
| `[blend:multiply]` | `chest_mult [blend:multiply]` | `blend_mode = "multiply"` |
| `[blend:screen]` | `eye_L_scrn [blend:screen]` | `blend_mode = "screen"` |
| `[blend:additive]` | `eye_R_add [blend:additive]` | `blend_mode = "additive"` |
| `[path:NAME]` | `arm [path:weapon]` | `path = "images/.../weapon.png"` |
| `[name:pre*suf]` | `hands [name:lh_*]` group | parser accepts; manifest carries cascaded names (planner does not rewrite in v1) |
| **Nested `[merge]` inside `[merge]`** | `outer [merge]` containing `inner [merge]` | inner collapses into outer; one entry emitted, no `sprite-frame-malformed` warning |

The nested-merge case is the regression most likely to bite future planner refactors: the doll fixture covers it once at the spritesheet level (frame `1.1 [merge]` inside frame `1 [merge]` collapses to two frames, not three). `tag_smoke` pins the behaviour at the polygon level too.

## Regenerate the golden

```sh
cd apps/photoshop
pnpm run test -- --update tag-smoke
```

`--update tag-smoke` rewrites `tag_smoke.expected.json` from the current planner output. Run only after a deliberate planner change; commit the golden alongside the code change so the diff documents the new behaviour.

## What this fixture catches when broken

- A tag that silently stops surfacing on the manifest entry (origin / blend / subfolder / path).
- Nested `[merge]` regressions (frame collapse, polygon collapse).
- Sprite_frame origin-marker resolution drift.
- `[scale:N]` arithmetic regression.
- `[ignore]` skip path bypass.
- `format_version` regression.
