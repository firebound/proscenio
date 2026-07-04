# Outliner

Uma lista plana centrada em elementos dos objetos com que o Proscenio se importa - slots, anexos, malhas de elemento e armaduras - para você selecionar um rapidamente num rig grande sem rolar o outliner nativo do Blender. Este painel é **blender-only**: favoritos, o filtro e o estado de seleção nunca chegam à exportação. Ele fica em segundo na barra lateral e vem recolhido por padrão.

O corpo é uma única `UIList` do Blender. O único controle na linha de cabeçalho do painel é o botão `Favorites only` (o ícone SOLO); busca e ordenação são recursos próprios de lista do Blender, alcançados pelas setas de filtro da lista.

**O que as linhas mostram.** Cada linha é um botão alinhado à esquerda que nomeia um objeto atrás de um ícone de tipo; clicar nele seleciona aquele objeto. O tipo define o ícone, o prefixo do rótulo e o recuo, então a lista se lê como o rig num relance:

- Um **slot** Empty aparece primeiro com um prefixo de nome `[slot]` e o ícone `LINK_BLEND`. Seus anexos recuam abaixo dele.
- Um **anexo de slot** (uma malha parentada sob um slot Empty) aparece com um prefixo de nome em seta e o ícone `OBJECT_DATAMODE`, recuado sob o seu slot.
- Uma **malha de elemento** (uma malha ou sprite do Proscenio) aparece com o ícone `MESH_DATA`. Quando está parentada a um único osso, ganha um sufixo `@ <bone>` que nomeia esse osso.
- Uma **armadura** aparece por último com um prefixo de nome `[arm]` e o ícone `ARMATURE_DATA`.

O recuo espelha a árvore de parentesco da cena: a armadura é a raiz, slots e malhas de elemento soltas ficam um nível abaixo dela, e os anexos de um slot ficam sob o slot.

**O que a lista filtra para dentro.** A lista vem de `bpy.data.objects` e depois é reduzida apenas ao rig, para que objetos de cena não relacionados fiquem fora do caminho:

- Câmeras, luzes e outros tipos não-Proscenio nunca aparecem.
- Uma malha crua modelada à mão só aparece quando carrega dados de elemento (após importação ou `Incorporate`); até lá fica oculta.
- Só a armadura escolhida no painel [Esqueleto](04-skeleton.md) aparece, para que um segundo rig na cena não lote a lista.
- Uma linha cujo objeto saiu da view layer (um datablock apagado ou desfeito que persiste em `bpy.data`) some, em vez de persistir como uma linha morta.

Slots Empty e qualquer malha parentada sob eles sempre pertencem, porque um slot e seus filhos fazem parte do rig por construção.

**Favoritos e filtragem.** O ícone SOLO na borda direita de cada linha fixa aquele objeto como favorito. O botão `Favorites only` no cabeçalho do painel então oculta toda linha não-favorita, para você recortar um rig grande até o punhado de objetos em que está trabalhando. Favoritos são flags por objeto; persistem com o `.blend` e, como o resto deste painel, nunca chegam à exportação.

A busca por nome é o Filter by Name nativo do Blender: abra as setas de filtro da lista e digite. O toggle nativo de ordenação por nome (A-Z) achata a árvore de parentesco em uma lista alfabética simples e remove o recuo junto, então recorra a ele quando quiser varrer por nome em vez de por hierarquia.

**Selecionando pela lista.** Um clique simples substitui a seleção e torna o objeto clicado ativo, seguindo o padrão de clique único do Blender. <kbd>Shift</kbd> + clique estende a seleção e <kbd>Ctrl</kbd> + clique alterna a linha clicada, espelhando os modificadores da viewport e do outliner nativo. Um marcador de seleção aparece em toda linha selecionada, não só na ativa, porque o realce de lista do Blender marca apenas a linha ativa.
