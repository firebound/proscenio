# Geração de Malha

Transforme o alpha de um sprite numa malha de recorte deformável que você pode pintar com peso. O painel é só para malha - num elemento sprite ele avisa e o aponta para o parentesco de osso (Ctrl+P > Bone) em vez disso. Ele mostra o rig-alvo (escolhido no painel [Esqueleto](04-skeleton.md)) e hospeda os parâmetros de traçado que ambos os pontos de entrada compartilham: o seletor de Interior Mode (Simple = esparso, Dense = preenchido), **Contour vertices** (o orçamento de contorno) e **Interior spacing** (o espaçamento do preenchimento, também o raio de reamostragem do desenho livre e de encaixe de dobra no modal interativo). Os campos exclusivos do modo denso - **Density follows bones** e seu raio / fator de osso - ficam esmaecidos sob o modo Simple.

## Automesh from Alpha

Um traçado de disparo único que percorre o contorno do alpha da imagem em uma malha; reexecuções preservam o quad base fixado por UV. Suas configurações próprias (o resto fica no painel pai acima):

- **Trace resolution** - um fator de redução da imagem. Um valor *maior* (1.0 = imagem cheia) traça uma silhueta mais fina mas custa mais; ele define a fidelidade do contorno, não a contagem de vértices.
- **Alpha threshold** e **Margin pixels** - o corte de alpha para o contorno e a que distância recuá-lo para dentro ou para fora.
- **Preserve base quad** - mantém o quad base fixado por UV entre reexecuções.
- **Preserve weights on regen** - tira um instantâneo dos pesos por UV antes da regeneração e os reprojeta na nova malha; desligado, a regeneração apaga a pintura. Trazido aqui porque este botão dispara a regeneração (o mesmo toggle vive no subpainel Snapshot da [Pintura de Peso](06-weight-paint.md#snapshot)).

## Automesh Interactive

Uma prévia modal do mesmo traçado. Avance pelas etapas para cortar / estender o contorno e posicionar pontos interiores, depois confirme; nada é escrito até você confirmar a etapa final. Suas entradas são a contagem e o espaçamento do laço interno, a margem de corte e o mesmo toggle `Preserve weights on regen`. O botão fica esmaecido até que o objeto ativo seja uma malha com uma textura de imagem.

## Debug Pipeline

Um auxílio de desenvolvedor, mostrado só com o modo debug ligado (Preferences > Add-ons > Proscenio). Escolha uma etapa do traçado e a próxima execução deixa uma malha wireframe acompanhante na coleção `Proscenio.Debug`; `Clear Debug Companions` as remove.
