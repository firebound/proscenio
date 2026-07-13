# Pipeline

O primeiro painel na barra lateral e o agrupador de todo o fluxo Photoshop para Blender para Godot. O corpo são três subpainéis em ordem de execução: Import, [Validate](#validate) e Export.

## Import

`Import Photoshop Manifest` lê um manifesto escrito pelo plugin do Photoshop do Proscenio, carimba uma malha quad por camada (compondo texturas de spritesheet para grupos `sprite_frame`) e parenteia tudo a uma armadura raiz de stub. O seletor de arquivo carrega duas opções de redo:

- **Placement** - `Landed (Feet on Z=0)` desloca a figura para que seu ponto mais baixo fique no Z=0 do mundo (o padrão, seguindo a convenção do motor de pivotar personagens nos pés); `Centered (Canvas at World Origin)` mantém a figura centralizada no canvas do manifesto, o que ajuda ao alinhar vários imports numa cena.
- **Root Bone Name** - o nome do único osso na armadura de stub; `root` por padrão.

Cada malha carimbada é marcada com sua camada de origem, então reimportar o mesmo manifesto reutiliza as malhas existentes - rotação, parentesco e pesos definidos pelo usuário sobrevivem à ida e volta. O importador reporta quantas malhas carimbou, quantas camadas pulou e quantas spritesheets compôs.

Veja [`examples/generated/simple_psd/`](../../../examples/generated/simple_psd/) para um manifesto trabalhado mínimo e seu resultado importado.

## Validate {#validate}

`Validate` roda a passagem completa de pré-exportação e lista o que encontra; a mesma passagem roda automaticamente antes de toda exportação, e qualquer linha de `error` a bloqueia. Fica entre o Import e o Export para a ordem de execução se ler de cima para baixo. Até você clicar em `Validate` o painel mostra `run Validate to see issues`; uma cena limpa mostra `no issues - ready to export`.

Esta é a validação estrutural e semântica da cena ao vivo - ela nunca roda a validação de JSON Schema. O schema é verificado no CI e no test runner, não na sessão do Blender (veja [Export](#export) para o que a exportação faz em vez disso).

Cada achado aparece como uma linha com um ícone `error` ou `info`. Uma linha que nomeia um objeto ofensor é um botão - clique nele para selecionar aquele objeto na viewport; achados sem objeto (o erro de sem-armadura) aparecem como um rótulo simples.

### Erros bloqueiam a exportação

- A cena não tem Armadura (a exportação exige uma; isto é reportado sozinho, antes de qualquer outra verificação).
- Um elemento carrega grupos de vértices mas nenhum resolve para ossos de armadura - o escritor levantaria erro na exportação.
- Um elemento sprite tem `hframes` ou `vframes` abaixo de 1.
- Um elemento tem um tipo de elemento desconhecido (nem `mesh` nem `sprite`).
- Uma cadeia de IK é controlada por um alvo animado mas seus ossos de cadeia não carregam quadros-chave - rode `Bake IK to Keyframes` primeiro (o exportador lê as fcurves cruas e escreveria ossos achatados).
- Dois slots compartilham um nome.
- Um slot não tem filhos de malha.
- O anexo padrão de um slot nomeia uma malha que não é filha do slot.

### Avisos informam mas ainda exportam

- Um elemento não tem osso pai nem grupos de vértices que batem com ossos de armadura - o escritor recorre a um campo de osso vazio.
- A direção de descanso de um osso se inclina para fora do plano XZ do mundo - o exportador projeta os ângulos de osso no XZ e o interpretaria errado.
- Um osso controla a rotação de um sprite mas não está no modo Euler XYZ - o driver lê XYZ, então a animação não vai acompanhar. Rode `Active to Euler` no painel [Esqueleto](04-skeleton.md#active-armature).
- Um elemento de malha não é plano (tem espessura em todos os eixos), então a etapa de achatar-para-plano perderia geometria.
- As UVs de quad de um elemento sprite-frame não abrangem a folha inteira 0-1, então a grade `hframes` / `vframes` ficaria embaralhada no Godot.
- Uma imagem de atlas referenciada por um material está faltando no disco - o Godot avisará na importação. Isto é um aviso, não um bloqueio.
- A malha de um elemento sprite não é mais um único quad (provavelmente uma ferramenta de malha rodou nela).
- Um elemento de malha não tem polígonos.
- Um anexo de slot segue um osso diferente do seu slot.
- Um filho de slot carrega quadros-chave de transformação de osso - um slot anima apenas a visibilidade.
- Um objeto está duplamente dirigido: carrega um parenteamento de osso cru E uma restrição de seguimento do Proscenio, então a influência do osso aplica duas vezes - `Clear Bone Follow` (ou `Unbind`) mantém a posição e descarta ambos.
- Um seguimento de osso está obsoleto: o descanso do rig mudou desde o vínculo, então o Blender e a importação do Godot discordam da posição de descanso do seguidor - rode `Bind to Bone` de novo para recalculá-lo.
- Um sprite está tombado fora do plano da imagem: seu quad fica de lado para a câmera (um parenteamento de osso por snap num osso no plano, ou um objeto girado à mão), então seu transform de descanso exportado sai encurtado - mantenha o sprite virado de frente.

Os subpainéis Elemento e Slot Ativo trazem inline um subconjunto barato dessas verificações a cada redesenho (o objeto ativo, o slot ativo), então a maioria dos problemas aparece antes de você clicar em `Validate`.

## Export {#export}

O subpainel Export abre com uma leitura do rig que o escritor vai exportar: `Exports: <name>`, marcado `picked` quando um rig é escolhido no painel [Esqueleto](04-skeleton.md) ou `first in scene - no rig picked` quando um é inferido. Abaixo dela ficam o caminho fixo, as duas configurações de exportação e os botões.

- **Pixels per unit** define a razão unidade-de-mundo-do-Blender para pixel-do-Godot (padrão 100, então 1 m no Blender vira 100 px no Godot). O escritor lê este campo de cena na primeira exportação, não um padrão de operador.
- **Bundle textures** copia toda textura que o documento referencia para a pasta de exportação após uma escrita bem-sucedida. A arte importada do PSD vive nas subpastas `images/` e `_spritesheets/`, mas o `.proscenio` referencia texturas por nome de arquivo simples e o importador do Godot só resolve irmãos; o empacotamento fecha essa lacuna. Origens já ao lado do arquivo são deixadas em paz, e uma origem faltante no disco é reportada em vez de copiada.

`Export (.proscenio)` primeiro roda a passagem completa de [validação](#validate) e aborta quando encontra qualquer `error`; senão ele roda o escritor e grava o JSON no caminho que você escolher no diálogo de exportação. Ele não valida contra o JSON Schema - essa verificação roda no CI e no test runner, não aqui.

O caminho escolhido é lembrado na cena, então `Re-export` reexecuta o escritor (validação incluída) para aquele mesmo caminho sem diálogo. A cena gerada usa apenas nós nativos do Godot - `Skeleton2D`, `Bone2D`, `Polygon2D` / `Sprite2D`, `AnimationPlayer` - sem GDExtension e sem dependência de runtime de plugin.
