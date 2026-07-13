# Slots

Um slot apresenta uma de N malhas de anexo por vez - use-o para trocas duras como espada / cajado / vazio, sobrancelha para cima / para baixo, ou uma mudança de expressão. O painel pai lista todo slot na cena com sua contagem de anexos (cada linha o seleciona) e hospeda **Create Slot**. Com malhas selecionadas, Create Slot as envolve num novo slot; no Modo de Pose com um osso ativo, ele ancora um slot vazio naquele osso (uma caixa de dica no painel explica os dois casos).

Um slot é agnóstico quanto ao tipo: um único slot pode conter tanto anexos de malha (pintados com peso) quanto anexos de sprite (fatiados por textura) - cada linha mostra seu tipo. No Godot cada slot vira um `Node2D` sob o osso com seus anexos como filhos irmãos; o anexo padrão começa visível (ou nada aparece, quando o padrão não nomeia nenhum), e uma trilha de animação `slot_attachment` inverte a visibilidade por chave. Para uma mudança contínua e controlada em vez de uma troca um-ou-outro, use [Drive from Bone](02-element.md#drive-from-bone).

## Slot Ativo

Mostrado quando um slot Empty é o objeto ativo (o painel pai Slots permanece visível de qualquer forma, então sua lista e o Create Slot nunca somem). Ele mostra como o slot segue seu osso, lista os anexos e adiciona novos.

Cada linha de anexo carrega uma estrela SOLO (preenchida no que é mostrado ao carregar a cena - clique em outra para mudar o padrão), o nome do anexo e um ícone de tipo malha/sprite, e um botão `Show Only` que autora a troca (abaixo). Dois botões adicionam anexos: `Attach Mesh` escolhe uma malha por nome (o caminho que funciona quando só o slot está selecionado), e `Add Selected` promove a malha já selecionada. Problemas de validação do slot aparecem no rodapé do painel.

### Autorar uma troca: quadros-chave de visibilidade show-only

Uma troca é autorada como quadros-chave de visibilidade diretos nas malhas de anexo - não há índice a rastrear. `Show Only` numa linha de anexo fixa aquele anexo visível e todo irmão oculto no quadro atual (`hide_render` e `hide_viewport` em conjunto, corte duro), então exatamente um anexo aparece daquele quadro em diante. O botão `(none) / Hide All` abaixo da lista fixa todo anexo oculto - o estado sem-anexo-visível, para uma pose de idle que não carrega arma. Como as chaves ficam na visibilidade das próprias malhas, uma troca é pré-visualizada nativamente na viewport do Blender enquanto você percorre a timeline: não há modo de pré-visualização separado, e o que a viewport mostra é o que o runtime do Godot reproduz.

Trocas são por animação. Uma troca segue a animação ativa por padrão - a selecionada no painel [Animação](07-animation.md) - então `idle` (sem arma), `attack_chicken` e `attack_staff` carregam cada uma sua própria linha do tempo de anexos; você escolhe a qual animação uma troca pertence simplesmente tornando aquela animação ativa antes de fixar a chave. O dropdown `Target anim` neste painel sobrepõe isso quando você quer que uma troca caia numa animação específica em vez da ativa - deixe-o vazio para seguir a animação ativa. O painel Animação lista cada animação exportada uma vez por nome, removendo duplicatas entre o movimento do rig e os datablocks de visibilidade por malha.

A exportação não muda de forma: uma troca ainda emite uma trilha `slot_attachment`, uma chave `none` não nomeia nenhum anexo, e um slot também pode descansar em branco quando seu padrão não nomeia nenhum, começando sem nada visível. Para migrar um slot autorado no modelo de índice mais antigo, rode o operador de uma passada `Convert Slot Index to Visibility` no Empty do slot; ele re-fixa cada índice armazenado como um quadro-chave de visibilidade show-only nos anexos e limpa a trilha legada.

No Blender 4.4+ a visibilidade de anexos de um slot e o movimento do rig ficam juntos numa única action por animação; no 4.2 eles vivem em actions separadas de mesmo nome que a exportação funde por nome. A versão mínima suportada permanece 4.2 de qualquer forma - só a arrumação dos datablocks difere.

Há duas maneiras de fazer um slot seguir um osso, e ambas exportam igual e reconstroem de forma idêntica no Godot.

**Bind to Bone** é a rota segura: mantém o Empty parentado por objeto (para que os quads de anexo planos fiquem no plano da imagem) e adiciona uma restrição `Child Of` cujo inverso cancela o descanso do osso, para o slot pegar carona só no delta de pose do osso. Ele permanece plano para qualquer orientação de osso.

**Parentear o osso à mão** o Empty (Ctrl+P > Bone) também é suportado e exporta bem, mas só para ossos apontando para dentro da tela. Um osso no plano (um deitado no plano da imagem) herda sua orientação de descanso e inclina os quads planos de perfil, colapsando-os - o painel avisa quando o osso de um slot parentado por osso faria isso e o aponta para o Bind to Bone em vez disso.

O painel mostra como cada slot segue - uma restrição do Proscenio ou um parentesco de osso - e nomeia seu pai. A restrição É o vínculo: o exportador lê o osso seguido diretamente dela, então não há um campo separado para manter em sincronia (um campo `slot_bone` pré-existente de um arquivo mais antigo ainda exporta como leitura de reserva; o painel o marca como legado e o Bind to Bone o adota na restrição). **Unbind** para o seguimento, removendo qualquer relação que esteja ativa e deixando o Empty parentado por objeto e inerte. O vínculo se recusa quando um slot já segue, então para revincular depois de mover um slot - ou depois de editar o descanso do rig, que o Validate marca como seguimento obsoleto - você faz Unbind e então Bind.
