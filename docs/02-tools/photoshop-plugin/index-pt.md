# Plugin do Photoshop

Um plugin [UXP](https://developer.adobe.com/photoshop/uxp/) (React + TypeScript) que transforma um PSD em camadas num manifesto mais PNGs que o importador do Blender lê. O artista dirige toda a exportação de dentro do Photoshop, sem nunca sair da tela.

O plugin traz quatro painéis encaixáveis sob `Plugins > Proscenio ...`: **Proscenio Exporter**, **Proscenio Tags**, **Proscenio Validate** e **Proscenio Debug**. Eles compartilham uma única leitura do documento aberto, então uma camada renomeada em **Proscenio Tags** atualiza a prévia em **Proscenio Validate** sem uma atualização manual. Cada painel abre com uma seção **Active document** mostrando o nome do documento e o tamanho da tela, com um botão `Refresh` que relê o Photoshop.

## O que faz

- **Marcar camadas pelo nome.** Marcadores entre colchetes (`[ignore]`, `[spritesheet]`, `[folder:name]` e outros) dirigem a exportação sem tocar na arte. O vocabulário completo vive no [guia avançado do Photoshop](../../00-guides/02-advanced/01-photoshop.md); o painel **Proscenio Tags** edita as mesmas tags através de controles em vez de à mão.
- **Exportar.** Uma varredura recursiva das camadas produz um PNG por camada mais um manifesto JSON. O manifesto é validado antes de ser escrito, então um manifesto quebrado nunca chega ao disco. Entradas cujo PNG falha ao escrever são descartadas e relatadas em vez de abortar a exportação inteira, então as entradas boas ainda são entregues.
- **Spritesheets.** Marcar um grupo como spritesheet o marca com a tag `sprite` e exporta um PNG por quadro (`name/0.png`, `name/1.png`, ...). Compor esses em uma única folha é trabalho do importador do Blender, não do Photoshop.
- **Espelhar de volta para o PSD.** O plugin consegue reconstruir um PSD a partir de um manifesto. Isso reconstrói o layout de origem; não faz o round-trip das edições do Blender de volta para o PSD.

## Proscenio Exporter

O painel principal. Ele é dono da pasta de saída, das opções de exportação, da execução da exportação e da importação de manifesto para PSD.

### Pasta de saída

A seção **Output folder** é onde a exportação escreve. O caminho escolhido persiste entre recarregamentos do plugin, então uma sessão retoma contra a mesma pasta. `Pick folder` (ou `Change folder` depois que uma está definida) abre o seletor do sistema; `Forget` descarta a pasta lembrada e recai no estado vazio. Se a pasta for movida ou apagada no meio da sessão, a próxima exportação relata que ela não está mais acessível e limpa a referência obsoleta, para que o painel peça uma pasta de novo.

### Opções de exportação

A seção **Export options** guarda os toggles e as configurações de conversão que a execução da exportação lê.

- `Skip hidden layers` exclui camadas que estão ocultas no Photoshop. Fica ligado por padrão.
- A seção **Pixels per unit** define o `pixels_per_unit` do manifesto, o fator de conversão que as ferramentas seguintes usam para transformar pixels do PSD em unidades de mundo do Blender e do Godot. Um valor mais alto resulta em objetos menores no espaço de mundo. O padrão é `100`. A seção ecoa a altura atual da tela tanto em pixels quanto em unidades resultantes como verificação de sanidade, e um botão `Reset to 100` restaura o padrão. O valor persiste entre recarregamentos, e uma importação de manifesto para PSD o semeia a partir do manifesto importado.
- A seção **Filename templates** sobrescreve os nomes de arquivo em disco. O template `mesh` (padrão `{name}.png`) controla os caminhos de PNG de malha e aceita os tokens `{name}` e `{kind}`; o template `sprite` (padrão `{name}/{index}.png`) controla os caminhos de quadro de sprite e aceita `{name}` e `{index}`. O prefixo `images/` e qualquer subpasta `[folder:...]` são adicionados automaticamente, então o template governa apenas a porção do arquivo. `Reset to defaults` restaura ambos. Um template que descarta o token que distingue suas entradas (um template `mesh` sem `{name}`, um template `sprite` sem `{index}`) colapsa todas as entradas em um único caminho e bloqueia a exportação em vez de sobrescrever PNGs silenciosamente.

### Executar exportação

O botão `Export manifest + PNGs` da seção **Run export** executa a exportação completa. Ele fica desabilitado até que um documento esteja aberto e uma pasta de saída seja escolhida. A exportação escreve o manifesto como `<document-stem>.photoshop_exported.json` ao lado de uma pasta `images/` de PNGs. A linha de resultado relata quantas entradas foram escritas; numa execução parcial, ela lista as entradas que pulou e por quê, para que o artista possa corrigir aquelas camadas e reexportar.

### Reexportar selecionadas

A seção **Re-export selected** reescreve apenas o(s) PNG(s) da camada atualmente selecionada no Photoshop, deixando o manifesto JSON intocado. Ela mostra o nome e o tipo da entrada de manifesto correspondente, e fica ativa apenas quando a camada selecionada mapeia para uma entrada. Use-a para atualizar a arte de um elemento sem uma exportação completa.

### Importar (manifesto para PSD)

A seção **Import (manifest to PSD)** reconstrói um PSD a partir de um manifesto. `Import manifest as PSD` abre um seletor para um manifesto JSON do Proscenio, o valida e então recria o documento com camadas posicionadas e um grupo por sprite. O novo documento é deixado aberto e não salvo de propósito - confirme-o com `File > Save As`. Manifestos inválidos e falhas de posicionamento por entrada são relatados inline; uma única entrada ruim é pulada em vez de abortar a importação inteira. Esta seção fica recolhida por padrão.

### Migração legada

A seção **Legacy migration** aparece no Exporter apenas quando o documento aberto tem camadas usando a antiga convenção de pular `_layerName`. Ela converte esses nomes para a tag `[ignore]` em lote: ela pré-visualiza cada renomeação (nome antigo para nome novo, clicar numa linha seleciona aquela camada no Photoshop) e `Convert N layer(s) to [ignore]` as aplica em uma única passada. O cabeçalho carrega um selo com a contagem de candidatas.

## Proscenio Tags

Um editor de árvore de camadas para as tags entre colchetes, para que o artista as defina através de controles em vez de digitá-las nos nomes das camadas. Cada linha mostra o nome de exibição da camada (com as tags removidas) e uma tira inline de selos para suas tags não padrão (folder, path, scale, origin, marcador de origin, padrão de nome). Selecionar o nome de uma linha seleciona aquela camada no Photoshop; linhas de grupo têm um toggle de expansão para recolher seus filhos.

Por linha, os controles são:

- um toggle `[ignore]` (pular a camada na exportação);
- um toggle `[merge]` (apenas grupos - achatar o grupo em um único PNG);
- um dropdown de tipo - `auto`, `mesh` (Polygon2D) ou `sprite` (Sprite2D);
- um dropdown de blend - `none`, `mult`, `scrn` ou `add`, escrevendo a tag `[blend:...]`;
- um expansor (`+`) que abre os campos avançados daquela linha.

Os campos avançados editam `[folder:NAME]`, `[path:NAME]`, `[scale:N]`, `[origin:X,Y]`, o marcador `[origin]` e (em grupos) o padrão de nome de filho `[name:PRE*SUF]`. Os valores digitados são um rascunho local: nada é confirmado até `Apply`, e `Revert` descarta o rascunho. Um valor que o parser de tags rejeitaria bloqueia `Apply` e marca o campo problemático em vez de não escrever nada silenciosamente. O botão `From selection` da linha de origin preenche X e Y a partir do centro da seleção de marquee atual do Photoshop.

Abaixo da árvore, a seção **Selected entry** é um inspetor somente leitura: para a camada selecionada no Photoshop, ela mostra o que a exportação vai emitir (nome, posição, tamanho, origin, blend, subpasta, contagem de quadros) e o(s) caminho(s) de PNG resolvido(s) em disco.

## Proscenio Validate

Um painel somente leitura que executa o planner de exportação como uma passada em seco e lista tudo que precisa de atenção antes de uma exportação real. O cabeçalho da sua seção **Validate** mostra um selo - a contagem de problemas, ou `ok` quando o manifesto está limpo. Os problemas vêm em grupos:

- **Warnings** - achados consultivos do planner, como caminhos de saída duplicados, tags conflitantes, um grupo de spritesheet malformado, limites vazios, escala subpixel ou um marcador `[origin]` fora de um container que o consome.
- **Skipped** - camadas que o planner deixou de fora e por quê (uma tag `[ignore]`, oculta, limites vazios ou uma camada de marcador de origin).
- **Manifest invalid** - erros bloqueantes que impedem a exportação, incluindo um template de nome de arquivo que colapsaria entradas em um único caminho.

Clicar em qualquer linha de aviso ou pulada seleciona a camada problemática no Photoshop para que seja rápido corrigir. Um documento cujo perfil de cor não é sRGB levanta um aviso independente: cores fora do gamut sRGB são recortadas na exportação, porque a engine lê PNGs como sRGB e ignora perfis embutidos. Converta o documento para sRGB (`Edit > Convert to Profile`) para autorar as cores que o jogo vai mostrar.

## Proscenio Debug

Um painel para inspecionar a exportação planejada e ajustar o logging. Sua seção **Preview** faz uma passada em seco da exportação (nada é escrito) e lista as entradas do manifesto com seu tipo, nome, caminho e quaisquer anotações de folder, blend ou origin; o cabeçalho exibe no selo a contagem de entradas. Ela também relata a âncora do documento (o pivô definido pelas primeiras guias horizontal e vertical do PSD, ou `(canvas centre)` quando nenhuma guia foi autorada) e os totais correntes de entradas, camadas puladas e avisos. `Refresh` reexecuta a passada em seco.

A seção **Debug logging** define o quanto o plugin registra no console das UXP Developer Tools. Escolha um nível (o padrão é `info`; `trace` ou `debug` é para reproduzir um bug, `off` o silencia); a escolha persiste entre recarregamentos. Os logs são marcados com `[proscenio:<area>]` e lidos sob `Plugins > Development > Developer Tools`.

## O formato do manifesto

A exportação escreve um manifesto PSD do Proscenio em `format_version: 1` - a versão atual e única entregue. Cada camada vira uma entrada cujo `kind` é `mesh` (um elemento respaldado por Polygon2D, o padrão para uma camada de arte) ou `sprite` (um elemento respaldado por Sprite2D, um ou mais quadros). O manifesto também carrega o nome do documento de origem, o tamanho da tela, `pixels_per_unit` e uma âncora de documento opcional. A lista exata de campos é gerada a partir do schema compartilhado e renderizada ao vivo sob a Referência de schema; esta página não a repete.

O manifesto é validado com o [ajv](https://ajv.js.org/) contra aquele schema tanto antes de uma exportação chegar ao disco quanto depois que um manifesto é escolhido para importação, de modo que nem uma exportação malformada nem um arquivo importado ruim passe da fronteira.

## Como é construído

O código é organizado em camadas: um adaptador isola a API da Adobe, `lib/` guarda a lógica pura e testável de tags e planejamento, e `api/` concentra os efeitos colaterais (escritas de arquivo, a API do Photoshop) para que o domínio permaneça livre de plataforma.

Veja [Arquitetura](../../01-project/01-architecture.md) para como o plugin se encaixa no pipeline.
