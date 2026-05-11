# Bugs found during manual testing

Bugs reproducíveis encontrados durante manual smoke / feature tests
(MANUAL_TESTING.md). Cada item cita reproducer + suspeita + arquivo
afetado. Vira PR fix ou issue dedicada.

Distinto de UI_FEEDBACK.md (que cobre polish, não comportamento).

---

## apps/blender

### Snap to UV bounds: IndexError em edit mode

**Repro:** Active Sprite > polygon mode > manual region > entra Edit mode no mesh > click "Snap to UV bounds".

**Erro:**

```text
File "apps/blender/operators/uv_authoring.py", line 102, in execute
    u = uv_layer.data[li].uv
        ~~~~~~~~~~~~~^^^^
IndexError: bpy_prop_collection[index]: index 0 out of range, size 0
```

**Causa:** em edit mode `mesh.uv_layers.active.data` é overridden pelo BMesh e fica `size 0`. O operator itera direto sem guard.

**Fix proposto:**

- `poll()` bloqueia edit mode (return False quando `context.mode == "EDIT_MESH"`)
- Ou execute() detecta `len(uv_layer.data) == 0` e retorna `{"CANCELLED"}` com warning

**Arquivo:** `apps/blender/operators/uv_authoring.py:85-122` (`PROSCENIO_OT_snap_region_to_uv`).

**Severity:** medium -- crash de operator não pode acontecer; usuário em edit mode é caso comum.

### Writer: pose-location Z (bone-local) descartado pra bones horizontais

**Repro:** action keyframa `pose.bones["mouth_pos"].location[2] = 0.05` (bone com rest pose horizontal, head=(0,0,0) tail=(0.3,0,0)). Roda writer. .proscenio output mostra position track com `[0.0, -0.0]` em vez do esperado `[0.0, -5.0]` (0.05 world Z * 100 ppu, com Y inversion).

**Causa:** `apps/blender/exporters/godot/writer/animations.py:138-144`:

```python
if "location" in entry:
    loc = entry["location"]
    bx = float(loc.get(0, 0.0))
    by = float(loc.get(1, 0.0))
    bz = float(loc.get(2, 0.0))
    if max(abs(bx), abs(by), abs(bz)) > 1e-6:
        position = [round(by * ppu, 6), round(-bx * ppu, 6)]
```

Formula assume bones com Y axis = world Z (verticais). Pra bones horizontais (Y axis = world X), bone-local Z = world Z, mas formula descarta `bz`. Position track sempre vira (0, 0).

**Fix proposto:** converter `(bx, by, bz)` pose location pra world delta usando matrix do rest pose do bone, depois aplicar `world_to_godot_xy`. Lida com qualquer orientação de bone.

**Arquivo:** `apps/blender/exporters/godot/writer/animations.py:138-144` (`_resolve_pose_entry`).

**Severity:** medium -- afeta qualquer rig 2D com bones horizontais (front-ortho convention). Bones verticais (típicos de rigs body-aligned) funcionam por acidente. Não causa crash, só silenciosamente perde translation tracks.

### Slot fields: PG <-> CP mirror não dispara (`is_slot`, `slot_default`, `is_outliner_favorite`)

**Repro:** Active Slot panel, click star vazia em attachment não-default. PG `slot_default` muda visualmente (star toggle), mas Custom Property `proscenio_slot_default` no Properties editor continua mostrando valor anterior.

**Causa:** dois bugs combinados:

1. `apps/blender/properties/object_props.py:220-227` (`slot_default`), `:239-247` (`is_slot`), `:230-237` (`is_outliner_favorite`) -- nenhum desses 3 fields tem `update=on_any_update` no IntProperty/StringProperty/BoolProperty. Os outros 11 fields têm.
2. `apps/blender/core/mirror.py:24-36` (`OBJECT_MIRROR_MAP`) -- mapping não inclui entries pros 3 fields acima. Mesmo se update callback disparasse, `mirror_all_fields` não saberia mirror eles.

Resultado: PG e CP divergem assim que usuário toca esses fields. Headless writer (sem addon) lê CP stale -> slot_default errado, is_slot errado.

**Fix proposto:**

1. Adicionar `update=on_any_update` nas 3 declarações em object_props.py.
2. Adicionar 3 tuplas em `OBJECT_MIRROR_MAP`:

   ```python
   ("proscenio_is_slot", "is_slot", bool),
   ("proscenio_slot_default", "slot_default", str),
   ("proscenio_outliner_favorite", "is_outliner_favorite", bool),
   ```

**Severity:** high -- afeta correctness do round-trip slot. Bug-of-omission no SPEC 005.1.c.1 (fix do mirror cobriu sprite fields, esqueceu slot fields que vieram em SPEC 004 depois).

### Drive from Bone: F9 redo trocando target NÃO migra driver, adiciona outro

**Repro:**

1. Active Sprite > Drive from Bone > Target=Frame index, click "Drive from Bone"
2. Driver criado em `mouth.proscenio.frame`
3. F9 redo > troca Target pra `Region X` (mesmo bone, mesma expression)
4. Operator re-roda

**Esperado:** driver migra de `proscenio.frame` pra `proscenio.region_x` (1 driver só, no novo target).

**Atual:** driver **adicionado** em `proscenio.region_x`, driver antigo em `proscenio.frame` permanece. Sprite mesh fica com 2 drivers em proscenio.* properties.

**Causa:** `apps/blender/operators/driver.py:_ensure_single_driver` só remove driver no `data_path` que está sendo escrito. Mudar target_property muda data_path, então drivers em outros proscenio.* properties não são tocados.

**Fix proposto:** quando re-rodando o operator no mesmo sprite + mesma armature/bone source com target diferente, remover drivers existentes em outros `proscenio.*` paths (que tenham o mesmo source bone).

Pseudocódigo:

```python
# Antes do driver_add:
if sprite.animation_data is not None:
    for fcurve in list(sprite.animation_data.drivers):
        if fcurve.data_path.startswith("proscenio.") and fcurve.data_path != data_path:
            # check se o source bone bate
            for var in fcurve.driver.variables:
                if any(t.id == armature and t.bone_target == self.bone_name for t in var.targets):
                    sprite.driver_remove(fcurve.data_path)
                    break
```

OR adicionar `replace_existing: BoolProperty(default=True)` na operator props pra permitir opt-out (caso usuário queira múltiplos drivers do mesmo bone).

**Arquivo:** `apps/blender/operators/driver.py:31-51` (`_ensure_single_driver` precisa virar mais esperto, ou execute() deve fazer cleanup adicional).

**Severity:** medium -- F9 redo é workflow esperado de "tweak parameters", behavior atual viola princípio de menos surpresa.

### Drive from Bone: transform_space LOCAL retorna 0 pra rotação world Z

**Repro:** Active Sprite > Drive from bone com Target=Frame index, Axis=Bone Rot Z, expression=`var * 2 + 2`. Click "Drive from Bone". Em pose mode, R Z 45 no bone. Initial frame fica 2 (não muda da rotação 0). Driver Variable Value mostra 0.0° apesar do bone estar rotacionado 45°.

**Causa:** `apps/blender/operators/driver.py:140`:

```python
target.transform_space = "LOCAL_SPACE"
```

Local Space retorna rotação relativa à orientação local do bone. Pra bones com axis vertical (Y aligned com world Z, como no fixture `mouth_drive`), R Z em pose mode rotaciona ao redor do bone-Y (twist), NÃO do bone-Z local. Local Z permanece 0. World Space pega a rotação Z do mundo direto -- comportamento esperado pra 2D cutout.

**Fix proposto:** `target.transform_space = "WORLD_SPACE"` -- alinha com expectativa de 2D cutout (bones em plano XY-mundo, rotação Z = rotação no plano). Ou expor "Space" como dropdown na UI do Drive from Bone.

**Arquivo:** `apps/blender/operators/driver.py:140` (`PROSCENIO_OT_create_driver.execute`).

**Severity:** high -- feature aparenta totalmente quebrada se usuário não souber Blender API a ponto de inspecionar driver no editor + trocar Space manualmente.

### Drive from Bone: keyframes residuais no fcurve do driver clampam output

**Repro:** Click "Drive from Bone" em sprite mesh. Olha no Drivers Editor o fcurve do driver. Tem keyframes em ~(0.667, 0.667), (1.0, 1.0), (1.333, 1.333) com Bezier interpolation + Constant extrapolation.

**Causa:** quando o operator chama `sprite.driver_add(data_path)`, Blender cria fcurve com 3 default keyframes pra IntProperty (provavelmente seed da geometry padrão). Esses keyframes mapeiam driver expression output -> final value. Constant extrapolation clamps qualquer valor fora de [0.667, 1.333] -> int(1.333)=1. Frame fixo em 1 não importa quanto o driver expression calcule.

**Fix proposto:** após `driver_add`, deletar os keyframes default do fcurve OU adicionar fcurve modifier "Generator" linear (`y = 1*x + 0`) explicitamente. Garante mapping 1:1 driver-output -> property-value.

**Arquivo:** `apps/blender/operators/driver.py:31-40` (`_ensure_single_driver`).

**Severity:** high -- combinado com o bug acima, esse é o motivo final do feature parecer quebrado. User precisa abrir Drivers Editor + selecionar fcurve + selecionar todos os keyframes + deletar manualmente pra fazer driver funcionar.

### mouth_drive fixture: bone vertical força LOCAL_SPACE bug acima

**Repro:** abrir `examples/mouth_drive/mouth_drive.blend` e tentar usar Drive from Bone pra controlar mouth via bone rotation Z em pose mode.

**Causa:** o fixture `scripts/fixtures/mouth_drive/build_blend.py:79-84` cria o bone vertical (`head=(0,0,0)` -> `tail=(0,0,0.5)`). Bone Y axis = world Z. R Z em pose mode = twist around bone-Y, não rotação local Z. Mesmo com WORLD_SPACE no driver, é confuso pro usuário.

**Fix proposto:** orientar o bone horizontalmente (`head=(0,0,0)` -> `tail=(0.5,0,0)`) ou ao longo de world Y (`tail=(0,0.5,0)`). Aí bone-Y = world Y, rotação Z em pose mode = rotação local Z do bone, e LOCAL_SPACE pega a rotação corretamente. Alinha com convenção 2D cutout (bones no plano XY mundo).

**Arquivo:** `scripts/fixtures/mouth_drive/build_blend.py:81-83`.

**Severity:** medium -- afeta UX da fixture, não da feature em geral. Fix combinado com os 2 bugs acima resolve a triade.

### Wrapper .tscn: script path falta `/godot/` em fixtures legacy

**Repro:** copiar `examples/<fixture>/` para `res://<fixture>/` em projeto Godot, abrir `*.tscn` -- script ext_resource quebra com "file not found".

**Causa:** `BlinkEyes.tscn`, `Doll.tscn`, `SharedAtlas.tscn` declaram `Script path="res://<fixture>/<File>.gd"`, mas o `.gd` mora em `<fixture>/godot/<File>.gd`. Path correto seria `res://<fixture>/godot/<File>.gd` (como faz `SimplePSD.tscn`).

**Fix:** trocar 3 paths nos `.tscn` afetados:

- `examples/blink_eyes/godot/BlinkEyes.tscn`: `res://blink_eyes/BlinkEyes.gd` -> `res://blink_eyes/godot/BlinkEyes.gd`
- `examples/authored/doll/godot/Doll.tscn`: `res://doll/Doll.gd` -> `res://doll/godot/Doll.gd`
- `examples/shared_atlas/godot/SharedAtlas.tscn`: `res://shared_atlas/SharedAtlas.gd` -> `res://shared_atlas/godot/SharedAtlas.gd`

`mouth_drive` já corrigido in-place (PR #38, post-CodeRabbit). `simple_psd` já estava correto.

**Severity:** medium -- wrapper scenes não funcionam out-of-the-box; usuário precisa fix manual ao copiar pra projeto Godot.

### ~~blink_eyes fixture: image path absoluto bake'a no .blend~~ FIXED

Fixed inline. `scripts/fixtures/blink_eyes/build_blend.py` agora chama
`bpy.path.relpath` após `save_as_mainfile` + salva de novo, persistindo
`//pillow_layers/eye_spritesheet.png` em vez do path absoluto. Aproveitada
a passagem para reorientar o bone ao longo de world Y (perpendicular ao
plano XZ), alinhando com a convenção do `mouth_drive` (Spine-style:
bones aparecem como pontos no Front Ortho).

**Provável que `simple_psd/build_blend.py` e `slot_cycle/build_blend.py`
ainda tenham o mesmo bug de path absoluto** -- auditar quando rodar
testes manuais nessas fixtures.

### (slot) Reproject UV: segunda chamada lenta + Y invertido

**Repro:** Active Sprite > polygon mode > "Reproject UV" duas vezes seguidas.

**Sintoma 1 (perf):** segunda chamada demora vários segundos como se fosse crashar.

**Sintoma 2 (orientação):** UV resultante fica de cabeça pra baixo no UV editor (V invertido).

**Suspeita 1:** mode_set OBJECT<->EDIT chained com smart_project + restore loop pode estar deselecionando todo mundo + reselecionando, causando spike de cost. Ou `bpy.ops.uv.smart_project` cacheia algo problematico.

**Suspeita 2:** smart_project usa face normal como projeção; head do doll tem normal apontando "pra cima" (Y axis no Blender 2D plane vira V invertido em UV space).

**Arquivo:** `apps/blender/operators/uv_authoring.py:39-66` (`PROSCENIO_OT_reproject_sprite_uv`).

**Severity:** low -- operacional, não crash. UV invertida é workaround manual ou parameter.

### Outliner panel: filtro nativo da UIList (campo de baixo) não filtra

**Repro:** Proscenio > subpanel Outliner > expandir filtro nativo do UIList (seta `▼` no rodapé) > digitar substring (ex: `brow.L`) no campo "Filter by Name".

**Sintoma:** lista não filtra. Continua mostrando todos objetos. Só funciona o campo do **topo** (com ícone `VIEWZOOM`), que é `scene_props.outliner_filter`.

**Causa:** `PROSCENIO_UL_sprite_outliner.filter_items` (apps/blender/panels/outliner.py:93-127) sobrescreve a lógica de filtro completa e ignora `self.filter_name` (o campo nativo do UIList). Só consulta `scene_props.outliner_filter`. Resultado: 2 search bars visíveis (1 nossa, 1 nativa) e só uma funciona -- confuso pro usuário.

**Fix proposto (opção A, simples):** em `filter_items`, OR o substring filter com `self.filter_name`:

```python
flt_text = (getattr(scene_props, "outliner_filter", "") or "").lower()
native_text = (self.filter_name or "").lower()
combined = flt_text or native_text  # nossa tem prioridade; cai pra nativa
...
if combined and combined not in obj.name.lower():
    continue
```

**Fix proposto (opção B, mais limpo):** desabilitar o filtro nativo do UIList (`use_filter_show=False` no draw_filter override) e deixar só nosso search no topo, que já tem ícone próprio e está consistente com o style do panel.

**Arquivo:** `apps/blender/panels/outliner.py:93-127`.

**Severity:** medium -- não crash, mas duplicidade engana usuário e parece bug de filtro quebrado.

### Skeleton panel: row click no UIList não seleciona bone no viewport

**Repro:** doll_workbench.blend > Pose Mode > deselect all (`Alt+A`) > Proscenio > subpanel Skeleton > click row `upper_arm.L` no UIList de bones.

**Sintoma:** linha highlight no panel (active_bone_index muda), mas viewport não reflete -- nenhum bone selecionado, nenhum active bone na armatura. Comportamento esperado pela MANUAL_TESTING.md item 1.8.2: click row -> seleciona bone correspondente em pose mode.

**Causa:** `apps/blender/properties/scene_props.py:54` define `active_bone_index` como `IntProperty` puro, sem `update=` callback. `apps/blender/panels/skeleton.py:73-80` usa `template_list` apontando pra esse PG, que só armazena o índice; não há operator no row draw nem update hook que sincronize com `armature.data.bones.active` ou `armature.pose.bones[...].bone.select`.

**Comparação:** Outliner panel resolve o mesmo problema com operator dedicado (`proscenio.select_outliner_object`) clicado via row draw_item. Skeleton panel não tem equivalente.

**Fix proposto (opção A):** novo operator `proscenio.select_bone_by_index` chamado de dentro de `PROSCENIO_UL_bones.draw_item`. Operator entra em pose mode (se preciso), set `armature.data.bones.active` + `pose_bone.bone.select = True`.

**Fix proposto (opção B, mais simples):** adicionar `update=` callback ao `active_bone_index` que faz a sincronização. Risco: callback dispara em todos os redraws e pode causar feedback loop com modos não-pose.

**Arquivo:** `apps/blender/properties/scene_props.py:54-59`, `apps/blender/panels/skeleton.py:12-31`.

**Severity:** medium -- panel oferece UX de selector de bone, mas não cumpre. Usuário precisa selecionar bone no viewport manualmente.

### Animation panel: row click não atribui action ao armature

**Repro:** doll_workbench.blend > Proscenio > Animation > click row `wave` no UIList > scrubar timeline.

**Sintoma:** doll não anima. Selection do row só atualiza `active_action_index`; `doll.rig.animation_data.action` continua o que tava antes (provavelmente `None` ou outra action). Pra animar, usuário precisa abrir Dope Sheet > Action Editor > assignar manualmente.

**Causa:** `apps/blender/properties/scene_props.py:48` define `active_action_index` como IntProperty sem `update=`. `apps/blender/panels/animation.py:53-61` usa `template_list` apontando pra esse PG sem operator que sincronize.

**Padrão repetido:** mesma família dos bugs "Skeleton panel row click não seleciona bone" e "Active Sprite Drive-from-Bone selectors" -- UI selectors do Proscenio armazenam índice mas não dirigem viewport / armature state. Vale considerar fix consolidado.

**Fix proposto:** novo operator `proscenio.set_active_action` chamado de dentro de `PROSCENIO_UL_actions.draw_item`. Operator atribui `action` ao `armature.animation_data.action` (criando `animation_data` se preciso) + opcionalmente reseta timeline pra `action.frame_range[0]`. Variante mais segura: só aplica se exatamente 1 armature na cena (heurística mesma do Skeleton panel `armatures[0]`).

**Feedback usuário (10-mai-2026):** "o swap de animação pelo seletor do proscenio seria bem útil".

**Arquivo:** `apps/blender/properties/scene_props.py:48-53`, `apps/blender/panels/animation.py:12-30`.

**Severity:** medium -- panel parece broken pro usuário (selecionou mas nada acontece). Funcionalidade óbvia que falta.

---
