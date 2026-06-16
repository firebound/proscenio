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

### Sprite multi-frame: preview no Blender != frame no Godot (diferença inerente, não-bug mas pegadinha de autoria)

**Status:** observado durante a validação de fidelidade dos exemplos (jun-2026). Não é defeito de código; é consequência do modelo (Blender mostra a região da atlas no quad; Godot `Sprite2D` mostra UMA célula no tamanho nativo de pixel da região/`hframes`).

**Sintoma:** um elemento `sprite` (ex: `mixed_feature.mouth`, region 64x64, hframes=4) aparece no Blender como o quad inteiro mapeado na região (4 frames espremidos), e no Godot como 1 frame no tamanho nativo (16x64 px). Se o quad autorado não casar com o aspecto do frame (`frame_px/ppu`), os BOUNDS divergem entre Blender e Godot. UVs de sprite NÃO entram no golden (o `build_sprite` só emite region/frames), então só afetam o preview do Blender.

**Por que importa:** "Blender == Godot exato" vale pra geometria/posição e pra meshes; pra sprites multi-frame a igualdade pixel-a-pixel é impossível por design. A regra de autoria pra manter os BOUNDS casando é `quad_units = frame_px / ppu` (vide `blink_eyes`: quad = tamanho do frame, UVs 0..1 sobre a spritesheet). Documentar isso evita "recriar" sprites tentando casar pixel que nunca vai casar.

**Arquivo:** convenção - `packages/fixtures/README.md` (seção sprites) e `apps/godot/addons/proscenio/builders/sprite_builder.gd`. Sem fix de código; é doc/autoria.

**Severity:** low - pegadinha de autoria/expectativa, sem crash nem perda de dado.
