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

### Sprite frame out-of-range: Blender faz modulo (wrap), exporter faz clamp - animação diverge

**Status:** RESOLVIDO (A+C aplicados) - exporter passou a fazer wrap (modulo) em vez de clamp, casando o preview do Blender. Paridade negativa fechada por medição: a textura do sprite é `extension=REPEAT`, então a célula exibida no Blender pra overflow positivo E negativo = `frame mod (hframes*vframes)`, exatamente o `%` do Python (`-1 -> célula 3`); não precisou replicar fmod. Probe Godot da cena importada confirma as células 0/1 reaparecendo no overflow. Achados secundários abaixo (UPDATE_DISCRETE, anim.step/fps, bezier) seguem ABERTOS. (Investigação original jun-2026 sessão mouth_drive, dois lados medidos.)

**Sintoma (relatado pelo usuário):** a animação `mouth_drive_anim` parece diferente no Blender e no Godot. No Blender a boca abre e fecha num ciclo; no Godot ela "trava" e o movimento some. O usuário, mexendo no editor do Godot, percebeu que trocar a interpolação da track de NEAREST pra CUBIC fazia ficar "parecido" - mas isso era ilusão (CUBIC borra as keys sobreviventes; não recupera frames perdidos). NÃO é problema de framerate nem de curva de interpolação.

**Causa raiz (medida nos dois lados):** o Blender e o exporter DISCORDAM sobre o que fazer quando o índice de frame estoura o grid do spritesheet.

- O driver do fixture mouth_drive é `var * 2 + 2` (`packages/fixtures/mouth_drive/build_blend.py:216`), que mapeia a rotação do osso `mouth_drive` em [-pi/2, +pi/2] para valores de frame de 0 ate **5**. O spritesheet tem so 4 celulas (128x32, `hframes=4`, frames validos 0..3). Logo o driver pede celulas 4 e 5 que nao existem.
- **Blender (preview shader):** `apps/blender/core/bpy_helpers/spritesheet/spritesheet_shader.py:104-108` usa operacao `MODULO` pra escolher a coluna (`col = frame % hframes`). Entao frame fora de range DA A VOLTA: `4 % 4 = 0`, `5 % 4 = 1`. No viewport do Blender a boca volta pra celula 0 (aberta) / 1 (meio) - movimento visivel.
- **Exporter:** `apps/blender/exporters/godot/writer/sprite_frame_animations.py:180` (caminho driver, `_bake_track`) faz `value = min(max(raw, 0), max_frame)` com `max_frame = hframes*vframes-1 = 3`. CLAMPA: 4 e 5 viram 3. Depois o dedup de consecutivos colapsa a sequencia inteira de "3,3,3,..." numa unica key. O movimento some.
- O mesmo clamp existe no caminho de keyframe direto: `_direct_frame_track` em `sprite_frame_animations.py:225` (`value = min(max(round(...), 0), max_frame)`). Precisa do mesmo tratamento pra consistencia (ex: se uma fixture tipo blink_eyes algum dia estourar o range).

**Evidencia medida - valor cru do driver no Blender, frames 12-21 = `2,3,4,4,5,5,4,4,3,2`. Celula visivel resultante:**

| frame Blender | valor driver | celula Blender (modulo) | celula Godot (clamp) |
| --- | --- | --- | --- |
| 12 | 2 | 2 (fechada) | 2 |
| 13 | 3 | 3 (falando) | 3 |
| 14-15 | 4 | 0 (ABERTA) | 3 |
| 16-17 | 5 | 1 (meio) | 3 |
| 18-19 | 4 | 0 (ABERTA) | 3 |
| 20 | 3 | 3 | 3 |
| 21 | 2 | 2 | 2 |

No Godot, depois do clamp+dedup, as keys de sprite_frame exportadas sao so `frame 2,1,0,2,3,2` (confirmado em `examples/generated/mouth_drive/mouth_drive.expected.proscenio` e na cena importada). Os frames de boca aberta sumiram.

**Bonus - docstring mentirosa:** `packages/fixtures/mouth_drive/build_blend.py:28-30` afirma que "a IntProperty clampa pra [0, hframes*vframes-1] = [0,3], o que da um sweep limpo". Isso e FALSO: o preview do Blender faz modulo (wrap), nao clamp. O autor do fixture entendeu errado o comportamento. A IntProperty `proscenio.frame` nao tem clamp efetivo na leitura (a medicao leu 4 e 5 cruas).

**Fix decidido (recomendacao A + C; B descartada):**

- **A (conserta o pipeline - obrigatorio):** trocar o `clamp` do exporter por `modulo` pra casar com o Blender. Em `sprite_frame_animations.py:180` e `:225`, usar `value = raw % (max_frame + 1)` (com guarda pra `max_frame+1 > 0`; tratar negativo com modulo Python que ja retorna nao-negativo, diferente do fmod do Blender - VERIFICAR paridade com o `ShaderNodeMath MODULO` do Blender pra valores negativos, que usa fmod e pode dar negativo). Modulo (wrap) e a convencao padrao de spritesheet e e o que o Blender ja faz. Isso alinha as duas pontas na mesma regra - qualquer animacao que estoure o range passa a sair igual nos dois.
- **C (higiene do fixture - junto com A):** corrigir o driver do mouth_drive pra um mapeamento honesto que fique dentro de [0,3] OU manter o estouro de proposito mas corrigir a docstring (linhas 28-30) pra dizer "modulo/wrap", nao "clamp". Decidir se o fixture quer testar o wrap (ai mantem o estouro, com doc correta) ou um sweep limpo (ai conserta o driver). Sozinha, C so mascara: a discordancia wrap-vs-clamp continua latente pra outros exemplos.
- **B (descartada):** mudar o preview do Blender pra clampar igual ao exporter. Rejeitada porque tira do Godot a capacidade de wrap (conserta pra baixo).

**Atencao paridade negativa:** o `MODULO` do Blender (ShaderNodeMath) usa fmod C (mantem o sinal: `-1 % 4 = -1`). Python `%` retorna nao-negativo (`-1 % 4 = 3`). Se o driver puder gerar frame negativo (o `var*2+2` no extremo `var=-pi/2` da ~-1.14 -> int -1), o exporter com Python `%` divergiria do Blender de novo. Replicar fmod no exporter (ou clampar negativo a 0 nos dois lados) pra fechar isso. CONFIRMAR como o Blender renderiza frame negativo antes de escolher.

**Verificacao visual pendente (nao feita):** li o shader e MEDI o valor do frame (0..5) no Blender, mas NAO renderizei os frames do Blender pra confirmar com os olhos que a celula 0/1 aparece via wrap. Confianca alta pela leitura do node group (operacao MODULO explicita). Se quiser certeza antes de mexer, renderizar 2-3 frames do Blender (ex: f15, f17) e comparar com o Godot.

**Como reproduzir (scripts headless usados):**

- Blender (valor por frame): `blender --background examples/generated/mouth_drive/mouth_drive.blend --python <script>` setando `scene.frame_set(f)` no range e lendo `obj.proscenio.frame` por frame. Confirma valores 0..5.
- Godot (cena importada): carregar `res://examples/mouth_drive/mouth_drive.proscenio` via `--headless --script`, pegar o `AnimationPlayer`, `get_animation("mouth_drive_anim")`, e amostrar `Sprite2D.frame` com `ap.seek(t, true)`. Confirma so 0..3. (Binario: `E:/godot/godot_std_console.exe`, 4.6.3; GDScript do projeto trata warning como erro - tipar tudo explicitamente.)

**Achados secundarios (mesma investigacao, prioridade menor, registrar pra nao perder):**

- A track de sprite_frame e importada como `update_mode = CONTINUOUS` (`apps/godot/addons/proscenio/builders/animation_builder.gd:148-154` - so seta interp NEAREST, nunca o update mode). Pra indice de frame discreto o correto e `UPDATE_DISCRETE`. Funciona hoje por causa do NEAREST, mas e fragil em blend/seek. Setar `value_track_set_update_mode(idx, UPDATE_DISCRETE)`.
- A animacao importada fica com `step = 1/30` (default do Godot; o importer nunca seta `anim.step`). O Blender autorou a 24fps. Isso muda a GRADE de frames do editor do Godot (30 vs 24), e so cosmetico (playback e em segundos, duracao identica), mas se quiser WYSIWYG na grade do editor: carregar `scene.render.fps` no schema/proscenio (hoje o formato descarta fps - so guarda segundos) e setar `anim.step = 1.0/fps` no importer.
- Gap de fidelidade bezier (geral, nao neste fixture): tracks de bone_transform exportam so valor+tempo das keys, descartam os handles bezier do Blender; o importer hardcoda CUBIC (position/scale) e CUBIC_ANGLE (rotation). CUBIC auto-tangente do Godot != bezier-com-handles do Blender, entao o easing de movimento de osso pode divergir. So vale investigar quando aparecer um caso com movimento de osso visivelmente diferente.

**Arquivos:** `apps/blender/exporters/godot/writer/sprite_frame_animations.py:180,225`; `apps/blender/core/bpy_helpers/spritesheet/spritesheet_shader.py:104-108`; `packages/fixtures/mouth_drive/build_blend.py:28-30,216`; (secundarios) `apps/godot/addons/proscenio/builders/animation_builder.gd:148-154`.

**Severity:** medium - animacao de sprite-frame sai visivelmente errada no Godot vs Blender sempre que o frame estoura o grid. Sem crash, mas quebra o WYSIWYG que e a promessa central do pipeline. Inclui uma fixture (mouth_drive) que exercita exatamente o caminho quebrado, entao da pra escrever teste de regressao golden + headline visual.
