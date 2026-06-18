# Bugs found during manual testing

Reproducible bugs whose fix is **not yet applied** - the defect still reproduces. Each cites a reproducer + suspect + affected file, and promotes into a PR fix or a dedicated issue.

Bugs whose fix already shipped and only await a GUI confirmation are walkable items in the QA Companion checklist ([`tools/qa-companion/checklist/`](../tools/qa-companion/checklist/)) - the locked owner of the manual-test surface (see [decisions.md](decisions.md)). This file is exclusively still-broken behavior. Distinct from [backlog-ui-feedback.md](backlog-ui-feedback.md) (polish, not behavior).

---

## apps/blender

### Re-import de PSD: doc diz "perde weights", código reprojeta de sidecar (divergência)

**Status:** encontrado durante a curadoria do QA surface (jun-2026), ao escrever o fluxo `FLOW-REIMPORT-WEIGHTS-01`. Precisa decidir qual lado é a verdade antes de o fluxo virar oráculo.

**Sintoma:** a doc `docs/00-guides/01-advanced/01-photoshop.md` documenta o re-import de manifesto como NÃO preservador de weights (re-import reconstrói o mesh pra quad, valores pintados resetam). Mas o código atual (`planes.py` + `tests/.../test_psd_reimport.py`) reprojeta os weights pintados a partir de um sidecar sobrevivente num re-import que muda placement. Ou seja: a "perna PERDE" da matriz de weights (automesh-regen PRESERVA / PSD-re-import PERDE / re-rig PERDE) pode não ser mais verdade no PSD-re-import.

**Por que importa:** as três operações de weight são deliberadamente distintas e conflá-las já causou bugs de doc antes. Se o código passou a preservar no PSD-re-import, ou a doc está desatualizada (corrigir doc), ou o comportamento regrediu/mudou sem querer (corrigir código). `FLOW-REIMPORT-WEIGHTS-01` foi escrito pro comportamento DOCUMENTADO (perde); se o código preserva, o fluxo vai falhar de propósito até isso ser resolvido.

**Repro:** importar manifesto -> skin (pintar weights) -> editar PSD mudando placement -> re-importar o mesmo manifesto -> inspecionar se os valores de weight pintados sobrevivem.

**Arquivo:** `apps/blender/.../planes.py` (caminho de re-import), `tests/.../test_psd_reimport.py`, doc `docs/00-guides/01-advanced/01-photoshop.md`.

**Severity:** medium - não é crash, mas é uma divergência doc-vs-código numa área (weights) historicamente propensa a confusão; deixa o oráculo de teste ambíguo.

### Sprite-frame import polish: discrete update mode, animation step/fps, bezier handles

Open follow-ups surfaced during the sprite-frame wrap investigation (the main bug - exporter clamped out-of-range frames while Blender wraps, which froze `mouth_drive` in Godot - was fixed by switching the exporter to modulo wrap; see `sprite_frame_animations._wrap_frame` and its tests). These three are still open robustness/fidelity gaps, no visible break today:

- **sprite_frame track imported as CONTINUOUS, not DISCRETE:** `apps/godot/addons/proscenio/builders/animation_builder.gd:148-154` sets interp NEAREST but never the update mode. A discrete frame index should be `UPDATE_DISCRETE`. Works today because of NEAREST, but is fragile under blend/seek. Set `value_track_set_update_mode(idx, UPDATE_DISCRETE)`.
- **imported animation keeps Godot's default `step = 1/30`:** the importer never sets `anim.step`, while Blender authored at 24fps. Cosmetic only (playback is in seconds, duration identical) but the editor's frame GRID reads 30 vs 24. For WYSIWYG on the grid, carry `scene.render.fps` through the schema (the `.proscenio` format currently drops fps, keeps only seconds) and set `anim.step = 1.0/fps` on import.
- **bezier handle fidelity gap (general, not this fixture):** `bone_transform` tracks export only value+time per key, dropping Blender's bezier handles; the importer hardcodes CUBIC (position/scale) and CUBIC_ANGLE (rotation). Godot's auto-tangent CUBIC != Blender's handle-driven bezier, so bone-motion easing can diverge. Investigate only when a case shows visibly different bone motion.

**Arquivos:** `apps/godot/addons/proscenio/builders/animation_builder.gd:148-154`; (fps) the importer + the `.proscenio` schema (no fps field today).

**Severity:** low - the visible sprite-frame wrap break is fixed; these are robustness/fidelity polish with no current visible divergence.

### Doll roundtrip waivers: waist 1px size drift + PPU=100 baseline (re-measure before a release tag)

Not a confirmed defect - a measurement to re-verify through the UXP path. The JSX reader that logged the -1px drift (Blender manifest `255x173` vs JSX-era `255x172`) is retired; the UXP png-writer now trims via `Document.trim(TRANSPARENT)`, a different bbox engine. Re-measure the `waist` element size on the doll roundtrip: on a persisting drift, align rounding (round-half-up on both sides) or re-document the waiver with the fresh number; on a match, close it. PPU=100 is the doll fixture's baseline assumption, re-measured alongside. (Moved here when `manual-testing.md` was retired; the smoke itself is the QA Companion `FLOW-DOLL` walk.)

**Severity:** low - known waiver, no visible break; re-measure only gates a clean release number.

## apps/blender - code-read audit (2026-06-15, not reproduced)

From the QA Companion audit, verified against current `main`; read-not-reproduced, so confirm a repro before fixing. Dead code + the duplicated driver-axis enum went to [backlog-code-quality.md](backlog-code-quality.md); doc gaps to [backlog-docs.md](backlog-docs.md). Grouped by area for a future robustness STUDY.

**Export / atlas correctness.**

- **Pixels-per-unit ignored on the first export** (high) - the operator uses its own ExportHelper default (100), not the panel's `scene.proscenio.pixels_per_unit`; only Re-export reads the scene value, so editing the panel field silently does nothing on the first export. `export_flow.py:158-167`, `pipeline.py:89`.
- **Apply Packed Atlas counts a no-UV sprite as rewritten** (med) - `_apply_to_object` returns True for `element_type=="sprite"` regardless of whether `_rewrite_uvs` succeeded; the "skipped (no UV layer)" guard only fires for non-sprite meshes. `atlas_pack/apply.py:165-216`.

**Operator robustness + feedback.**

- **Bake Current Pose keys both quaternion and euler** (med) - inserts on both rotation channels for every bone regardless of `bone.rotation_mode`, leaving garbage fcurves on the unused channel. `pose_library.py:143-145`.
- **Quick Armature lock-to-front-ortho ignored at invoke** (low) - `invoke` reads the other options from the PG but not `lock_to_front_ortho`, so the panel toggle has no effect unless overridden via F3. `quick_armature.py:200-221`.
- **Copy Weights to Selected returns FINISHED on a zero-coverage transfer** (low) - a fully-uncovered transfer registers as a successful undo step with no weights applied (only the report downgrades to WARNING). `copy_weights_to_selected.py:49-51`.
- **Bake IK to Keyframes leaves the selection altered** (low) - mutates per-bone selection to scope `nla.bake`, never restores it. `authoring_ik.py:201-213`.
- **Action-row CANCELLED feedback suppressed at log level "errors"** (low) - the no-armature/not-found/multi-armature warnings go through the gated `report_warn`, so a failed click is silent. `report.py:50-53`, `selection.py`.

**Photoshop-import side effects (Blender side).**

- **Re-import always rebuilds the armature** (low) - `import_manifest` calls `build_root_armature` every run, so the doc's "rotation, parenting, weights survive" reuse claim is likely false; verify the round-trip or correct the doc. `importers/photoshop/__init__.py:68-91`. Tied to the Godot reimporter decision in [backlog-godot-importer.md](backlog-godot-importer.md).
- **Import silently overwrites the panel pixels-per-unit** (low) - `_sync_scene_pixels_per_unit` overwrites the scene value with the manifest's on every import, no warning. `importers/photoshop/__init__.py:94-107`.
