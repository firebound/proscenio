# Animação

Um resumo somente leitura de toda Action no arquivo - as Actions que o escritor emite como trilhas de `AnimationPlayer` do Godot na exportação. O Proscenio não autora animação; você fixa poses com as ferramentas nativas do Blender (Action Editor, Dopesheet, drivers) e este painel é a janela para o que a exportação vai carregar. Ele fica em sétimo na barra lateral e vem recolhido por padrão.

O painel abre com a leitura do alvo de exportação (`Exports: <name>`), a mesma linha que os painéis [Geração de Malha](05-mesh-generation.md) e [Pintura de Peso](06-weight-paint.md) mostram, porque clicar numa linha atribui a Action àquela armadura. Abaixo dela fica a lista de Actions, depois uma contagem total. Sem Actions no arquivo a lista é substituída por `no actions to export`.

**A lista de actions.** Cada linha nomeia uma Action atrás de um ícone `ACTION` e mostra sua faixa de quadros como `[start-end]`. A lista é de seleção única: clicar numa linha atribui aquela Action ao rig escolhido no painel [Esqueleto](04-skeleton.md), então a timeline a percorre e reproduz. O seletor do Esqueleto é a fonte única da verdade aqui - se nenhuma armadura estiver escolhida, o clique reporta isso e não atribui nada em vez de adivinhar um rig. A ordem de origem é mantida, e uma contagem de todas as Actions fica abaixo da lista.

**O que a exportação emite.** Na exportação o escritor itera toda Action e emite uma entrada de animação por Action. Três tipos de canal se fundem naquela única entrada, chaveados pelo nome da Action:

- **Transformações de osso** - as fcurves de posição, rotação e escala nos ossos de deformação do rig viram trilhas `bone_transform`. Um canal sem movimento fora da pose de descanso é descartado para que o descanso do Bone2D sobreviva à importação; as fcurves de um osso de controle (um alvo de IK ou de polo) são filtradas e nunca chegam ao documento.
- **Índices de slot** - quadros-chave no índice de um slot viram uma trilha `slot_attachment` no slot, com interpolação constante para que a troca seja um corte duro.
- **Quadros de sprite controlados** - um `frame` de sprite controlado a partir de um osso de pose (o atalho [Drive from Bone](02-element.md#drive-from-bone)) é assado ao percorrer a Action e ler o osso posado, emitindo uma trilha `sprite_frame` com chaves de interpolação constante a cada mudança.

Como todos os três são chaveados pelo nome da Action, os índices de slot e as propriedades de sprite controladas animam na mesma timeline que os ossos.

**Onde as animações vão parar no Godot.** Toda Action vai parar no `AnimationPlayer` da cena importada sob a biblioteca padrão (de nome vazio), para que uma cena Wrapper possa hospedar um segundo `AnimationPlayer` para animações do lado do jogo sem colisão de nomes.

**Ressalvas.** Strips de NLA ainda não são consumidas, então asse uma pilha de NLA em uma única Action antes de depender dela na exportação. O painel lê as Actions direto do arquivo, então uma Action sem nenhum canal chaveado de osso de deformação, slot ou quadro controlado não contribui com trilhas mesmo que ainda apareça na lista.
