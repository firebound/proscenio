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

**Severity:** medium - operator funciona (não crash), mas resultado é destrutivo de UVs autoradas. Usuário precisa transformar manualmente pra recuperar layout original. Bloqueante pra workflow onde UVs foram cuidadosamente alinhadas (típico em pixel art). Owned pela spec ui-help-surfaces (036).

### Help topic `sprite_frame_preview` é orphan - sem entry point na UI

**Status:** o fix `6749412` chegou a wirar um help button via `draw_subbox_header`, mas o restructure da spec 022 (#96) regrediu silenciosamente - `panels/_helpers.py` ainda define `draw_subbox_header` com ZERO callers. O help button está ausente de novo; re-wirar nos `_draw_*.py` das sub-boxes. (Item `[blocking]` da spec ui-help-surfaces / 036.)

**Repro:** abre fixture com sprite_frame mesh (ex: `examples/generated/mouth_drive/mouth_drive.blend` ou blink_eyes) > select sprite_frame mesh > N-panel > Proscenio > Active Sprite > sub-box "Sprite frame" expandido.

**Sintoma:** sub-box "Sprite frame" tem só label header + fields (hframes / vframes / frame / centered) + Setup/Remove Preview buttons. **NÃO tem ícone `?`** pra abrir help topic. Visual confirmado em screenshot do usuário (10-mai-2026 sessão 1.13 item 9).

**Causa:** `apps/blender/panels/_draw_sprite_frame.py:26` desenha `box.label(text="Sprite frame", icon="IMAGE_DATA")` - label puro, sem operator. Não chama `draw_subpanel_header` nem invoca `proscenio.help` com `topic="sprite_frame_preview"`. Help topic está definido em `apps/blender/core/help_topics.py:432` + tem FeatureStatus entry em `apps/blender/core/feature_status.py:115`, mas inacessível via UI - só dá pra abrir programaticamente via `bpy.ops.proscenio.help(topic="sprite_frame_preview")`.

**Fix proposto:**

- Em `_draw_sprite_frame.py:24-26`, trocar `box.label(text="Sprite frame", icon="IMAGE_DATA")` por header row com label + status icon + help button análogo a `draw_subpanel_header(layout, feature_id, help_topic)`. Adicionar helper `_helpers.draw_subbox_header()` pra reuso (Active Sprite sub-boxes não são panels, headers funcionam diferente).
- Mesma família de gap aplica a outras sub-boxes (Sprite frame / Polygon body / Texture region / Drive from Bone). Inventário: confirmar quais tópicos já têm entry visível e quais são orphan.

**Arquivo:** `apps/blender/panels/_draw_sprite_frame.py:24-26`, e provavelmente outros `_draw_*.py`.

**Severity:** low-medium - não é crash, mas help topic existe e foi documentado/testado como acessível via UI; checklist 1.13 item 9 falha por causa disso. Indica que o pattern de "help button per sub-box" está incompleto.

## apps/photoshop

### Export do manifest falha por completo quando uma única layer falha (sem try/catch + gate atômico)

Gatilho da spec [040-end-to-end-verification](040-end-to-end-verification/STUDY.md); surfaced pela auditoria do caminho de export (findings F-01 / F-02 em [checklist/photoshop.md](040-end-to-end-verification/checklist/photoshop.md)). Foi o que bloqueou um export real (12-jun-2026).

**Repro:** Photoshop > painel Proscenio Exporter > escolher pasta de saída > abrir um PSD com layers > "Export manifest + PNGs". Reproduz quando (a) uma layer não pode ser duplicada / merge / `trim` / `saveAs.png` pelo UXP, OU (b) uma layer foi renomeada / movida / reordenada depois que o preview foi montado.

**Sintoma:** banner de falha genérico (`kind: 'failed'` com a `Error.message` crua); **nenhum** `*.photoshop_exported.json` é escrito em disco; PNGs parciais das layers que deram certo podem ficar para trás.

**Causa raiz (dois fatores compostos):**

- **Sem try/catch por layer.** `runWrites` chama `writeLayerPng` sem proteção (`png-writer.ts:29-43` + `46-77`); qualquer rejeição da API UXP (`documents.add`, `layer.duplicate`, `merge`, `trim`, `saveAs.png`) propaga, rejeita o `core.executeAsModal` e cai no catch externo que retorna `failed` — o manifest nunca chega a ser escrito.
- **Gate atômico tudo-ou-nada.** O manifest só é gravado se `results.every(r => r.ok)` (`export-flow.ts:120-137`). Uma única layer que não resolve (`findLayerByPath === null`) zera `allOk` e suprime o manifest do documento inteiro. O match é por nome bruto, byte-exato (`_layer-find.ts:22-31`), então qualquer rename no meio da sessão quebra.

**Fix proposto:**

- Envolver `writeLayerPng` em try/catch por-layer, coletando a falha como `{ ok: false, outputPath, reason }` em vez de deixar propagar — uma layer ruim vira um aviso por-entrada, não um abort global.
- Reavaliar o gate atômico: ou (a) escrever o manifest com as entradas que deram certo + relatar as puladas, ou (b) manter atômico mas com erro **acionável** nomeando a layer culpada (nome + motivo) no lugar do banner genérico.
- Tornar `findLayerByPath` resiliente a rename: casar por id de layer quando disponível, ou re-resolver a partir do plano em vez do nome bruto (`_layer-find.ts:22-31`). Relacionado: F-24 (nomes-irmãos duplicados roteiam toda edição para o primeiro match).

**Suspeitos secundários (mesmo painel):** F-03 token de pasta obsoleto (`createFile`/`write` rejeitam sem affordance de "escolher pasta de novo", `manifest-writer.ts:14-18`); F-04 botão Export habilitado pelo snapshot mas `runExport` lê `app.activeDocument` ao vivo → `no-document` se o doc fechar (`export-flow.ts:94-98`).

**Arquivos:** `apps/photoshop/src/api/png-writer.ts:29-77`, `apps/photoshop/src/api/export-flow.ts:118-155`, `apps/photoshop/src/api/_layer-find.ts:22-31`.

**Severity:** high - bloqueia o export do manifest por completo, sem mensagem acionável. Confirmado por usuário em uso real.
