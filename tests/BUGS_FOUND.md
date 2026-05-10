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

### Wrapper .tscn: script path falta `/godot/` em fixtures legacy

**Repro:** copiar `examples/<fixture>/` para `res://<fixture>/` em projeto Godot, abrir `*.tscn` -- script ext_resource quebra com "file not found".

**Causa:** `BlinkEyes.tscn`, `Doll.tscn`, `SharedAtlas.tscn` declaram `Script path="res://<fixture>/<File>.gd"`, mas o `.gd` mora em `<fixture>/godot/<File>.gd`. Path correto seria `res://<fixture>/godot/<File>.gd` (como faz `SimplePSD.tscn`).

**Fix:** trocar 3 paths nos `.tscn` afetados:

- `examples/blink_eyes/godot/BlinkEyes.tscn`: `res://blink_eyes/BlinkEyes.gd` -> `res://blink_eyes/godot/BlinkEyes.gd`
- `examples/doll/godot/Doll.tscn`: `res://doll/Doll.gd` -> `res://doll/godot/Doll.gd`
- `examples/shared_atlas/godot/SharedAtlas.tscn`: `res://shared_atlas/SharedAtlas.gd` -> `res://shared_atlas/godot/SharedAtlas.gd`

`mouth_drive` já corrigido in-place (PR #38, post-CodeRabbit). `simple_psd` já estava correto.

**Severity:** medium -- wrapper scenes não funcionam out-of-the-box; usuário precisa fix manual ao copiar pra projeto Godot.

### blink_eyes fixture: image path absoluto bake'a no .blend

**Repro:** abrir `examples/blink_eyes/blink_eyes.blend` em outra máquina ou após mover o repo -- material reporta image not found.

**Causa:** `scripts/fixtures/blink_eyes/build_blend.py:113`:

```python
tex.image = bpy.data.images.load(str(SHEET_PATH), check_existing=True)
```

`SHEET_PATH` é `Path` absoluto (REPO/examples/...). Blender salva absolute filepath no .blend datablock. Outro path = quebra.

**Fix proposto:** após `load()`, chamar `tex.image.filepath = bpy.path.relpath(str(SHEET_PATH))`. Ou load direto com `//pillow_layers/eye_spritesheet.png` se BLEND já estiver salvo.

**Severity:** medium -- fixture quebra cross-machine. CI passa porque o golden test não renderiza, só compara writer output.

**Provável que o mesmo problema afete:** `simple_psd/build_blend.py`, `slot_cycle/build_blend.py`. Auditar.

### (slot) Reproject UV: segunda chamada lenta + Y invertido

**Repro:** Active Sprite > polygon mode > "Reproject UV" duas vezes seguidas.

**Sintoma 1 (perf):** segunda chamada demora vários segundos como se fosse crashar.

**Sintoma 2 (orientação):** UV resultante fica de cabeça pra baixo no UV editor (V invertido).

**Suspeita 1:** mode_set OBJECT<->EDIT chained com smart_project + restore loop pode estar deselecionando todo mundo + reselecionando, causando spike de cost. Ou `bpy.ops.uv.smart_project` cacheia algo problematico.

**Suspeita 2:** smart_project usa face normal como projeção; head do doll tem normal apontando "pra cima" (Y axis no Blender 2D plane vira V invertido em UV space).

**Arquivo:** `apps/blender/operators/uv_authoring.py:39-66` (`PROSCENIO_OT_reproject_sprite_uv`).

**Severity:** low -- operacional, não crash. UV invertida é workaround manual ou parameter.

---
