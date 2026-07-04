# Slots

Um slot apresenta uma de N malhas de anexo por vez - use-o para trocas duras como espada / cajado / vazio, sobrancelha para cima / para baixo, ou uma mudança de expressão. O painel pai lista todo slot na cena com sua contagem de anexos (cada linha o seleciona) e hospeda **Create Slot**. Com malhas selecionadas, Create Slot as envolve num novo slot; no Modo de Pose com um osso ativo, ele ancora um slot vazio naquele osso (uma caixa de dica no painel explica os dois casos).

Um slot é agnóstico quanto ao tipo: um único slot pode conter tanto anexos de malha (pintados com peso) quanto anexos de sprite (fatiados por textura) - cada linha mostra seu tipo. No Godot cada slot vira um `Node2D` sob o osso com seus anexos como filhos irmãos; o padrão começa visível, e uma trilha de animação `slot_attachment` inverte a visibilidade por chave. Para uma mudança contínua e controlada em vez de uma troca um-ou-outro, use [Drive from Bone](02-element.md#drive-from-bone).

## Slot Ativo

Mostrado quando um slot Empty é o objeto ativo (o painel pai Slots permanece visível de qualquer forma, então sua lista e o Create Slot nunca somem). Ele mostra como o slot segue seu osso, lista os anexos e adiciona novos.

Cada linha de anexo carrega uma estrela SOLO (preenchida no que é mostrado ao carregar a cena - clique em outra para mudar o padrão), o nome do anexo e um ícone de tipo malha/sprite, e um botão de quadro-chave que fixa a visibilidade deste anexo na trilha `slot_attachment` do slot no cabeçote de reprodução. Dois botões adicionam anexos: `Attach Mesh` escolhe uma malha por nome (o caminho que funciona quando só o slot está selecionado), e `Add Selected` promove a malha já selecionada. Problemas de validação do slot aparecem no rodapé do painel.

Há duas maneiras de fazer um slot seguir um osso, e ambas exportam igual e reconstroem de forma idêntica no Godot.

**Bind to Bone** é a rota segura: mantém o Empty parentado por objeto (para que os quads de anexo planos fiquem no plano da imagem) e adiciona uma restrição `Child Of` cujo inverso cancela o descanso do osso, para o slot pegar carona só no delta de pose do osso. Ele permanece plano para qualquer orientação de osso.

**Parentear o osso à mão** o Empty (Ctrl+P > Bone) também é suportado e exporta bem, mas só para ossos apontando para dentro da tela. Um osso no plano (um deitado no plano da imagem) herda sua orientação de descanso e inclina os quads planos de perfil, colapsando-os - o painel avisa quando o osso de um slot parentado por osso faria isso e o aponta para o Bind to Bone em vez disso.

O painel mostra como cada slot segue - uma restrição do Proscenio, um parentesco de osso, ou um `slot_bone` que está definido mas inerte (vinculado mas ainda não seguindo no Blender; o Bind to Bone conecta o seguimento ao vivo) - e nomeia seu pai. **Unbind** para o seguimento, removendo qualquer relação que esteja ativa e deixando o Empty parentado por objeto e inerte. O vínculo se recusa quando um slot já segue, então para revincular depois de mover um slot você faz Unbind e então Bind.
