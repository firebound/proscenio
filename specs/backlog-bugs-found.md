# Bugs found during manual testing

Bugs reproducíveis encontrados durante manual smoke / feature tests
(manual-testing.md). Cada item cita reproducer + suspeita + arquivo
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

**Sintoma:** linha highlight no panel (active_bone_index muda), mas viewport não reflete - nenhum bone selecionado, nenhum active bone na armatura. Comportamento esperado pela manual-testing.md item 1.8.2: click row → seleciona bone correspondente em pose mode.

**Causa:** `apps/blender/properties/scene_props.py:54` define `active_bone_index` como `IntProperty` puro, sem `update=` callback. `apps/blender/panels/skeleton.py:73-80` usa `template_list` apontando pra esse PG, que só armazena o índice; não há operator no row draw nem update hook que sincronize com `armature.data.bones.active` ou `armature.pose.bones[...].bone.select`.

**Comparação:** Outliner panel resolve o mesmo problema com operator dedicado (`proscenio.select_outliner_object`) clicado via row draw_item. Skeleton panel não tem equivalente.

**Fix proposto (opção A):** novo operator `proscenio.select_bone_by_index` chamado de dentro de `PROSCENIO_UL_bones.draw_item`. Operator entra em pose mode (se preciso), set `armature.data.bones.active` + `pose_bone.bone.select = True`.

**Fix proposto (opção B, mais simples):** adicionar `update=` callback ao `active_bone_index` que faz a sincronização. Risco: callback dispara em todos os redraws e pode causar feedback loop com modos não-pose.

**Arquivo:** `apps/blender/properties/scene_props.py:54-59`, `apps/blender/panels/skeleton.py:12-31`.

**Severity:** medium - panel oferece UX de selector de bone, mas não cumpre. Usuário precisa selecionar bone no viewport manualmente.

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

**Severity:** medium - não crash, mas operator inusável out-of-the-box sem setup explícito que não tá documentado nem na UI. Bloqueia 1.15 items 1 e 2 do manual-testing.

### Automesh Interactive (modal): ferramentas extend / cut quebradas

**Repro:** `examples/generated/automesh/automesh.blend` > select sprite plane > Mesh Generation > Automesh Interactive > Automesh (modal) > avança até o Stage 2 (extend / cut) > usa as ferramentas de extend e de cut.

**Sintoma:** as ferramentas não fazem nada OU geram muitos artefatos indesejados na malha (revisão manual 08-jun-2026). Stage 4 (interior points add / shift+click delete) parece funcionar; o problema é o Stage 2 extend / cut.

**Suspeita:** `apps/blender/operators/automesh/automesh_authoring.py` - o dispatch do pen tool no Stage 2 (EXTEND / CUT) ou a splice do outer contour. Os scenarios T1 / T6 de `manual-testing.md` 1.23 / 1.25 (Stage 2 extend / cut, cut overlay vermelho, snap / merge / loop) nunca foram validados em sessão - estão `[ ]`. Precisa repro com console aberto pra capturar traceback / inspecionar a malha resultante.

**Arquivo:** `apps/blender/operators/automesh/automesh_authoring.py` (Stage 2 EXTEND / CUT) + `core/bpy_helpers/automesh` (splice / triangulação).

**Severity:** medium-high - inviabiliza o autoring interativo de silhueta (o ponto principal do modal). Confirmar causa exata antes de fix.

---

## apps/photoshop

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
