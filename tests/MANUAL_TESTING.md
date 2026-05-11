# Manual testing checklist

Testes hands-on que não cabem em pytest / Blender headless / GUT.
Organizados por app + feature.

Atualizar status conforme rodar. Failures (`[!]`) viram issues / fixes em
PRs separados. Antes de mergear PR grande, marcar manual tests da branch
como `[x]` ou `[!]`.

Status legend:

- `[ ]` pendente
- `[~]` em andamento / parcial
- `[x]` validado
- `[!]` falhou -- abrir issue / fix

Recomendação: comece pelos smoke tests. Se quebrar lá, não adianta ir adiante.

---

## 0. Smoke tests críticos

Validam que addon carrega + workflow básico funciona.

- [x] **Addon load**: Edit > Preferences > Add-ons > "proscenio" check. Sem warnings de import.
- [x] **Addon reload**: Edit > Preferences > addon disable + enable. Após pycache clear + restart, registra limpo em cena fresh, doll.blend, doll_workbench.blend.
- [x] **Reload Scripts** (F3 > "Reload Scripts" ou Code editor): nenhuma exception no console.
- [x] **Operator dispatch**: Diagnostics panel > "Run Smoke Test" -> INFO bar mostra "Proscenio smoke test OK", console imprime mesma string.
- [x] **Properties registered**: abrir `examples/authored/doll/doll_workbench.blend`, selecionar mesh, ver "Proscenio" panel no Item tab da N-panel.
- [x] **Scene props**: Scene PG não espelha pra CPs (by design). Verificar via panel surface: Export panel mostra `pixels_per_unit` field + `last_export_path` text; Atlas panel mostra pack settings.
- [~] **PG hydration**: abrir um .blend antigo (legacy) com Custom Properties manuais (`proscenio_type=sprite_frame`) -- PG inicializa com mesmo valor. Deferred -- testar quando produzir cena from-scratch e validar populate.

---

## 1. Apps/Blender

Workbench file recomendado: `examples/authored/doll/doll_workbench.blend` (clone do baseline). NÃO mexer no `doll.blend` canônico.

### 1.1 Active Sprite panel

- [x] sprite_type dropdown: polygon <-> sprite_frame muda body do panel
- [x] hframes/vframes/frame fields: edit -> Custom Property mirror atualiza
- [x] Region mode auto: hint label "computed from UV bounds at export"
- [x] Region mode manual: 4 floats (region_x/y/w/h) editáveis
- [!] "Snap to UV bounds" button (polygon, manual mode): preenche os 4 floats baseado em UV. **Bug**: edit mode crasha (`IndexError` em `uv_layer.data[li]`, faltam guards de poll/contexto). Object mode funciona se UVs forem válidas. (Doll baseline tem UVs degeneradas em (0,0) -- esperado para snap retornar bbox vazio nesse caso.)
- [x] "Reproject UV" button (polygon): reprojeta UV active layer. Caveats em BUGS_FOUND.md (perf da segunda call, V invertido em meshes 3D-ish).
- [x] material_isolated checkbox: salva no PG + CP

### 1.2 Sprite Frame preview shader

Em sprite_frame mesh com material image-textured (ex: `eye` em blink_eyes; `mouth` em mouth_drive. **Não testar em doll** -- meshes do doll são todas polygon, eyes incluídas):

- [x] "Setup Preview" button: quad em Material Preview mostra cell ativo do spritesheet (testado em blink_eyes com frame=2)
- [x] Mudar `obj.proscenio.frame` 0->1->2->3 manualmente: cell visível atualiza live
- [x] Animar `frame` via keyframes: scrub timeline cicla cells
- [x] "Remove Preview": quad volta a mostrar atlas inteiro
- [x] Re-Setup idempotente: clicar 2x não duplica nodes (verificado no shader graph: 1× node group "Proscenio Sprite Frame")
- [x] Solid shading mode: flat diffuse (slicer invisível, esperado)

### 1.3 Drive from bone

Active Sprite > Drive from bone box:

- [x] Picker `Armature` filtra só ARMATURE objects
- [x] Picker `Bone` dropdown lista bones do armature escolhido (vazio se nenhum)
- [x] Click "Drive from Bone" cria fcurve em `proscenio.<target_property>`
- [x] Bone rotation em pose mode: driver value muda live. PR #39 fixou os 3 bugs originais (LOCAL_SPACE / AUTO Quaternion / seed keyframes) + commit 8196e9d alinhou eixo default com Blender Front Ortho (ROT_Y, não ROT_Z). Verificado em mouth_drive_workbench.
- [x] Re-click "Drive from Bone" mesmo target: substitui driver, não duplica
- [x] F9 redo panel: trocar `target_property` re-wires driver
- [x] Custom expression `var * 0.5 + 0.3` em Region X: scroll continuous funciona. **Caveat:** trocar target via F9 não migra driver (adiciona outro), bug em BUGS_FOUND.md.

### 1.4 Active Slot panel

Workbench file: `examples/slot_swap/slot_swap.blend` (arm + slot Empty + club/sword attachments). `doll_slots.blend` foi retirado -- slot coverage agora em `slot_swap/` e `slot_cycle/`.

- [x] Selecionar slot Empty: "Active Slot" subpanel aparece (testado em slot_swap workbench)
- [x] Subpanel hide quando active object não é Empty + is_slot
- [x] Lista attachments com kind icon (polygon)
- [x] Default attachment marcado com SOLO_ON star, outro com SOLO_OFF
- [!] Click star vazia: vira default, **CP NÃO atualiza** (PG mirror não inclui slot fields). Bug em BUGS_FOUND.
- [x] "Add Selected Mesh" button: select mesh + slot empty, button adiciona ao slot

### 1.5 Slot creation flows

Em workbench limpo:

- [x] **Path A**: pose mode + bone selecionado -> "Create Slot" -> Empty `<bone>.slot` parent_type=BONE. Validado em slot_swap_workbench.
- [!] **Path B**: object mode + N meshes selecionadas -> "Create Slot" -> Empty wraps meshes. **Bug:** posição do slot fica errada quando seed mesh tem parent (mesh "pula" pra outro canto da cena ao virar attachment). Bug em BUGS_FOUND.md.
- [x] DnD mesh -> slot Empty no outliner reparenteia (Blender 5.1 suporta DnD reparent no outliner -- confirmado via docs oficiais). Também funciona via `Ctrl+P` ou shift modifier. Attachment aparece no panel após reparent.

### 1.6 Slot validation

Em slot_swap_workbench / scenario custom (doll_slots retired):

- [ ] Slot sem children: erro vermelho "no MESH children" (não testado explicitamente nesta sessão)
- [!] slot_default fantasma (set CP `proscenio_slot_default = "fake"`): erro "default 'fake' is not a child". **Bug:** validator lê PG only, edits direto na CP não são detectados. Bug em BUGS_FOUND.md.
- [ ] Divergent bone: slot Empty parent_bone=`forearm.L`, child mesh parent_bone=`forearm.R`: warning amarelo (não testado)
- [!] Bone-transform keys em slot child (`club` com `club.action` keyframando location): warning "carries bone-transform keyframes". **Bug:** validator não dispara warning -- `club.action` com keys de location passou silencioso. Bug em BUGS_FOUND.md.
- [!] Slot attachments flaggadas como "no parent bone" (false positive). **Bug:** validator dispara em attachment que tá legitimamente parented ao slot Empty (que por sua vez é parented ao bone). Bug em BUGS_FOUND.md.
- [~] Validate button -> resultados aparecem no Validation subpanel. **UI feedback:** botão Validate mora no Export panel, não no Validation panel -- confunde usuário. Feedback em UI_FEEDBACK.md.
- [~] Click issue na Validation panel -> seleciona objeto offending. Funciona via outliner, mas viewport não reflete se objeto está com `hide_viewport=True` (caso comum em slot non-default attachments). Feedback em UI_FEEDBACK.md.

### 1.7 Outliner panel

- [x] Lista todos sprite meshes + armatures + slot Empties + attachments (não bones, não Empties não-slot, não cameras/lights). Label `<name> @ <parent_bone>` só aparece com `parent_type=BONE` rígido -- doll usa skinning então label só mostra nome. Coverage gap registrado em `specs/007-testing-fixtures/TODO.md` (falta fixture `rigid_prop/`).
- [!] Filtro substring funciona. **Bug:** campo nativo do UIList (rodapé `▼`) não filtra -- só o campo do topo (ícone VIEWZOOM, `scene_props.outliner_filter`) funciona. `filter_items` ignora `self.filter_name`. Bug em BUGS_FOUND.md.
- [x] Favorites toggle (star) persiste no save (`is_outliner_favorite` é Object PG)
- [x] "Show favorites only" filtra corretamente (botão SOLO_ON ao lado do search no header)
- [x] Click linha -> seleciona no scene + active object troca (`proscenio.select_outliner_object` operator dispara no row click)
- [x] Categorização visual via ícones distintos: `LINK_BLEND` (slot), `OBJECT_DATAMODE` (attachment indent `-> name`), `MESH_DATA` (sprite -- polygon e sprite_frame com mesmo ícone, sem diferenciação interna), `ARMATURE_DATA` (armature, prefixo `[arm]`). Validado criando slot em workbench dedicado.

### 1.8 Skeleton panel

- [x] Lista bones do active armature (header `Armature 'doll.rig' -- N bone(s)` + UIList com nome / parent / length). Pega `armatures[0]` da scene (não active object); cena com >1 armature mostra warning.
- [!] Click bone -> seleciona em pose mode. **Gap:** `active_bone_index` é IntProperty puro sem `update=` callback; row click só atualiza index do PG, não sincroniza viewport selection. Bug em BUGS_FOUND.md.
- [x] Active bone index sticky entre saves (Scene PG persiste no .blend)

### 1.9 Animation panel

- [x] Lista actions do .blend (`bpy.data.actions`, com frame range), footer com count total
- [~] Active action sticky entre saves (funciona, mas utilidade nula até o selector drive algo -- ver gap abaixo)
- [!] Scrub timeline com action selected funciona. **Gap:** row click só atualiza `active_action_index`; não atribui action ao `armature.animation_data.action`. Scrub mostra rest pose ou action que já estava assignada via Dope Sheet. Bug em BUGS_FOUND.md. Feedback do usuário: "o swap de animação pelo seletor do proscenio seria bem útil".

### 1.10 Atlas panel

Workbench file: `examples/atlas_pack/atlas_pack.blend` (9 sprites 3x3, cada com PNG próprio 32x32 + material próprio + cor + dígito 1..9 pra identificar visualmente onde cada um caiu no atlas packed).

- [x] "Pack Atlas" button: gera `atlas_pack_workbench.atlas.png` (256x256, 9 sprites empacotados) + `atlas_pack_workbench.atlas.json` (schema format_version=2: atlas_w/h, padding, placements dict com x/y/w/h + source_w/h + slice_x/y/w/h por sprite). INFO bar: "packed 9 sprite(s) into 256x256 px atlas".
- [x] Pack idempotente: re-roda sem duplicar. JSON segunda run idêntico em atlas_w/h, padding, placements (cada sprite na mesma x,y).
- [~] Pack após Apply: usa atlas existente como source, idempotente. Não testado isoladamente; coberto indiretamente pelos items 8/9/10 (várias execuções de Pack após estado pós-Apply mexendo em padding/max_size/pot). Pack opera sem crash mas semântica do "atlas existente como source" merece teste dedicado quando shape pipeline evoluir.
- [x] "Apply Packed Atlas": UVs de cada sprite reescritas pra apontar pra sua sub-região no atlas; sprites linkados a `Proscenio.PackedAtlas` material; viewport ainda mostra dígito correto em cada sprite. **Pré-condição obrigatória:** Object Mode -- em Edit Mode silenciosamente skip todos os sprites (bug em BUGS_FOUND.md). Operator deveria ter poll() guard.
- [x] material_isolated=True: sprite_5 manteve `sprite_5.mat` (não foi trocado pelo shared); Image Texture do material trocou pra atlas packed; outros 8 sprites linkados a `Proscenio.PackedAtlas` shared (8 users). Confirmado via Material Slots dropdown: shared mostra 8 users, sprite_5.mat sem prefixo "0" (ainda em uso), outros sprite_N.mat com prefixo "0" (órfãos).
- [x] "Unpack": restaura UVs originais (consome + remove layer `<active>.pre_pack`) + cada sprite_N volta pra `sprite_N.mat`. `Proscenio.PackedAtlas` fica orphan (0 users) -- esperado. `proscenio_pre_pack` CP deletada.
- [!] Ciclo Pack > Apply > Pack > Apply: estado **NÃO idempotente**. Cada Apply consecutivo remapeia UVs como se estivessem em source-image space, mas após primeiro Apply elas já estão em atlas space -> shrink iterativo (UVs convergem pra ponto único no slot). Pack em si é idempotente (item 2); a quebra é no Apply re-clickado. Bug em BUGS_FOUND.md.
- [x] pack_padding_px setting respeitado. pack_padding_px=8 -> atlas.json `"padding": 8`, stride entre sprites na mesma coluna passa de 36 (padding=2) pra 48 px (padding=8). Gap visível no atlas.png.
- [x] pack_max_size: cap=64 com 9 sprites 32x32 -- pack falha graciosamente. ERROR bar: `Proscenio: pack failed -- 9 sprite(s) do not fit in 64x64 px atlas.` Sem crash. Atlas files do item 8 ficam intactos.
- [x] pack_pot=True: atlas resultante 256x256 (POT, 2^8). Coincide com tamanho pot=False porque packer não shrinka start_size pra fit tight -- 9 sprites caberiam em ~96x96, mas start_size default é 256. POT semântica preservada (atlas é POT); para ver round-up real precisaria de mais sprites empurrando além de start_size.

### 1.11 Validation panel

- [x] "Validate" button: roda `validation.validate_export(scene)`, popula `validation_results`, seta `validation_ran=True`. Botão mora no Export panel (já loggado em UI_FEEDBACK como reposicionar pra Validation panel).
- [x] Errors em vermelho (`row.alert = True`), warnings em cinza (icon INFO). Confirmado: vertex_group inválido em sprite_1 -> row vermelho; sprite_2 unparented -> row cinza com icon INFO.
- [x] Click issue: row click invoca `proscenio.select_issue_object` -> sprite offending vira active object no 3D viewport. Validado em ambos error e warning rows.
- [x] Validation results sticky entre saves (`validation_ran` + `validation_results` são Scene PG, persistem no .blend).
- [x] Export auto-roda validação inline ([export_flow.py:42-53](../apps/blender/operators/export_flow.py#L42-L53) `_gate_on_validation`). Bloqueia **apenas se houver issues com severity=="error"**; warnings passam. `validation_ran` flag é estado de UI (mostra "run Validate" vs results), **não é gate**. Item original ("flag bloqueia export até primeira run") era descrição errada; corrigido para refletir código real.

### 1.12 Export panel

- [x] "Export Godot" button: ExportHelper file picker abre, sidebar tem field `Pixels per unit`. Path escolhido -> .proscenio escrito. INFO bar `wrote <name>.proscenio`.
- [x] Last export path sticky em `Scene.proscenio.last_export_path` (campo visível no panel; persiste no .blend após save/reload).
- [x] "Re-export" usa sticky path sem prompt (botão visível só se `last_export_path` non-empty; sem dialog; INFO bar `re-exported -> <name>.proscenio`).
- [x] Pixels per unit setting respeitado. PPU=50 no Scene PG -> .proscenio header `"pixels_per_unit": 50.0` + polygon vertices em 16x16 px (vs 32x32 px com PPU=100; mesh 0.32m * 50 = 16 px). Re-export usa Scene PG `props.pixels_per_unit`. **Caveat código:** `PROSCENIO_OT_export_godot` tem operator-local `pixels_per_unit` FloatProperty (default 100) que sobrescreve no file dialog -- divergência potencial vs Scene PG. Worth investigar se export do file dialog também respeita Scene PG ou só Re-export.
- [x] Validation gate bloqueia export se errors críticos não resolvidos. Confirmado: vertex_group `bogus` em sprite_1 -> Export blocked com ERROR bar exata `Proscenio: export blocked by 1 validation error(s) -- see Validation panel.` Operator retorna `{CANCELLED}`, file dialog não abre. Mesmo gate vale pra Re-export.

### 1.13 Help + status badges

- [x] Cada subpanel mostra ícone status + `?` alinhados à direita do header. Active Sprite/Skeleton/Animation/Atlas/Validation/Export = CHECKMARK; Outliner = TOOL_SETTINGS.
- [x] Hover ícone -> tooltip per-band. CHECKMARK -> `Exports to .proscenio...`; TOOL_SETTINGS -> `Authoring shortcut. Lives entirely on the Blender side...`.
- [x] Click ícone status -> abre popup `status_legend` (title "Status badges" + 5 sections + see-also STATUS.md).
- [x] Click `?` em cada subpanel -> abre help popup topic-specific (topic id == feature_id).
- [x] Pipeline overview popup (root `?`) renderiza topic `pipeline_overview` com sections + see-also.
- [x] Drive-from-bone help topic conteúdo confere (sections What it does / How to use it presentes).
- [~] See-also links resolvem em paths reais. **Paths existem on disk** (STATUS.md, specs/000-initial-plan, etc verificados). **Mas:** rendered como `layout.label` puro (`help_dispatch.py:88-89`), não clickable. Visualmente parecem links + ícone URL no header da seção, induz expectativa de click. UX gap loggado em UI_FEEDBACK.md.
- [x] `slot_system` topic abre via Active Slot `?` button. Confirmado em slot_swap_workbench (slot Empty chamado `weapon`).
- [!] `sprite_frame_preview` topic abre via Active Sprite `?` button (sprite_frame mode). **Bug:** topic existe em `help_topics.py:432` + `feature_status.py:115` mas nenhuma sub-box do panel renderiza `?` button pra ele. `_draw_sprite_frame.py:26` mostra só label puro `box.label(text="Sprite frame", icon="IMAGE_DATA")` -- orphan help topic. Bug em BUGS_FOUND.md.

### 1.14 Quick Armature

- [~] "Quick Armature" operator: 3D viewport, click-drag head -> tail desenha bone. Funciona mas com bug crítico: bones sempre criados no plano Z=0 (horizontais) mesmo em Front Ortho -- inviabiliza uso pro workflow Proscenio XZ. Bug em BUGS_FOUND.md.
- [x] Bone aparece em armature `Proscenio.QuickRig` (criada no invoke se não existir). Confirmado: qbone.000..004 listados.
- [x] Multiple drags em sequência: cria múltiplos bones na mesma QuickRig (sem parent automático).
- [x] Shift hold no PRESS: bone novo parented ao anterior (sem connect). Confirmado: relations.parent setado.
- [x] ESC ou RIGHTMOUSE: sai do modal. Confirmado funcional (apesar de UX confusa -- não tem feedback visual claro do modal).
- [!] Cancel sem nenhum bone criado: armature vazio NÃO removido. Operator `_finish` (quick_armature.py:141) só limpa status text + `_drag_head`; deixa `Proscenio.QuickRig` orphan na cena com zero bones. Polui workspace a cada cancel acidental. Checklist espera cleanup que não existe.
- [x] Drag muito curto (< 1e-4): skip funciona. INFO bar `bone too short, skipped` reportado várias vezes durante a sessão.

**Sessão 1.14 (10-mai-2026):** vários problemas de UX impedem teste cabal. Bug do plano Z=0 + falta de preview + falta de feedback visual modal + sem control de connect/disconnect parent durante o drag. Refator grande necessário antes do operator virar útil. Caveats e sugestões loggados em UI_FEEDBACK.md "Quick Armature operator" + "Skeleton panel". Usuário escolheu **skipar tests restantes** e mover pra próxima seção. Voltar quando refator estiver feita.

### 1.15 Pose library

- [!] "Save Pose to Library": com armature em pose mode, pose name -> action criada. **Falhou:** ERROR bar `Proscenio: pose library refused: Error: Unexpected library type. Failed to create pose asset`. Blender 4.x+ requer asset library writable configurada em Preferences > File Paths > Asset Libraries; Proscenio wrapper só propaga erro sem orientar usuário. Bug em BUGS_FOUND.md.
- [ ] Action salva apenas keyframes do current pose. **Bloqueado pelo item 1** -- impossível inspecionar action que nunca foi criada.
- [x] "Bake Current Pose": atual pose vira keyframe no frame_current. Confirmado: `baked pose at frame 16 for 65 bone(s)` -- todos os 65 bones do doll.rig keyframados em location/rotation_quaternion/rotation_euler/scale. Não é "@ frame 1" como checklist diz; é o frame_current da timeline (mais útil). Texto da checklist poderia ser ajustado.

### 1.16 Auxiliares

- [ ] "Create Ortho Camera": camera Top + ortho positioned, scene ready pra render
- [ ] "Toggle IK Chain": pose bone selected -> IK constraint added; re-toggle remove
- [ ] "Reproject Sprite UV": reprojeta UV do sprite ativo

### 1.17 Photoshop import

- [ ] "Import Photoshop Manifest" operator: file picker abre
- [ ] `examples/authored/doll/01_to_photoshop/doll.photoshop_manifest.json`: stamp polygon + sprite_frame meshes corretamente
- [ ] `examples/simple_psd/simple_psd.photoshop_manifest.json`: stamp simples funciona
- [ ] Imported scene tem stub armature root + meshes parented
- [ ] PSD layer names viram object names (sem colisão)

### 1.18 Writer (export -- via UI ou headless)

- [ ] `doll.blend` -> `.proscenio`: sem warnings (exceto bone weights de meshes sem matching bone)
- [ ] `doll_slots.blend` -> `.proscenio`: contém `slots[]` + `brow_raise` animation com `slot_attachment` tracks
- [ ] Re-export bytes idênticos (determinístico, sorted)
- [ ] Slot sem bone parent: campo `bone` omitted no JSON
- [ ] hide_viewport / hide_render não filtram meshes (esperado -- writer ignora)
- [ ] Atlas auto-discovery: encontra `<blend_stem>.atlas.png` próximo ao .blend

---

## 2. Apps/Godot

### 2.1 Plugin core

- [ ] Plugin enables limpo no Project Settings > Plugins
- [ ] EditorImportPlugin reconhece `.proscenio` files (re-import seta no FileSystem)
- [ ] Re-import preserva customizações no wrapper scene

### 2.2 Importer

- [ ] `doll.proscenio` -> `doll.scn` com Skeleton2D + Polygon2D children
- [ ] `doll_slots.proscenio` -> Slots viram Node2D parent + visible-toggled children
- [ ] sprite_frame meshes -> Sprite2D com hframes/vframes
- [ ] polygon meshes -> Polygon2D com UV + vertex weights
- [ ] Animations -> AnimationPlayer com bone tracks (position/rotation/scale)
- [ ] slot_attachment tracks -> visible toggle keyframes constant interpolation
- [ ] Atlas auto-discovery: `atlas.png` next to `.proscenio` carregado como CompressedTexture2D

### 2.3 Wrapper scene pattern

- [ ] Instance `doll.scn` em wrapper `Doll.tscn`, attach script -> playback OK
- [ ] Re-import `.proscenio` não sobrescreve wrapper customizations
- [ ] Wrapper script acessa AnimationPlayer + dispara animações

### 2.4 Plugin uninstall test (regra "no GDExtension")

- [ ] Generate `.scn` com plugin enabled
- [ ] Disable plugin no Project Settings
- [ ] Reload project -> abrir scene -> roda sem erros (Skeleton2D/Polygon2D são core nodes)

---

## 3. Apps/Photoshop

### 3.1 UXP plugin

Quando UXP migration shippa:

- [ ] PSD layers visíveis -> "Export Manifest" button -> JSON file
- [ ] Manifest -> "Import" button -> reconstrói layer structure no PSD novo
- [ ] Roundtrip: export -> import = bytes equivalentes (modulo metadata flags)

### 3.2 JSX legacy (ainda funcional, será deprecated)

- [ ] `apps/photoshop/proscenio_export.jsx` em File > Scripts > Browse: abre dialog
- [ ] doll.psd export: gera manifest JSON + render_layers PNGs
- [ ] `apps/photoshop/proscenio_import.jsx`: importa manifest, recria layers

---

## 4. Cross-app roundtrip

### 4.1 doll full pipeline

- [ ] `doll.blend` -> render_layers PNG (via `scripts/fixtures/doll/render_layers.py`)
- [ ] PNGs -> Photoshop (manual ou via JSX import) -> .psd
- [ ] .psd -> JSX export -> manifest mirror
- [ ] manifest -> Blender via Import Photoshop Manifest -> meshes recriados
- [ ] Output Blender ~= input Blender (modulo round-trip drift documentada)

### 4.2 doll -> Godot

- [ ] `doll.blend` -> Export Godot -> `doll.proscenio`
- [ ] `doll.proscenio` -> Godot import -> `doll.scn`
- [ ] Wrapper scene plays -> doll renderiza no editor + runtime
- [ ] `doll_slots.blend` -> mesmo pipeline -> brow_raise animation visível

### 4.3 simple_psd

- [ ] `simple_psd.psd` -> JSX export -> manifest
- [ ] manifest -> Blender import -> stamped scene
- [ ] export Blender -> Godot -> playback

---

## 5. Pré-shipping (futuro, antes de v0.2.0)

- [ ] CI matrix expansion (Blender 4.2 LTS + Godot 4.3) -- backlog
- [ ] Reload addon após cada commit que mexe em registration -- verificar register / unregister simétrico
- [ ] Performance: doll.blend export tempo, atlas pack tempo com 50+ sprites

---

## Notes

- Atualizar este arquivo após cada smoke session.
- Failures `[!]` viram issues a corrigir em PRs separados.
- Antes de mergear PR grande, marcar manual tests da branch como `[x]` ou `[!]`.
- Use `examples/authored/doll/doll_workbench.blend` (Save As do baseline) pra mexer livremente. NÃO editar `doll.blend` canônico.
