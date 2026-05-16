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
- `[!]` falhou - abrir issue / fix

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
- [~] **PG hydration**: abrir um .blend antigo (legacy) com Custom Properties manuais (`proscenio_type=sprite_frame`) - PG inicializa com mesmo valor. Deferred - testar quando produzir cena from-scratch e validar populate.

---

## 1. Apps/Blender

Workbench file recomendado: `examples/authored/doll/doll_workbench.blend` (clone do baseline). NÃO mexer no `doll.blend` canônico.

### 1.1 Active Sprite panel

- [x] sprite_type dropdown: polygon <-> sprite_frame muda body do panel
- [x] hframes/vframes/frame fields: edit -> Custom Property mirror atualiza
- [x] Region mode auto: hint label "computed from UV bounds at export"
- [x] Region mode manual: 4 floats (region_x/y/w/h) editáveis
- [!] "Snap to UV bounds" button (polygon, manual mode): preenche os 4 floats baseado em UV. **Bug**: edit mode crasha (`IndexError` em `uv_layer.data[li]`, faltam guards de poll/contexto). Object mode funciona se UVs forem válidas. (Doll baseline tem UVs degeneradas em (0,0) - esperado para snap retornar bbox vazio nesse caso.)
- [x] "Reproject UV" button (polygon): reprojeta UV active layer. Caveats em BUGS_FOUND.md (perf da segunda call, V invertido em meshes 3D-ish).
- [x] material_isolated checkbox: salva no PG + CP

### 1.2 Sprite Frame preview shader

Em sprite_frame mesh com material image-textured (ex: `eye` em blink_eyes; `mouth` em mouth_drive. **Não testar em doll** - meshes do doll são todas polygon, eyes incluídas):

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

Workbench file: `examples/generated/slot_swap/slot_swap.blend` (arm + slot Empty + club/sword attachments). `doll_slots.blend` foi retirado - slot coverage agora em `slot_swap/` e `slot_cycle/`.

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
- [x] DnD mesh -> slot Empty no outliner reparenteia (Blender 5.1 suporta DnD reparent no outliner - confirmado via docs oficiais). Também funciona via `Ctrl+P` ou shift modifier. Attachment aparece no panel após reparent.

### 1.6 Slot validation

Em slot_swap_workbench / scenario custom (doll_slots retired):

- [ ] Slot sem children: erro vermelho "no MESH children" (não testado explicitamente nesta sessão)
- [!] slot_default fantasma (set CP `proscenio_slot_default = "fake"`): erro "default 'fake' is not a child". **Bug:** validator lê PG only, edits direto na CP não são detectados. Bug em BUGS_FOUND.md.
- [ ] Divergent bone: slot Empty parent_bone=`forearm.L`, child mesh parent_bone=`forearm.R`: warning amarelo (não testado)
- [!] Bone-transform keys em slot child (`club` com `club.action` keyframando location): warning "carries bone-transform keyframes". **Bug:** validator não dispara warning - `club.action` com keys de location passou silencioso. Bug em BUGS_FOUND.md.
- [!] Slot attachments flaggadas como "no parent bone" (false positive). **Bug:** validator dispara em attachment que tá legitimamente parented ao slot Empty (que por sua vez é parented ao bone). Bug em BUGS_FOUND.md.
- [~] Validate button -> resultados aparecem no Validation subpanel. **UI feedback:** botão Validate mora no Export panel, não no Validation panel - confunde usuário. Feedback em UI_FEEDBACK.md.
- [~] Click issue na Validation panel -> seleciona objeto offending. Funciona via outliner, mas viewport não reflete se objeto está com `hide_viewport=True` (caso comum em slot non-default attachments). Feedback em UI_FEEDBACK.md.

### 1.7 Outliner panel

- [x] Lista todos sprite meshes + armatures + slot Empties + attachments (não bones, não Empties não-slot, não cameras/lights). Label `<name> @ <parent_bone>` só aparece com `parent_type=BONE` rígido - doll usa skinning então label só mostra nome. Coverage gap registrado em `specs/007-testing-fixtures/TODO.md` (falta fixture `rigid_prop/`).
- [!] Filtro substring funciona. **Bug:** campo nativo do UIList (rodapé `▼`) não filtra - só o campo do topo (ícone VIEWZOOM, `scene_props.outliner_filter`) funciona. `filter_items` ignora `self.filter_name`. Bug em BUGS_FOUND.md.
- [x] Favorites toggle (star) persiste no save (`is_outliner_favorite` é Object PG)
- [x] "Show favorites only" filtra corretamente (botão SOLO_ON ao lado do search no header)
- [x] Click linha -> seleciona no scene + active object troca (`proscenio.select_outliner_object` operator dispara no row click)
- [x] Categorização visual via ícones distintos: `LINK_BLEND` (slot), `OBJECT_DATAMODE` (attachment indent `-> name`), `MESH_DATA` (sprite - polygon e sprite_frame com mesmo ícone, sem diferenciação interna), `ARMATURE_DATA` (armature, prefixo `[arm]`). Validado criando slot em workbench dedicado.

### 1.8 Skeleton panel

- [x] Lista bones do active armature (header `Armature 'doll.rig' - N bone(s)` + UIList com nome / parent / length). Pega `armatures[0]` da scene (não active object); cena com >1 armature mostra warning.
- [!] Click bone -> seleciona em pose mode. **Gap:** `active_bone_index` é IntProperty puro sem `update=` callback; row click só atualiza index do PG, não sincroniza viewport selection. Bug em BUGS_FOUND.md.
- [x] Active bone index sticky entre saves (Scene PG persiste no .blend)

### 1.9 Animation panel

- [x] Lista actions do .blend (`bpy.data.actions`, com frame range), footer com count total
- [~] Active action sticky entre saves (funciona, mas utilidade nula até o selector drive algo - ver gap abaixo)
- [!] Scrub timeline com action selected funciona. **Gap:** row click só atualiza `active_action_index`; não atribui action ao `armature.animation_data.action`. Scrub mostra rest pose ou action que já estava assignada via Dope Sheet. Bug em BUGS_FOUND.md. Feedback do usuário: "o swap de animação pelo seletor do proscenio seria bem útil".

### 1.10 Atlas panel

Workbench file: `examples/generated/atlas_pack/atlas_pack.blend` (9 sprites 3x3, cada com PNG próprio 32x32 + material próprio + cor + dígito 1..9 pra identificar visualmente onde cada um caiu no atlas packed).

- [x] "Pack Atlas" button: gera `atlas_pack_workbench.atlas.png` (256x256, 9 sprites empacotados) + `atlas_pack_workbench.atlas.json` (schema format_version=2: atlas_w/h, padding, placements dict com x/y/w/h + source_w/h + slice_x/y/w/h por sprite). INFO bar: "packed 9 sprite(s) into 256x256 px atlas".
- [x] Pack idempotente: re-roda sem duplicar. JSON segunda run idêntico em atlas_w/h, padding, placements (cada sprite na mesma x,y).
- [~] Pack após Apply: usa atlas existente como source, idempotente. Não testado isoladamente; coberto indiretamente pelos items 8/9/10 (várias execuções de Pack após estado pós-Apply mexendo em padding/max_size/pot). Pack opera sem crash mas semântica do "atlas existente como source" merece teste dedicado quando shape pipeline evoluir.
- [x] "Apply Packed Atlas": UVs de cada sprite reescritas pra apontar pra sua sub-região no atlas; sprites linkados a `Proscenio.PackedAtlas` material; viewport ainda mostra dígito correto em cada sprite. **Pré-condição obrigatória:** Object Mode - em Edit Mode silenciosamente skip todos os sprites (bug em BUGS_FOUND.md). Operator deveria ter poll() guard.
- [x] material_isolated=True: sprite_5 manteve `sprite_5.mat` (não foi trocado pelo shared); Image Texture do material trocou pra atlas packed; outros 8 sprites linkados a `Proscenio.PackedAtlas` shared (8 users). Confirmado via Material Slots dropdown: shared mostra 8 users, sprite_5.mat sem prefixo "0" (ainda em uso), outros sprite_N.mat com prefixo "0" (órfãos).
- [x] "Unpack": restaura UVs originais (consome + remove layer `<active>.pre_pack`) + cada sprite_N volta pra `sprite_N.mat`. `Proscenio.PackedAtlas` fica orphan (0 users) - esperado. `proscenio_pre_pack` CP deletada.
- [!] Ciclo Pack > Apply > Pack > Apply: estado **NÃO idempotente**. Cada Apply consecutivo remapeia UVs como se estivessem em source-image space, mas após primeiro Apply elas já estão em atlas space -> shrink iterativo (UVs convergem pra ponto único no slot). Pack em si é idempotente (item 2); a quebra é no Apply re-clickado. Bug em BUGS_FOUND.md.
- [x] pack_padding_px setting respeitado. pack_padding_px=8 -> atlas.json `"padding": 8`, stride entre sprites na mesma coluna passa de 36 (padding=2) pra 48 px (padding=8). Gap visível no atlas.png.
- [x] pack_max_size: cap=64 com 9 sprites 32x32 - pack falha graciosamente. ERROR bar: `Proscenio: pack failed - 9 sprite(s) do not fit in 64x64 px atlas.` Sem crash. Atlas files do item 8 ficam intactos.
- [x] pack_pot=True: atlas resultante 256x256 (POT, 2^8). Coincide com tamanho pot=False porque packer não shrinka start_size pra fit tight - 9 sprites caberiam em ~96x96, mas start_size default é 256. POT semântica preservada (atlas é POT); para ver round-up real precisaria de mais sprites empurrando além de start_size.

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
- [x] Pixels per unit setting respeitado. PPU=50 no Scene PG -> .proscenio header `"pixels_per_unit": 50.0` + polygon vertices em 16x16 px (vs 32x32 px com PPU=100; mesh 0.32m * 50 = 16 px). Re-export usa Scene PG `props.pixels_per_unit`. **Caveat código:** `PROSCENIO_OT_export_godot` tem operator-local `pixels_per_unit` FloatProperty (default 100) que sobrescreve no file dialog - divergência potencial vs Scene PG. Worth investigar se export do file dialog também respeita Scene PG ou só Re-export.
- [x] Validation gate bloqueia export se errors críticos não resolvidos. Confirmado: vertex_group `bogus` em sprite_1 -> Export blocked com ERROR bar exata `Proscenio: export blocked by 1 validation error(s) - see Validation panel.` Operator retorna `{CANCELLED}`, file dialog não abre. Mesmo gate vale pra Re-export.

### 1.13 Help + status badges

- [x] Cada subpanel mostra ícone status + `?` alinhados à direita do header. Active Sprite/Skeleton/Animation/Atlas/Validation/Export = CHECKMARK; Outliner = TOOL_SETTINGS.
- [x] Hover ícone -> tooltip per-band. CHECKMARK -> `Exports to .proscenio...`; TOOL_SETTINGS -> `Authoring shortcut. Lives entirely on the Blender side...`.
- [x] Click ícone status -> abre popup `status_legend` (title "Status badges" + 5 sections + see-also STATUS.md).
- [x] Click `?` em cada subpanel -> abre help popup topic-specific (topic id == feature_id).
- [x] Pipeline overview popup (root `?`) renderiza topic `pipeline_overview` com sections + see-also.
- [x] Drive-from-bone help topic conteúdo confere (sections What it does / How to use it presentes).
- [~] See-also links resolvem em paths reais. **Paths existem on disk** (STATUS.md, specs/000-initial-plan, etc verificados). **Mas:** rendered como `layout.label` puro (`help_dispatch.py:88-89`), não clickable. Visualmente parecem links + ícone URL no header da seção, induz expectativa de click. UX gap loggado em UI_FEEDBACK.md.
- [x] `slot_system` topic abre via Active Slot `?` button. Confirmado em slot_swap_workbench (slot Empty chamado `weapon`).
- [!] `sprite_frame_preview` topic abre via Active Sprite `?` button (sprite_frame mode). **Bug:** topic existe em `help_topics.py:432` + `feature_status.py:115` mas nenhuma sub-box do panel renderiza `?` button pra ele. `_draw_sprite_frame.py:26` mostra só label puro `box.label(text="Sprite frame", icon="IMAGE_DATA")` - orphan help topic. Bug em BUGS_FOUND.md.

### 1.14 Quick Armature

- [~] "Quick Armature" operator: 3D viewport, click-drag head -> tail desenha bone. Funciona mas com bug crítico: bones sempre criados no plano Z=0 (horizontais) mesmo em Front Ortho - inviabiliza uso pro workflow Proscenio XZ. Bug em BUGS_FOUND.md.
- [x] Bone aparece em armature `Proscenio.QuickRig` (criada no invoke se não existir). Confirmado: qbone.000..004 listados.
- [x] Multiple drags em sequência: cria múltiplos bones na mesma QuickRig (sem parent automático).
- [x] Shift hold no PRESS: bone novo parented ao anterior (sem connect). Confirmado: relations.parent setado.
- [x] ESC ou RIGHTMOUSE: sai do modal. Confirmado funcional (apesar de UX confusa - não tem feedback visual claro do modal).
- [!] Cancel sem nenhum bone criado: armature vazio NÃO removido. Operator `_finish` (quick_armature.py:141) só limpa status text + `_drag_head`; deixa `Proscenio.QuickRig` orphan na cena com zero bones. Polui workspace a cada cancel acidental. Checklist espera cleanup que não existe.
- [x] Drag muito curto (< 1e-4): skip funciona. INFO bar `bone too short, skipped` reportado várias vezes durante a sessão.

**Sessão 1.14 (10-mai-2026):** vários problemas de UX impedem teste cabal. Bug do plano Z=0 + falta de preview + falta de feedback visual modal + sem control de connect/disconnect parent durante o drag. Refator grande necessário antes do operator virar útil. Caveats e sugestões loggados em UI_FEEDBACK.md "Quick Armature operator" + "Skeleton panel". Usuário escolheu **skipar tests restantes** e mover pra próxima seção. Voltar quando refator estiver feita.

#### 1.14 re-test pos-SPEC-012.1 (Wave 12.1 ship)

Branch `feat/spec-012.1-quick-armature-feedback`. Re-roda apenas o **smoke set** (itens que **nao** mudam no Wave 12.2 inversion D10 + axis lock D11 + grid snap D12 + panel D15). Full suite fica deferida pra pos-Wave-12.2 ship.

**Smoke set (Wave 12.1 estavel - sem retrabalho previsto):**

- [x] **T1 Auto-snap Front Ortho on invoke.** PASS. Snap dispara, INFO bar + status bar + cheatsheet bottom-center todos corretos. System Console `_log_view` mostra pre-snap PERSP + post-snap ORTHO com matriz Front identity.
- [x] **T2 View restore on exit (sem user-move).** PASS. View retornou exato (loc/rot/dist matching pre-snap snapshot). INFO bar `view restored to pre-snap` + `confirmed/cancelled`. Bug inicial (matrix tolerance demais estrita) fixado migrando comparison pra decomposed values (location + rotation Quaternion + distance + perspective) em `_view_pose_equal` com tolerance 1e-3.
- [x] **T2b View kept on exit (com user-move).** PASS. User rotaciona via middle-click; exit detecta diff (rotation > tolerance) -> view kept. INFO bar `view kept (user-moved during modal)`. Bug original (saltava pra angulo aleatorio) resolvido com decomposed comparison + restore via decomposed assign.
- [x] **T4 Preview line + anchor circle.** PASS. Linha laranja + circulo 12-segments aparecem durante drag, atualizam smooth. Bonus regression encontrado e corrigido: clicks fora do canvas (panel/header/toolbar) disparavam tentativas de bone -> filter `_event_in_invoke_region` agora compara `event.mouse_x/y` contra rect WINDOW region resolvido via `_find_window_region` + itera overlay regions e rejeita se cursor cair em qualquer um. Bonus QoL: cursor fora da canvas vira preview vermelho `(0.9, 0.25, 0.25, 0.85)` + cheatsheet ganha 3a linha "cursor outside canvas - move back to author bones" + tooltip `outside canvas` perto do cursor (POST_PIXEL handler).
- [x] **T8 Empty QuickRig sweep on cancel.** PASS. Esc imediato sem bones não deixa orphan no Outliner.
- [x] **T9 Sweep só se operator criou.** PASS. Re-invocar com QuickRig com bones de sessão anterior + Esc imediato preserva o rig (sweep só age em rig criado nesta sessão via `_created_armature_this_session` flag).
- [x] **T-Enter confirm.** PASS. Enter + Numpad Enter ambos disparam exit com `confirmed`. INFO bar reporta count correto.
- [x] **T-Selection restore.** PASS. Active object pre-invoke restaurado pos-exit (selection set inteira via snapshot/restore em `_snapshot_selection`/`_restore_selection`). `Numpad .` (frame selected) zoom no mesh original, NAO no QuickRig.

**Drive-by bugs descobertos + corrigidos durante sessão:**

- PEP 563 quebra `bpy.props` registration em Blender 5.1 (`from __future__ import annotations` deixa annotation como string, metaclass `_RNAMeta` falha `isinstance(value, _PropertyDeferred)` check). Fix: removido `from __future__ import annotations` de `quick_armature.py`. Codebase-wide latente loggado em `tests/BUGS_FOUND.md` + auditoria pendente em `specs/012-quick-armature-ux/TODO.md` Wave 12.2.
- `view_matrix` 4x4 acumula float drift entre mode toggles -> falsos positivos em comparison. Fix: comparar via decomposed values (location/rotation/distance) em vez do matrix raw. Restore via decomposed assign também.
- `context.region` em modal handler congela em invoke; quando invocado via N-panel button aponta UI sidebar. Fix: snapshot WINDOW region via `_find_window_region(context.area)` + filter via `event.mouse_x/y` contra rect.
- WINDOW region rect cobre área inteira do viewport (panels overlay são sobrepostos). Filtering apenas pelo WINDOW rect deixava clicks em panel passar. Fix: itera todas regions da área; rejeita se cursor cair em qualquer overlay (UI/TOOLS/HEADER/ASSET_SHELF).
- Double-invoke (user clica botao Quick Armature 2x sem sair do primeiro modal) empilhava handlers. Fix: invoke detecta handles existentes + sweep antes de re-init.
- `_log_view` pre-snap + post-snap + exit (before/after restore decision) printados pro System Console permitiram debug rapido das comparison e restore paths.

**Smoke deferidos (mudam comportamento no Wave 12.2 - testar apos ship 12.2):**

- T3 Opt-out F3 (`lock_to_front_ortho`) - vai ganhar UI no painel (D15).
- T5 Cheatsheet texto - layout muda de 2 -> 3 linhas + novos chords (D11, D12, D14).
- T6 Bone creation default - inverte (D10: LMB sozinho = chain, antes = unparented root).
- T7 Shift chain - inverte (D10: Shift = new root, antes = chain).
- T9 Sweep só se operator criou (corner case) - logic igual mas retesta com chord vocab novo.
- T10 Reload scripts safety - reteste apos chord vocab + panel mudancas.
- T11 Esc com bones criados - logic igual mas confirma INFO bar message com chord vocab final.
- Axis lock (D11) X/Z toggle + linha colorida no preview.
- Grid snap (D12) Ctrl held + alinhamento por increment configuravel.
- In-modal undo/redo (D7) Ctrl+Z / Ctrl+Shift+Z.
- Naming prefix (D2) com Scene PG override + F3 redo override.
- Panel "Quick Armature defaults" sub-box (D15) - lock_to_front_ortho checkbox, prefix, default_chain, snap_increment.

**Trigger pra re-test full suite:** Wave 12.2 PR merged em `main`. Re-rodar full T1-T11 + items deferidos acima.

#### 1.14 re-test pos-SPEC-012.2 (Wave 12.2 ship + iterative refinement)

Branch `feat/spec-012.1-quick-armature-feedback` (mesmo branch carregou Wave 12.1 + 12.2 + 9 refinement commits via PR #50). Status após rounds iterativos de feedback do user:

**Wave 12.2 features (todos confirmados em smoke iterativo):**

- [x] **T-ChordInvert (D10).** PASS. LMB sem modifier chains connected; Shift+LMB = unparented; Alt+LMB = parented disconnected. Cheatsheet + status bar atualizam quando `default_chain` toggla.
- [x] **T-AxisLock (D11).** PASS. X / Z toggle axis lock; press 2x clears. Linha colorida vermelha (X) ou azul (Z) renderiza através do head antes do PRESS.
- [x] **T-GridSnap (D12).** PASS. Ctrl held arredonda cursor X/Z pro `snap_increment` configurado no Scene PG. Y preservado (picture plane).
- [x] **T-UndoRedo (D7).** PASS. Ctrl+Z dentro do modal remove ultimo bone; Ctrl+Shift+Z replays. New PRESS clears redo stack.
- [x] **T-NamingPrefix (D2).** PASS. PG `name_prefix` aplicado nos auto-named bones; sanitize whitespace.
- [x] **T-PanelSubbox (D15).** PASS. Skeleton subpanel renderiza sub-box "Quick Armature defaults" com 4 fields. Valores persistem no .blend.
- [x] **T-DashedDisconnected.** PASS. Alt+drag mostra linha tracejada amarela do parent.tail ao novo head.
- [x] **T-StatusBarIcons + ViewportHeader.** PASS. Status bar bottom-left + viewport header top renderizam chord vocabulary com ícones nativos Blender (`MOUSE_LMB_DRAG`, `EVENT_SHIFT/ALT/CTRL/X/Z/RETURN/ESC`).
- [x] **T-ActiveArmaturePicker (Opção 3 hybrid).** PASS. Picker no topo da Skeleton subpanel; explicit pointer é fonte única de verdade no operator-time; auto-populate via `load_post` + `deferred_hydrate` handler quando scene tem armature única.
- [x] **T-AutoPromoteQuickRig.** PASS. Quick Armature cria QuickRig + auto-promove pointer pro picker.
- [x] **T-StaleClearOnDelete.** PASS. `on_depsgraph_update` handler limpa pointer quando armature deletada + tag VIEW_3D pra redraw imediato.

**Refinement commits (iterative feedback do user):**

- `16c7995` chord refinement (Blender nomenclatura: connected/unparented/disconnected) + Alt chord + parent.tail anchor + color-coded preview + target armature
- `254d03f` dashed preview line + statusbar icons + active armature pointer
- `69aff3d` single hint location + viewport header icons + picker auto-fill + drop POST_PIXEL cheatsheet
- `43b4d36` drop draw-time picker auto-fill (ID write crash) + register hint convention em blender-dev.md
- `a4f0eec` picker é fonte única de verdade (drop heuristics no resolver, manter só no handler) + INFO box + `proscenio.set_active_armature` operator
- `7d5a099` vertical armature buttons + stale picker auto-clear via depsgraph handler
- `9eb5a52` respect Blender auto-rename (`arm_obj.name` em vez de literal pra evitar shadow por orphan)
- `ff12680` defensive try/except no `on_depsgraph_update` + crash gizmo log em BUGS_FOUND

**Drive-by bugs descobertos + corrigidos durante Wave 12.2 sessão:**

- `_target_armature_name` literal vs Blender auto-rename `.001` quando data block orphan existia. Fix: storage `arm_obj.name`.
- Picker draw-time mutation crashed com `AttributeError: Writing to ID classes in this context is not allowed`. Fix: drop draw-time write; handler `auto_populate_active_armature` no `load_post` + `deferred_hydrate` cobre initial fill; mutação explícita via operator pra deletion ou button.
- Stale picker apos delete da armature. Fix: novo `on_depsgraph_update` handler limpa pointer + tag_redraw.

**Crash isolado (1x) durante smoke:** Blender 5.1.1 NULL write em `gizmo_button2d_draw` após `view3d.snap_cursor_to_center`. Stack trace 100% Blender internals + AMD GPU driver loaded. User identificou como driver issue pós-restart. Defensive `try/except` adicionado no `on_depsgraph_update` mesmo assim. Logged in `tests/BUGS_FOUND.md` como suspeito upstream/driver, severity low, trigger pra escalar: 2x+ repro.

**Status final Wave 12.2:** todas features locked do STUDY D1-D15 implementadas. PR #50 ready pra review/merge depois de full smoke pos-driver-restart.

### 1.15 Pose library

- [!] "Save Pose to Library": com armature em pose mode, pose name -> action criada. **Falhou:** ERROR bar `Proscenio: pose library refused: Error: Unexpected library type. Failed to create pose asset`. Blender 4.x+ requer asset library writable configurada em Preferences > File Paths > Asset Libraries; Proscenio wrapper só propaga erro sem orientar usuário. Bug em BUGS_FOUND.md.
- [ ] Action salva apenas keyframes do current pose. **Bloqueado pelo item 1** - impossível inspecionar action que nunca foi criada.
- [x] "Bake Current Pose": atual pose vira keyframe no frame_current. Confirmado: `baked pose at frame 16 for 65 bone(s)` - todos os 65 bones do doll.rig keyframados em location/rotation_quaternion/rotation_euler/scale. Não é "@ frame 1" como checklist diz; é o frame_current da timeline (mais útil). Texto da checklist poderia ser ajustado.

### 1.16 Auxiliares

- [x] "Create Ortho Camera": cria `Proscenio.PreviewCam` em (0, -10, 0) com rotação (π/2, 0, 0), type ORTHO, ortho_scale=19.2 (= max(1920,1080)/PPU=100). Setada como scene.camera. Re-click "updated" (sem duplicar). Confirmado via headless inspect.
- [x] "Toggle IK Chain": add IK constraint "Proscenio IK" com chain_count=2, sem target (target wiring manual). Re-toggle remove a constraint. INFO bar reporta `added IK to '<bone>'` e `removed IK from '<bone>'` corretamente. Confirmado em hand.L do doll.rig. Workflow gap (auto-bake action antes do export) loggado em UI_FEEDBACK.md.
- [~] "Reproject Sprite UV": reprojeta UVs via Smart UV Project. Funciona (INFO bar `reprojected UVs on 'sprite_1'`), mas UV resultante fica rotacionada 90° + flipada horizontalmente. Confirmado em atlas_pack sprite_1: precisou `R -90 S X -1` no UV editor pra voltar ao layout original. Bug atualizado em BUGS_FOUND.md (mesma família do já reportado V invertido + perf 2ª call).

### 1.17 Photoshop import

- [x] "Import Photoshop Manifest" operator: ImportHelper file picker abre, filter `.json`, sidebar com `Placement` (default "Landed") + `Root Bone Name` (default "root").
- [x] `examples/authored/doll/00_blender_base/doll_base.photoshop_manifest.json` E `02_photoshop_setup/export/doll_tagged.photoshop_exported.json` (PS-roundtrip) ambos stamp OK - INFO bar `Proscenio: stamped 22 mesh(es) (armature: doll.rig)`. Doll só tem polygon (sprite_frame eyes são planned, não real); sprite_frame path validado via simple_psd no item seguinte.
- [x] `examples/generated/simple_psd/simple_psd.photoshop_manifest.json` stamp - INFO bar inclui "composed M spritesheet(s)" indicando sprite_frame layers detectados (arrow_0..3 grouping).
- [x] Imported scene tem stub armature (`doll.rig` com bone `root`) + 22 meshes parented `parent_type=OBJECT` ao armature object. Por design (`importers/photoshop/planes.py`) - evita bone-direction rotation flip que poria meshes em XY ao invés de XZ.
- [x] PSD layer names = object names sem colisão. 22 meshes nomeados conforme `manifest.layers[].name` sem sufixos `.001/.002`.

**Cross-app roundtrip diff (00_blender_base vs 02_photoshop_setup):** drift esperado registrado:

- size: +2px em ambos eixos em todas as 22 layers - PSD export captura bbox alpha-aware com 1px edge padding cada lado.
- path: `render_layers/<name>.png` -> `images/<name_underscored>.png`. Folder convention difere (bpy vs JSX) + `.` em layer name vira `_` (PSD não permite `.`).
- position, z_order, kind, canvas size, format_version, layer count, layer names: **zero drift**.

### 1.18 Writer (export - via UI ou headless)

- [x] `doll.blend` -> `.proscenio` writer roda limpo. Únicos warnings: `belly/chest/waist vertex group has no matching bone - dropping from weights` (3 warnings esperados; vertex groups dessas spine-region meshes não batem nome de bone porque doll usa weighted distribution ao longo da spine chain). Golden regenerated successfully.
- [x] Slot fixture (`slot_swap.blend` substitui `doll_slots.blend` retirado em PR #40) -> `.proscenio` contém `"slots": [...]` com 2 attachments + bone field + default + 1 action `swing` (que merge swing + weapon swap). slot_cycle adiciona cobertura adicional do cycle pattern.
- [x] Re-export bytes idênticos. 2 runs consecutivos de `export_proscenio.py` sobre `doll.blend` produzem bytes-por-bytes idênticos (`diff` retorna 0). Sprites sorted by name (`scene_discovery.py:24`), output via `json.dumps(sort_keys=True, indent=2)` no `_normalize`.
- [x] Slot sem bone parent: campo `bone` omitted no JSON. Confirmado: slot_swap (bone=`arm`) tem `"bone": "arm"` no JSON; slot_cycle (sem parent_bone no Empty) tem zero `"bone":` field no slot entry.
- [x] hide_viewport / hide_render não filtram meshes. Validado headless: mesh `arm` em slot_swap com `hide_viewport=True+hide_render=True` ainda aparece na lista de sprites do `.proscenio` output. `find_sprite_meshes` (`scene_discovery.py:18-25`) itera todos MESH sem checar hide flags.
- [x] Atlas auto-discovery: 2 paths verificados.
  - Path 1 (material image): slot_swap.expected.proscenio `"atlas": "arm.png"`, slot_cycle `"atlas": "attachment_blue.png"` - filename do primeiro Image Texture node descoberto.
  - Path 2 (sibling fallback): cenário com mesh sem material image-textured + arquivo `atlas.png` no mesmo dir do output -> `find_atlas_image` retorna `"atlas.png"` (`scene_discovery.py:39-42`).

---

## 2. Apps/Godot

### 2.1 Plugin core

- [x] Plugin enables limpo no Project Settings > Plugins (auto-enabled via project.godot, sem warnings).
- [x] EditorImportPlugin reconhece `.proscenio` files. Painel Import mostra "Proscenio Character" importer, right-click oferece Reimport, gera `.scn` no `.godot/imported/`.
- [x] Re-import preserva customizações no wrapper scene. Confirmado em SlotSwap.tscn: adicionado `MyCustom` Sprite2D child do root, save, Reimport `slot_swap.proscenio`, reabre tscn -> MyCustom intacto. Wrapper pattern SPEC 001 Option A funciona.

### 2.2 Importer

- [x] `slot_swap.proscenio` -> Skeleton2D + Polygon2D children (substitui doll, que ficou skipped no canonical Godot sync por ser authoring-only PS roundtrip). SlotSwapCharacter root contém Skeleton2D + slot Node2D + Polygon2D `arm`.
- [x] `slot_swap.proscenio` -> Slot vira Node2D parent + visible-toggled children (substitui doll_slots retired). Confirmado: `weapon` Node2D contém `club` (visible=ON, default) + `sword` (visible=OFF).
- [x] sprite_frame meshes -> Sprite2D com hframes/vframes. Validado em `blink_eyes`: node `eye` é Sprite2D com texture=eye_spritesheet.png, hframes=4, vframes=1, frame=0, centered=ON.
- [~] polygon meshes -> Polygon2D com UV + vertex weights. **UV + polygon validados** em slot_swap (arm Polygon2D: polygon size=4, UV size=4, texture=arm.png). **Weights NÃO exercitáveis** no Godot dev project - zero fixtures sincronizadas têm `weights[]` (atlas_pack/blink_eyes/mouth_drive/shared_atlas/simple_psd/slot_cycle/slot_swap todas com weights=[]). Doll era a única com weighted skinning (spine-region meshes + forearm spillover) mas está skipped do sync por ser authoring-only PS roundtrip. Path coberto via Blender headless tests (golden diffs), não via inspeção visual no Godot. Fechará quando `doll-from-photoshop` fixture (specs/007 Coverage gaps) chegar.
- [!] Animations -> AnimationPlayer com bone tracks. **Bug writer:** lê `rotation_euler[2]` (Z) hardcoded em `animations.py:147` mas fixtures keyframam `[1]` (Y, convention Front Ortho per scripts/fixtures/README.md). slot_swap `swing` action emit 3 keys com só `{time}`, sem rotation field. Godot importa AnimationPlayer com track de 0 propriedades. Bug em BUGS_FOUND.md.
- [~] slot_attachment tracks -> visible toggle keyframes constant interpolation. **Toggle funciona** em swing.001 - 2 visibility tracks (club + sword) com constant interp, 3 keys flipando ON/OFF corretamente. **Mas:** sword Polygon2D fica na posição (0,0) em vez do slot location porque writer lê `matrix_world` stale em meshes com `hide_viewport=True`. Bug em BUGS_FOUND.md.
- [x] Atlas auto-discovery: `atlas.png` next to `.proscenio` carregado como CompressedTexture2D. Validado em shared_atlas: 3 Polygon2D (red_circle/green_triangle/blue_square) compartilham mesma CompressedTexture2D (`atlas.png`) com UV por quadrante.

### 2.3 Wrapper scene pattern

- [x] Instance `.scn` em wrapper, attach script -> playback OK. Validado em SlotSwap.tscn: F6 play runtime sem crash.
- [x] Re-import `.proscenio` não sobrescreve wrapper customizations. Já validado em 2.1.3 (MyCustom Sprite2D persistiu pós-reimport).
- [x] Wrapper script acessa AnimationPlayer + dispara animações. SlotSwap.gd com `@onready var animation_player: AnimationPlayer = $SlotSwapCharacter/AnimationPlayer` + `play("swing.001")` em `_ready()` (guard `Engine.is_editor_hint()`). Runtime: visibility de club/sword flipa em loop, animação tocando.

### 2.4 Plugin uninstall test (regra "no GDExtension")

- [x] Generate `.scn` com plugin enabled (importer auto-rodou ao primeiro open do project, .scn cached em `.godot/imported/`).
- [x] Disable plugin no Project Settings (Project > Project Settings > Plugins > uncheck Proscenio).
- [x] Reload project -> abrir scene -> roda sem erros. `.proscenio` source files somem do FileSystem dock (extensão não-reconhecida sem plugin), mas SlotSwap.tscn ainda abre e F6 roda normalmente - TSCN ext_resource resolve via UID/.import sidecar pro `.scn` cached. Skeleton2D / Bone2D / Polygon2D / AnimationPlayer / Sprite2D todos core nodes; zero dependency em GDExtension/runtime addon code. Plugin = importer-only por design.

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

- [ ] `00_blender_base/doll_base.blend` -> render_layers PNG (via `examples/authored/doll/scripts/render_layers.py`)
- [ ] PNGs -> Photoshop (Proscenio Exporter panel: Import manifest as PSD) -> `01_photoshop_base/doll_ps_base.psd`
- [ ] PSD copy + tags -> `02_photoshop_setup/doll_tagged.psd` -> Proscenio Exporter -> `export/doll_tagged.photoshop_exported.json` + images
- [ ] Manifest -> Blender via Import Photoshop Manifest -> `03_blender_setup/doll_rigged.blend`
- [ ] Output Blender ~= input Blender (modulo round-trip drift documentada)

### 4.2 doll -> Godot

- [ ] `03_blender_setup/doll_rigged.blend` -> Export Godot -> `doll.proscenio`
- [ ] `doll.proscenio` -> Godot import -> `doll.scn`
- [ ] Wrapper scene plays -> doll renderiza no editor + runtime
- [ ] `doll_slots.blend` -> mesmo pipeline -> brow_raise animation visível

### 4.3 simple_psd

- [ ] `simple_psd.psd` -> JSX export -> manifest
- [ ] manifest -> Blender import -> stamped scene
- [ ] export Blender -> Godot -> playback

---

## 5. Pré-shipping (futuro, antes de v0.2.0)

- [ ] CI matrix expansion (Blender 4.2 LTS + Godot 4.3) - backlog
- [ ] Reload addon após cada commit que mexe em registration - verificar register / unregister simétrico
- [ ] Performance: doll.blend export tempo, atlas pack tempo com 50+ sprites

---

## Notes

- Atualizar este arquivo após cada smoke session.
- Failures `[!]` viram issues a corrigir em PRs separados.
- Antes de mergear PR grande, marcar manual tests da branch como `[x]` ou `[!]`.
- Use `examples/authored/doll/doll_workbench.blend` (Save As do baseline) pra mexer livremente. NÃO editar `doll.blend` canônico.
