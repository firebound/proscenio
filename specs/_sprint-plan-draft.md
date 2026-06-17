# Plano de implementação — rascunho (2026-06-16)

Rascunho descartável para decidir como quebrar as issues da [`backlog.md`](backlog.md) em trabalhos (specs) coesos e implementáveis um de cada vez. Não é spec nem fonte de verdade — é só para alinhar o agrupamento e depois apagar.

## O que virou spec de fato (2026-06-16)

Ao criar o boilerplate, descobri que a spec **036 (ui-help-surfaces)** já existente cobria parte do que eu tinha planejado. Para não duplicar, o resultado final foi:

- **036 (já existe)** absorve: o polimento do Element (clamp/rename/centered/header), o left-align e a árvore indentada do Outliner, o help-orphan do preview de sprite, o Reproject UV, o materials-panel e os tooltips.
- **Specs novas criadas:** 043 Outliner (bugs de seleção + busca única + favoritos), 044 Weight Paint (sync do modo + parâmetros do bind), 045 Skeleton/Quick Armature/Animation (cancelar + picker + chrome), 046 Slots (lista nativa reusável + anexar via picker), 047 Godot (verificar region + docs), 048 Photoshop (performance da leitura).
- **A padronização de listas** deixou de ser spec própria: o componente reusável nasce na 046 (Slots) e a 044 (Weight Paint) o adota; o left-align do Outliner já estava na 036.
- **Capacidades grandes** (materials-panel build, skin-coordination, y-depth, driver-management, incorporate-mesh, named-snapshots, rotation-mode, revisão de chords) seguem como specs próprias futuras — continuam na backlog, não viraram pasta ainda.

As seções abaixo são o raciocínio original do agrupamento; valem como contexto, mas a lista de specs reais é a de cima.

## O que a leitura do código mudou

Antes de agrupar, mandei agentes lerem o código de cada área. Três coisas que o backlog dizia precisam ser corrigidas:

- A region manual do sprite **provavelmente não é bug**. O `sprite_builder.gd` já multiplica a region normalizada pelo tamanho da textura, igual ao mesh, com comentário explicando. O relato do walk parece ter olhado código antigo. O certo é escrever um teste para confirmar, e só tratar como conserto se o teste falhar.
- O problema do Esc no Quick Armature **é bug de verdade**, não só falta de clareza: hoje o Esc não cancela direito, então a armature criada automaticamente fica para trás mesmo quando você desiste.
- O Animation panel pegar "a primeira armature da cena" **é bug de comportamento**: ele ignora a armature que você escolheu no Skeleton e não avisa. O conserto reaproveita o mesmo mecanismo de "armature ativa" que o Skeleton já usa.
- Não existe um componente de lista compartilhado entre os painéis. Outliner, Skeleton e Animation já usam a lista nativa do Blender; Slots e Weight Paint desenham as linhas na mão. Padronizar significa criar um componente de lista e migrar esses dois — e o conserto do "qual linha está selecionada" do Outliner é pré-requisito disso.
- A queixa de que faltam atalhos no Quick Armature e que os atalhos atuais (taps de Shift/Ctrl) são ruins é real: o esquema de atalhos precisa ser repensado, não só ganhar mais um.

## Como agrupei

A régua foi: juntar o que mexe nos mesmos arquivos e se testa junto; fazer uma varredura única só quando o código é genuinamente compartilhado (o componente de lista); e deixar capacidades novas e grandes como specs próprias, fora da fila de polimento. O tamanho de cada trabalho está em palavras (pequeno = uma sessão; médio = alguns dias; grande = precisa de design antes).

### Outliner — corrigir a seleção e enxugar a lista

Junta dois bugs e a limpeza visual do mesmo painel, que compartilham os mesmos arquivos de seleção. Os bugs: o painel não acompanha o objeto que você seleciona direto na viewport (continua mostrando o anterior), e a lista mostra objetos já apagados/desfeitos — clicar neles dá erro de "não está no view layer". A limpeza: deixar só a busca nativa do Blender (hoje são duas), indentar a hierarquia e alinhar os nomes à esquerda, e decidir se favoritos sobem para o topo. Este trabalho também conserta o cálculo de "qual linha está ativa", que vira pré-requisito da padronização das listas. Tamanho médio. Dá para verificar rodando os testes de Outliner do QA Companion e reproduzindo o erro do view layer.

### Weight Paint — sincronizar o modo de pintura e expor os parâmetros do bind

O bug central: o Edit Weights do Proscenio não acompanha o modo de pintura de peso do Blender. Os dois sintomas (os vértices só ficam brancos depois de sair e voltar ao modo, e sair do modo pelos controles nativos não encerra o Edit Weights) têm a mesma causa e andam juntos — incluindo trocar o rótulo do botão para "Exit Painting Mode" enquanto está no modo. No mesmo painel, expor os parâmetros `max_distance` e `falloff_power` do bind (hoje só aparecem no F9), mostrando-os apenas quando o modo é Proximity — o encanamento já existe, falta só desenhar. Tamanho médio. O teste de Edit Weights do QA Companion reprova hoje; ele é a verificação.

### Skeleton e Quick Armature — corrigir o cancelar, respeitar o picker e limpar o cabeçalho

Tudo no mesmo par de painéis. Os dois consertos: o Esc do Quick Armature passa a cancelar de verdade e remover a armature criada à toa; e o Animation panel passa a usar a armature escolhida no Skeleton (avisando quando não há uma), em vez de chutar a primeira da cena. Junto, o polimento de cabeçalho/rótulos: marcar bones "disconnected" (hoje só marca "connected"), mostrar o nome da armature no cabeçalho, renomear o sub-painel "Armature" para "Active Armature" e remover as instruções que sobraram no cabeçalho da viewport. Tamanho médio. Verificável pelos testes de Skeleton e Animation.

### Element — polimento de rótulos e visibilidade

Um lote rápido de ajustes pequenos no mesmo painel, sem mudança de comportamento: limitar o campo de frame ao número de frames que existem; renomear o rótulo "Initial frame" para "Frame"; documentar a diferença entre "centered" e a origem que vem do Photoshop; esconder o sub-painel Texture Region quando o elemento for mesh; mostrar o nome do elemento ativo no cabeçalho; e deixar claro para que serve o Reproject UV. Tamanho pequeno — cabe num PR só.

### Padronizar as listas dos painéis

Criar um componente de lista nativo reutilizável e migrar para ele as listas que hoje são desenhadas na mão: a de slots (e a de anexos do slot ativo) e a de overrides por bone do Weight Paint. Aproveita para remover o aviso redundante de "slot vazio". Depende do conserto de seleção feito no trabalho do Outliner. Tamanho médio a grande; o pedaço mais arriscado é a lista de anexos do slot, porque ela é montada sobre filhos dinâmicos, não sobre uma coleção do Blender. As listas que já são nativas (Skeleton, Animation) podem adotar o componente depois, mas é baixo valor.

### Godot — verificar a region do sprite e dois ajustes de documentação

Escrever um teste para a region manual do sprite (provavelmente já está certa) e só consertar se falhar; documentar a convenção de sufixo `_001` na colisão de nomes de nó; e documentar por que o preview de sprite multi-frame no Blender é diferente do frame no Godot (é inerente ao modelo, não tem conserto de código). Tamanho pequeno.

### Photoshop — performance da leitura do documento

Dois itens de performance do plugin. Um rápido: tirar o "ocupado" global da lista de tags, que hoje re-renderiza a lista inteira a cada rename. Um grande: trocar a leitura do documento por uma chamada em lote (a leitura atual percorre o DOM), o que torna a função assíncrona e só se prova contra um PSD real — então só faz sentido numa sessão real de Photoshop, junto do item irmão que está no `deferred.md`.

### Trabalhos maiores — cada um vira spec própria

São grandes ou precisam de design antes; não entram na fila de polimento:

- Painel de Materials novo (inspeção e configuração de materiais em massa).
- Coordenação de "skins" entre slots — coordenação entre os três apps; provável spec própria e depende do caminho de migração de formato.
- Controle de profundidade em Y para evitar z-fight depois do import do Photoshop — precisa decidir o mecanismo (automático pela ordem das camadas ou manual) e se entra no formato exportado.
- Gestão de drivers no Element panel (listar, editar e remover vários drivers, não só substituir).
- Botão para adotar uma malha criada no Blender como elemento do Proscenio.
- Snapshots nomeados no Weight Paint (save points com nome, em vez do snapshot automático confuso).
- Escolha de modo de rotação no Quick Armature (Euler vs quaternion) com troca segura.
- Revisão do esquema de interação do Quick Armature (os taps são ruins e os atalhos estão saturados), incluindo o pick-parent na viewport — há demanda. Já está na backlog como `qa-quickarm-interaction-revision`.

### Tarefas soltas e rápidas

Cabem em qualquer PR vizinho ou num lote só: re-ligar o botão de ajuda do preview de sprite frame (que ficou órfão) e escrever a regra de não quebrar linha em prosa nas convenções de docs. Ambas já vivem nos seus arquivos de backlog (bugs-found e code-quality).

## Em que ordem

Os três trabalhos de conserto (Outliner, Weight Paint, Skeleton/Animation) podem andar em paralelo, porque são painéis diferentes — e é onde está o maior valor, porque destravam bugs. O polimento do Element e os tooltips (que vão para o spec 036) entram a qualquer momento. A padronização das listas vem depois do Outliner, porque reaproveita o conserto de seleção dele. Godot e Photoshop são independentes — o de Photoshop espera uma sessão real com o plugin. Os trabalhos maiores entram como specs próprias conforme a prioridade do produto.

## Decisões já tomadas (2026-06-16)

- A quantidade de trabalhos (cerca de cinco no Blender, mais Godot, Photoshop e os grandes separados) está num tamanho bom — nem espalhado demais, nem mega-spec.
- Os ajustes de tooltip entram no spec 036 (ui-help-surfaces) já planejado, em vez de virar spec própria.
- O pick-parent na viewport fica, e foi reescopado para incluir a revisão dos atalhos do Quick Armature (já registrado na backlog como `qa-quickarm-interaction-revision`, no lugar do antigo `qa-pick-parent-viewport`).
- A region manual do sprite foi rebaixada para "verificar com teste" e entra no trabalho do Godot.
