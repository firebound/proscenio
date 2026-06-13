# Checklist - cross-app flows

The end-to-end scripts that string Photoshop -> Blender -> Godot (or the relevant
subset) together. Each flow is a numbered, re-runnable manual-test script: a human
walks it before a release tag, confirming the checkpoint at the end of every step,
then records the end state.

Format conventions: [STUDY.md](../STUDY.md). Per-app widget/operator tables live in
[blender.md](blender.md), [photoshop.md](photoshop.md), [godot.md](godot.md); this file
references their item IDs in parentheses where a flow step exercises one specific control.

## Tokens

`FLOW-<TOKEN>-NN` - stable IDs for the cross-app scripts.

| Token | Flow family | Anchor fixture |
| --- | --- | --- |
| `DOLL` | full rigged roundtrip (skinning + actions) | [`examples/authored/doll/`](../../../examples/authored/doll/) |
| `SLOTSWAP` | slot system + bone swing | [`examples/generated/slot_swap/`](../../../examples/generated/slot_swap/) |
| `SLOTCYCLE` | slot system, 3 attachments cycling | [`examples/generated/slot_cycle/`](../../../examples/generated/slot_cycle/) |
| `ATLAS` | atlas packer Pack / Apply / Unpack | [`examples/generated/atlas_pack/`](../../../examples/generated/atlas_pack/) |
| `PSD` | PSD-sourced manifest import roundtrip | [`examples/generated/simple_psd/`](../../../examples/generated/simple_psd/), [`examples/authored/doll/`](../../../examples/authored/doll/) |
| `REIMPORT` | wrapper-scene reimport safety | [`examples/authored/doll/04_godot_import/`](../../../examples/authored/doll/04_godot_import/) |

## Status vocabulary

`pending` · `pass` · `fail` · `blocked` · `n/a` · `regressed` (see [STUDY.md](../STUDY.md#status-vocabulary)).
A `fail` / `regressed` MUST carry a one-line repro and cross-link a row in
[backlog-bugs-found.md](../../backlog-bugs-found.md). `blocked` cites the upstream flow/item ID that failed.

---

## DOLL - full rigged roundtrip

### [ ] FLOW-DOLL-01 · doll: tagged PSD -> rigged Blender import  (PS -> Blender)
- **Pre:** `examples/authored/doll/02_photoshop_setup/doll_tagged.psd` open in Photoshop; a clean Blender file; output folder empty.
1. PS: Exporter > pick the output folder (PS-EXPORT-02) -> the chosen path is shown and remembered.
2. PS: Exporter > `Export manifest + PNGs` (PS-EXPORT-14) -> a v2 manifest JSON plus one PNG per visible layer land side by side in the output folder; no validation error dialog (PS-EXPORT-23).
3. Blender: Active Sprite subpanel > `Import Photoshop Manifest`, point at the manifest (BL-PIPE-06) -> every tagged layer becomes a quad sprite at its pivot/region; a stub `doll.rig` armature with one root bone appears and parents every mesh.
4. Blender: Outliner subpanel, filter for a known mesh and click its row (BL-OUTLN-07) -> the clicked sprite (e.g. `chest`) becomes the active object and its textures resolve (no pink/missing).
- **Expect (end state):** all doll layers present as quads, parented to the single-bone stub rig, textures resolved, names tag-stripped.
- **Status:** pending

### [ ] FLOW-DOLL-02 · doll: build skeleton + skin + animate  (Blender)
- **Pre:** FLOW-DOLL-01 imported set in Blender, or open `examples/authored/doll/03_blender_setup/doll_rigged.blend` (Save As a workbench copy first).
1. Blender: Skeleton subpanel > `Quick Armature` (BL-SKEL-19), draw a bone chain head->tail with LMB press-drag (BL-SKEL-20), then `Enter` to confirm (BL-SKEL-26) -> bones land Front-Ortho-aligned; the on-screen cheatsheet tracked the cursor; no leaked draw handler on exit.
2. Blender: Skeleton subpanel > `Use existing armature` for `doll.rig` (BL-SKEL-07) -> the picker armature is set as the bind target.
3. Blender: Skinning subpanel > `Bind to Picker Armature` (BL-WPAINT-13) -> each mesh gains bone-named vertex groups and follows the pose.
4. Blender: Skinning subpanel > `Edit Weights` (BL-WPAINT-17), paint one stroke (BL-WPAINT-18), then `ESC` to exit (BL-WPAINT-19) -> weights update on the painted mesh; modal exits cleanly.
5. Blender: Animation subpanel, click the `idle` action row (BL-ANIM-06), scrub the timeline -> the spine bob plays; the read-only action summary lists `idle`, `wave`, `walk`.
- **Expect (end state):** doll rig with bone-named vertex groups deforming the meshes; the three authored actions present and playable.
- **Status:** pending

### [ ] FLOW-DOLL-03 · doll: validate, export, Godot import  (Blender -> Godot)
- **Pre:** FLOW-DOLL-02 rigged/skinned/animated doll in Blender; a clean `apps/godot` (or example) project folder.
1. Blender: Export subpanel > `Validate` (BL-VALID-03) -> validator passes (every sprite checks against armature, atlas, required fields); zero blocking issue rows (BL-VALID-07).
2. Blender: Export subpanel > `Export (.proscenio)` (BL-PIPE-14) -> a `.proscenio` JSON is written next to the `.blend`; the per-mesh PNGs are referenced by filename.
3. Godot: copy the `.proscenio` and every PNG it names into one flat folder; let the importer run (GD-IMPORT-06) -> the scene regenerates in build order skeleton -> atlas -> slots -> mesh/sprite -> animation (GD-IMPORT-07); no missing-dependency dialog.
4. Godot: instance the generated scene under a wrapper and play `idle` (GD-BUILD-29) -> the textured, skinned doll renders and the spine-bob animation plays; skinned `Polygon2D` meshes deform with the `Skeleton2D` (GD-BUILD-18).
- **Expect (end state):** the Godot scene renders the textured, rigged doll; `idle`/`wave`/`walk` populate the AnimationPlayer library; no missing-resource errors.
- **Status:** pending

---

## SLOTSWAP - slot system + bone swing

### [ ] FLOW-SLOTSWAP-01 · slot_swap: author the slot + swing action  (Blender)
- **Pre:** open `examples/generated/slot_swap/slot_swap.blend` (Save As `slot_swap_workbench.blend`); addon enabled.
1. Blender: select the `arm` mesh plus the `club`/`sword` meshes, Skeleton subpanel > `Create Slot` (BL-SLOT-07) -> a slot Empty `weapon` is anchored under the active bone and the selected meshes become its attachments (or confirm the prebuilt `weapon` slot exists).
2. Blender: select the `weapon` Empty; the Active Slot subpanel appears (BL-SLOT-11) listing `club` and `sword` as attachments (BL-SLOT-04).
3. Blender: mark `club` as the default via its SOLO star (BL-SLOT-17) -> `club` is the load-time visible attachment; `sword` hidden.
4. Blender: scrub the `swing` action timeline -> arm swings -pi/6 -> +pi/6 -> -pi/6; the weapon swaps club -> sword -> club at the apex via the `proscenio_slot_index` track.
- **Expect (end state):** one `weapon` slot with club (default) + sword; the `swing` action animates both bone rotation and the slot index.
- **Status:** pending

### [ ] FLOW-SLOTSWAP-02 · slot_swap: export -> Godot visibility swap  (Blender -> Godot)
- **Pre:** FLOW-SLOTSWAP-01 slot authored; clean Godot project folder.
1. Blender: Export subpanel > `Validate` (BL-VALID-03) -> passes; the slot + attachments report no issues.
2. Blender: Export subpanel > `Export (.proscenio)` (BL-PIPE-14) -> `.proscenio` written with a `slots[]` entry and a `slot_attachment` track.
3. Godot: copy `.proscenio` + `arm.png`/`club.png`/`sword.png` into one folder; reimport (GD-IMPORT-06) -> a `Node2D` slot anchor builds with both attachments as visibility-toggled children (GD-BUILD-10, GD-BUILD-13); `club` visible at load, `sword` hidden.
4. Godot: instance under a wrapper and play `swing` -> the `slot_attachment` track expands to per-child `:visible` tracks (GD-BUILD-33); the weapon flips club -> sword -> club in time with the swing.
- **Expect (end state):** Godot scene shows the arm swinging and the weapon swapping mid-swing via per-attachment visibility; no missing-texture errors.
- **Status:** pending

---

## SLOTCYCLE - slot system, 3 attachments cycling

### [ ] FLOW-SLOTCYCLE-01 · slot_cycle: cycle action -> Godot N-way visibility  (Blender -> Godot)
- **Pre:** open `examples/generated/slot_cycle/slot_cycle.blend` (Save As a workbench copy); clean Godot project folder.
1. Blender: select the `cycle.slot` Empty; the Active Slot subpanel appears (BL-SLOT-11) with `attachment_red`/`green`/`blue` listed (BL-SLOT-04); `attachment_red` is the default (BL-SLOT-17).
2. Blender: scrub the `cycle` action (24 frames) -> the `proscenio_slot_index` steps 0->1->2->0 with constant interpolation, swapping red -> green -> blue -> red.
3. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14) -> `.proscenio` written with the `slots[]` entry (default `attachment_red`) and a constant-interp `slot_attachment` track.
4. Godot: copy `.proscenio` + the 3 attachment PNGs into one folder; reimport (GD-IMPORT-06) -> the slot `Node2D` builds (GD-BUILD-10) with red visible at load, green + blue hidden (GD-BUILD-13); the track expands to 3 `:visible` tracks with NEAREST interp (GD-BUILD-33).
5. Godot: instance under a wrapper and play `cycle` -> exactly one attachment is visible per phase, cycling red -> green -> blue -> red.
- **Expect (end state):** Godot scene cycles through the three colored attachments, one visible at a time, looping; no missing-texture errors.
- **Status:** pending

---

## ATLAS - atlas packer Pack / Apply / Unpack

### [ ] FLOW-ATLAS-01 · atlas_pack: Pack + Apply + Unpack roundtrip  (Blender)
- **Pre:** open `examples/generated/atlas_pack/atlas_pack.blend` (Save As a workbench copy); Object Mode; file saved.
1. Blender: Atlas subpanel > `Pack Atlas` (BL-ATLAS-12) -> `atlas_pack.atlas.png` (single sheet, 9 sub-images) + `atlas_pack.atlas.json` manifest are written; each sprite's `texture_region` is recorded.
2. Blender: Atlas subpanel > `Apply Packed Atlas` (BL-ATLAS-17) -> UVs are rewritten to packed coords (BL-ATLAS-22) and sprite materials swap to the shared `Proscenio.PackedAtlas` material (BL-ATLAS-20).
3. Blender: scrub the viewport -> every sprite still shows its own digit on its own color (proof Apply did not scramble UVs).
4. Blender: Atlas subpanel > `Unpack Atlas` (BL-ATLAS-26) -> UVs restore to original 0..1 from the `pre_pack` snapshot (BL-ATLAS-30) and the original per-sprite materials are restored.
5. Blender: `Ctrl+Z` after a fresh Apply (BL-ATLAS-25) -> the Apply is cleanly undone (UVs/materials back to pre-Apply state).
- **Expect (end state):** sprites render identically before pack and after unpack; the packed atlas + manifest exist on disk; no material/UV corruption.
- **Status:** pending

### [ ] FLOW-ATLAS-02 · atlas_pack: packed atlas -> Godot single-texture draw  (Blender -> Godot)
- **Pre:** FLOW-ATLAS-01 with Pack + Apply applied (atlas active in the scene); clean Godot project folder.
1. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14) -> `.proscenio` references the packed `atlas_pack.atlas.png` rather than nine per-sprite PNGs.
2. Godot: copy `.proscenio` + `atlas_pack.atlas.png` into one folder; reimport (GD-IMPORT-06) -> the atlas loads once (GD-BUILD-09) and every sprite resolves its region from the shared texture (GD-BUILD-28).
3. Godot: instance under a wrapper -> all nine sprites render their correct digit/color from the single packed atlas; no per-sprite PNG required.
- **Expect (end state):** Godot scene draws all nine sprites from one shared atlas texture; no missing-dependency dialog.
- **Status:** pending

---

## PSD - PSD-sourced manifest import roundtrip

### [ ] FLOW-PSD-01 · simple_psd: v2 manifest -> Blender polygon + sprite_frame  (PS-manifest -> Blender)
- **Pre:** `examples/generated/simple_psd/simple_psd.photoshop_manifest.json` + `pillow_layers/` PNGs on disk; clean Blender file.
1. Blender: Active Sprite subpanel > `Import Photoshop Manifest`, point at `simple_psd.photoshop_manifest.json` (BL-PIPE-06) -> `square` lands as a polygon quad and `arrow` as a sprite_frame plane (4 frames composed into an internal sheet); stub `root` armature parents both.
2. Blender: select `arrow`; Active Sprite subpanel shows `Sprite Frame` type with `hframes=4`/`vframes=1`; the in-panel preview slicer shows the chosen cell (no export needed).
3. Blender: Active Sprite subpanel > `Snap to UV bounds` on `square` (BL-ELEM-28) -> the texture region populates from the current UV.
4. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14) -> `.proscenio` written; the sprite_frame `arrow` carries its grid metadata.
- **Expect (end state):** both layers imported with correct coordinate conversion (PSD top-left -> Blender XZ-centred); polygon + sprite_frame types set; `.proscenio` exported.
- **Status:** pending

### [ ] FLOW-PSD-02 · simple_psd: sprite_frame -> Godot Sprite2D slicing  (Blender -> Godot)
- **Pre:** FLOW-PSD-01 `.proscenio` exported; clean Godot project folder.
1. Godot: copy `.proscenio` + the composed spritesheet + `square.png` into one folder; reimport (GD-IMPORT-06) -> `square` builds as `Polygon2D` (GD-BUILD-14) and `arrow` as `Sprite2D` with `hframes`/`vframes` set (GD-BUILD-20); arrow z-order lands closer to camera than square.
2. Godot: instance under a wrapper, set `arrow.frame` 0..3 -> the `region_rect` slices by `hframes`/`vframes`; each frame shows the matching arrow direction (up/right/down/left).
3. Godot: play the autoplay animation if present -> the `sprite_frame` track drives the arrow frame index (GD-BUILD-32).
- **Expect (end state):** Godot scene renders the polygon square and the 4-frame arrow Sprite2D slicing correctly; no missing-texture errors.
- **Status:** pending

### [ ] FLOW-PSD-03 · doll: PSD-base import roundtrip (manifest parity)  (PS -> Blender)
- **Pre:** `examples/authored/doll/01_photoshop_base/doll_ps_base.psd` (placed from the base manifest); the doll tag-oracle PSD `02_photoshop_setup/doll_tagged_test.psd`.
1. PS: open `doll_tagged_test.psd`; Tags panel, expand a tagged group (PS-TAGS-06) and confirm the tag glyphs ([ignore] PS-TAGS-09, [merge] PS-TAGS-10) reflect the authored taxonomy.
2. PS: Validate panel > `Refresh`/inspect (PS-AUX-16) -> no unexpected warning (PS-AUX-11) or skipped (PS-AUX-13) rows for the tagged layers.
3. PS: Exporter > `Export manifest + PNGs` (PS-EXPORT-14) -> the re-exported manifest is written; every v1 tag in the oracle survives into the manifest entries.
4. Blender: `Import Photoshop Manifest` on the re-export (BL-PIPE-06) -> every tag's downstream effect lands (folders -> collections, [merge] flattened, [origin]/[scale] applied, [spritesheet] groups -> sprite_frame).
- **Expect (end state):** the full v1 tag taxonomy round-trips PS -> manifest -> Blender with no drift; matches the recorded baseline/oracle.
- **Status:** pending

---

## REIMPORT - wrapper-scene reimport safety

### [ ] FLOW-REIMPORT-01 · wrapper scene survives re-export  (Blender -> Godot, iterate)
- **Pre:** a Godot project with `examples/authored/doll/04_godot_import/Doll.tscn` instancing a generated `doll.proscenio`; `Doll.gd` on the wrapper root; the scene already imported once.
1. Godot: open `Doll.tscn` -> it loads with no missing-resource errors; the instanced character shows every rigged plane at the correct Z-order/position.
2. Godot: add wrapper-only work on the root (a `RemoteTransform2D` following a bone, a collider, a `_ready` override) -> the additions live in `Doll.tscn`/`Doll.gd`, never inside the imported scene.
3. Blender: edit the source (e.g. repaint a layer or tweak a pose), `Re-export` via the sticky path (BL-PIPE-16) -> a new `.proscenio` is written with no dialog.
4. Godot: trigger a reimport on editor focus (GD-IMPORT-06) -> the inner generated scene fully regenerates (GD-IMPORT-20) but the wrapper `Doll.tscn`/`Doll.gd` and all wrapper-only nodes survive untouched (GD-IMPORT-19).
5. Godot: play the wrapper scene -> `Doll.gd::_ready` resolves a non-null AnimationPlayer and `idle` plays; the wrapper-only collider/RemoteTransform2D still present and wired.
- **Expect (end state):** the regenerated inner scene reflects the Blender edit; the user's wrapper work is fully preserved across the reimport; no missing-resource errors.
- **Status:** pending

---

## Findings

Divergences surfaced while authoring/walking these flows. Types: `drift` · `undocumented` ·
`unimplemented` · `dead` · `suspected-bug` (see [STUDY.md](../STUDY.md#findings-section)).
High-sev findings with a repro promote to [backlog-bugs-found.md](../../backlog-bugs-found.md).

| ID | Type | Sev | Control | Detail | Code |
| --- | --- | --- | --- | --- | --- |
| _none yet_ | | | | | |
