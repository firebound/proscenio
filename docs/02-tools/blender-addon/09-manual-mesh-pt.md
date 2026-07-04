# Malha Manual

Construa a silhueta de um elemento de malha à mão - você clica os vértices em vez de traçar o alpha da imagem. É a contrapartida manual da [Geração de Malha](05-mesh-generation.md): uma maneira separada e mutuamente exclusiva de fazer uma malha (um método por elemento), então os campos de traçado do automesh não se aplicam aqui. Este painel é **blender-only** e, como os outros painéis de malha, é só para malha - num elemento sprite ele avisa e o aponta para o parentesco de osso (Ctrl+P > Bone) em vez disso. Ele fica logo abaixo da Geração de Malha na barra lateral e vem recolhido por padrão.

**Quando recorrer a ela.** Use a Malha Manual quando o traçado de alpha não consegue encontrar a forma que você quer - bordas fracas ou suavizadas por anti-aliasing, arte sobreposta, ou uma silhueta que você simplesmente quer posicionar com exatidão. Por padrão o resultado é a triangulação *simples* do contorno que você desenha; um toggle **Interior mode** no painel o troca por um preenchimento *denso* uniforme (usando o botão compartilhado de espaçamento interior) quando você quer mais triângulos deformáveis.

**Desenho (duas fases).** Clique em `Draw with vertices` para entrar no modal; enquanto ele roda o botão vira `Exit Draw with vertices`, e uma seção recolhível **Shortcuts** espelha o cheatsheet de gestos da barra de status. Você primeiro **desenha** o contorno, depois o **fecha** para **editá-lo**:

- **LMB** posiciona um vértice; clicar no primeiro vértice de novo fecha o laço e entra na fase EDIT (ele não se aplica mais imediatamente - pressione Enter para aplicar).
- **Wheel / 0-9** definem a contagem de subdivisão da aresta sendo desenhada - cada aresta mantém a contagem com que foi desenhada, então você pode variar a densidade ao redor do contorno.
- **X / Z** travam o próximo posicionamento a um eixo; uma linha-guia colorida mostra a direção travada.
- **RMB** arrasta um vértice posicionado (em qualquer fase).
- **DEL** (ou **Ctrl+Z**) remove o último vértice enquanto se desenha.

Na fase **EDIT** (depois que o laço se fecha) você refina o anel fechado:

- **LMB numa aresta** insere um vértice ali, dividindo a aresta (as duas metades herdam sua contagem de subdivisão).
- **Wheel / 0-9 sobre uma aresta** mudam a contagem de subdivisão daquela aresta depois do fato.
- **DEL** remove o vértice sob o cursor (o anel mantém pelo menos três).
- **Tab** alterna a ferramenta ativa: **Contorno externo** -> **Ponto interior** -> **Dobra interior** (a ferramenta atual é mostrada na barra de status e no cabeçalho Shortcuts do painel). As duas ferramentas de interior adicionam detalhe dentro da silhueta, usando as mesmas entradas de ponto / dobra que o auto-gen interativo consome:
  - **Ponto interior** - um clique de **LMB** solta um único vértice interior.
  - **Dobra interior** - um arraste de **LMB** desenha livremente uma linha de dobra, ou cliques sucessivos de **LMB** constroem uma dobra aresta por aresta (uma faixa elástica pré-visualiza o próximo segmento); **Wheel / 0-9** definem a contagem de subdivisão assada na próxima aresta (a mesma densidade por aresta que a caneta de contorno); **Enter** finaliza a cadeia de cliques.
  - O posicionamento é restrito ao **interior do contorno**: um gesto que cairia fora é negado com um aviso de cursor vermelho, e um clique na borda encaixa no **contorno externo** em vez disso (inserindo um vértice de contorno, qualquer que seja a ferramenta ativa).
  - Em ambas as ferramentas, **RMB** arrasta qualquer vértice - interior ou de contorno - e **Alt+LMB** apaga o traço interior sob o cursor (ele se realça ao passar o mouse); **DEL** / **Ctrl+Z** remove o último vértice ou traço. Reabrir o desenho recarrega esses traços para você revisitá-los.

Uma triangulação ao vivo pré-visualiza a malha que o contorno vai construir (tanto em Simple quanto em Dense). **ENTER** constrói a malha no elemento selecionado; **ESC** cancela (uma linha aberta em progresso limpa primeiro, depois um segundo Esc sai).

**Continuando um desenho.** A Malha Manual lembra o contorno que você desenhou (e seus traços interiores): reabra `Draw with vertices` no mesmo elemento e ele carrega direto na fase EDIT para você continuar refinando em vez de começar do zero. Para jogar a malha fora e voltar ao plano importado nu, use **Revert to Plane** no painel [Elemento](02-element.md) (só elementos de malha importados do PSD); ele pede confirmação primeiro, porque destrói a malha gerada e a sua pintura de peso.

A Malha Manual é exclusiva com os modos Automesh: enquanto um modal de autoria roda, o botão do outro fica desabilitado, então um único elemento nunca é construído pela metade de duas maneiras. A malha que ela escreve é um recorte deformável comum que você pinta com peso no painel [Pintura de Peso](06-weight-paint.md), exatamente como um resultado de automesh.
