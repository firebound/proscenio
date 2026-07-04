# Blender: configuração e animação

O Blender é o hub do pipeline: ele importa as camadas do Photoshop, você faz o rig e o skinning delas aqui, e ele exporta o `.proscenio` para o Godot.

Na [Viewport 3D](https://docs.blender.org/manual/en/latest/editors/3dview/introduction.html), abra a [Barra Lateral](https://docs.blender.org/manual/en/latest/editors/3dview/sidebar.html) com <kbd>N</kbd> e mude para a aba **Proscenio** - cada subpainel abaixo vive ali.

Os subpainéis do Proscenio são contextuais e consultam a seleção atual.

## Importe o manifesto do Photoshop

1. *Abra o `.blend` alvo*: o seu arquivo Blender para este personagem.

2. *Importe o manifesto*: no painel **Pipeline**, clique em `Import Photoshop Manifest` e aponte para o manifesto que você exportou.

Cada camada se torna um sprite quad (pivô, região de atlas e nomenclatura já preenchidos de acordo com o que foi feito no lado do Photoshop). A importação também constrói uma armadura provisória chamada `<psd>.rig` com um único osso e torna cada malha filha dela, então a figura se move como uma peça só - as malhas ainda não têm pesos para dobrar (essa é a etapa de skinning abaixo).

O diálogo de importação tem duas opções que vale definir deliberadamente:

- `Placement`: `Landed (Feet on Z=0)` (padrão; corresponde à convenção de pivô nos pés do Godot) ou `Centered (Canvas at World Origin)` quando você precisa alinhar várias importações em uma cena.

- `Root Bone Name`: nomeia aquele único osso da armadura (padrão `root`; substitua por `spine` ou a sua própria convenção).

> [!NOTE]
> Criando malhas à mão em vez de importar? Modele-as diretamente, depois retome a partir de [Defina o tipo de cada elemento](#set-each-elements-type) - o resto do fluxo do Blender é idêntico.

## Construa o esqueleto

Adicione os ossos reais à armadura importada. O Quick Armature é o caminho rápido; você também pode adicionar ossos no Modo de edição como em qualquer rig do Blender.

1. *Inicie a sessão modal*: `Skeleton > Quick Armature` alinha à vista Frontal Ortográfica e permite desenhar ossos direto na viewport.

2. *Desenhe cada osso*: com um **pressionar, arrastar, soltar** (cabeça → cauda), a sessão permanece ativa para você assentar uma cadeia inteira e depois confirmar.

Enquanto a sessão está ativa, uma folha de referência na tela espelha estas entradas:

| Entrada | O que faz |
| - | - |
| arrastar <kbd>LMB</kbd> | Novo osso, `connected` - encadeia no osso anterior (a cabeça do novo osso se encaixa na cauda do pai) |
| arrastar <kbd>Shift</kbd> + <kbd>LMB</kbd> | Novo osso, `unparented` - independente, sem pai |
| arrastar <kbd>Alt</kbd> + <kbd>LMB</kbd> | Novo osso, `disconnected` - filho do osso anterior, mas a cabeça fica onde você pressiona (deixa um vão) |
| <kbd>X</kbd> / <kbd>Z</kbd> | Alterna o travamento de eixo - restringe o arraste àquele eixo |
| <kbd>Ctrl</kbd> (enquanto arrasta) | Encaixe na grade - posiciona cabeça e cauda no incremento de encaixe |
| <kbd>Ctrl+Z</kbd> / <kbd>Ctrl+Shift+Z</kbd> | Desfaz / refaz o último osso nesta sessão |
| <kbd>Enter</kbd> | Confirma e sai |
| <kbd>Esc</kbd> / clique-direito | Cancela e sai |

- A tabela pressupõe o comportamento de **cadeia** padrão. Desligue `default_chain` nas opções do Quick Armature e o arraste simples com <kbd>LMB</kbd> passa a ser sem pai, enquanto o arraste com <kbd>Shift</kbd> + <kbd>LMB</kbd> conecta em vez disso; toda outra entrada permanece inalterada.
- Novos ossos recebem um nome automático: o prefixo mais um índice preenchido com zeros começando em zero (`qbone.000`, `qbone.001`, ...). O prefixo é `qbone` por padrão e é configurável nas mesmas opções.

## Modele malhas deformáveis (opcional)

Um quad plano importado não consegue dobrar, então precisamos adicionar vértices para obter deformação cutout. Quanto mais vértices, mais suave a dobra - mas também mais pesado o rig. A receita exata depende da arte e da animação, mas aqui estão alguns pontos de partida:

Para obter deformação cutout, transforme o sprite em uma malha mais densa com o painel **Geração de malha**:
`Automesh from Alpha` (de uma vez) ou `Automesh Interactive` (prévia modal).

Isto é independente do esqueleto - o automesh apenas remodela a geometria, não toca nos ossos. Pule-o para sprites que só precisam de movimento rígido ou de troca de sprite-frame.

## Vincule e pinte os pesos

A vinculação liga os vértices de cada malha aos ossos para que a malha siga a pose.

1. *Defina a armadura-alvo*: no subpainel **Esqueleto**, escolha a sua armadura como armadura ativa - a vinculação da Pintura de peso tem ela como alvo.

2. *Vincule*: no subpainel Vincular do painel **Pintura de peso**, clique em `Bind to Target Armature` (escolha um modo de vinculação se necessário).

   Alternativa nativa: selecione as malhas, pressione <kbd>Ctrl+P</kbd>, depois `Armature Deform`.

3. *Pinte*: clique em `Edit Weights` para o modal de pintura de peso no painel, ou use o próprio Modo de Pintura de Peso do Blender.

   Qualquer caminho produz grupos de vértices nomeados a partir dos ossos. Consulte o [fluxo de trabalho do Blender](../02-advanced/02-blender.md) para a receita completa de skinning (densidade do automesh, modos de vinculação, transferência de pesos, instantâneos).

> [!WARNING]
> **Os nomes dos ossos são o contrato.** O escritor exporta um peso apenas quando o nome de um grupo de vértices corresponde exatamente ao nome de um osso.
>
> O Blender os sincroniza em uma direção: renomeie um **osso** e o Blender renomeia automaticamente o grupo de vértices correspondente em toda malha que aquela armadura deforma (comportamento padrão). O inverso não é verdadeiro - renomear um **grupo de vértices** não toca no osso, então isso quebra a correspondência e o peso é descartado silenciosamente.
>
> Então: nomeie os ossos de forma significativa desde cedo e sempre renomeie pelo lado do osso, nunca pelo grupo de vértices. A renomeação automática só alcança as malhas que a armadura deforma - uma malha que ainda é apenas filha por objeto (como as malhas importadas são até você vinculá-las) é ignorada, então renomeie o grupo de vértices dela à mão. Consulte as [regras de pesos de skinning](../../../specs/decisions.md#skinning-weights-export).

## Defina o tipo de cada elemento {#set-each-elements-type}

Camadas importadas chegam com o tipo já definido a partir do Photoshop se você as marcou corretamente, mas malhas criadas à mão podem ser definidas aqui.

Selecione uma malha e trabalhe no painel **Elemento** - ele hospeda o seletor de tipo de elemento, e os subpainéis por tipo (Malha ativa / Sprite ativo), Região de textura e Drive from Bone vivem sob ele.

1. *Escolha o tipo de elemento*: há dois, e cada um mapeia para um nó do Godot:
   - `Mesh` (padrão) - uma malha cutout que exporta para um [`Polygon2D`](https://docs.godotengine.org/en/stable/classes/class_polygon2d.html).
   - `Sprite` - um quad rígido que exporta para um [`Sprite2D`](https://docs.godotengine.org/en/stable/classes/class_sprite2d.html). Para um `Sprite`, o subpainel **Sprite ativo** define `hframes` / `vframes` / `Frame`; o fatiador de prévia no painel mostra a célula escolhida na viewport 3D sem exportar.

   Uma camada marcada com `[mesh]` no Photoshop chega aqui como um `Mesh` - "mesh" é apenas um sinalizador de criação, não um terceiro tipo.

2. *Defina a região de textura*: no subpainel **Região de textura**, `auto` calcula a região a partir dos limites de UV na exportação; `manual` permite fatiar um atlas à mão. Clique em `Snap to UV bounds` para preencher a região a partir do UV atual.

## Refine o rig (opcional)

Estes dão o polimento no rig e são todos opcionais.

- *Controle uma propriedade de sprite a partir de um osso (troca suave)*: use o subpainel **Drive from Bone** para conectar um driver do Blender entre um osso de pose e uma propriedade de sprite - bom para mudanças que variam continuamente com a rotação, por exemplo.

- *Auxiliares de pose*: no Modo de pose, o subpainel **Esqueleto** adiciona `Bake Current Pose`, `Toggle IK` e `Save Pose to Library`, todos do lado do Blender. `Bake Current Pose` insere quadros-chave em cada osso no quadro atual - essas chaves exportam como quaisquer outras, então é assim que você fixa um quadro posado (ou guiado por IK) na animação. `Toggle IK` e `Save Pose to Library` permanecem no Blender: um asset de pose simplesmente vai parar no seu Asset Browser.

> [!NOTE]
> IK não faz round-trip de volta para o Godot. `Toggle IK` é um auxiliar de pose do Blender - o escritor exporta quadros-chave de osso brutos, não constraints, e a cena gerada usa apenas nós nativos. Para levar movimento guiado por IK ao Godot, primeiro asse o resultado do IK em quadros-chave de osso (o Bake Action do Blender com visual keying), ou reconstrua o IK no motor após a importação com os modificadores de IK de esqueleto 2D embutidos do Godot.

## Troque variantes com slots (opcional) {#swap-variants-with-slots-optional}

Use um slot quando um ponto de fixação alterna entre N variantes discretas: espada / cajado / mão vazia, boca aberta / fechada, sobrancelha para cima / para baixo, uma troca de expressão. O slot é dono das variantes; você alterna entre elas com um único índice.

1. *Crie o slot*: selecione as malhas que você quer envolver, depois `Skeleton > Create Slot`. → Um Vazio de slot é ancorado sob o osso ativo, e as malhas selecionadas se tornam seus anexos.

2. *Escolha a variante padrão*: no subpainel **Slot ativo**, escolha qual anexo fica visível no carregamento da cena (o ícone SOLO).

3. *Anime a troca*: insira quadros-chave em `proscenio_slot_index` no slot para alternar os anexos ao longo do tempo. → Na importação, o Godot expande aquela única trilha em trilhas de visibilidade por anexo.

Consulte [`examples/generated/slot_cycle/`](../../../examples/generated/slot_cycle/) para o fixture mínimo de slot.

> [!TIP]
> **Troca suave vs. troca dura.** `Drive from Bone` é para mudanças contínuas e guiadas. Para uma troca **isto/ou aquilo** limpa - antebraço frente/trás, espada/cajado, sobrancelha cima/baixo - use [slots](#swap-variants-with-slots-optional) em vez disso.

## Anime

Anime com as ferramentas nativas do Blender (Editor de Ações, Dopesheet, drivers).

O Proscenio não cria animação - o subpainel **Animação** é um resumo somente leitura das ações que o escritor vai exportar. Cada Ação se torna uma entrada na exportação; strips de NLA ainda **não** são consumidos, então asse tudo em uma única Ação primeiro. Índices de slot e propriedades de sprite guiadas animam na mesma linha do tempo.

## Empacote o atlas (opcional)

Empacotar é opcional. Pule-o e cada sprite mantém a sua própria textura - o PNG por camada, ou o spritesheet composto para um `Sprite` de múltiplos quadros - e a exportação referencia essas como estão.

Se você empacotar, o subpainel **Atlas** compõe as texturas em uma única folha: `Pack Atlas` constrói o atlas e reescreve o `texture_region` de cada sprite, `Unpack Atlas` reverte isso, e `Apply Packed Atlas` revincula a um atlas que você empacotou externamente. `Pack Atlas` pega cada elemento com uma textura - `Mesh` e `Sprite` igualmente - não há como um sprite individual sair do atlas em si. Defina `Isolated material` em um sprite para manter o seu próprio shader (aditivo, personalizado); ele ainda desenha a partir do atlas empacotado, apenas não através do material compartilhado.

Um `Sprite` de múltiplos quadros empacotado dessa forma ainda fatia corretamente: a folha inteira permanece como um bloco contíguo no atlas (os UVs do quad do sprite cobrem a folha completa, então o empacotador a pega inteira), e o Godot subdivide aquele bloco - o `region_rect` do sprite - por `hframes` / `vframes`, não o atlas inteiro. Então os índices de `frame` permanecem idênticos aos do Blender; uma boca de 4 quadros ainda são os quadros 0-3 do seu próprio bloco, onde quer que aquele bloco tenha ido parar.

A exportação referencia qualquer atlas que esteja empacotado na cena em vez de gerar um.

## Encontre coisas em rigs grandes

Rigs grandes afogam o outliner nativo do Blender - só o fixture do boneco tem 64 ossos e 22 malhas de sprite. O subpainel **Outliner** dá uma lista plana centrada em sprites com um filtro de substring e um alternador de favoritos; clique em uma linha para tornar aquele objeto ativo.

## Valide e exporte

1. *Valide*: `Pipeline > Validate` verifica cada sprite contra a armadura, o atlas e os campos obrigatórios. → Qualquer erro bloqueia a exportação até você corrigi-lo.

2. *Exporte*: `Pipeline > Export (.proscenio)` escreve o JSON `.proscenio` ao lado do `.blend` de origem. Em salvamentos posteriores, `Re-export` reutiliza o caminho fixado sem diálogo.
