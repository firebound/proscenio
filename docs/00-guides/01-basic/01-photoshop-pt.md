# Photoshop: a base

O Photoshop é onde a arte vive. O exportador UXP transforma o seu `.psd` em camadas nas duas coisas de que o Blender precisa: um manifesto (um JSON descrevendo cada camada) e um PNG por camada.

## Crie o PSD: tipos de camada e tags

Toda camada visível se torna um objeto no lado do Blender. Que tipo de objeto depende das **tags entre colchetes** escritas no nome da camada - tokens como `[tag]` ou `[tag:value]`. As tags são removidas do nome antes da exportação, então `arm.R [mesh] [folder:body]` exporta como `arm.R`.

Você pode digitar as tags nos nomes das camadas à mão, mas o painel **Tags** do plugin é o caminho mais fácil: ele mostra a árvore de camadas do documento com controles de tag por linha, escreve os colchetes nos nomes das camadas para você e sinaliza avisos e camadas ignoradas ao vivo conforme você avança.

A tag decide o tipo da camada:

| Tipo | Como marcar | No que se torna |
| - | - | - |
| `polygon` | padrão para qualquer camada de arte (ou `[polygon]`) | um sprite cutout -> `Polygon2D` do Godot |
| `mesh` | `[mesh]` na camada | importa como um sprite `polygon`, apenas sinalizado como fonte de malha deformável (uma dica para o skinning) - não é um tipo separado a jusante |
| `sprite_frame` | `[spritesheet]` no **grupo** | um sprite spritesheet (cada camada filha é um quadro) -> `Sprite2D` do Godot |

Então, a jusante, existem apenas dois tipos de sprite, `polygon` e `sprite_frame` - uma camada `[mesh]` é apenas um `polygon` sinalizado para o skinning (o sinalizador segue junto como metadados).

Outras tags moldam como uma camada exporta:

| Tag | Onde | Função |
| - | - | - |
| `[ignore]` | camada ou grupo | ignorada por completo - sem entrada, sem PNG (use para referências e anotações) |
| `[merge]` | grupo | achata todos os filhos em um único PNG |
| `[folder:NAME]` | grupo | torna-se uma `Collection` do Blender chamada `NAME` |
| `[origin]` / `[origin:X,Y]` | camada ou grupo | define o pivô (centroide implícito, ou coordenadas de pixel PSD explícitas) |
| `[blend:multiply]` / `[blend:screen]` / `[blend:additive]` | camada | marca o modo de mesclagem pretendido (mantido como metadados; ainda não exportado para o Godot) |
| `[scale:N]` | camada ou grupo | multiplica o tamanho da caixa delimitadora por `N` |

A taxonomia completa (cada tag, as regras de percurso para grupos e camadas ocultas, a ordem-z, a âncora do documento) vive no [fluxo de trabalho do Photoshop](../02-advanced/01-photoshop.md).

## Exporte o manifesto e os PNGs

1. *Abra a fonte*: o `.psd` em camadas no Photoshop.

2. *Abra o exportador*: `Plugins > Proscenio Exporter` (carregado via o plugin UXP em [`apps/photoshop/`](../../../apps/photoshop/)).

3. *Escolha uma pasta de saída*: onde o manifesto e os PNGs vão parar.

4. *Exporte*: clique em `Export manifest + PNGs`. → O plugin escreve um JSON de manifesto v2 ao lado de um PNG por camada.

<!-- screenshot: Proscenio Exporter panel in Photoshop with Export button highlighted -->
