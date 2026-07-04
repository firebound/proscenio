# Photoshop

O guia aprofundado do lado do Photoshop: como criar um `.psd` para que ele exporte de forma limpa, o que as tags entre colchetes fazem e como se comporta reimportar no Blender após edições. Para a versão rápida, consulte o [passo a passo básico](../01-basic/01-photoshop.md).

## O contrato

O pipeline corre em **um sentido**. Suas camadas de PSD se tornam um JSON de manifesto mais PNGs por camada; o Blender lê o manifesto e carimba planos que você pode rigar. O PSD continua sendo a fonte da verdade para a arte raster, e você regenera o manifesto toda vez que exporta - não há round-trip de Blender para PSD ([por quê](#why-there-is-no-blender-to-psd-round-trip)).

Regra prática: edite o PSD, nunca o manifesto à mão, e reimporte no Blender para aplicar suas mudanças.

## Layout do projeto

Quando você exporta, o plugin escreve o manifesto e os PNGs por camada na pasta que você escolhe. O Blender adiciona a pasta `_spritesheets/` depois, na importação - é lá que ele compõe cada grupo de spritesheet em uma única folha, não do lado do Photoshop:

```text
<your project>/
├── firebound.psd                    your hand-authored source
└── firebound/                       export target (you pick it in the folder picker)
    ├── manifest.json                written by the plugin
    ├── images/                      written by the plugin
    │   ├── torso.png                one per polygon layer
    │   └── eye/
    │       ├── 0.png                one per frame of a spritesheet group
    │       └── 1.png
    └── _spritesheets/               created by Blender on import
        └── eye.png                  the composed sheet per spritesheet group
```

No Blender, abra o `.blend`, clique em `Import Photoshop Manifest` no subpainel **Sprite ativo** e aponte para `manifest.json`. Você recebe um plano por camada com materiais conectados e um único osso `root` - pronto para rigar e animar.

## Reimportando após edições no PSD {#re-importing-after-psd-edits}

Quando você edita o PSD, reexporta e roda a importação de novo no Blender, ela não duplica nada: encontra cada plano existente pela sua tag e o atualiza no lugar. A tag é uma propriedade personalizada oculta, `proscenio_import_origin = "psd:<layer_name>"`, comparada com cada camada (o nome do objeto é ignorado - consulte [Três nomes, um vínculo](#three-names-one-link)). Uma camada que ainda existe é atualizada, uma nova camada ganha um plano novo, e o plano de uma camada removida é deixado em paz e registrado como órfão em vez de deletado.

A parte importante é o que "atualizar no lugar" faz com cada plano, e isso depende de se o posicionamento da camada (seu tamanho e deslocamento) mudou:

- **Mesmo posicionamento** - o caso comum de retoque de arte (você repintou dentro da mesma caixa). A malha é deixada totalmente intacta: a densificação do Automesh e os pesos pintados ficam exatamente como estavam, e apenas a textura é atualizada para a nova arte.
- **Posicionamento alterado** - a camada foi redimensionada ou movida. A importação **reconstrói a malha** de volta a um quad plano no novo tamanho e UVs, mas os pesos pintados não são perdidos: eles vivem na Propriedade Personalizada `proscenio_weight_sidecar` no nível do objeto, que sobrevive à reconstrução da geometria, e o importador os reprojeta sobre o quad novo pela âncora de UV. Uma vinculação nativa de Auto Weights que não escreveu sidecar é capturada num instantâneo logo antes da reconstrução, então os pesos dela também são preservados. A densidade do Automesh de fato volta ao quad simples - rode o Automesh de novo (com `Preserve weights on regen`) para adensar novamente, e os pesos reprojetados se redistribuem pela malha mais densa.

De qualquer forma, o *objeto* é reutilizado, então os dados no nível do objeto sobrevivem:

- transformação (rotação, posição) e parentesco - incluindo a única armadura raiz, que é reutilizada em vez de reconstruída, então um rig que você cresceu sobre ela permanece no lugar;
- os grupos de vértices e seus pesos pintados (mantidos intactos numa reimportação de mesmo posicionamento, reprojetados sobre o novo quad numa de posicionamento alterado);
- configurações por sprite (tipo de sprite, metadados de sprite-frame, o sinalizador `is_slot`, sobrescritas de região);
- pertencimento a slot e trilhas de animação que miram o plano pelo nome.

> [!NOTE]
> A reimportação **preserva** os pesos. Este é o mesmo mecanismo de instantâneo-por-UV-e-então-reprojeção que um [regen do Automesh](../../02-tools/blender-addon/06-weight-paint.md#snapshot) usa, então uma reimportação preserva os pesos do jeito que uma reexecução do Automesh faz - distinto de uma nova revinculação (re-rig), que começa de uma vinculação limpa e não consulta o sidecar. Você ainda pode iterar o PSD livremente antes de fazer o skinning, mas não precisa mais: pinte e rigue uma vez, depois continue editando a arte, e seus pesos seguem junto.

### Três nomes, um vínculo {#three-names-one-link}

A razão de a reimportação ser segura (e a única coisa que pode quebrá-la) se resume a três nomes que são independentes entre si:

- o **nome da camada PSD** - digamos `torso`;
- o **nome do objeto Blender** - como quer que você chame o plano;
- a **tag `proscenio_import_origin`** no plano - aqui `psd:torso`.

Apenas a tag é o vínculo. Na reimportação, o importador pareia cada camada PSD ao plano cuja tag é `psd:<that layer>`, e ignora o nome do objeto por completo. Tudo abaixo decorre dessa única regra:

- **Você renomeia o plano no Blender** (`torso` -> `body_main`): seguro. A tag ainda diz `psd:torso`, então a reimportação o encontra e atualiza. O nome do objeto é cosmético.
- **Você deleta a tag**: o plano agora está desvinculado. A reimportação não o vê mais como o plano do `torso`, então carimba um plano `torso` novo ao lado do seu agora órfão - você acaba com uma duplicata.
- **Você renomeia a camada no PSD** (`torso` -> `chest`): isso quebra o vínculo. O manifesto agora tem `chest`, mas seu plano ainda está marcado com `psd:torso`, então a reimportação orfana seu plano (com pesos e tudo) e carimba um `chest` em branco. Para preservar os pesos, edite a tag para `psd:chest` **antes** de reimportar (consulte [Renomeie uma camada no meio do projeto](#rename-a-layer-mid-project)).
- **Você aponta a tag para uma camada diferente** de propósito: a reimportação então alimenta a arte daquela camada neste plano. Avançado - só quando você sabe por quê.

Normalmente você nunca toca na tag. Depois de uma reimportação você pode confirmá-la em Propriedades do Objeto > Propriedades Personalizadas, como `proscenio_import_origin`.

## Tags entre colchetes

Você guia a exportação escrevendo **tags entre colchetes** no nome de uma camada - tokens como `[tag]` ou `[tag:value]`. Uma tag pode ficar em qualquer lugar do nome, uma camada pode carregar várias, e a palavra-chave não diferencia maiúsculas de minúsculas (`[Ignore]` funciona). O que sobra depois de as tags reconhecidas serem removidas se torna o nome de exibição; um colchete não reconhecido como `[WIP]` é deixado nesse nome intacto.

```text
arm.R [folder:body] [origin:10,20] [scale:2.5]
^^^^^                ^^^^^^^^^^^^^^ ^^^^^^^^^^^
display name        tag             tag
```

| Tag | Onde vai | O que faz |
| - | - | - |
| `[ignore]` | camada ou grupo | descartada por completo - sem entrada no manifesto, sem PNG |
| `[merge]` | grupo | achata o grupo inteiro em um PNG, como se fosse uma única camada de arte |
| `[folder:NAME]` | grupo | torna-se uma `Collection` do Blender chamada `NAME`; os filhos a herdam |
| `[mesh]` / `[poly]` / `[polygon]` | camada | todas são interpretadas como o mesmo `kind: mesh`; são sinônimos hoje porque a exportação constrói o mesmo polígono padrão (Polygon2D) para cada uma - justamente o nó que uma camada de arte sem tag recebe, já que só `kind: sprite` diverge (para Sprite2D). `[mesh]` reserva a intenção de malha deformável para o futuro trabalho de deformação de malha; até isso chegar a escolha é cosmética |
| `[sprite]` | camada | é interpretada como `kind: sprite` - um elemento respaldado por Sprite2D em vez de um polígono (`[spritesheet]` abaixo é a forma de grupo que constrói quadros) |
| `[spritesheet]` | grupo | marca o grupo como um sprite-frame; suas camadas filhas numeradas se tornam os quadros |
| `[origin]` | camada | marca o centroide daquela camada como o pivô do seu grupo pai `[spritesheet]` ou `[merge]` (a própria camada marcadora não é exportada) |
| `[origin:X,Y]` | camada ou grupo | um pivô explícito em pixels de PSD; sobrescreve o centro implícito |
| `[scale:N]` | camada ou grupo | multiplica o tamanho da caixa delimitadora por `N`; um resultado subpixel gera um aviso de validação |
| `[blend:VALUE]` | camada | registra o modo de mesclagem pretendido (`normal`, `multiply`, `screen`, `additive`) como metadados. O Blender renderiza a camada como mesclagem alpha simples (ele não pré-visualiza multiply / screen / additive de verdade), e o modo ainda não chega ao Godot - o `.proscenio` não tem campo de modo de mesclagem (backlog) |
| `[path:NAME]` | camada | sobrescreve o nome folha do caminho de exportação em disco (sem barras - subpastas são tarefa do `[folder:NAME]`) |
| `[name:pre*suf]` | grupo | um modelo de nome para descendentes; `*` é substituído pelo nome de cada descendente |

Algumas coisas acontecem independentemente das tags:

- Camadas ocultas e `[ignore]` são ignoradas; uma camada sem pixels visíveis também é ignorada.
- Grupos sem tag são percorridos recursivamente; os nomes de saída se juntam com `__` (então `body` > `torso` vira `body__torso`).
- Um grupo cujos filhos diretos são nomeados com números simples contíguos a partir de zero (`0`, `1`, `2`, ...) é detectado como spritesheet por conta própria; `[spritesheet]` apenas força esse agrupamento.
- Dentro de um spritesheet, quadros de tamanhos diferentes são preenchidos com transparência até a caixa do maior quadro, para que a grade permaneça regular.
- Camadas bloqueadas exportam como qualquer outra - o bloqueio é ignorado.
- A ordem de empilhamento semeia o `Y Location (Draw Order)` de cada plano (o topo da pilha é o mais alto); o Blender os espalha ao longo de Y para que não haja Z-fighting, e a exportação nega essa ordem inteira no `z_index` do Godot.
- Uma guia horizontal e uma vertical do PSD definem o pivô da figura, exportado como a âncora do documento; o Blender coloca o mundo `(0, 0, 0)` ali.

Mantenha os nomes de exibição com letras ASCII, dígitos, hifens e sublinhados. O manifesto mantém seu nome literalmente, mas qualquer outra coisa - pontos, espaços - é substituída por `_` quando o nome vira um nome de arquivo PNG ou um nó do Godot, então um nome limpo permanece previsível ao longo do pipeline. (As tags entre colchetes são removidas primeiro, então espaços dentro de uma tag não são problema.)

## Receitas

### Primeira importação de um novo personagem

1. *Crie o PSD*: uma camada por parte do corpo, grupos de spritesheet para anexos animados, `[ignore]` em camadas de referência e anotação.
2. *Exporte*: no plugin, escolha a pasta de saída (ela é lembrada durante a sessão) e clique em `Export`.
3. *Importe no Blender*: abra o `.blend` alvo, clique em `Import Photoshop Manifest` e selecione `manifest.json`.

Você chega com planos nas suas posições de PSD, materiais vinculados e um único osso `root`. Rigue a partir daí.

### Itere em um personagem existente

1. *Edite o PSD*: pinte, reposicione, renomeie, adicione ou remova camadas.
2. *Reexporte*: clique em `Export` para a mesma pasta; o manifesto e os PNGs são sobrescritos.
3. *Reimporte*: rode `Import Photoshop Manifest` de novo e aponte para o mesmo `manifest.json`.

Os planos atualizam no lugar onde as tags correspondem, novas camadas são carimbadas, e planos de camadas removidas são reportados como órfãos em vez de deletados. Os pesos pintados sobrevivem à ida e volta (consulte [o contrato de reimportação acima](#re-importing-after-psd-edits)), então você pode continuar editando a arte depois de fazer o skinning.

### Crie um grupo de spritesheet

Coloque os quadros em um grupo e nomeie cada camada de quadro com um número simples, contando a partir de zero - um grupo `eye` contendo camadas `0`, `1`, `2`. Um grupo assim é detectado como spritesheet automaticamente; adicione `[spritesheet]` quando quiser deixá-lo explícito (ou para forçá-lo em um grupo ambíguo). Duas regras que o detector impõe:

- os nomes dos quadros são números puros - `0`, não `frame0` ou `eye_0`;
- eles seguem contiguamente a partir de zero (`0`, `1`, `2`, sem lacunas), e há pelo menos dois.

### Renomeie uma camada no meio do projeto {#rename-a-layer-mid-project}

A frágil. Para renomear `torso` para `chest` sem perder pesos:

1. No Blender, anote o valor de `proscenio_import_origin` do plano existente.
2. Renomeie a camada no PSD e reexporte.
3. **Antes** de reimportar, mude a tag daquele plano de `psd:torso` para `psd:chest`, para que o importador direcione a atualização a ele.
4. Reimporte. O UV e o PNG do plano são atualizados; os pesos persistem - reprojetados do sidecar sobre o quad reconstruído, igual a qualquer reimportação de posicionamento alterado.

Pule o passo 3 e você fica com um plano `chest` novo mais um plano `torso` órfão. Recuperável, mas tedioso.

### Adicione um quadro de spritesheet após o rig

Adicione o novo quadro numerado ao grupo de spritesheet existente no PSD e reexporte, depois reimporte no Blender. Os metadados da malha são incrementados para incluir o novo quadro, `hframes` / `vframes` são recalculados, as trilhas de animação existentes em `:frame` continuam funcionando, e você pode inserir quadros-chave até o novo índice.

## O que sobrevive a uma exportação de PSD

As tags entre colchetes acima cobrem o que cada tag faz; isto é sobre quais recursos nativos do Photoshop de fato passam pela exportação (ela rasteriza cada camada para um PNG):

| Recurso do Photoshop | Como exporta |
| - | - |
| Camadas de pixel raster | suportadas - a entrada canônica |
| Grupos de camadas (pastas) | suportados - percorridos recursivamente |
| Camadas ocultas | suportadas - ignoradas |
| Objetos inteligentes, efeitos de camada, camadas de ajuste, máscaras | não garantidos - achatados no PNG da camada na exportação, inseparáveis do seu raster |
| Camadas de texto, vetor e forma | não garantidas - rasterizadas na exportação; os dados vetoriais são perdidos |
| Modos de cor não-RGB (CMYK, etc.) | não suportados - o pipeline pressupõe saída PNG RGB(A) |
| Profundidade de cor de 16 bits / 32 bits | não garantida - o PNG exportado é forçado a 8 bits |

Quando algo é **não garantido**, achate-o ou rasterize-o em uma camada de pixel simples antes de rigar sobre ele.

## Além do Photoshop

O schema do manifesto é agnóstico a DCC de propósito: um exportador de Krita ou GIMP que emita um manifesto em conformidade se encaixa no mesmo importador do Blender sem alterações. O Photoshop apenas foi comprovado primeiro, porque o plugin UXP existe. (Mais sobre esse design de contrato aberto em [Arquitetura](../../01-project/01-architecture.md).)

## Por que não há round-trip de Blender para PSD {#why-there-is-no-blender-to-psd-round-trip}

Fora de escopo por design. O Blender é uma ferramenta de rigging, não de pintura, então empurrar o estado do rig para um programa de pintura não tem uso claro - e o formato PSD é rico demais (objetos inteligentes, texto, máscaras, efeitos) para reconstruir fielmente a partir do Blender. Um link ao vivo de Blender para Photoshop está estacionado como uma ideia de longo prazo.

A única direção reversa que o plugin de fato entrega, de manifesto para PSD, reconstrói um PSD a partir de um manifesto e seus PNGs - para mover um manifesto para um PSD novo ou recuperar uma fonte perdida, não para empurrar edições de rig de volta.
