# UI feedback (defer)

Coisas que **funcionam** mas poderiam melhorar -- UX polish, copy, layout,
defaults. Não são bugs (não vão para `[!]` no MANUAL_TESTING.md), são
melhorias de qualidade. Eventualmente viram issues / spec próprio.

Formato livre. Quando tiver massa crítica de itens, agrupa por área e
abre spec dedicado (ex: `specs/011-ui-polish/`).

## Cross-panel / general

- Drag-and-drop reorder de subpanels (Blender nativo + outros plugins permitem) -- aplicar onde der.
- Tudo aparece aninhado / com recuo dentro de "Pipeline v0.1.0", o que dá impressão de submenu disso. Não faz sentido. Mover versão pro footer / Help panel.

## Active Sprite panel

- Mostrar nome do mesh selecionado no header do panel: "Active Sprite: <obj_name>" em vez de só "Active Sprite".
- Sub-blocks (Sprite Frame / Polygon body, Texture Region, Drive from Bone) deveriam ser collapsibles individualmente (acordeão). Hoje vê tudo de uma vez sem jeito de esconder.
- `Initial frame` field deveria ser clamped em `[0, hframes*vframes-1]` (hoje aceita qualquer int). Pode causar confusão -- usuário digita 99 sem feedback de que só existem 4 frames. Idem `frame` field se editado fora desse range. UI atual: `min=0` está, `max` falta (ou usa `soft_max`).
- `Initial frame` label confunde no contexto de animação. Quando usuário keyframa o field, ele NÃO é "initial" -- é THE frame value sendo animado. Renomear label pra `Frame` (mais simples, alinha com Sprite2D do Godot). Description pode manter "frame index at rest pose; animation tracks override at runtime" -- explica o duplo papel sem polluir a label. File: `apps/blender/properties/object_props.py:124`.

## Active Slot panel

- (vazio)

## Skeleton panel

- Visualização atual está ruim:
  - `length` field é inútil, não serve de nada -- remover
  - Em vez de mostrar parent como string, mostrar hierarquia indentada (como Blender outliner nativo)
  - Click no bone na lista deveria selecionar o bone no Blender (3D viewport / pose mode)
  - Ou permitir rename inline
- Hoje o panel é só inspect read-only, não serve de muito

## Outliner panel

- Recursos OK no geral, ainda enxuto
- Favoritos: útil, manter
- Alinhamento dos nomes das meshes está centralizado -- horrível. **Regra geral pra todas as listas: alinhar à esquerda**.

## Animation panel

- (a testar)

## Atlas panel

- (a testar)

## Validation panel

- (a testar)

## Export panel

- (a testar)

## Help / status badges

- Help panel completamente inútil e ilegível como tá -- substituir por botão único que abre popup
- Versão (Pipeline v0.1.0) poderia ficar aqui no Help panel
- Adicionar botão "GitHub" / link pro repo

## Diagnostics panel

- Agregar com Help -> "Help & Diagnostics" panel único
