# Primeiros passos

O Proscenio é um pipeline Photoshop -> Blender -> Godot para animação 2D cutout: você pinta a arte no Photoshop, faz o rig e a anima no Blender e entrega uma cena nativa ao Godot. Esta página cobre o que você precisa ter instalado, onde vive cada plugin e o formato do loop, e então passa o bastão para o passo a passo básico com o detalhamento etapa por etapa.

## Pré-requisitos

Você cria nas três ferramentas, então precisa das três instaladas:

- **Photoshop 2024+** - onde a arte vive e o `.psd` em camadas é criado.
- **Blender 4.2+** - o hub do pipeline: importar, fazer o rig, aplicar o skinning, animar e exportar.
- **Godot 4.6+** - o alvo de runtime para o qual o `.proscenio` é importado como cena nativa.

## Onde obter cada plugin

O caminho mais rápido são os pacotes pré-compilados anexados a cada [release do GitHub](https://github.com/firebound/proscenio/releases): cada tag traz um arquivo pronto para instalar por ferramenta.

- **Plugin do Photoshop** - `proscenio-photoshop-<version>.ccx`. Dê um duplo-clique nele e o instalador UXP do Photoshop assume (ele pede permissão para um desenvolvedor não confiável, já que o plugin não é assinado). Um `proscenio-photoshop-<version>.zip` com o mesmo conteúdo também é anexado, caso você prefira carregá-lo manualmente.
- **Complemento do Blender** - `proscenio-blender-<version>.zip`. Instale-o em `Edit > Preferences > Add-ons > Install from Disk`, depois habilite-o.
- **Plugin do Godot** - `proscenio-godot-<version>.zip`. Descompacte o `addons/proscenio` dele na pasta `addons/` do seu projeto e habilite-o em `Project > Project Settings > Plugins`.

Uma vez instalado, cada plugin vive onde você cria:

- **Plugin do Photoshop** - o exportador [UXP](https://developer.adobe.com/photoshop/uxp/). Ele carrega dentro do Photoshop e adiciona os painéis **Proscenio** em `Plugins > Proscenio ...`.
- **Complemento do Blender** - o complemento em Python. Uma vez habilitado, ele adiciona a aba **Proscenio** à barra lateral da 3D Viewport (abra-a com <kbd>N</kbd>).
- **Plugin do Godot** - o plugin de editor em GDScript. Ele registra um importador que transforma qualquer arquivo `.proscenio` em uma cena na importação.

Prefere compilar a partir do código-fonte? O código-fonte de cada plugin vive no repositório em [`apps/photoshop/`](../../../apps/photoshop/), [`apps/blender/`](../../../apps/blender/) e [`apps/godot/`](../../../apps/godot/).

## O formato do loop

Um personagem passa pelas três ferramentas em ordem, cada uma entregando à próxima um único arquivo:

1. **Photoshop** - marque as camadas e exporte um manifesto mais um PNG por camada.
2. **Blender** - importe o manifesto, construa o esqueleto, aplique o skinning nas malhas, defina os tipos de elemento, adicione slots, anime, opcionalmente empacote um atlas e exporte o `.proscenio`.
3. **Godot** - solte o `.proscenio` e envolva a cena gerada com a sua própria jogabilidade.

Cada etapa é idempotente, então editar qualquer estágio e empurrar a mudança adiante de novo mantém todos os lados em sincronia sem descartar o seu trabalho a jusante. Essa passagem repetida é [o loop de iteração](../03-iterate.md).

## Próximos passos

- Siga o [passo a passo básico](../01-basic/index.md) para o loop completo, uma página por ferramenta.
- Assim que passar do seu primeiro personagem, os [fluxos de trabalho avançados](../02-advanced/index.md) aprofundam nos painéis, contratos e pegadinhas de cada ferramenta.
- Para a referência por aplicativo, consulte o [Hub de ferramentas](../../02-tools/index.md).
