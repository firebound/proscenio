# Cross-app flows - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

## DOLL - full rigged roundtrip

### FLOW-DOLL-01 · doll: tagged PSD -> rigged Blender import  (PS -> Blender)
- status: pending
- review: keep
- pre: `examples/authored/doll/02_photoshop_setup/doll_tagged.psd` open in Photoshop; a clean Blender file; output folder empty.
- steps:
  1. PS: Exporter > pick the output folder (PS-EXPORT-02) -> the chosen path is shown and remembered.
  2. PS: Exporter > `Export manifest + PNGs` (PS-EXPORT-14) -> a v2 manifest JSON plus one PNG per visible layer land side by side in the output folder; no validation error dialog (PS-EXPORT-23).
  3. Blender: Active Sprite subpanel > `Import Photoshop Manifest`, point at the manifest (BL-PIPE-06) -> every tagged layer becomes a quad sprite at its pivot/region; a stub `doll.rig` armature with one root bone appears and parents every mesh.
  4. Blender: Outliner subpanel, filter for a known mesh and click its row (BL-OUTLN-07) -> the clicked sprite (e.g. `chest`) becomes the active object and its textures resolve (no pink/missing).
- observe: all doll layers present as quads, parented to the single-bone stub rig, textures resolved, names tag-stripped.

### FLOW-DOLL-02 · doll: build skeleton + skin + animate  (Blender)
- status: pending
- review: keep
- pre: FLOW-DOLL-01 imported set in Blender, or open `examples/authored/doll/03_blender_setup/doll_rigged.blend` (Save As a workbench copy first).
- steps:
  1. Blender: Skeleton subpanel > `Quick Armature` (BL-SKEL-19), draw a bone chain head->tail with LMB press-drag (BL-SKEL-20), then `Enter` to confirm (BL-SKEL-26) -> bones land Front-Ortho-aligned; the on-screen cheatsheet tracked the cursor; no leaked draw handler on exit.
  2. Blender: Skeleton subpanel > `Use existing armature` for `doll.rig` (BL-SKEL-07) -> the picker armature is set as the bind target.
  3. Blender: Skinning subpanel > `Bind to Picker Armature` (BL-WPAINT-13) -> each mesh gains bone-named vertex groups and follows the pose.
  4. Blender: Skinning subpanel > `Edit Weights` (BL-WPAINT-17), paint one stroke (BL-WPAINT-18), then `ESC` to exit (BL-WPAINT-19) -> weights update on the painted mesh; modal exits cleanly.
  5. Blender: Skinning subpanel > re-run `Bind to Picker Armature` once per mode, stepping the Bind mode dropdown through BONE_HEAT, PROXIMITY, ENVELOPE, SINGLE_NEAREST, EMPTY (the dropdown is F3-redo exposed; BL-WPAINT-06/10/11/12) -> each mode reports its `Mode=<name>` INFO and produces a distinct vertex-weight distribution: pose the bone and the deformation visibly differs between PROXIMITY (smooth 1/d falloff), SINGLE_NEAREST (one bone per vert, rigid), and EMPTY (all-zero, no deform until painted).
  6. Blender: under a planar mode (e.g. PROXIMITY), in the per-bone override box set one bone to Soft, another to Hard, then Clear the Hard one (BL-WPAINT-11/12) -> Soft gives proximity falloff, Hard collapses to single-nearest on that bone, and Clear reverts it to the bind default; posing shows each override change deformation (overrides are inert under BONE_HEAT, which returns before the override pass).
  7. Blender: Animation subpanel, click the `idle` action row (BL-ANIM-06), scrub the timeline -> the spine bob plays; the read-only action summary lists `idle`, `wave`, `walk`.
- observe: doll rig with bone-named vertex groups deforming the meshes; the 5 bind modes each yield a distinct deformation and per-bone Soft/Hard/Clear visibly retune it; the three authored actions present and playable.

### FLOW-DOLL-03 · doll: validate, export, Godot import  (Blender -> Godot)
- status: pending
- review: keep
- pre: FLOW-DOLL-02 rigged/skinned/animated doll in Blender; a clean `apps/godot` (or example) project folder.
- steps:
  1. Blender: Export subpanel > `Validate` (BL-VALID-03) -> validator passes (every sprite checks against armature, atlas, required fields); zero blocking issue rows (BL-VALID-07).
  2. Blender: Export subpanel > `Export (.proscenio)` (BL-PIPE-14) -> a `.proscenio` JSON is written next to the `.blend`; the per-mesh PNGs are referenced by filename.
  3. Godot: copy the `.proscenio` and every PNG it names into one flat folder; let the importer run (GD-IMPORT-06) -> the scene regenerates in build order skeleton -> atlas -> slots -> mesh/sprite -> animation (GD-IMPORT-07); no missing-dependency dialog.
  4. Godot: instance the generated scene under a wrapper and play `idle` (GD-BUILD-29) -> the textured, skinned doll renders and the spine-bob animation plays; skinned `Polygon2D` meshes deform with the `Skeleton2D` (GD-BUILD-18).
  5. Godot: inspect a rigid (non-skinned) plane that was bone-parented in Blender (e.g. a `[mesh]`-untagged sprite parented Ctrl+P > Bone) -> it lands as a child of the `Bone2D` whose name matches its `bone_name` (found via `skeleton.find_child(bone_name)`; GD-BUILD-07/19/27), not under the skeleton root; play `idle` and the plane rides that bone's transform rigidly (translation + rotation match, no mesh deform; GD-BUILD-02..06).
- observe: the Godot scene renders the textured, rigged doll; skinned `Polygon2D` deforms under `Skeleton2D` and the rigid plane parents under its named `Bone2D` and follows that bone's transform; `idle`/`wave`/`walk` populate the AnimationPlayer library; no missing-resource errors.

## SLOTSWAP - slot system + bone swing

### FLOW-SLOTSWAP-01 · slot_swap: author the slot + swing action  (Blender)
- status: pending
- review: keep
- pre: open `examples/generated/slot_swap/slot_swap.blend` (Save As `slot_swap_workbench.blend`); addon enabled.
- steps:
  1. Blender: select the `arm` mesh plus the `club`/`sword` meshes, Skeleton subpanel > `Create Slot` (BL-SLOT-07) -> a slot Empty `weapon` is anchored under the active bone and the selected meshes become its attachments (or confirm the prebuilt `weapon` slot exists).
  2. Blender: select the `weapon` Empty; the Active Slot subpanel appears (BL-SLOT-11) listing `club` and `sword` as attachments (BL-SLOT-04).
  3. Blender: mark `club` as the default via its SOLO star (BL-SLOT-17) -> `club` is the load-time visible attachment; `sword` hidden.
  4. Blender: scrub the `swing` action timeline -> arm swings -pi/6 -> +pi/6 -> -pi/6; the weapon swaps club -> sword -> club at the apex via the `proscenio_slot_index` track.
- observe: one `weapon` slot with club (default) + sword; the `swing` action animates both bone rotation and the slot index.

### FLOW-SLOTSWAP-02 · slot_swap: export -> Godot visibility swap  (Blender -> Godot)
- status: pending
- review: keep
- pre: FLOW-SLOTSWAP-01 slot authored; clean Godot project folder.
- steps:
  1. Blender: Export subpanel > `Validate` (BL-VALID-03) -> passes; the slot + attachments report no issues.
  2. Blender: Export subpanel > `Export (.proscenio)` (BL-PIPE-14) -> `.proscenio` written with a `slots[]` entry and a `slot_attachment` track.
  3. Godot: copy `.proscenio` + `arm.png`/`club.png`/`sword.png` into one folder; reimport (GD-IMPORT-06) -> a `Node2D` slot anchor builds with both attachments as visibility-toggled children (GD-BUILD-10, GD-BUILD-13); `club` visible at load, `sword` hidden.
  4. Godot: instance under a wrapper and play `swing` -> the `slot_attachment` track expands to per-child `:visible` tracks (GD-BUILD-33); the weapon flips club -> sword -> club in time with the swing.
- observe: Godot scene shows the arm swinging and the weapon swapping mid-swing via per-attachment visibility; no missing-texture errors.

## SLOTCYCLE - slot system, 3 attachments cycling

### FLOW-SLOTCYCLE-01 · slot_cycle: cycle action -> Godot N-way visibility  (Blender -> Godot)
- status: pending
- review: keep
- pre: open `examples/generated/slot_cycle/slot_cycle.blend` (Save As a workbench copy); clean Godot project folder.
- steps:
  1. Blender: select the `cycle.slot` Empty; the Active Slot subpanel appears (BL-SLOT-11) with `attachment_red`/`green`/`blue` listed (BL-SLOT-04); `attachment_red` is the default (BL-SLOT-17).
  2. Blender: scrub the `cycle` action (24 frames) -> the `proscenio_slot_index` steps 0->1->2->0 with constant interpolation, swapping red -> green -> blue -> red.
  3. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14) -> `.proscenio` written with the `slots[]` entry (default `attachment_red`) and a constant-interp `slot_attachment` track.
  4. Godot: copy `.proscenio` + the 3 attachment PNGs into one folder; reimport (GD-IMPORT-06) -> the slot `Node2D` builds (GD-BUILD-10) with red visible at load, green + blue hidden (GD-BUILD-13); the track expands to 3 `:visible` tracks with NEAREST interp (GD-BUILD-33).
  5. Godot: instance under a wrapper and play `cycle` -> exactly one attachment is visible per phase, cycling red -> green -> blue -> red.
- observe: Godot scene cycles through the three colored attachments, one visible at a time, looping; no missing-texture errors.

## ATLAS - atlas packer Pack / Apply / Unpack

### FLOW-ATLAS-01 · atlas_pack: Pack + Apply + Unpack roundtrip  (Blender)
- status: pending
- review: keep
- pre: open `examples/generated/atlas_pack/atlas_pack.blend` (Save As a workbench copy); Object Mode; file saved.
- steps:
  1. Blender: Atlas subpanel > `Pack Atlas` (BL-ATLAS-12) -> `atlas_pack.atlas.png` (single sheet, 9 sub-images) + `atlas_pack.atlas.json` manifest are written; each sprite's `texture_region` is recorded.
  2. Blender: Atlas subpanel > `Apply Packed Atlas` (BL-ATLAS-17) -> UVs are rewritten to packed coords (BL-ATLAS-22) and sprite materials swap to the shared `Proscenio.PackedAtlas` material (BL-ATLAS-20).
  3. Blender: scrub the viewport -> every sprite still shows its own digit on its own color (proof Apply did not scramble UVs).
  4. Blender: Atlas subpanel > `Unpack Atlas` (BL-ATLAS-26) -> UVs restore to original 0..1 from the `pre_pack` snapshot (BL-ATLAS-30) and the original per-sprite materials are restored.
  5. Blender: `Ctrl+Z` after a fresh Apply (BL-ATLAS-25) -> the Apply is cleanly undone (UVs/materials back to pre-Apply state).
  6. Blender: Unpack, then on one sprite enable Object Properties > `Isolated material` (BL-ELEM-11), Pack Atlas + Apply Packed Atlas again -> the isolated sprite keeps its own per-sprite material (not relinked to `Proscenio.PackedAtlas`) while that material's TEX_IMAGE node now points at the packed `atlas_pack.atlas.png`; every non-isolated sprite shares the single `Proscenio.PackedAtlas` material.
  7. Blender: Unpack, then on one sprite enable `Exclude from atlas` (BL-ELEM-12), Pack Atlas -> the excluded sprite is absent from `atlas_pack.atlas.png` (sheet packs the remaining sprites only) and keeps its original 0..1 UVs and its own material untouched; on Export the `.proscenio` references that sprite's own PNG, not the atlas.
- observe: sprites render identically before pack and after unpack; the isolated sprite keeps its own material drawing from the packed sheet while others share `Proscenio.PackedAtlas`; the excluded sprite stays off the sheet with original UVs/material and ships its own PNG; the packed atlas + manifest exist on disk; no material/UV corruption.

### FLOW-ATLAS-02 · atlas_pack: packed atlas -> Godot single-texture draw  (Blender -> Godot)
- status: pending
- review: keep
- pre: FLOW-ATLAS-01 with Pack + Apply applied (atlas active in the scene); clean Godot project folder.
- steps:
  1. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14) -> `.proscenio` references the packed `atlas_pack.atlas.png` rather than nine per-sprite PNGs.
  2. Godot: copy `.proscenio` + `atlas_pack.atlas.png` into one folder; reimport (GD-IMPORT-06) -> the atlas loads once (GD-BUILD-09) and every sprite resolves its region from the shared texture (GD-BUILD-28).
  3. Godot: instance under a wrapper -> all nine sprites render their correct digit/color from the single packed atlas; no per-sprite PNG required.
- observe: Godot scene draws all nine sprites from one shared atlas texture; no missing-dependency dialog.

## PSD - PSD-sourced manifest import roundtrip

### FLOW-PSD-01 · simple_psd: v2 manifest -> Blender polygon + sprite_frame  (PS-manifest -> Blender)
- status: pending
- review: keep
- pre: `examples/generated/simple_psd/simple_psd.photoshop_manifest.json` + `pillow_layers/` PNGs on disk; clean Blender file.
- steps:
  1. Blender: Active Sprite subpanel > `Import Photoshop Manifest`, point at `simple_psd.photoshop_manifest.json` (BL-PIPE-06) -> `square` lands as a polygon quad and `arrow` as a sprite_frame plane (4 frames composed into an internal sheet); stub `root` armature parents both.
  2. Blender: select `arrow`; Active Sprite subpanel shows `Sprite Frame` type with `hframes=4`/`vframes=1`; the in-panel preview slicer shows the chosen cell (no export needed).
  3. Blender: Active Sprite subpanel > `Snap to UV bounds` on `square` (BL-ELEM-28) -> the texture region populates from the current UV.
  4. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14) -> `.proscenio` written; the sprite_frame `arrow` carries its grid metadata.
- observe: both layers imported with correct coordinate conversion (PSD top-left -> Blender XZ-centred); polygon + sprite_frame types set; `.proscenio` exported.

### FLOW-PSD-02 · simple_psd: sprite_frame -> Godot Sprite2D slicing  (Blender -> Godot)
- status: pending
- review: keep
- pre: FLOW-PSD-01 `.proscenio` exported; clean Godot project folder.
- steps:
  1. Godot: copy `.proscenio` + the composed spritesheet + `square.png` into one folder; reimport (GD-IMPORT-06) -> `square` builds as `Polygon2D` (GD-BUILD-14) and `arrow` as `Sprite2D` with `hframes`/`vframes` set (GD-BUILD-20); arrow z-order lands closer to camera than square.
  2. Godot: instance under a wrapper, set `arrow.frame` 0..3 -> the `region_rect` slices by `hframes`/`vframes`; each frame shows the matching arrow direction (up/right/down/left).
  3. Godot: play the autoplay animation if present -> the `sprite_frame` track drives the arrow frame index (GD-BUILD-32).
- observe: Godot scene renders the polygon square and the 4-frame arrow Sprite2D slicing correctly; no missing-texture errors.

### FLOW-PSD-03 · doll: PSD-base import roundtrip (manifest parity)  (PS -> Blender)
- status: pending
- review: keep
- pre: `examples/authored/doll/01_photoshop_base/doll_ps_base.psd` (placed from the base manifest); the doll tag-oracle PSD `02_photoshop_setup/doll_tagged_test.psd`.
- steps:
  1. PS: open `doll_tagged_test.psd`; Tags panel, expand a tagged group (PS-TAGS-06) and confirm the tag glyphs ([ignore] PS-TAGS-09, [merge] PS-TAGS-10) reflect the authored taxonomy.
  2. PS: Validate panel > `Refresh`/inspect (PS-AUX-16) -> no unexpected warning (PS-AUX-11) or skipped (PS-AUX-13) rows for the tagged layers.
  3. PS: Exporter > `Export manifest + PNGs` (PS-EXPORT-14) -> the re-exported manifest is written; every v1 tag in the oracle survives into the manifest entries.
  4. Blender: `Import Photoshop Manifest` on the re-export (BL-PIPE-06) -> assert each tag class lands distinctly so a failure is attributable: [ignore] -> the tagged layer produces no manifest entry and no Blender plane; [merge] -> the tagged group flattens to a single composited plane (its child layers do not each become planes); [origin] -> the plane's pivot/origin sits at the tagged anchor (not the layer-bounds default); [scale] -> the plane's stamped size reflects the tag's scale factor, not the raw pixel bounds; [spritesheet] -> the tagged group imports as one sprite_frame plane with the grid metadata (hframes/vframes), not as separate per-frame planes.
- observe: each v1 tag class verified independently - [ignore] drops the layer, [merge] flattens, [origin] sets pivot, [scale] sizes the plane, [spritesheet] yields a gridded sprite_frame - matching the recorded baseline/oracle with no drift.

## REIMPORT - wrapper-scene reimport safety

### FLOW-REIMPORT-01 · wrapper scene survives re-export  (Blender -> Godot, iterate)
- status: pending
- review: keep
- pre: a Godot project with `examples/authored/doll/04_godot_import/Doll.tscn` instancing a generated `doll.proscenio`; `Doll.gd` on the wrapper root; the scene already imported once.
- steps:
  1. Godot: open `Doll.tscn` -> it loads with no missing-resource errors; the instanced character shows every rigged plane at the correct Z-order/position.
  2. Godot: add wrapper-only work on the root (a `RemoteTransform2D` following a bone, a collider, a `_ready` override) -> the additions live in `Doll.tscn`/`Doll.gd`, never inside the imported scene.
  3. Blender: edit the source (e.g. repaint a layer or tweak a pose), `Re-export` via the sticky path (BL-PIPE-16) -> a new `.proscenio` is written with no dialog.
  4. Godot: trigger a reimport on editor focus (GD-IMPORT-06) -> the inner generated scene fully regenerates (GD-IMPORT-20) but the wrapper `Doll.tscn`/`Doll.gd` and all wrapper-only nodes survive untouched (GD-IMPORT-19).
  5. Godot: play the wrapper scene -> `Doll.gd::_ready` resolves a non-null AnimationPlayer and `idle` plays; the wrapper-only collider/RemoteTransform2D still present and wired.
- observe: the regenerated inner scene reflects the Blender edit; the user's wrapper work is fully preserved across the reimport; no missing-resource errors.

## DRIVER - drive sprite frame/region from a bone

### FLOW-DRIVER-01 · driver: drive sprite frame/region from a pose bone  (Blender -> Godot)
- status: pending
- review: keep
- pre: a Blender file with a skinned/rigged sprite (e.g. FLOW-DOLL-02 set, or `examples/authored/doll/03_blender_setup/doll_rigged.blend`); the active object is a `proscenio` sprite mesh with a Sprite Frame type set (hframes*vframes > 1).
- steps:
  1. Blender: select the sprite; Active Element subpanel > Drive from Bone box (BL-ELEM-31..43). With no Bone picked, confirm the `Drive from Bone` button is greyed/disabled (row.enabled gates on a non-empty source armature with bones plus a non-empty source bone; BL-ELEM-40).
  2. Blender: set Armature to the rig, Bone to a deform bone, Axis to `Bone Rot Y` (ROT_Y, the front-ortho visible axis), Target to `Frame index`; leave the two-range linear map In Min/In Max at -pi/2..+pi/2 and Out Min/Out Max at 0..(hframes*vframes-1) (BL-ELEM-41/42).
  3. Blender: click `Drive from Bone` (proscenio.create_driver) -> an INFO reports `driver on '<sprite>.proscenio.frame' <- <arm>:<bone>.ROT_Y`; the sprite gains a SCRIPTED driver on `proscenio.frame` with a single TRANSFORMS var reading the bone (WORLD_SPACE, XYZ Euler for rotation).
  4. Blender: pose the bone across its range and read the box's live `Value:` readout (BL-ELEM-39) -> the driven `proscenio.frame` steps monotonically from Out Min to Out Max as the bone rotates In Min -> In Max (whole-number readout for the integer frame target).
  5. Blender: pick a bone that is not in the chosen armature (or clear the armature after picking a bone) and click `Drive from Bone` -> the operator reports an error (`bone '<name>' not in armature '<arm>'` or `pick a source armature in the panel`) and adds no driver.
  6. Blender: Export subpanel > `Validate` then `Export (.proscenio)` (BL-VALID-03, BL-PIPE-14); copy into a Godot folder and reimport (GD-IMPORT-06) -> confirm what crosses the boundary: the driven frame is materialized into the exported `sprite_frame`/region track for the sampled range (baked), not carried as a live Blender driver (Godot has no Blender-driver concept).
- observe: Drive-from-Bone wires a single SCRIPTED driver mapping the chosen bone axis through the linear range into `proscenio.frame`/`region_*`; the live Value readout tracks the pose; the disabled-no-bone and bad-armature paths are guarded; and the driven result reaches Godot baked into the sprite_frame/region track rather than as a live driver.
- intent: cover the Drive-from-Bone authoring path (driver.py) - no existing flow drives a sprite frame/region from a bone, and the export-parity question (driven value vs dropped) is unanswered.
- code: `apps/blender/operators/driver.py`, `apps/blender/panels/_draw_driver_shortcut.py`, `apps/blender/core/armature/driver_expression.py`

## WEIGHTS - weight-preservation matrix

### FLOW-WEIGHTS-REGEN-01 · weights: automesh regen PRESERVES painted weights  (Blender)
- status: pending
- review: keep
- pre: a Blender file with an automesh-able sprite and a picker armature with deform bones (e.g. the automesh fixture / a `[mesh]` sprite with an image texture); Object Mode.
- steps:
  1. Blender: set the picker armature (Skeleton subpanel), Skinning subpanel > Automesh the sprite, then `Bind to Picker Armature` -> the mesh gains bone-named vertex groups and a `proscenio_weight_sidecar` Custom Property with one entry per vert (entries > 0).
  2. Blender: paint a recognizable weight pattern (Edit Weights, one strong stroke) and pose the bone -> note the resulting deformation as the baseline.
  3. Blender: Skinning subpanel > ensure `Preserve on regen` is ON, then re-run Automesh with a different resolution (e.g. 0.5) to force a topology change (BL-MESH-14/25) -> an INFO reports `sidecar: <N> reprojected + <M> auto-seed of <T> verts`; the post-regen sidecar has one entry per new vert and provenance includes `reprojected` (or `auto_seed`); posing the bone reproduces the baseline deformation (weights survived the rebuild).
  4. Blender: turn `Preserve on regen` OFF and re-run Automesh with another forcing resolution change (BL-WPAINT-31) -> the reproject hook is a no-op (the sidecar is not re-stamped; its `mesh_topology_hash` still points at the pre-regen topology) and the painted weights are gone, so the bone no longer deforms the mesh as before.
- observe: with preserve_on_regen ON, an automesh regen snapshots and reprojects the painted weights (INFO reprojected/auto-seed counts, deformation unchanged); with it OFF the regen wipes them. This is the automesh-regen-PRESERVES leg and must stay distinct from the re-import and re-rig LOSES legs.
- intent: the PRESERVES leg of the three-way weight distinction - automesh regen snapshots + reprojects when preserve_on_regen is ON.
- code: `apps/blender/operators/automesh/automesh.py`, `apps/blender/core/skinning/weight_reproject.py`, `apps/blender/core/skinning/weight_snapshot.py`

### FLOW-REIMPORT-WEIGHTS-01 · weights: PSD re-import LOSES painted weights  (PS -> Blender, iterate)
- status: pending
- review: keep
- pre: a manifest + PNGs on disk and a Blender file where one imported plane has been skinned (bone-named vertex groups + painted weights) - e.g. import `examples/generated/simple_psd/simple_psd.photoshop_manifest.json`, then bind + paint one plane.
- steps:
  1. Blender: with the skinned plane selected, confirm its `proscenio_import_origin` tag (Object Properties > Custom Properties, e.g. `psd:square`), its bone-named vertex groups, and a posed-bone deformation baseline.
  2. PS/disk: edit the source layer so its placement bounds change (resize or reposition the layer), then re-export the manifest + PNGs to the same path.
  3. Blender: `Import Photoshop Manifest` on the re-export (BL-PIPE-06) -> the plane updates in place (matched by tag, not name): the object, its transform/parenting, the vertex-group NAMES, per-sprite settings (sprite type, sprite-frame metadata, is_slot), slot membership, and name-targeted animation tracks all survive.
  4. Blender: pose the bone again -> the mesh has been rebuilt to a fresh quad, so the painted weight VALUES and any automesh density are reset (the deformation no longer matches the step-1 baseline) per the documented "re-import is not weight-preserving" warning.
- observe: a placement-changing PSD re-import keeps object/transform/parenting/vertex-group-names/per-sprite-settings/slots/name-targeted-anim but resets painted weight values + automesh density because the mesh is rebuilt to a quad. This is the PSD-re-import-LOSES leg - distinct from automesh-regen-PRESERVES and re-rig-LOSES.
- intent: the LOSES leg for PSD re-import - the documented order-of-operations trap (rebuild to quad resets painted weight VALUES while names/parenting survive). Keep separate from automesh-regen-PRESERVES.
- code: `apps/blender/importers/photoshop/planes.py`; docs `docs/00-guides/02-advanced/01-photoshop.md` (re-importing after PSD edits)

### FLOW-RERIG-01 · weights: re-rig LOSES weights and keys  (Blender, regression guard)
- status: pending
- review: keep
- pre: a Blender file with a skinned mesh bound to armature A (bone-named vertex groups, painted weights, and at least one action keying A's bones) - e.g. the FLOW-DOLL-02 rigged set.
- steps:
  1. Blender: pose armature A and note the deformation baseline; scrub the keyed action and note the bone motion baseline.
  2. Blender: change the rig - rename/add/remove a deform bone in armature A (or pick a different armature B as the picker) so the bind target's bone set no longer matches the painted groups.
  3. Blender: Skinning subpanel > `Bind to Picker Armature` against the changed armature -> the bind re-runs against the new bone set.
  4. Blender: pose the rig and scrub the action -> the previously painted weights do NOT carry to the new bones and the prior action keys do NOT survive the re-rig (documented limitation); the deformation/motion differ from the baselines. Record this as the expected (failing-to-preserve) behavior, not a passing preserve.
- observe: re-binding a skinned mesh to a changed armature loses the painted weights and the prior animation keys today - the documented re-rig limitation. This is the re-rig-LOSES leg; it completes the survives/does-not matrix with FLOW-REIMPORT-01 and stays distinct from the automesh-regen-PRESERVES and PSD-re-import-LOSES legs. If a future change makes re-rig preserve weights/keys, this flow should start failing and be re-specified.
- intent: the LOSES leg for re-rig - a documented limitation (re-binding to a changed armature does not carry weights or keys today). Guard so the suite catches the day this silently changes.
- code: `apps/blender/operators/skinning/bind_mesh.py`; docs `docs/01-project/04-deferred.md` (mid-edit non-destructive re-rig)
