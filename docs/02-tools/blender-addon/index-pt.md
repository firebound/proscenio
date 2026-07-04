# Addon do Blender

Referência painel a painel da barra lateral do Proscenio. Abra-a no Blender em **Viewport 3D > Barra Lateral (`N`) > Proscenio**.

Para o fluxo de ponta a ponta, comece pelo [passo a passo do Blender](../../00-guides/01-basic/02-blender.md); esta seção documenta cada painel e subpainel individualmente.

> [!NOTE]
> **Páginas provisórias.** Estas páginas de referência são um primeiro esboço. Cada painel e subpainel traz uma descrição breve e específica que espelha a ajuda `?` de dentro do addon; elas se expandem com o tempo.

## O que ele faz

O addon é onde o trabalho pesado do pipeline acontece:

- **Autoria de malha (automesh)** - traça o alpha de um sprite para uma malha deformável, com um clique ou por um modal interativo de várias etapas; a regeneração que preserva pesos reprojeta a pintura quando você redensifica.
- **Autoria de esqueleto (Quick Armature)** - desenhe ossos na viewport arrastando da cabeça à cauda.
- **Vínculo e pintura de peso** - cinco modos de vínculo (Bone Heat, Proximity, Envelope, Single Nearest, Empty), um modal Edit Weights ajustado para 2D, cópia de pesos entre sprites e um sidecar de pesos que registra a proveniência.
- **Slots** - grupos de troca de sprite animados por índice de slot.
- **Atlas** - empacota, desempacota e aplica um atlas de textura compartilhado.
- **Ingestão da arte de origem** - importa um manifesto do Photoshop para planos mais um osso raiz (a reimportação reutiliza os planos e a armadura e preserva os pesos pintados - intactos numa camada de mesmo posicionamento, reprojetados a partir do sidecar numa camada alterada).
- **Exportação para o Godot** - valida a cena, grava o `.proscenio` e reexporta com um clique para o mesmo caminho depois.

Cada recurso tem seu próprio painel abaixo; os modos de vínculo e as regras de peso entre automesh e reimportação estão detalhados em [Pintura de Peso](06-weight-paint.md) e [Geração de Malha](05-mesh-generation.md).

## A barra lateral

Todo painel é exibido em qualquer seleção e avisa (em vez de se ocultar) quando precisa de outra. Cada cabeçalho traz um selo de status mais um `?` que abre a ajuda correspondente inline (veja [Recursos do cabeçalho](#header-affordances) abaixo).

- [Outliner](01-outliner.md) - lista plana centrada em sprites de slots, malhas e armaduras.
- [Elemento](02-element.md) - configurações por elemento (Polygon2D vs Sprite2D, região de textura, controle a partir de osso).
- [Slots](03-slots.md) - a lista de slots do projeto e o detalhe de anexação por slot.
- [Esqueleto](04-skeleton.md) - o seletor de armadura, a lista de ossos, os auxiliares de pose e o Quick Armature.
- [Geração de Malha](05-mesh-generation.md) - traça o alpha de um sprite para uma malha deformável.
- [Pintura de Peso](06-weight-paint.md) - vincula e refina os pesos dos ossos (somente elementos de malha).
- [Animação](07-animation.md) - resumo somente leitura das ações que o escritor exporta.
- [Atlas](08-atlas.md) - empacota as imagens de origem em um atlas compartilhado.
- [Pipeline](10-pipeline.md) - importa um manifesto do Photoshop, valida a cena e exporta o `.proscenio`.
- [Auxiliares](11-helpers.md) - auxiliares de autoria na viewport que ficam fora da exportação.

## Recursos do cabeçalho {#header-affordances}

Todo cabeçalho de painel e subpainel traz dois controles na sua borda direita, e uma subcaixa dentro de um corpo (o bloco Material Preview do sprite) repete o mesmo par na sua linha de título. Num painel N estreito ambos são removidos para não se sobreporem ao título. As convenções abaixo valem em todo lugar, então as páginas de cada painel não as repetem.

O **botão de ajuda `?`** abre a ajuda daquele recurso inline - um popup com um resumo de uma linha, o que ele faz, como usá-lo, onde ele se encaixa no pipeline e quaisquer ressalvas - mais um botão `Open online docs` que aponta para a página correspondente nesta seção. Uma linha cuja ajuda própria difere da do seu subpainel (o botão Save Pose to Library sob o Modo de Pose) carrega seu próprio `?`.

O **selo de status** mostra onde o recurso fica no pipeline. Passe o cursor sobre ele para ver o tooltip da faixa; clique nele para abrir a legenda abaixo. A faixa godot-ready usa uma marca do Godot, a blender-only usa uma marca do Blender, e as demais usam um ícone embutido.

## Selos de status

A legenda única para as quatro faixas que um selo de status pode mostrar. O selo de todo cabeçalho de painel resolve para uma destas, e clicar em qualquer selo reabre esta legenda.

- **godot-ready** - exporta para o `.proscenio` e embarca no importador do Godot; edições em seus campos alcançam a cena em tempo de execução.
- **blender-only** - um atalho de autoria que vive inteiramente no lado do Blender e nunca chega à exportação.
- **planned** - projetado, com um placeholder de UI, ainda não implementado.
- **out-of-scope** - intencionalmente não exportado (restrições de IK, shape keys, qualquer coisa que o Godot não consome).
