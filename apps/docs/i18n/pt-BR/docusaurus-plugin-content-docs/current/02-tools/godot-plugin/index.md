# Plugin do Godot

Um plugin de editor em GDScript: um único [`EditorImportPlugin`](https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html) mais um punhado de builders que transformam um arquivo `.proscenio` numa cena nativa do Godot a cada reimportação.

## O que faz

- **Reimportação para uma cena nativa.** O plugin regenera uma cena (Skeleton2D + Bone2D + Polygon2D / Sprite2D + AnimationPlayer) sempre que um arquivo `.proscenio` entra ou muda no projeto. A reimportação sobrescreve a cena gerada por inteiro - ela reconstrói a árvore do zero e não há diff nem merge contra a saída anterior, porque o `.proscenio` é a fonte e a cena é um artefato gerado que a engine possui. A cena gerada roda com o plugin desinstalado: são nós puros do Godot 4, sem GDExtension e sem dependência de runtime.
- **Segurança da cena-wrapper.** Como a reimportação sobrescreve, as edições nunca vivem dentro da cena gerada; a forma suportada de mantê-las é envolver a cena gerada no seu próprio `.tscn` que a instancia. O wrapper guarda seus scripts, nós extras e o seu próprio `AnimationPlayer`, então ele sobrevive intocado a cada reimportação.
- **Leitura tipada.** O importador lê o documento como um Resource tipado (`ProscenioDocument.from_dict`), checa o `format_version` e constrói a árvore de nós em ordem: esqueleto, atlas, slots antes dos sprites, sprites, animação.

## Como é construído

Pequeno e focado: um plugin de importação e cinco builders, cada um tratando apenas dos tipos de nó que reconhece ao ler o campo `type` em cada elemento. Sem herança nem polimorfismo, apenas funções chamadas em sequência. A camada de leitura tipada é gerada a partir do schema.

## A superfície do importador

O plugin registra um único `EditorImportPlugin` cuja identidade é fixa em código, não configurável por arquivo:

- Ele reivindica a extensão `.proscenio`, apresenta-se no dock **Import** do editor como `Proscenio Character` e assa cada fonte para um `PackedScene` `.scn`.
- Ele declara um preset, `Default`, e não expõe opções por importação - a lista de opções está vazia, então o dock **Import** mostra o preset sem nada a ajustar. Uma reimportação é dirigida inteiramente pelo conteúdo do `.proscenio`, nunca pelas configurações do dock de importação.
- Ele roda na ordem de importação `100`, a ordem de importação de cenas da própria engine, então ele assa depois dos recursos de ordem padrão. Essa ordenação é estrutural: a assadura resolve o atlas e os PNGs por elemento através do `ResourceLoader` contra os arquivos irmãos, e na ordem padrão um `.proscenio` poderia ser assado antes de suas texturas importarem e entregar uma cena com texturas em branco.

## Elementos: malha e sprite

Cada entrada no array `elements` do documento carrega um `type` que seleciona o nó que um builder emite. Uma entrada sem `type` é lida como malha - o padrão vive na camada de leitura tipada, então um elemento sem tipo nunca é descartado.

Um elemento `type: "mesh"` vira um `Polygon2D`. O builder lê:

- `polygon` - o anel de contorno, como pares `[x, y]`.
- `polygons` - arrays opcionais de índices de vértice por face para malhas de múltiplas faces (triangulação de automesh, recortes de múltiplas ilhas); cada face é renderizada através de `Polygon2D.polygons`. Ausente ou vazio significa que o anel `polygon` único é a forma inteira.
- `uv` - coordenadas normalizadas `[0, 1]`, escaladas para pixels de textura em tempo de construção; uma malha sem textura mantém os valores brutos.
- `weights` - pesos de vértice por osso que fazem o skinning da malha (veja Roteamento de slots para como uma malha com skinning é parenteada).
- `texture`, `texture_region`, `modulate`, `z_index` - os campos de aparência compartilhados abaixo.

Um elemento `type: "sprite"` vira um `Sprite2D`. O builder lê:

- `hframes`, `vframes`, `frame` - a grade de spritesheet e a célula exibida.
- `centered`, `offset` - o pivô e o offset em pixels do Sprite2D.
- `texture_region` - um sub-retângulo opcional do atlas, normalizado `[0, 1]` como as UVs de malha e convertido para pixels assim que o tamanho da textura é conhecido. A região só é habilitada quando há uma textura presente e o retângulo em pixels pode ser definido na mesma passada; um sprite sem textura é entregue com a região desabilitada (um retângulo habilitado de área zero não desenharia nada). Quando a região está habilitada, o builder também recorta o filtro de textura na borda da região para que os quadros vizinhos do atlas não vazem na emenda.
- `flip_h`, `flip_v` - as inversões horizontal e vertical exclusivas do Sprite2D.
- `texture`, `modulate`, `z_index` - os campos de aparência compartilhados abaixo.

`modulate` (um tingimento RGBA) e `z_index` (ordem de desenho) se aplicam a ambos os tipos; um `modulate` ausente mantém o branco padrão do Godot. Ambos os tipos resolvem sua textura da mesma forma, em ordem: o próprio nome de arquivo `texture` do elemento carregado ao lado do `.proscenio`; na falta disso, `<nome do elemento>.png` ao lado do `.proscenio` (nome de arquivo por convenção); na falta disso, o `atlas` de todo o documento.

Um `sprite` de múltiplos quadros é o caso por trás da nota de prévia abaixo.

## Roteamento de slots e visibilidade padrão

Slots permitem que vários elementos compartilhem uma âncora e troquem em tempo de execução. O builder de slots roda antes dos builders de elementos, para que os elementos possam ser roteados sob um slot:

- Cada entrada no array `slots` do documento vira um `Node2D` nomeado a partir do slot. Ele é parenteado sob o `Bone2D` correspondente quando o slot nomeia um `bone`, ou sob a raiz `Skeleton2D` quando `bone` está vazio ou o osso nomeado está ausente (um osso ausente registra um aviso e ancora na raiz).
- Todo nome no array `attachments` do slot é mapeado para aquele slot. Um elemento cujo nome está nos attachments de algum slot é reparenteado sob o `Node2D` do slot em vez de ser parenteado a um osso.
- O `default` do slot nomeia o attachment mostrado em repouso: aquele único elemento começa visível, todo outro attachment do slot começa oculto, e uma track de animação `slot_attachment` os alterna em tempo de execução.

Um elemento que não está em nenhum slot recai em ser parenteado sob o `Bone2D` do seu `bone` (ou a raiz do esqueleto quando o osso está ausente), e permanece visível. Uma malha com skinning (uma que carrega `weights`) é a exceção a tudo isso: ela deve ser irmã do `Skeleton2D`, então é parenteada sob o pai do esqueleto (a raiz do rig) e nunca é roteada para um slot nem sob um osso; se o `Skeleton2D` não tiver pai, o builder pula aquela malha e registra um erro em vez de entregar uma forma colapsada.

## Tracks de animação

As animações viram uma `AnimationLibrary` no `AnimationPlayer`, com cada animação do documento contribuindo com seu `length` e sua flag `loop`. O builder emite três tipos de track, selecionados pelo `type` de cada track; um tipo não reconhecido registra um aviso e é pulado:

- `bone_transform` - mira um `Bone2D` e emite até três value tracks, `position`, `rotation` e `scale`. Apenas os canais de fato presentes nas chaves são emitidos, então uma animação só de posição não registra um canal fantasma de rotação que zeraria a pose. A rotação interpola com o modo cúbico ciente de ângulo para dar a volta corretamente em +/-pi; posição e escala usam cúbico simples.
- `sprite_frame` - mira um `Sprite2D` (e apenas um elemento sprite; um alvo não-sprite registra um erro) e faz chaves do seu `frame`. Índices de quadro são discretos, então a track usa interpolação por vizinho mais próximo, sem mistura.
- `slot_attachment` - mira um `Node2D` de slot e emite uma track de visibilidade por attachment filho. A cada chave, o attachment nomeado na chave é o único visível; as trocas são cortes secos (interpolação por vizinho mais próximo), não misturas.

As tracks resolvem seus alvos por nome de folha através de `find_child`, e é por isso que os nomes dos nós são mantidos literalmente (veja Nomes de nós).

## Nomes de nós

Os builders definem o nome de cada nó como o nome do elemento, literalmente. Quando dois irmãos colidem, o `add_child` do Godot acrescenta automaticamente um sufixo numérico (`_001`, `_002`, ...) - esse sufixo é do Godot, não algo que o plugin escreve. O importador nunca desambigua *prefixando* um tipo (nenhum `sprite_foo` / `mesh_foo`), porque as tracks de animação resolvem seus alvos por nome de folha através de `find_child(target, ...)`: um prefixo mudaria o nome que uma track procura e quebraria a busca, enquanto um sufixo numérico só cai em um nome que já era ambíguo.

## A prévia de sprite difere do Blender

Um elemento `sprite` de múltiplos quadros é renderizado no Godot como um `Sprite2D` mostrando um quadro em seu tamanho nativo em pixels (`region_px / hframes`), enquanto o Blender mostra o quad autorado inteiro. Isso é inerente ao modelo, não um bug de importação: prévias pixel-exatas de Blender e Godot não são alcançáveis para sprites de múltiplos quadros por design, o invariante é a geometria e os limites, não os pixels. A regra de autoria que mantém os limites casando, `quad_units = frame_px / pixels_per_unit`, vive com os fixtures (`packages/fixtures/README.md`, "Sprite quads (multi-frame)").

Veja [Arquitetura](../../01-project/01-architecture.md) para como o plugin se encaixa no pipeline, e a Referência de schema para o formato `.proscenio` que ele lê: a forma do [documento](../../content/proscenio/document.mdx), os contratos de campo de [elementos](../../content/proscenio/elements.mdx) e [slots](../../content/proscenio/slots.mdx), e as tracks e chaves de [animação](../../content/proscenio/animation.mdx).
