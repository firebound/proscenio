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

Em sprite_frame mesh com material image-textured (eye.L, eye.R no doll):

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

- [ ] "Pack Atlas" button: gera `atlas_pack.atlas.png` (atlas único 9-em-1) + `atlas_pack.atlas.json` (sprite -> placement map)
- [ ] Pack idempotente: re-roda sem duplicar (atlas.png/atlas.json não mudam byte a byte na segunda run)
- [ ] Pack após Apply: usa atlas existente como source, idempotente
- [ ] "Apply Packed Atlas": UVs de cada sprite reescritas pra apontar pra sua sub-região no atlas; sprites linkados a `Proscenio.PackedAtlas` material; viewport ainda mostra dígito correto em cada sprite (prova que UV remap não embaralhou)
- [ ] material_isolated=True: sprite mantém material próprio (`sprite_N.mat`), swap só substitui Image Texture pelo atlas packed
- [ ] "Unpack": restaura UVs originais (snapshot via UV layer `<active>.pre_pack`) + materiais originais voltam
- [ ] Ciclo Pack > Apply > Pack > Apply: estado idempotente (atlas.png byte-identical, sem rotation de placements)
- [ ] pack_padding_px setting respeitado (sprites no atlas têm gap N px entre si)
- [ ] pack_max_size: cap pequeno (ex: 64 px) com 9 sprites de 32x32 não cabe -- pack falha graciosamente com warning, não crash
- [ ] pack_pot=True: dimensões round-up pra power of 2 (com 9x32x32 = ~96x96 footprint, atlas vira 128x128 POT)

### 1.11 Validation panel

- [ ] "Validate" button: roda toda validação
- [ ] Errors em vermelho, warnings em amarelo
- [ ] Click issue: seleciona objeto offending
- [ ] Validation results sticky entre saves
- [ ] `validation_ran` flag bloqueia export até primeira run

### 1.12 Export panel

- [ ] "Export Godot" button: file picker abre, escolhe path -> escreve .proscenio
- [ ] Last export path sticky no `Scene.proscenio.last_export_path`
- [ ] "Re-export Godot" usa sticky path sem prompt
- [ ] Pixels per unit setting respeitada no output
- [ ] Validation gate bloqueia export se errors críticos não resolvidos

### 1.13 Help + status badges

- [ ] Cada subpanel mostra ícone status + ? alinhados à direita do header
- [ ] Hover ícone -> tooltip per-band (godot-ready / blender-only / planned / out-of-scope)
- [ ] Click ícone -> abre `status_legend` popup
- [ ] Click ? em cada subpanel -> abre topic-specific help popup
- [ ] Pipeline overview popup (root ?) renderiza todos sections + see-also
- [ ] Drive-from-bone help topic conteúdo confere
- [ ] See-also links resolvem em paths reais
- [ ] `slot_system` topic abre via Active Slot ? button
- [ ] `sprite_frame_preview` topic abre via Active Sprite ? button (sprite_frame mode)

### 1.14 Quick Armature

- [ ] "Quick Armature" operator: 3D viewport, click-drag head -> tail desenha bone
- [ ] Bone aparece em armature `Proscenio.QuickRig`
- [ ] Multiple drags em sequência: cria chain
- [ ] Shift hold no press: bone novo parented ao anterior
- [ ] ESC ou RIGHTMOUSE: sai do modal
- [ ] Cancel sem nenhum bone criado: armature vazio removido (não polui scene)
- [ ] Drag muito curto (< 1e-4): skip, não cria bone

### 1.15 Pose library

- [ ] "Save Pose to Library": com armature em pose mode, pose name -> action criada
- [ ] Action salva apenas keyframes do current pose
- [ ] "Bake Current Pose": atual pose vira keyframe @ frame 1

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
