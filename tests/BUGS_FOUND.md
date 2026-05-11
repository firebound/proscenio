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

### Reproject UV: segunda chamada lenta + UV resultante rotacionada/flipada

**Repro:** Active Sprite > polygon mode > "Reproject UV". Sintomas em primeira E segunda chamadas.

**Sintoma 1 (perf):** segunda chamada demora vários segundos como se fosse crashar (testes anteriores em doll).

**Sintoma 2 (orientação):** UV resultante fica rotacionada 90° + horizontalmente invertida. Confirmado em atlas_pack_workbench sprite_1 (11-mai-2026): após Reproject UV, layout precisou de `R -90 S X -1` (rotate -90° + scale X = -1 no UV editor) pra voltar ao mapeamento original.

**Suspeita 1:** mode_set OBJECT<->EDIT chained com smart_project + restore loop pode estar deselecionando todo mundo + reselecionando, causando spike de cost. Ou `bpy.ops.uv.smart_project` cacheia algo problemático.

**Suspeita 2:** `bpy.ops.uv.smart_project` (uv_authoring.py:53) usa face normal pra escolher projeção. Para um quad no plano XZ (Front Ortho convention), a normal aponta -Y -- smart_project pode estar interpretando isso como "back side" e flipar U + rotacionar 90° pra alinhar. UVs originais (autorados manualmente em build_blend.py com layout específico pra evitar mirror em Front Ortho) são SOBRESCRITAS por essa projeção automática que não respeita o setup original.

**Fix proposto:**

- Substituir `bpy.ops.uv.smart_project` por reprojeção manual: detectar plano do mesh (X, Y ou Z aligned), mapear UVs naive (face vertices em world space -> UV [0..1] baseado em bounding box no plano detectado), respeitando o flip-U-pra-Front-Ortho que `build_blend.py` faz.
- Alternativa: `bpy.ops.uv.unwrap` (cube/cylinder/sphere projection explícita) em vez de smart_project, com config determinística.
- Mínimo: documentar limitação no help topic do Reproject UV ("re-roda Smart UV Project, pode mudar orientação de UVs autoradas manualmente").

**Arquivo:** `apps/blender/operators/uv_authoring.py:39-66` (`PROSCENIO_OT_reproject_sprite_uv`).

**Severity:** medium -- operator funciona (não crash), mas resultado é destrutivo de UVs autoradas. Usuário precisa transformar manualmente pra recuperar layout original. Bloqueante pra workflow onde UVs foram cuidadosamente alinhadas (típico em pixel art).

---

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

### Atlas Apply: skipped N sprites quando alguma mesh em Edit Mode (suspeita)

**Repro (tentativa):** atlas_pack_workbench.blend > Pack Atlas (OK, packed 9 sprites 256x256) > Apply Packed Atlas. Operator reporta "applied packed atlas to 0 sprite(s); skipped 9 (no UV layer)".

**Sintoma post-mortem (via inspect headless):**

- `sprite_N.data.uv_layers["UVMap"]` ainda existe mas `len(data) == 0` (UV loop data wiped).
- Nenhuma layer `.pre_pack` criada.
- `proscenio_pre_pack` CP setada com `uv_layer_snapshot == ""` -- prova que `duplicate_active_uv_layer` retornou early porque `len(active.data) == 0` (apps/blender/operators/atlas_pack/_paths.py:35).

**Headless repro falhou em reproduzir:** rodar `duplicate_active_uv_layer` isoladamente em fresh `atlas_pack.blend` mantém `uv_layers.active.data` com len=4. Bug aparece só no interativo.

**Suspeita:** mesh em Edit Mode quando Apply roda. Em edit mode, `mesh.uv_layers.active.data` reporta zero entries -- precisa de BMesh access. Mesmo padrão do bug logado anteriormente "Snap to UV bounds: IndexError em edit mode" (apps/blender/operators/uv_authoring.py:102).

**Outras hipóteses não descartadas:**

- Operator wipa UV data inadvertidamente em algum path interno (`read_manifest`, `_ensure_shared_material`).
- `uv_layers.new(do_init=False)` no Blender 5.1.1 invalida active reference em condições específicas (não reproduzido headless).
- Multi-object edit mode em todos os sprites simultaneamente.

**Fix proposto:**

- `apply.py` deve adicionar guard em poll(): `return ... and context.mode == "OBJECT"` -- previne run em edit mode.
- `apply.py:execute` + `duplicate_active_uv_layer` precisam logar warning explícito (não apenas skipped count) quando data len=0 detectado: pode ser edit mode, mesh corrompido, ou mesh sem UV.
- Considerar BMesh fallback em apps/blender/operators/atlas_pack/* análogo ao que uv_authoring.py precisa.

**Arquivo:** `apps/blender/operators/atlas_pack/apply.py:148-159`, `apps/blender/operators/atlas_pack/_paths.py:24-46`.

**Severity:** medium-high -- operator silenciosamente wipa UV data + relata "skipped" sem indicar a causa. Usuário fica preso sem clue. Pode ser causa pre-existente do "actual UV data already empty" cenário.

**CONFIRMADO (10-mai-2026):** root cause é Edit Mode. Usuário tinha todos os 9 sprites selecionados em Edit Mode quando clicou Apply. Em Object Mode o operator funciona normalmente. Fix definitivo: adicionar poll() check `context.mode == "OBJECT"` em PROSCENIO_OT_apply_packed_atlas + PROSCENIO_OT_pack_atlas + PROSCENIO_OT_unpack_atlas (mesma família).

### Atlas Apply: re-click NÃO é idempotente -- UVs encolhem a cada click

**Repro:** atlas_pack_workbench.blend > Object Mode > Pack Atlas > Apply Packed Atlas (OK, viewport correto) > **Apply Packed Atlas** denovo.

**Sintoma:** UVs encolhem dentro do slot do atlas. Cada Apply remapeia as UVs como se elas estivessem em "source image space" (0..1 do PNG original), mas após primeiro Apply elas já estão em atlas space (ex: 0..0.125 pra sprite 32px em atlas 256px). Segundo Apply trata 0..0.125 como source-image 0..1 e re-empacota dentro do já-pequeno slot. Repetir N vezes -> UVs convergem pra ponto único no canto do slot.

**Causa:** `apply.py:148-173` (`_rewrite_uvs`):

```python
src_px_x = u * src_w
src_px_y = v * src_h
new_u = (slot.x + (src_px_x - slice_rect.x)) / atlas_w
new_v = (slot_y_bu + (src_px_y - slice_rect.y)) / atlas_h
```

Lê UV atual + transforma assumindo que `u, v` estão em source space. Sem flag detectando "já foi aplicado".

**Fix proposto:**

- Opção A (defensive): no _snapshot_pre_pack, se o CP `proscenio_pre_pack` já existe + layer `.pre_pack` ainda presente, restaurar UVs do `.pre_pack` antes de re-aplicar. Garante que Apply sempre parte do source-image space.
- Opção B (block): poll() detecta presença de pre_pack snapshot + retorna False, com hint "Apply already applied -- Unpack first to reapply" ou similar. Forço re-flow Unpack > Pack > Apply.
- Opção C (auto-unpack): segundo Apply detecta snapshot existente e auto-Unpack antes de re-Apply. Transparente mas pode surpreender se usuário queria layering.

Recomendação: Opção A é mais robusta + invisível ao usuário; Opção B é mais explícita mas adiciona fricção.

**Arquivo:** `apps/blender/operators/atlas_pack/apply.py:80-97` (_snapshot_pre_pack), `apply.py:148-173` (_rewrite_uvs).

**Severity:** medium-high -- quebra silenciosamente o estado da fixture; usuário não tem warning. Se Pack for re-executado e Apply rodar de novo (ciclo natural), UVs vão drift cada iteração.

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

Mesmo bug aplica ao shared material -- se `Proscenio.PackedAtlas` for renomeado, próximo Apply cria um novo (re-discovery falha + cria) deixando o renomeado órfão.

**Fix proposto:**

- Snapshot deveria guardar referência por pointer (não por nome): usar `bpy.types.PropertyGroup` com `PointerProperty(type=bpy.types.Material)` em vez de CP string. Blender atualiza pointer automaticamente quando datablock renomeia.
- Alternativa low-effort: na restauração, se `materials.get(name)` falha, escanear materials por algum marker (CP `proscenio_original_for: "sprite_5"`) que cada material carrega depois do Apply.
- Mínimo aceitável: warning explícito no INFO bar quando snapshot.material name não acha (ex: "sprite_5: original material 'sprite_5.mat' not found -- maybe renamed; restored UVs only").

**Arquivo:** `apps/blender/operators/atlas_pack/apply.py:80-97` (snapshot escrita), `apps/blender/operators/atlas_pack/unpack.py:70-83` (restauração).

**Severity:** medium -- não trava, mas perde estado original sem avisar. Usuário descobre só ao olhar Properties > Material.

### Help topic `sprite_frame_preview` é orphan -- sem entry point na UI

**Repro:** abre fixture com sprite_frame mesh (ex: `examples/mouth_drive/mouth_drive.blend` ou blink_eyes) > select sprite_frame mesh > N-panel > Proscenio > Active Sprite > sub-box "Sprite frame" expandido.

**Sintoma:** sub-box "Sprite frame" tem só label header + fields (hframes / vframes / frame / centered) + Setup/Remove Preview buttons. **NÃO tem ícone `?`** pra abrir help topic. Visual confirmado em screenshot do usuário (10-mai-2026 sessão 1.13 item 9).

**Causa:** `apps/blender/panels/_draw_sprite_frame.py:26` desenha `box.label(text="Sprite frame", icon="IMAGE_DATA")` -- label puro, sem operator. Não chama `draw_subpanel_header` nem invoca `proscenio.help` com `topic="sprite_frame_preview"`. Help topic está definido em `apps/blender/core/help_topics.py:432` + tem FeatureStatus entry em `apps/blender/core/feature_status.py:115`, mas inacessível via UI -- só dá pra abrir programaticamente via `bpy.ops.proscenio.help(topic="sprite_frame_preview")`.

**Fix proposto:**

- Em `_draw_sprite_frame.py:24-26`, trocar `box.label(text="Sprite frame", icon="IMAGE_DATA")` por header row com label + status icon + help button análogo a `draw_subpanel_header(layout, feature_id, help_topic)`. Adicionar helper `_helpers.draw_subbox_header()` pra reuso (Active Sprite sub-boxes não são panels, headers funcionam diferente).
- Mesma família de gap aplica a outras sub-boxes (Sprite frame / Polygon body / Texture region / Drive from Bone). Inventário: confirmar quais tópicos já têm entry visível e quais são orphan.

**Arquivo:** `apps/blender/panels/_draw_sprite_frame.py:24-26`, e provavelmente outros `_draw_*.py`.

**Severity:** low-medium -- não é crash, mas help topic existe e foi documentado/testado como acessível via UI; checklist 1.13 item 9 falha por causa disso. Indica que o pattern de "help button per sub-box" está incompleto.

### Quick Armature: bones criados sempre no plano Z=0 (horizontais), nunca no plano Y=0 do Proscenio

**Repro:** atlas_pack_workbench.blend > Skeleton panel > Quick Armature > Front Ortho (numpad 1) > drag de cima pra baixo no viewport.

**Sintoma:** bone criado fica horizontal (head.Z == tail.Z == 0), independente de pra onde o mouse vai no eixo Z visualizado. Drag vertical no Front Ortho resulta em bone horizontal -- aparenta colapsar Z=0 silenciosamente.

**Causa:** `apps/blender/core/bpy_helpers/viewport_math.py:14-51` (`mouse_event_to_z0_point`) projeta ray do mouse no plano **Z=0** (XY plane, "ground plane"). Em Front Ortho o `view_vec.z ≈ 0` (câmera olha ao longo de Y) -> linha 39 cai no fallback -> linha 41 chama `region_2d_to_location_3d(..., Vector((0,0,0)))` -> linha 43 retorna `(x, y, 0.0)` forçando Z=0.

Proscenio é workflow XZ (Spine / 2D cutout convention -- bones no plano Y=0 visíveis em Front Ortho). Helper foi escrito assumindo top-down (Z=0 plane), incompatível com a convention principal do addon.

**Fix proposto:**

- Renomear helper pra `mouse_event_to_plane_point(plane_axis)` ou similar; deixar caller especificar plano.
- Em `quick_armature.py:70` + `:79`, passar `plane_axis="Y"` pra projetar em Y=0 (XZ plane) -- combina com Front Ortho.
- Considerar detectar a view atual automaticamente: Top Ortho -> Z=0, Front Ortho -> Y=0, Right Ortho -> X=0. Mas complica UX (bone muda de plano se user gira camera). Simpler: hardcode Y=0 pra Proscenio uso.

**Arquivo:** `apps/blender/core/bpy_helpers/viewport_math.py:14-51`, `apps/blender/operators/quick_armature.py:70,79`.

**Severity:** high -- inviabiliza o operator pro workflow primário do addon. Bones quick-rigged não funcionam em Front Ortho (a vista padrão de 2D cutout). Combinado com falta de preview (UI_FEEDBACK), torna Quick Armature inusável hoje.

### Save Pose to Library: `Unexpected library type` sem orientação ao usuário

**Repro:** doll_workbench.blend > Pose Mode > select bones + aplicar pose > N-panel > Proscenio > Skeleton > Save Pose to Library.

**Sintoma:** ERROR bar `Proscenio: pose library refused: Error: Unexpected library type. Failed to create pose asset`. Operator falha sem indicar o que fazer.

**Causa:** Blender 4.x+ removeu defaults writable do Pose Library. `bpy.ops.poselib.create_pose_asset` recusa quando nenhuma asset library destino configurada em Preferences > File Paths > Asset Libraries (com path acessível pra escrita). Erro propagado vem do Blender core; `pose_library.py:68-70` só repassa via `report_error(self, f"pose library refused: {exc}")`.

Usuário não sabe que precisa configurar asset library primeiro. Mesmo trocando uma área pra Asset Browser não resolve -- precisa adicionar library destino nas Preferences.

**Fix proposto:**

- Pré-check em `execute()`: detectar se existe asset library writable (`bpy.context.preferences.filepaths.asset_libraries` -- iterar + checar `path` exists + writable).
- Se nenhuma: `report_error(self, "no writable asset library configured. Add one in Preferences > File Paths > Asset Libraries.")` com instrução acionável.
- Ainda melhor: botão "Open Preferences" no panel próximo ao Save Pose, ou auto-criar asset library default em `~/Documents/Blender/Proscenio Pose Library/`.

**Arquivo:** `apps/blender/operators/pose_library.py:23-73` (PROSCENIO_OT_save_pose_asset).

**Severity:** medium -- não crash, mas operator inusável out-of-the-box sem setup explícito que não tá documentado nem na UI. Bloqueia 1.15 items 1 e 2 do MANUAL_TESTING.

---
