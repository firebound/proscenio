# Elemento

Configurações por elemento que o escritor lê para a malha ativa. O painel pai contém o seletor de tipo de elemento e um ajuste de ordem de desenho; o corpo se divide em subpainéis. O cabeçalho lê `Element: <name>` enquanto há espaço e cai para `Element` num painel estreito.

O **tipo de elemento** decide o nó do Godot: `Mesh` exporta um `Polygon2D` (um recorte deformável com UVs e pesos), `Sprite` exporta um `Sprite2D` (uma spritesheet fatiada por uma grade hframes x vframes). `Depth offset` é um ajuste manual de ordem de desenho em unidades de camada do PSD, somado por cima da profundidade da ordem do PSD antes de virar o `z_index` do Godot - um valor positivo empurra o elemento para trás, um valor negativo o puxa para frente, então você pode reordenar um plano sem reimportar. Uma malha autorada à mão que ainda não tem dados de elemento do Proscenio mostra um botão `Incorporate as Element` que a adota com um padrão Mesh ou Sprite. O tipo de elemento fica travado enquanto você está no modo de Pintura de Peso. Problemas de validação do elemento ativo aparecem no rodapé do painel.

## Malha Ativa {#active-mesh}

Mostrado quando o tipo de elemento é Mesh. A malha exporta como um Polygon2D - seus vértices carregam suas próprias posições, então a origem do Blender é assada na exportação. O corpo mostra as contagens de polígonos e de grupos de vértices e três controles:

- `Reproject UV` reconstrói o layout de UV da malha a partir da sua geometria (uma projeção planar - U segue X, V segue Z) para a textura se alinhar de novo depois que você move vértices.
- `Isolated material` mantém o material próprio deste sprite ao empacotar, em vez de vinculá-lo ao material compartilhado do atlas empacotado - para sprites de efeito que precisam do próprio shader.
- `Exclude from atlas` mantém o sprite totalmente fora do [Pack Atlas](08-atlas.md): suas UVs e material ficam intocados e ele embarca sua própria textura.

## Sprite Ativo

Mostrado quando o tipo de elemento é Sprite. Apenas os metadados da spritesheet são exportados, não a geometria do quad:

- **hframes / vframes** - a grade da spritesheet (colunas x linhas).
- **frame** - a célula mostrada na pose de descanso; as trilhas de animação a sobrescrevem.

O sprite está sempre centralizado no seu nó - a matemática de deslocamento do escritor assume isso, então esta é uma constante interna fixa em vez de um toggle. A tag `[origin]` do PSD define o pivô de um sprite; ela é ignorada numa Mesh.

Abaixo dos campos, uma leitura reporta o tamanho do atlas vinculado, o tamanho da região (atlas inteiro, ou o retângulo manual) e o tamanho resultante por quadro para a grade atual.

### Material Preview

A subcaixa **Material Preview** hospeda `Setup Preview` / `Remove Preview`. `Setup Preview` insere um grupo de nós `SpriteFrameSlicer` entre os nós TexCoord e ImageTexture do material e alimenta suas entradas a partir de `frame` / `hframes` / `vframes`, para o Material Preview mostrar a célula ativa no quad em vez do atlas inteiro e acompanhar o valor ao vivo conforme `frame` anima. É idempotente - reexecutar atualiza um fatiador existente em vez de duplicá-lo. `Remove Preview` desconecta o fatiador e remove os drivers. O fatiador é invisível sob os motores Solid / Workbench (eles só honram `diffuse_color`), e ele assume células contíguas - atlas com espaçamento entre células ainda não são suportados.

## Attach to Bone

Mostrado para um elemento sprite. Parenteia rigidamente o sprite a um único osso - a maneira não-slot de fazer um sprite seguir um osso, sem troca. `Parent To Bone` preenche antecipadamente o osso de pose ativo quando há um atual, senão passa por um diálogo de escolha; `Clear Bone Parent` o desanexa. Exporta como um `Sprite2D` parentado a esse `Bone2D`. Um osso deitado no plano da imagem gira o sprite rígido para fora do plano da câmera - o painel avisa e o aponta para um [slot](03-slots.md) para um seguimento plano em qualquer osso.

## Região de Textura

Qual parte da textura o elemento amostra. **Auto** lê a região a partir dos limites de UV da malha na exportação (para um sprite, a região é omitida e o atlas inteiro é usado); **Manual** lê `region_x/y/w/h` literalmente para o fatiamento do atlas. Numa malha em modo Manual, `Snap to UV bounds` preenche os quatro campos a partir do layout de UV atual. Reproject UV muda as UVs; a região só as lê.

## Drive from Bone {#drive-from-bone}

Conecta um driver do Blender entre um osso de pose e uma propriedade `proscenio.*` de um sprite - bom para mudanças que variam continuamente com a rotação (rolagem de íris, um flag de limiar). Para uma troca limpa do tipo um-ou-outro, use um [slot](03-slots.md) em vez disso.

Escolha a propriedade `Target` (índice de quadro, ou um canal de região), a `Armature` de origem, o `Bone` e o `Axis`. O eixo assume por padrão `Bone Rot Y` (rotação em torno do Y do mundo, o eixo da câmera front-ortho - o ângulo 2D visível); os outros canais de rotação e de localização também são oferecidos. Por padrão, o driver é um mapa linear com clamp: `In Min` / `In Max` são o intervalo do canal do osso e `Out Min` / `Out Max` o intervalo do valor-alvo, com o intervalo de entrada padrão abrangendo rotação de negativo a positivo, para que um osso girado para trás não seja limitado a zero. O toggle `Advanced expression` troca os dois intervalos por uma expressão crua sobre `var` (o canal do osso). Uma linha `Value` ao vivo lê de volta o alvo controlado. Reexecutar no mesmo alvo substitui seu driver em vez de duplicá-lo; a lista de drivers existentes abaixo os remove um de cada vez.
