# UI feedback (defer)

Coisas que **funcionam** mas poderiam melhorar - UX polish, copy, layout,
defaults. Não são bugs (não vão para `[!]` no manual-testing.md), são
melhorias de qualidade. Eventualmente viram issues / spec próprio.

Formato livre. Quando tiver massa crítica de itens, agrupa por área e
promove pro backlog.

A reconciliação de 2026-06-11 das specs 027-035 removeu os itens já trabalhados (resolvidos saíram; adiados / gated / dropados foram pro [`deferred.md`](deferred.md), [`gated.md`](gated.md), [`dropped.md`](dropped.md)). O que resta aqui é polish ainda não atacado (a maioria mora na spec ui-help-surfaces).

## Cross-panel / general

- Drag-and-drop reorder de subpanels (Blender nativo + outros plugins permitem) - aplicar onde der.

## Active Sprite panel

- Mostrar nome do mesh selecionado no header do panel: "Active Sprite: <obj_name>" em vez de só "Active Sprite".
- `Initial frame` field deveria ser clamped em `[0, hframes*vframes-1]` (hoje aceita qualquer int). Pode causar confusão - usuário digita 99 sem feedback de que só existem 4 frames. Idem `frame` field se editado fora desse range. UI atual: `min=0` está, `max` falta (ou usa `soft_max`).
- `Initial frame` label confunde no contexto de animação. Quando usuário keyframa o field, ele NÃO é "initial" - é THE frame value sendo animado. Renomear label pra `Frame` (mais simples, alinha com Sprite2D do Godot). Description pode manter "frame index at rest pose; animation tracks override at runtime" - explica o duplo papel sem polluir a label. File: `apps/blender/properties/object_props.py:124`.
- **`Centered` vs origin do PS - clarificar / documentar.** `centered` (`object_props.py:104`, `name="Centered"`, "Whether the Sprite2D's offset centers on its origin") só existe pro element_type `sprite`, NÃO pro `mesh`: Polygon2D não tem conceito de "centered" (os vertices carregam a posição). Confunde porque a origem do objeto vem do `[origin]` do PS - `centered` (pivot do Sprite2D no Godot) e origin (pivot do objeto vindo do PS) são coisas separadas. Documentar a distinção no help do Active Sprite e considerar se `centered` deveria ser derivado da origin importada em vez de toggle manual.

## Outliner panel

- Recursos OK no geral, ainda enxuto
- Falta hierarquia / árvore indentada (armature > slots > attachments, meshes parented a bones) - hoje é lista plana. Mesma pegada do pedido do Skeleton panel (hierarquia indentada estilo outliner nativo).
- Favoritos: útil, manter
- Alinhamento dos nomes das meshes está centralizado - horrível. **Regra geral pra todas as listas: alinhar à esquerda**.

## Materials panel (proposed - doesn't exist yet)

Sem panel dedicado pra inspeção / configuração de materials. Hoje usuário caça pelos materiais no Shader Editor ou Properties > Material per-objeto. Sugestão: novo subpanel **Materials** com:

- **Inspeção:** lista materials da cena (ou filtrada por seleção). Mostra: nome, qtd users, qtd Image Texture nodes, image filepath(s).
- **Cross-material quick config:** botões que aplicam a todos / seleção / regex:
  - **Interpolation toggle:** Closest / Linear / Cubic / Smart - aplica a TODOS Image Texture nodes dos materials selecionados. Resolve o caso "import Photoshop traz tudo Linear, eu quero Closest pixel-art".
  - **Blend mode toggle:** Opaque / Clip / Hashed / Blend - aplica a TODOS materials. Crítico: importer hoje seta `HASHED` por default, que renderiza dither stipple em pixels semi-transparentes. Pixel art quer `CLIP` (binary cutoff). Bulk toggle resolve.
  - **Extension mode:** Repeat / Extend / Clip - mesmo padrão.
  - **Alpha mode:** Straight / Premultiplied.
  - **Alpha threshold slider:** 0..1, default 0.5 - visível para `CLIP` blend mode.
  - **Mipmaps on/off**, **Anisotropic filtering** (futuro).
- **Bulk image path fix:** detectar broken image filepaths + botão "Repair" que abre file picker pra resolver missing texture.
- **Material report:** quantos materials únicos, quantos compartilham mesma imagem (atlas candidates), quantos com `material_isolated=True`.

**Motivação:** Proscenio assume convenções (Closest, edge-padding, pixel-art conventions) mas não força nem expõe controle. Usuário tem que conhecer Blender deep pra ajustar. Panel dedicado dá autonomia + visibilidade.

**Alternativa low-effort se panel completo for overkill:** adicionar uma seção "Material setup" no Active Sprite panel com checkbox `Pixel art` - quando ligado, seta Closest interpolation + nearest filter no Image Texture node do material ativo. Toggle one-click pra caso comum.

## Validation panel

- **Click em issue de objeto hidden seleciona no outliner mas viewport não reflete.** Comportamento Blender padrão, mas confuso pro usuário que clica achando que vai ver o offending object destacado. Sugestão: `proscenio.select_issue_object` operator deve também `hide_viewport=False` + frame view na target (View > Frame Selected). Workaround: usuário precisa unhide manual antes da seleção fazer sentido visual.

## Help / status badges

- Help panel completamente inútil e ilegível como tá - substituir por botão único que abre popup

## Diagnostics panel

- Agregar com Help → "Help & Diagnostics" panel único
