# Bugs found during manual testing

Bugs reproducíveis encontrados durante manual smoke / feature tests
(backlog-manual-testing.md). Cada item cita reproducer + suspeita + arquivo
afetado. Vira PR fix ou issue dedicada.

Distinto de backlog-ui-feedback.md (que cobre polish, não comportamento).

---

## apps/blender

### Blender 5.1.1 crash em gizmo_button2d_draw apos view3d.snap_cursor_to_center (suspeito upstream)

**Repro:** intermitente. Sessão de smoke manual (15-mai-2026): após clear do active_armature picker + invoke Quick Armature + algumas operações de viewport, Blender crashou em `EXCEPTION_ACCESS_VIOLATION (NULL write)`. Last logged op: `bpy.ops.view3d.snap_cursor_to_center()`. Re-roda do mesmo workflow não reproduziu.

**Stack trace:**

```text
blender.exe: immVertex3f
blender.exe: imm_draw_circle_fill_3d
blender.exe: button2d_draw_intern
blender.exe: gizmo_button2d_draw
blender.exe: WM_gizmomap_draw
blender.exe: DRW_draw_gizmo_2d
blender.exe: drw_draw_render_loop_3d
blender.exe: DRW_draw_view
blender.exe: view3d_main_region_draw
```

**Análise:** stack 100% Blender internals. Nenhum frame Proscenio. `imm_draw_circle_fill_3d` (filled circle) não é chamado pelos nossos overlays - usamos `LINE_LOOP` via `draw_circle_3d`. Modules carregados incluem AMD GPU drivers (`atio6axx.dll`, `amdihk64.dll`). Provável: bug Blender 5.1.1 gizmo drawing OU AMD driver issue.

**Mitigação defensive (quick-armature feedback pass):** `on_depsgraph_update` handler (`apps/blender/properties/_handlers.py`) wrapped em `try/except Exception` blanket - depsgraph callbacks rodam dentro do draw/event loop e exception bubble-out pode deixar C side mid-state, candidato pra trigger crashes em draw subsequente. Handler agora swallow silenciosamente.

**Severity:** low - intermitente, não reproduzido na re-tentativa, fora do nosso código. Mantido watch caso vire recorrente.

**Trigger pra escalar:** se reproduzir 2x+ em sessões diferentes → file Blender bug report com este stack trace.

### Validator NÃO detecta keyframes de transform em slot attachments

**Repro:** slot_swap workbench. Select `club` (filha de `weapon` slot). Insert Keyframe em Location (cria `clubAction`). Run Validate via Export panel. Nenhum warning sobre os keyframes.

**Esperado:** warning tipo `[club] slot attachment 'club' carries transform keyframes -- runtime slot swap will ignore them`.

**Por que importa:** o slot system emite UM `bone_transform` track pro slot Empty inteiro -- attachments seguem ele. Se attachment próprio tem keyframes de location/rotation/scale, o writer ignora (não tem track type pra isso no slot_attachment), MAS o animator pensa que está animando algo. Resultado runtime: attachment "estático" em runtime apesar de keyframes no .blend.

**Causa:** `apps/blender/core/validation/active_slot.py` (`_check_slot_child_transform_keys`) provavelmente existe mas (a) não é chamado, (b) tem bug na detecção, ou (c) só checa rotation_quaternion, não Euler/location.

**Fix proposto:** walker em validate_export() que pra cada mesh filho direto de slot Empty (parent.proscenio.is_slot=True), checa animation_data.action.fcurves e flagga fcurves com data_path em `("location", "rotation_euler", "rotation_quaternion", "scale")`.

**Severity:** medium -- regra documentada no slot system. Sem o warning, usuário descobre o problema só em runtime (sprite parece travado).

### Validator flagga slot attachments como "no parent bone" (false positive)

**Repro:** slot_swap workbench. Run Validate via Export panel. Resultados:

- `[club] sprite has no parent bone and no vertex groups matching armature bones -- writer will fall back to empty bone field`
- `[sword] sprite has no parent bone and no vertex groups matching armature bones -- writer will fall back to empty bone field`

**Causa:** validator (provavelmente em `apps/blender/core/validation/active_sprite.py` ou similar) checa que mesh tem `parent_type=BONE` OU vertex_groups bateindo com armature bones. club e sword tem `parent_type=OBJECT` (filhos de `weapon` slot Empty), sem vertex groups -- batem na regra. Mas o slot system **explicitamente** desvia desse contrato: attachments seguem o slot Empty (que tem o bone parent), não precisam de parent_bone próprio.

**Fix proposto:** validator skipa check de parent bone pra mesh cujo `parent.proscenio.is_slot == True` (ou CP `proscenio_is_slot`). Attachment de slot herda bone via slot Empty.

**Severity:** medium -- não bloqueia export (são warnings, não errors), mas polui a Validation panel com noise toda vez que existir slot na cena.

### Validator lê PG só, ignora edits direto em Custom Properties

**Repro:** edita `proscenio_slot_default` direto na Custom Properties UI do Properties editor pra valor inválido (ex: `"fake"` quando attachments são club/sword). Active Slot panel não atualiza (PG.slot_default fica = "sword"). Run Validate -- nenhum erro reportado sobre o slot_default fantasma.

**Causa:** validator usa `core.props_access.object_props(obj)` que retorna o PG. PG não recebe update quando CP é editado manualmente (Blender não tem callback de CP change). Resultado: writer vai EMITIR o valor real do CP `"fake"` no .proscenio, mas validator (que lê PG) não vê problema.

**Two-pronged fix:**

1. Validator deve preferir o que o writer vai emitir. Writer usa `read_field` (PG → CP fallback) ou `read_bool_flag`. Validator deve usar a mesma função pra ler valores -- fonte de verdade unificada.
2. Documentar (no help / panel hint) que "editar Custom Properties direto não atualiza UI" -- workflow esperado é via panels, CP é fallback.

**Severity:** medium -- workflow CP-first é nicho mas existe; usuário fazendo isso vai exportar valor inválido sem aviso.

### Create Slot Path B: novo Empty fica em posição errada quando seed já tem parent

**Repro:** slot_swap_workbench. Object Mode, multi-select club + sword (ou só club, sword é hide_viewport=True). Active Slot panel > Create Slot. Novo Empty `slot` criado dentro de `weapon` Empty. Club visualmente pula pra outra posição na cena.

**Causa:** `apps/blender/operators/slot/create.py:82`:

```python
empty.location = seed.matrix_world.to_translation()
```

`empty.location` é **local** ao parent (weapon Empty no caso, porque o operator faz `empty.parent = seed.parent` na linha 79). Atribuir world translation a um campo local sem inverter o parent matrix compounda: a posição final de `empty` em world space = `weapon.matrix_world @ world_translation`, sai do lugar.

A reparente das meshes (linhas 87-92) preserva world matrix delas via `matrix_parent_inverse` + `matrix_world =`, mas isso é depois -- as meshes ainda terminam em world position correta na maioria dos casos. O que pula é o EMPTY, e visualmente as meshes sob ele acompanham o display offset do parent.

**Fix proposto:** trocar linha 82 por:

```python
empty.matrix_world = seed.matrix_world.copy()
```

Ou setar `empty.location` em local space inverso explicitamente:

```python
empty.matrix_parent_inverse = empty.parent.matrix_world.inverted()
empty.location = seed.matrix_world.to_translation()  # agora consistente
```

**Severity:** medium -- Path B funciona para meshes sem parent (cenário documentado no slot system), mas quebra para meshes já parented (cenário comum: criando slot dentro de um rig que já tem armature).

### Reproject UV: segunda chamada lenta + UV resultante rotacionada/flipada

**Repro:** Active Sprite > polygon mode > "Reproject UV". Sintomas em primeira E segunda chamadas.

**Sintoma 1 (perf):** segunda chamada demora vários segundos como se fosse crashar (testes anteriores em doll).

**Sintoma 2 (orientação):** UV resultante fica rotacionada 90° + horizontalmente invertida. Confirmado em atlas_pack_workbench sprite_1 (11-mai-2026): após Reproject UV, layout precisou de `R -90 S X -1` (rotate -90° + scale X = -1 no UV editor) pra voltar ao mapeamento original.

**Suspeita 1:** mode_set OBJECT<->EDIT chained com smart_project + restore loop pode estar deselecionando todo mundo + reselecionando, causando spike de cost. Ou `bpy.ops.uv.smart_project` cacheia algo problemático.

**Suspeita 2:** `bpy.ops.uv.smart_project` (uv_authoring.py:53) usa face normal pra escolher projeção. Para um quad no plano XZ (Front Ortho convention), a normal aponta -Y - smart_project pode estar interpretando isso como "back side" e flipar U + rotacionar 90° pra alinhar. UVs originais (autorados manualmente em build_blend.py com layout específico pra evitar mirror em Front Ortho) são SOBRESCRITAS por essa projeção automática que não respeita o setup original.

**Fix proposto:**

- Substituir `bpy.ops.uv.smart_project` por reprojeção manual: detectar plano do mesh (X, Y ou Z aligned), mapear UVs naive (face vertices em world space → UV [0..1] baseado em bounding box no plano detectado), respeitando o flip-U-pra-Front-Ortho que `build_blend.py` faz.
- Alternativa: `bpy.ops.uv.unwrap` (cube/cylinder/sphere projection explícita) em vez de smart_project, com config determinística.
- Mínimo: documentar limitação no help topic do Reproject UV ("re-roda Smart UV Project, pode mudar orientação de UVs autoradas manualmente").

**Arquivo:** `apps/blender/operators/uv_authoring.py:39-66` (`PROSCENIO_OT_reproject_sprite_uv`).

**Severity:** medium - operator funciona (não crash), mas resultado é destrutivo de UVs autoradas. Usuário precisa transformar manualmente pra recuperar layout original. Bloqueante pra workflow onde UVs foram cuidadosamente alinhadas (típico em pixel art).

---

### Skeleton panel: row click no UIList não seleciona bone no viewport

**Repro:** doll_workbench.blend > Pose Mode > deselect all (`Alt+A`) > Proscenio > subpanel Skeleton > click row `upper_arm.L` no UIList de bones.

**Sintoma:** linha highlight no panel (active_bone_index muda), mas viewport não reflete - nenhum bone selecionado, nenhum active bone na armatura. Comportamento esperado pela backlog-manual-testing.md item 1.8.2: click row → seleciona bone correspondente em pose mode.

**Causa:** `apps/blender/properties/scene_props.py:54` define `active_bone_index` como `IntProperty` puro, sem `update=` callback. `apps/blender/panels/skeleton.py:73-80` usa `template_list` apontando pra esse PG, que só armazena o índice; não há operator no row draw nem update hook que sincronize com `armature.data.bones.active` ou `armature.pose.bones[...].bone.select`.

**Comparação:** Outliner panel resolve o mesmo problema com operator dedicado (`proscenio.select_outliner_object`) clicado via row draw_item. Skeleton panel não tem equivalente.

**Fix proposto (opção A):** novo operator `proscenio.select_bone_by_index` chamado de dentro de `PROSCENIO_UL_bones.draw_item`. Operator entra em pose mode (se preciso), set `armature.data.bones.active` + `pose_bone.bone.select = True`.

**Fix proposto (opção B, mais simples):** adicionar `update=` callback ao `active_bone_index` que faz a sincronização. Risco: callback dispara em todos os redraws e pode causar feedback loop com modos não-pose.

**Arquivo:** `apps/blender/properties/scene_props.py:54-59`, `apps/blender/panels/skeleton.py:12-31`.

**Severity:** medium - panel oferece UX de selector de bone, mas não cumpre. Usuário precisa selecionar bone no viewport manualmente.

### Atlas Unpack: rename de material entre Apply e Unpack quebra restauração silenciosamente

**Repro:** atlas_pack_workbench.blend > Pack > Apply (com `sprite_5` `material_isolated=True`) > Properties > Material > renomear `sprite_5.mat` pra `foo.mat` > Unpack Atlas.

**Sintoma:** `sprite_5` continua com `foo.mat` (renomeado) ao invés de voltar pro material original. Sem warning. INFO bar reporta "unpacked N sprite(s)" mesmo com o restore parcial.

**Causa:** `unpack.py:70-79`:

```python
mat_name = str(snapshot.get("material", ""))
mat = bpy.data.materials.get(mat_name)  # lookup BY NAME
if mat is None:
    return  # <-- silent early return
materials[0] = mat
```

Snapshot guarda nome (string) do material no momento do Apply. Se nome mudou depois, `bpy.data.materials.get(name)` retorna None e a função retorna sem reportar.

Mesmo bug aplica ao shared material - se `Proscenio.PackedAtlas` for renomeado, próximo Apply cria um novo (re-discovery falha + cria) deixando o renomeado órfão.

**Fix proposto:**

- Snapshot deveria guardar referência por pointer (não por nome): usar `bpy.types.PropertyGroup` com `PointerProperty(type=bpy.types.Material)` em vez de CP string. Blender atualiza pointer automaticamente quando datablock renomeia.
- Alternativa low-effort: na restauração, se `materials.get(name)` falha, escanear materials por algum marker (CP `proscenio_original_for: "sprite_5"`) que cada material carrega depois do Apply.
- Mínimo aceitável: warning explícito no INFO bar quando snapshot.material name não acha (ex: "sprite_5: original material 'sprite_5.mat' not found - maybe renamed; restored UVs only").

**Arquivo:** `apps/blender/operators/atlas_pack/apply.py:80-97` (snapshot escrita), `apps/blender/operators/atlas_pack/unpack.py:70-83` (restauração).

**Severity:** medium - não trava, mas perde estado original sem avisar. Usuário descobre só ao olhar Properties > Material.

### Help topic `sprite_frame_preview` é orphan - sem entry point na UI

**Update (2026-06-10 audit):** o fix `6749412` chegou a wirar um help button via `draw_subbox_header`, mas o restructure da spec 022 (#96) regrediu silenciosamente - `panels/_helpers.py` ainda define `draw_subbox_header` com ZERO callers. Re-wirar nos `_draw_*.py` das sub-boxes.

**Repro:** abre fixture com sprite_frame mesh (ex: `examples/generated/mouth_drive/mouth_drive.blend` ou blink_eyes) > select sprite_frame mesh > N-panel > Proscenio > Active Sprite > sub-box "Sprite frame" expandido.

**Sintoma:** sub-box "Sprite frame" tem só label header + fields (hframes / vframes / frame / centered) + Setup/Remove Preview buttons. **NÃO tem ícone `?`** pra abrir help topic. Visual confirmado em screenshot do usuário (10-mai-2026 sessão 1.13 item 9).

**Causa:** `apps/blender/panels/_draw_sprite_frame.py:26` desenha `box.label(text="Sprite frame", icon="IMAGE_DATA")` - label puro, sem operator. Não chama `draw_subpanel_header` nem invoca `proscenio.help` com `topic="sprite_frame_preview"`. Help topic está definido em `apps/blender/core/help_topics.py:432` + tem FeatureStatus entry em `apps/blender/core/feature_status.py:115`, mas inacessível via UI - só dá pra abrir programaticamente via `bpy.ops.proscenio.help(topic="sprite_frame_preview")`.

**Fix proposto:**

- Em `_draw_sprite_frame.py:24-26`, trocar `box.label(text="Sprite frame", icon="IMAGE_DATA")` por header row com label + status icon + help button análogo a `draw_subpanel_header(layout, feature_id, help_topic)`. Adicionar helper `_helpers.draw_subbox_header()` pra reuso (Active Sprite sub-boxes não são panels, headers funcionam diferente).
- Mesma família de gap aplica a outras sub-boxes (Sprite frame / Polygon body / Texture region / Drive from Bone). Inventário: confirmar quais tópicos já têm entry visível e quais são orphan.

**Arquivo:** `apps/blender/panels/_draw_sprite_frame.py:24-26`, e provavelmente outros `_draw_*.py`.

**Severity:** low-medium - não é crash, mas help topic existe e foi documentado/testado como acessível via UI; checklist 1.13 item 9 falha por causa disso. Indica que o pattern de "help button per sub-box" está incompleto.

### Save Pose to Library: `Unexpected library type` sem orientação ao usuário

**Repro:** doll_workbench.blend > Pose Mode > select bones + aplicar pose > N-panel > Proscenio > Skeleton > Save Pose to Library.

**Sintoma:** ERROR bar `Proscenio: pose library refused: Error: Unexpected library type. Failed to create pose asset`. Operator falha sem indicar o que fazer.

**Causa:** Blender 4.x+ removeu defaults writable do Pose Library. `bpy.ops.poselib.create_pose_asset` recusa quando nenhuma asset library destino configurada em Preferences > File Paths > Asset Libraries (com path acessível pra escrita). Erro propagado vem do Blender core; `pose_library.py:68-70` só repassa via `report_error(self, f"pose library refused: {exc}")`.

Usuário não sabe que precisa configurar asset library primeiro. Mesmo trocando uma área pra Asset Browser não resolve - precisa adicionar library destino nas Preferences.

**Fix proposto:**

- Pré-check em `execute()`: detectar se existe asset library writable (`bpy.context.preferences.filepaths.asset_libraries` - iterar + checar `path` exists + writable).
- Se nenhuma: `report_error(self, "no writable asset library configured. Add one in Preferences > File Paths > Asset Libraries.")` com instrução acionável.
- Ainda melhor: botão "Open Preferences" no panel próximo ao Save Pose, ou auto-criar asset library default em `~/Documents/Blender/Proscenio Pose Library/`.

**Arquivo:** `apps/blender/operators/pose_library.py:23-73` (PROSCENIO_OT_save_pose_asset).

**Severity:** medium - não crash, mas operator inusável out-of-the-box sem setup explícito que não tá documentado nem na UI. Bloqueia 1.15 items 1 e 2 do backlog-manual-testing.

### Automesh Interactive (modal): ferramentas extend / cut quebradas

**Repro:** `examples/generated/automesh/automesh.blend` > select sprite plane > Mesh Generation > Automesh Interactive > Automesh (modal) > avança até o Stage 2 (extend / cut) > usa as ferramentas de extend e de cut.

**Sintoma:** as ferramentas não fazem nada OU geram muitos artefatos indesejados na malha (revisão manual 08-jun-2026). Stage 4 (interior points add / shift+click delete) parece funcionar; o problema é o Stage 2 extend / cut.

**Suspeita:** `apps/blender/operators/automesh/automesh_authoring.py` - o dispatch do pen tool no Stage 2 (EXTEND / CUT) ou a splice do outer contour. Os scenarios T1 / T6 de `backlog-manual-testing.md` 1.23 / 1.25 (Stage 2 extend / cut, cut overlay vermelho, snap / merge / loop) nunca foram validados em sessão - estão `[ ]`. Precisa repro com console aberto pra capturar traceback / inspecionar a malha resultante.

**Arquivo:** `apps/blender/operators/automesh/automesh_authoring.py` (Stage 2 EXTEND / CUT) + `core/bpy_helpers/automesh` (splice / triangulação).

**Severity:** medium-high - inviabiliza o autoring interativo de silhueta (o ponto principal do modal). Confirmar causa exata antes de fix.

### Edit Weights: brush curve presets disparam erro

**Repro:** Weight Paint > Edit Weights > entra em Weight Paint mode (bound mesh) > clica num dos presets de "Brush curve preset" (Hard Edge / Soft Falloff / Crease / Smooth Blend).

**Sintoma:** dá erro ao clicar (revisão manual 08-jun-2026). Texto exato do erro / traceback ainda não capturado.

**Suspeita:** `apps/blender/operators/skinning/brush_preset.py:31-49` (`execute`) - a manipulação de `brush.curve.curves[0].points` (remove até 2, set `.location` dos 2 primeiros, `points.new(x, y)` pro resto, `brush.curve.update()`). Candidatos: (a) `points.new(x, y)` com x colidindo / fora de ordem após o set de `.location`; (b) reordenação automática do CurveMap deslocando índices entre o set e o new; (c) API de curva do brush de weight paint mudou no Blender 5.1. Menos provável: o WARNING "Active brush has no curve mapping" (guard já existente) sendo percebido como erro.

**Fix proposto:** capturar o traceback exato no console primeiro. Provável fix robusto: limpar todos os pontos exceto os 2 mínimos, inserir os novos em ordem crescente de x via `points.new`, e só então setar `.location` dos 2 fixos, com `brush.curve.update()` ao final; ou reconstruir o mapping inteiro num bloco try/except que reporta WARNING em vez de propagar RuntimeError.

**Arquivo:** `apps/blender/operators/skinning/brush_preset.py:31-49`.

**Severity:** medium - o preset é QoL (poupa ida ao editor de curva); quebrado, o user cai no fluxo manual. Precisa traceback exato.

### Create Slot por seleção de mesh: Empty em posição aparentemente aleatória quando origin da mesh não foi aplicada

**Repro:** Object Mode > seleciona mesh(es) cuja origin NÃO foi aplicada (origin no (0,0,0), geometria offsetada) > Slots > Create Slot.

**Sintoma:** o slot Empty aparece numa posição que parece aleatória / longe da geometria visível (revisão manual 08-jun-2026, criando slots por seleção de mesh).

**Suspeita:** mesma família do bug "Create Slot Path B: novo Empty fica em posição errada quando seed já tem parent", mas com trigger distinto. `apps/blender/operators/slot/create.py` posiciona o Empty a partir da translation do objeto seed (`seed.matrix_world.to_translation()` / `seed.location`); quando a origin não está aplicada, a translation não coincide com o centro visível da geometria, então o Empty cai na origin do objeto (longe dos vertices).

**Fix proposto:** posicionar o Empty no centro do bounding box da geometria selecionada (média dos `matrix_world @ v.co`) em vez da object translation, OU avisar / oferecer "apply origin" quando a origin diverge do centro da geometria. Confirmar no operator atual qual referência de posição é usada.

**Arquivo:** `apps/blender/operators/slot/create.py`.

**Severity:** medium - Create Slot por seleção de mesh é fluxo novo e útil; posicionamento confuso prejudica a primeira impressão. Workaround: aplicar origin (Object > Set Origin) antes de criar o slot.

### Per-bone Soft/Hard overrides são inertes no modo BONE_HEAT (o default)

**Repro:** Weight Paint > Bind > Mode = "Bone Heat (Blender native)" (default) > seta alguns bones pra Soft / Hard na box "Per-bone Soft/Hard overrides" > Bind to Picker Armature.

**Sintoma:** os overrides por-bone não têm efeito nenhum. Os pesos saem 100% do bone heat nativo do Blender, ignorando Soft / Hard.

**Causa:** `apps/blender/core/bpy_helpers/skinning/bind_apply.py:225` - `apply_bind` retorna cedo via `_apply_bone_heat` quando `mode == "BONE_HEAT"`, ANTES de `_apply_bone_mode_overrides` (linha 249, alcançado só pelos modos planar PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY). `_apply_bone_heat` delega pro `bpy.ops.object.parent_set(ARMATURE_AUTO)` e nunca lê `proscenio_bone_modes`. Como BONE_HEAT é o default e a box de overrides aparece sempre, o usuário seta Soft / Hard achando que muda algo.

**Fix proposto:** (a) esconder / desabilitar a box de overrides quando Mode == BONE_HEAT, com hint "overrides só valem nos modos planar"; ou (b) aplicar os overrides como pós-passe mesmo depois do bone heat (recomputar as colunas dos bones override via planar e splicar - mais trabalho). Mínimo: avisar na UI que overrides não valem no bone heat.

**Arquivo:** `apps/blender/core/bpy_helpers/skinning/bind_apply.py:225,249`; `apps/blender/panels/weight_paint.py` `_draw_bind` (gating da box).

**Severity:** medium - affordance proeminente que não faz nada no modo default; confunde e mina a confiança na feature.

### Writer exporta `armatures[0]` e ignora o active-armature picker

**Repro:** cena com 2+ armatures (ex: rig principal + `Proscenio.QuickRig` de teste). Setar o picker do Skeleton panel pra segunda armature. Export Godot.

**Sintoma:** o `.proscenio` sai com o esqueleto da PRIMEIRA armature em scene order, não a escolhida no picker. O panel mostra warning "2 armatures - writer uses the first only", mas o picker (fonte de verdade desde a feedback pass do Quick Armature) não alimenta o writer.

**Causa:** `apps/blender/exporters/godot/writer/scene_discovery.py:14-17` (`find_armature`) itera `scene.objects` e retorna a primeira ARMATURE; nunca lê o PointerProperty do picker (`scene_props.py:473-486`).

**Fix proposto:** `find_armature` prefere o picker quando setado e válido (fallback pra scene order quando vazio); o warning do Skeleton panel passa a citar o nome efetivamente usado. Descoberto na auditoria 2026-06-10 (o picker shippou na UI mas o writer nunca foi atualizado).

**Severity:** medium-high - output correctness em cena multi-armature; usuário acha que escolheu o rig e o export usa outro silenciosamente.

### Fixtures simple_psd / slot_cycle: provável path absoluto de imagem bake'ado no .blend

Herdado do fix do blink_eyes (que ganhou `bpy.path.relpath` + re-save e saiu deste arquivo): `packages/fixtures/slot_cycle/build_blend.py` carrega imagem sem rewrite pra relativo antes do save (auditoria 2026-06-10: nenhum `relpath` no arquivo), e `simple_psd` delega ao importer Photoshop, que também não relativiza. Auditar ambos ao rodar os testes manuais dessas fixtures; aplicar o padrão do blink_eyes (`bpy.path.relpath` após `save_as_mainfile` + save de novo).

**Severity:** low - quebra portabilidade do `.blend` da fixture entre máquinas, não o pipeline.

### Weight Transfer: sem warning quando targets ficam fora do alcance (cobertura zero silenciosa)

**Repro:** Weight Paint > Weight Transfer > active mesh (source) + selecionar target mesh afastado (> max_distance, default 0.5 world units) > Copy Weights to Selected.

**Sintoma:** targets fora do raio recebem dict vazio (zero peso) silenciosamente. INFO bar reporta "Copied weights to N vert(s)" mas não avisa que M targets / verts ficaram sem nada.

**Causa:** `apps/blender/core/skinning/weight_transfer.py:45` - vert além de `max_distance` recebe `{}`; `apps/blender/operators/skinning/copy_weights_to_selected.py` `_apply_to_target` conta só os aplicados, não reporta os zerados. Sem warning de cobertura baixa nem de mesh inteiramente fora do alcance.

**Fix proposto:** reportar por-target a cobertura (`X/Y verts receberam peso`); WARNING quando a cobertura for 0 ou muito baixa ("target '<name>' fora do alcance - aumente Max Distance ou aproxime as malhas"). Surfacar `max_distance` no painel (hoje só F9).

**Arquivo:** `apps/blender/operators/skinning/copy_weights_to_selected.py:40-52`.

**Severity:** low-medium - não crash, mas o transfer "falha" sem avisar; usuário acha que copiou e a malha fica sem deformar.

---

## apps/photoshop

### JSX exporter: `pixels_per_unit` não roundtripa (hardcoded 100)

**Repro:** Roundtrip oracle the photoshop UXP migration:

1. Blender escreve `00_blender_base/doll_base.photoshop_manifest.json` com `pixels_per_unit = 1000.0` (PPU do `render_layers.py`).
2. Proscenio Exporter panel (Import manifest as PSD) lê manifest, popula `01_photoshop_base/doll_ps_base.psd` (não persiste PPU em metadado).
3. Re-exportar `02_photoshop_setup/doll_tagged.psd` → `02_photoshop_setup/export/doll_tagged.photoshop_exported.json` com `pixels_per_unit = 100`.

Diff esperado byte-equal contra a (1) falha só nesse campo (+ paths esperados por design).

**Causa:** `proscenio_export.jsx:54` declara `DEFAULT_PIXELS_PER_UNIT = 100` e usa direto no manifest sem nada pra ler do PSD. `proscenio_import.jsx` não grava o PPU original em XMP/custom metadata, então export.jsx não tem fonte de verdade.

**Fix proposto:**

- `proscenio_import.jsx`: gravar `pixels_per_unit` em `doc.info` ou XMP custom namespace (`http://proscenio.spacewizard.studios/v1/`) ao popular o PSD.
- `proscenio_export.jsx`: ler de volta o XMP/custom field; fallback pra 100 quando ausente.
- Aplicar mesmo padrão no porte UXP (10.3 export + 10.5 import).

**Arquivo:** `apps/photoshop/proscenio_export.jsx:54,100`; `apps/photoshop/proscenio_import.jsx` (no write site).

**Severity:** medium - quebra parity oracle. UXP exporter reproduz o mesmo bug por enquanto (default 100); só foi descoberto agora porque esse roundtrip rodou pela primeira vez. Bloquearia a retirada da JSX sem fix porque importer roundtrip falha em escala.

### JSX exporter: `waist` size difere 1px entre Blender bbox e Photoshop layer.bounds

**Repro:** Roundtrip doll oracle, diff em `waist`:

- Blender manifest: `size = [255, 173]`.
- JSX re-export: `size = [255, 172]`.

Layers vizinhos com PNG do mesmo render_layers source casam exato; só `waist` difere.

**Causa suspeita:** rounding diferente entre `Pillow.getbbox()` no exporter Python e `layer.bounds` no Photoshop após PNG ser placed. Pode ser pixel anti-aliased na borda inferior do `waist.png` que Photoshop conta como transparente e Pillow conta como visível (ou vice-versa).

**Fix proposto:**

- Investigar: abrir `render_layers/waist.png` em PS, conferir bbox visível direto na ferramenta de medida vs Pillow `getbbox()`.
- Decisão depende do achado: ajustar threshold de transparência num dos lados, ou aceitar como ruído sub-pixel e arredondar consistente (round-half-up em ambos).

**Arquivo:** `apps/photoshop/proscenio_export.jsx:269-295` (`exportLayerToFile` lê `layer.bounds`); cross-ref com `packages/fixtures/_shared/` ou onde o Blender computa size.

**Severity:** low - 1px de diferença num único asset, não bloqueia funcionalmente. Log + investigar quando 10.7 estiver perto.

---
