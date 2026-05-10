# UI feedback (defer)

Coisas que **funcionam** mas poderiam melhorar -- UX polish, copy, layout,
defaults. Não são bugs (não vão para `[!]` no MANUAL_TESTING.md), são
melhorias de qualidade. Eventualmente viram issues / spec próprio.

Formato livre. Quando tiver massa crítica de itens, agrupa por área e
abre spec dedicado (ex: `specs/011-ui-polish/`).

## Cross-panel / general

- Drag-and-drop reorder de subpanels (Blender nativo + outros plugins permitem) -- aplicar onde der.
- Tudo aparece aninhado / com recuo dentro de "Pipeline v0.1.0", o que dá impressão de submenu disso. Não faz sentido. Mover versão pro footer / Help panel.
- **Nomenclatura: "sprite" é sobrecarregado** -- herdado do COA Tools, mas tecnicamente "sprite" no contexto Godot/2D-cutout = `Sprite2D` (sprite_frame mesh com spritesheet), enquanto "polygon" mesh é uma classe **diferente** (`Polygon2D` com vertex weights). Hoje o projeto chama ambos de "sprite" indiscriminadamente: PG `sprite_type`, panel "Active Sprite", `sprites[]` no `.proscenio`, etc. Confunde leitor que conhece os termos Godot. **Proposta:** renomear pra termo neutro tipo `mesh` / `cutout_mesh` / `proscenio_mesh`. `sprite_type` vira `mesh_type` com valores `polygon` / `sprite_frame`. Operação grande (toca PG, panel, writer, schema, importer) -- merece spec dedicada com migration path.

## Active Sprite panel

- Mostrar nome do mesh selecionado no header do panel: "Active Sprite: <obj_name>" em vez de só "Active Sprite".
- Sub-blocks (Sprite Frame / Polygon body, Texture Region, Drive from Bone) deveriam ser collapsibles individualmente (acordeão). Hoje vê tudo de uma vez sem jeito de esconder.
- `Initial frame` field deveria ser clamped em `[0, hframes*vframes-1]` (hoje aceita qualquer int). Pode causar confusão -- usuário digita 99 sem feedback de que só existem 4 frames. Idem `frame` field se editado fora desse range. UI atual: `min=0` está, `max` falta (ou usa `soft_max`).
- `Initial frame` label confunde no contexto de animação. Quando usuário keyframa o field, ele NÃO é "initial" -- é THE frame value sendo animado. Renomear label pra `Frame` (mais simples, alinha com Sprite2D do Godot). Description pode manter "frame index at rest pose; animation tracks override at runtime" -- explica o duplo papel sem polluir a label. File: `apps/blender/properties/object_props.py:124`.
- `Drive from Bone` -- expression default `var` é misleading pra o caso `Frame index`. Bone rotation em radianos típica varia [-pi, pi], mas frame range é [0, hframes*vframes-1]. Expression `var` faz negativos clamparem em 0 e valores acima de N-1 clamparem no max -- usuário rotaciona bone e parece que driver não funciona.
- **Expression como string crua é hostil** pra usuário não-programador: `var * 0.5 + 0.3` parece números mágicos. Usuário tem que entender que `var` = rotação em radianos e fazer álgebra mental pra mapear [bone_min, bone_max] em [prop_min, prop_max]. Animator não pensa nisso -- pensa em "quando bone rotaciona deste jeito, sprite mostra essa faixa".
- **Proposta UX:** substituir Expression por 2 ranges editáveis:
  - "Bone rotation range" -- 2 sliders / fields: `from -90°` to `+90°`
  - "Sprite property range" -- 2 sliders: `from 0` to `3` (pra Frame index, com default = full range; pra Region X, default = `0` to `1`)
  - Auto-genera expression linear: `(var - bone_min) / (bone_max - bone_min) * (prop_max - prop_min) + prop_min`
  - Modo "Advanced" colapsável que expõe a string crua pra power users que querem expressões custom (não-lineares, branching, etc).
- **Bonus:** preview HUD na panel mostrando "agora bone está em 0.78 rad (45°) -> property = 2 (de 0..3)" enquanto rotaciona.
- `Drive from Bone` debug é dolorido. Pra inspecionar driver value live precisa abrir Drivers Editor em outra janela / area, e ao mover seleção pra entrar em Pose Mode, perde o foco no fcurve no Drivers Editor (precisa re-clicar nele). Alternativas pro Active Sprite panel:
  - Quando driver existe em `proscenio.<target>`, mostrar inline: "Driver from `<armature>:<bone>.<axis>` -- value: 0.78 rad (45°) -> frame: 3".
  - Quick action button "Inspect Driver" abre uma popup compacta com expression, variable value, current driver result.
  - Botão "Reset Driver" (apaga + recria) pra iterar em expressions sem mexer no Drivers Editor.
- **Mesh <-> Pose Mode swap dolorido**: pra animar drivers, usuário precisa selecionar bone em Pose Mode na armature -> active object muda -> Active Sprite panel some (porque depende do mesh estar active). Não há jeito visual fácil de "ver os campos do sprite" enquanto manipula o bone. Sugestões:
  - Mostrar `Sprite watched: <obj>` no header do Drive from bone box quando active object é armature/pose bone que tem driver alimentando algum `proscenio.*` de outro mesh.
  - Pin / sticky panel mode -- usuário marca `Active Sprite: locked to <obj>` e o painel para de seguir active object.
  - Side-by-side debug HUD: pequeno overlay no viewport com `frame: 2` / `region_x: 0.45` enquanto bone rotaciona.

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
