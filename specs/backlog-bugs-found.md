# Bugs found during manual testing

Reproducible bugs whose fix is **not yet applied** - the defect still reproduces. Each cites a reproducer + suspect + affected file, and promotes into a PR fix or a dedicated issue.

Bugs whose fix already shipped and only await a GUI confirmation live in [`manual-testing.md`](manual-testing.md) (the 2026-06-12 reconciliation moved them out of here). This file is exclusively still-broken behavior. Distinct from [backlog-ui-feedback.md](backlog-ui-feedback.md) (polish, not behavior).

---

## apps/blender

### Reproject UV: segunda chamada lenta + UV resultante rotacionada/flipada

**Repro:** Active Sprite > polygon mode > "Reproject UV". Sintomas em primeira E segunda chamadas.

**Sintoma 1 (perf):** segunda chamada demora vários segundos como se fosse crashar (testes anteriores em doll).

**Sintoma 2 (orientação):** UV resultante fica rotacionada 90° + horizontalmente invertida. Confirmado em atlas_pack_workbench sprite_1 (11-mai-2026): após Reproject UV, layout precisou de `R -90 S X -1` (rotate -90° + scale X = -1 no UV editor) pra voltar ao mapeamento original.

**Suspeita 1:** mode_set OBJECT<->EDIT chained com smart_project + restore loop pode estar deselecionando todo mundo + reselecionando, causando spike de cost. Ou `bpy.ops.uv.smart_project` cacheia algo problemático.

**Suspeita 2:** `bpy.ops.uv.smart_project` (uv_authoring.py:53) usa face normal pra escolher projeção. Para um quad no plano XZ (Front Ortho convention), a normal aponta -Y - smart_project pode estar interpretando isso como "back side" e flipar U + rotacionar 90° pra alinhar. UVs originais (autorados manualmente em build_blend.py com layout específico pra evitar mirror em Front Ortho) são SOBRESCRITAS por essa projeção automática que não respeita o setup original.

**Fix proposto:**

- Substituir `bpy.ops.uv.smart_project` por reprojeção manual: detectar plano do mesh (X, Y ou Z aligned), mapear UVs naive (face vertices em world space → UV [0..1] baseado em bounding box no plano detectado), respeitando o flip-U-pra-Front-Ortho que `build_blend.py` faz.
- Alternativa: `bpy.ops.uv.unwrap` (cube/cylinder/sphere projection explícita) em vez de smart_project, com config determinística.
- Mínimo (parcialmente feito): limitação documentada no docstring + tooltip, e o start em Edit Mode é rejeitado. O fix de orientação em si NÃO foi aplicado - ainda usa smart_project.

**Arquivo:** `apps/blender/operators/uv_authoring.py:39-66` (`PROSCENIO_OT_reproject_sprite_uv`).

**Severity:** medium - operator funciona (não crash), mas resultado é destrutivo de UVs autoradas. Usuário precisa transformar manualmente pra recuperar layout original. Bloqueante pra workflow onde UVs foram cuidadosamente alinhadas (típico em pixel art). Owned pelo trabalho de UI/help surfaces.

### Help topic `sprite_frame_preview` é orphan - sem entry point na UI

**Status:** o fix `6749412` chegou a wirar um help button via `draw_subbox_header`, mas o restructure da sidebar (#96) regrediu silenciosamente - `panels/_helpers.py` ainda define `draw_subbox_header` com ZERO callers. O help button está ausente de novo; re-wirar nos `_draw_*.py` das sub-boxes. (Item `[blocking]` do trabalho de UI/help surfaces.)

**Repro:** abre fixture com sprite_frame mesh (ex: `examples/generated/mouth_drive/mouth_drive.blend` ou blink_eyes) > select sprite_frame mesh > N-panel > Proscenio > Active Sprite > sub-box "Sprite frame" expandido.

**Sintoma:** sub-box "Sprite frame" tem só label header + fields (hframes / vframes / frame / centered) + Setup/Remove Preview buttons. **NÃO tem ícone `?`** pra abrir help topic. Visual confirmado em screenshot do usuário (10-mai-2026 sessão 1.13 item 9).

**Causa:** `apps/blender/panels/_draw_sprite_frame.py:26` desenha `box.label(text="Sprite frame", icon="IMAGE_DATA")` - label puro, sem operator. Não chama `draw_subpanel_header` nem invoca `proscenio.help` com `topic="sprite_frame_preview"`. Help topic está definido em `apps/blender/core/help_topics.py:432` + tem FeatureStatus entry em `apps/blender/core/feature_status.py:115`, mas inacessível via UI - só dá pra abrir programaticamente via `bpy.ops.proscenio.help(topic="sprite_frame_preview")`.

**Fix proposto:**

- Em `_draw_sprite_frame.py:24-26`, trocar `box.label(text="Sprite frame", icon="IMAGE_DATA")` por header row com label + status icon + help button análogo a `draw_subpanel_header(layout, feature_id, help_topic)`. Adicionar helper `_helpers.draw_subbox_header()` pra reuso (Active Sprite sub-boxes não são panels, headers funcionam diferente).
- Mesma família de gap aplica a outras sub-boxes (Sprite frame / Polygon body / Texture region / Drive from Bone). Inventário: confirmar quais tópicos já têm entry visível e quais são orphan.

**Arquivo:** `apps/blender/panels/_draw_sprite_frame.py:24-26`, e provavelmente outros `_draw_*.py`.

**Severity:** low-medium - não é crash, mas help topic existe e foi documentado/testado como acessível via UI; checklist 1.13 item 9 falha por causa disso. Indica que o pattern de "help button per sub-box" está incompleto.

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

## apps/blender - code-read audit (2026-06-15, not reproduced)

From the QA Companion audit, verified against current `main`; read-not-reproduced, so confirm a repro before fixing. Dead code + the duplicated driver-axis enum went to [backlog-code-quality.md](backlog-code-quality.md); doc gaps to [backlog-docs.md](backlog-docs.md). Grouped by area for a future robustness STUDY.

**Export / atlas correctness.**

- **Pixels-per-unit ignored on the first export** (high) - the operator uses its own ExportHelper default (100), not the panel's `scene.proscenio.pixels_per_unit`; only Re-export reads the scene value, so editing the panel field silently does nothing on the first export. `export_flow.py:158-167`, `pipeline.py:89`.
- **Apply Packed Atlas counts a no-UV sprite as rewritten** (med) - `_apply_to_object` returns True for `element_type=="sprite"` regardless of whether `_rewrite_uvs` succeeded; the "skipped (no UV layer)" guard only fires for non-sprite meshes. `atlas_pack/apply.py:165-216`.

**Operator robustness + feedback.**

- **Select Issue Object can traceback on an out-of-view object** (med) - `select_issue_object` -> `select_named_or_warn` -> `select_only` has no view-layer guard (spec 043 guarded only the outliner path); selecting an object outside the active view layer raises. `selection.py:40`, `_shared/select.py:23-35`.
- **Bake Current Pose keys both quaternion and euler** (med) - inserts on both rotation channels for every bone regardless of `bone.rotation_mode`, leaving garbage fcurves on the unused channel. `pose_library.py:143-145`.
- **Quick Armature lock-to-front-ortho ignored at invoke** (low) - `invoke` reads the other options from the PG but not `lock_to_front_ortho`, so the panel toggle has no effect unless overridden via F3. `quick_armature.py:200-221`.
- **Copy Weights to Selected returns FINISHED on a zero-coverage transfer** (low) - a fully-uncovered transfer registers as a successful undo step with no weights applied (only the report downgrades to WARNING). `copy_weights_to_selected.py:49-51`.
- **Bake IK to Keyframes leaves the selection altered** (low) - mutates per-bone selection to scope `nla.bake`, never restores it. `authoring_ik.py:201-213`.
- **Action-row CANCELLED feedback suppressed at log level "errors"** (low) - the no-armature/not-found/multi-armature warnings go through the gated `report_warn`, so a failed click is silent. `report.py:50-53`, `selection.py`.

**Inert / wrong-target controls.**

- **Show-provenance-overlay panel toggle is inert outside the modal** (med) - the toggle registers no draw handler; the overlay only exists inside the Edit Weights modal, so as a standalone toggle it does nothing. `weight_paint.py:338`, `edit_weights.py:97-99`.
- **Diagnostics / Help "?" open the wrong help topic** (low) - both hard-code `help_topic="pipeline_overview"` with no matching HELP_TOPICS entry. `diagnostics.py:29`, `help.py:44`.
- **Run Smoke Test bypasses the report gate + prefix** (low) - raw `self.report` instead of `report_info`. `help_dispatch.py:110`.

**Photoshop-import side effects (Blender side).**

- **Re-import always rebuilds the armature** (low) - `import_manifest` calls `build_root_armature` every run, so the doc's "rotation, parenting, weights survive" reuse claim is likely false; verify the round-trip or correct the doc. `importers/photoshop/__init__.py:68-91`. Tied to the Godot reimporter decision in [backlog-godot-importer.md](backlog-godot-importer.md).
- **Import silently overwrites the panel pixels-per-unit** (low) - `_sync_scene_pixels_per_unit` overwrites the scene value with the manifest's on every import, no warning. `importers/photoshop/__init__.py:94-107`.
