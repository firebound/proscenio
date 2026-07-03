# Pintura de Peso

Vincula uma malha de recorte ao rig e refina os pesos de osso dela. O painel é só para malha - ele avisa quando o elemento ativo é um sprite. Ele mostra o rig-alvo (escolhido no painel [Esqueleto](04-skeleton.md)) sobre o qual os subpainéis atuam. O vínculo mais os pesos resultantes exportam para o Polygon2D; as ferramentas de edição, instantâneo e transferência ficam no lado do Blender.

## Bind

Constrói os pesos de vértice que permitem ao rig deformar a malha. **Mode** escolhe o algoritmo: Bone Heat é o padrão nativo do Blender; Proximity / Envelope / Single-nearest / Empty são as alternativas (Proximity adiciona os campos `Max Distance` e `Falloff Power`). O botão `Bind to Target Armature` fica desabilitado até que um rig seja escolhido.

**Soft / Hard por osso** sobrescreve o falloff de um único osso: Soft compartilha peso suavemente com os vizinhos (pano, cabelo), Hard dá uma fronteira nítida de vizinho-mais-próximo (juntas de dedo), e o X limpa uma sobrescrita de volta ao padrão do modo. As sobrescritas se aplicam só aos modos planares - sob Bone Heat a caixa mostra uma dica, porque Bone Heat as ignora. A lista rola para que um rig com muitos ossos não empurre o botão Bind para fora da tela.

## Edit Weights

Entra numa sessão modal de pintura de peso no grupo ativo com uma sobreposição de proveniência (vértices auto-semeados vs pintados à mão). O botão fica desabilitado até você vincular (ele precisa de um instantâneo populado); assim que você está pintando ele vira `Exit Painting Mode`. As predefinições de curva de pincel (Hard Edge / Soft Falloff / Crease / Smooth Blend) moldam o pincel para tarefas 2D comuns. Uma caixa **Viewport display** traz as alavancas Weight Opacity e Zero Weights do próprio Blender para a textura aparecer através do gradiente enquanto se pinta. `Clear Empty Vertex Groups` remove grupos deixados vazios por revínculos ou edições.

## Snapshot {#snapshot}

O instantâneo de pesos armazena, por vértice, uma âncora de UV mais seus pesos e proveniência (auto-semeado / pintura à mão / reprojetado); é a rede de segurança que sobrevive a uma reconstrução de malha. `Preserve weights on regen` tira um instantâneo dos pesos por UV antes de uma reexecução do automesh e os reprojeta na nova malha (desligado = a regeneração apaga a pintura). Uma pílula reporta as contagens de pintura / semente / reprojetados, e `Reset to Last Saved Weights` reverte os pesos ao vivo para o instantâneo.

Abaixo disso, pontos de salvamento nomeados: `Save Snapshot` adiciona um ponto de salvamento manual (ilimitado), e o modal Edit Weights adiciona alguns auto-instantâneos rotativos por sessão; cada linha restaura seu instantâneo. `Export Snapshot` e `Import Snapshot` escrevem o instantâneo num arquivo JSON ou carregam um de volta - útil para versionar pesos ou movê-los entre arquivos. A importação empurra os pesos para a malha ao vivo quando a topologia bate; senão ela armazena só o instantâneo (reexecute o Automesh com Preserve weights on regen para reprojetar).

## Weight Transfer

Copia pesos da malha ativa para toda outra malha selecionada pelo vértice mais próximo no espaço do mundo - uma impressão para recortes em camadas ou divididos que se sobrepõem a uma base com rig. Vértices-alvo além do `Max Distance` (o campo do painel, também exposto no redo do F9) não recebem pesos.
