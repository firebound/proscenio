# Blender

O guia aprofundado do lado do Blender: como criar um personagem Proscenio, o que sobrevive a salvamentos e recarregamentos do complemento, e o que o complemento faz entre o Photoshop de um lado e o Godot do outro.

Para a versão rápida, consulte o [passo a passo básico](../01-basic/02-blender.md).

## O contrato

O Blender é o **hub** do pipeline. Ele lê o manifesto PSD que entra e escreve o `.proscenio` que sai. Você cria do jeito que sempre faz no Blender - [pintura de peso](https://docs.blender.org/manual/en/latest/sculpt_paint/weight_paint/index.html), [dopesheet](https://docs.blender.org/manual/en/latest/editors/dope_sheet/introduction.html), [NLA](https://docs.blender.org/manual/en/latest/editors/nla/introduction.html), [drivers](https://docs.blender.org/manual/en/latest/animation/drivers/introduction.html) - e recorre à fina aba lateral **Proscenio** apenas para os controles específicos do pipeline.

Regra prática: trabalhe no Blender como Blender, use o painel Proscenio para as partes do pipeline, e exporte quando estiver pronto.

A reexportação é idempotente, então você pode fazê-la quantas vezes quiser.

## Layout do projeto

```text
<your project>/
├── firebound.psd               source PSD
├── firebound/
│   ├── manifest.json           from the Photoshop plugin
│   ├── images/                 per-layer PNGs
│   └── _spritesheets/          composed sprite-frame sheets
├── firebound.blend             your rig + animation
└── firebound.proscenio         written by the exporter (sticky path)
```

O `.blend` é seu e permanece autoritativo para tudo que você cria no Blender - rig, pesos, animações, slots. O `.proscenio` é regenerado a cada exportação, então nunca o edite à mão.

## O que sobrevive a quê

| Ação | O que acontece |
| - | - |
| Salvar e reabrir o `.blend` | Tudo persiste - Blender normal. |
| Recarregar o complemento | Dados da cena intocados; as configurações do Proscenio se re-hidratam ao abrir o arquivo. Você só perde o estado ao vivo de operadores, como um arraste do Quick Armature em andamento. |
| Reimportar o manifesto PSD | O objeto sobrevive - transformação, parentesco (a armadura raiz é reutilizada, não reconstruída), configurações, slots e animação mirada por nome todos são preservados, e os **pesos pintados** também: uma reimportação de mesmo posicionamento deixa a malha totalmente intacta, e uma de posicionamento alterado reconstrói o quad mas reprojeta os pesos do `proscenio_weight_sidecar` (o mesmo caminho de preservação que um [regen do Automesh](../../02-tools/blender-addon/06-weight-paint.md#snapshot) usa). A densidade do Automesh volta ao normal numa reconstrução - rode o Automesh de novo para adensar novamente. Uma nova revinculação (re-rig) é o caso que ainda descarta pesos, porque começa limpo e nunca lê o sidecar. Camadas órfãs são deixadas em paz e registradas. Consulte [o contrato de reimportação](01-photoshop.md#re-importing-after-psd-edits). |
| Desinstalar o complemento | Dados da cena, pesos, ações, materiais de atlas e as propriedades `proscenio_*` brutas permanecem. A UI do painel desaparece, mas os drivers de `Drive from Bone` continuam funcionando - eles são drivers nativos do Blender. |
| Subir versões do Blender | [Blocos de dados](https://docs.blender.org/manual/en/latest/files/data_blocks.html) são preservados; o complemento pode quebrar por deriva da API `bpy`, então teste no próximo LTS primeiro. |
| Mover a pasta do projeto | Os arquivos se movem bem, mas o caminho de exportação fixado é absoluto hoje - escolha-o de novo na próxima exportação. |

## Por que você edita pelo painel

O complemento armazena cada configuração duas vezes:

- um **objeto tipado** - canônico, e o que o painel edita;
- uma [Propriedade Personalizada](https://docs.blender.org/manual/en/latest/files/custom_properties.html) `proscenio_*` bruta - uma chave arbitrária que o Blender permite guardar em qualquer bloco de dados, editável em Propriedades do Objeto.

A sincronização corre em um sentido: o objeto tipado se hidrata a partir da Propriedade Personalizada quando você abre o arquivo, e a espelha de volta ao salvar.

Então edite pelo painel. Uma Propriedade Personalizada que você cutuca à mão no meio da sessão é ignorada - nada a devolve ao objeto tipado até a próxima reabertura, e o próximo salvamento a sobrescreve. A única exceção é o caminho de exportação headless (`blender --background`), onde o painel nunca foi registrado, então o exportador recorre à propriedade bruta.

## O painel de criação

Abra a barra lateral com <kbd>N</kbd> e mude para a aba **Proscenio**. Todo painel abre recolhido. Seus painéis, de cima para baixo:

- **Pipeline** (primeiro) - todo o fluxo PSD -> Blender -> Godot em três subpainéis: **Importar** (`Import Photoshop Manifest`), **Validar** (a lista de problemas, clique-para-selecionar) e **Exportar** (a leitura do alvo de exportação "Exports: \<name\>", o caminho fixado, `pixels_per_unit`, `Export` / `Re-export`).
- **Elemento** - o seletor de tipo de elemento (`Mesh` / `Sprite`); o cabeçalho diz "Element: \<name\>" do elemento ativo. Os subpainéis por tipo **Malha ativa** / **Sprite ativo** (campos de Polygon2D / metadados de spritesheet de Sprite2D), mais **Região de textura** e **Drive from Bone**.
- **Slots** - a lista de slots do projeto e `Create Slot`; o subpainel **Slot ativo** carrega o seletor de anexo padrão, a lista de anexos e `Bind to Bone` (mostrado quando um [Vazio](https://docs.blender.org/manual/en/latest/modeling/empties.html) `is_slot` é selecionado).
- **Esqueleto** - o seletor de armadura mais a hierarquia de ossos, os auxiliares de **Modo de pose** (`Bake Current Pose`, `Toggle IK`, `Save Pose to Library`) e **Quick Armature**.
- **Geração de malha** - `Automesh from Alpha` (de uma vez) e `Automesh Interactive` (a entrada de criação modal), mais o pipeline de depuração.
- **Pintura de peso** - `Bind to Target Armature`, `Edit Weights`, transferência de pesos e instantâneos.
- **Outliner** - uma lista plana centrada em sprites com um filtro de substring e favoritos.
- **Animação** - um resumo somente leitura das ações que o exportador vai emitir.
- **Atlas** - o nome de arquivo do atlas mais `Pack Atlas` / `Unpack Atlas` / `Apply Packed Atlas`.
- **Auxiliares** - `Preview Camera`.
- **Sobre** (rodapé) - a versão + link do repositório, o botão `Open help` (o popup de tópicos) e o smoke test sob `debug_mode`. Não há um painel de Ajuda separado - ele conflitaria com Auxiliares.

Todo cabeçalho de subpainel tem um selo de status e um botão `?` que abre a ajuda específica do tópico.

### A regra de nomenclatura que morde {#the-naming-rule-that-bites}

O exportador pareia um [grupo de vértices](https://docs.blender.org/manual/en/latest/modeling/meshes/properties/vertex_groups/index.html) a um osso apenas quando seus nomes correspondem **exatamente**.

Renomear um **osso** é seguro. O Blender renomeia automaticamente o grupo de vértices correspondente em toda malha que aquela armadura deforma, então o pareamento segue junto. Isso é comportamento padrão do Blender, não algo que o complemento adiciona.

Dois casos ainda quebram o pareamento:

- **Você renomeia o grupo de vértices em vez do osso.** A sincronização só vai em um sentido - renomear o grupo não toca no osso.
- **O grupo de vértices está em uma malha que a armadura não deforma** (uma ainda apenas parenteada por objeto, digamos). A renomeação automática nunca o alcança.

Então renomeie pelo lado do osso, mantenha suas malhas de deformação vinculadas, e a correspondência se mantém.

## Receitas

### Primeiro rig a partir de um manifesto do Photoshop

1. *Exporte do Photoshop*: rode o plugin e exporte para uma pasta.
2. *Importe no Blender*: abra o `.blend` alvo, depois clique em `Import Photoshop Manifest` no painel **Pipeline** e aponte para o manifesto. Os planos chegam nas suas posições de PSD, com materiais vinculados, com um único osso `root`.
3. *Adicione os ossos*: no [Modo de edição](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/introduction.html), ou com `Quick Armature` para um clique-arraste modal.
4. *Vincule as malhas*: selecione-as e pressione <kbd>Ctrl+P</kbd>, depois [`Armature Deform`](https://docs.blender.org/manual/en/latest/animation/armatures/skinning/parenting.html) (ou use o painel **Pintura de peso**). Pinte os pesos.
5. *Defina o tipo de cada elemento* no painel **Elemento**.
6. *Valide e exporte*: `Validate`, depois `Export`.

### Itere

Edite no Blender, salve e clique em `Re-export` no subpainel **Exportar**. O caminho é reutilizado por padrão e o Godot capta a mudança na próxima vez que sua janela tiver foco.

### Renomeie um osso no meio do projeto

Renomear um osso é mais leve do que parece. O Blender o propaga pela maioria de suas próprias referências automaticamente:

- grupos de vértices em malhas deformadas;
- canais de [curva-F](https://docs.blender.org/manual/en/latest/editors/graph_editor/fcurves/introduction.html) de [Ação](https://docs.blender.org/manual/en/latest/animation/actions.html);
- drivers, constraints e objetos parenteados a osso.

Os passos:

1. *Renomeie o osso* no Modo de edição ou [Modo de pose](https://docs.blender.org/manual/en/latest/animation/armatures/posing/introduction.html).
2. *Corrija o que o Blender deixa passar*: as lacunas [da regra de nomenclatura acima](#the-naming-rule-that-bites) (um grupo de vértices em uma malha que não deforma), mais qualquer script externo ou dado fora da cena que fixe o nome antigo no código.
3. *Valide e reexporte*.

Ainda assim, nomear os ossos uma vez e manter isso é melhor do que renomear depois.

### Adicione uma variante de sprite-frame após o rig

Adicione o novo quadro ao grupo de spritesheet existente no PSD e reexporte, depois reimporte o manifesto no Blender. Os metadados de spritesheet da malha são incrementados para incluir o novo índice, as trilhas de animação existentes continuam funcionando, e você pode inserir quadros-chave até o novo quadro.

### Empacote e desempacote o atlas

1. O subpainel **Atlas** encontra os materiais que carregam texturas de imagem.
2. `Pack Atlas` compõe as imagens por sprite em uma única folha e reescreve o `texture_region` de cada sprite.
3. `Unpack Atlas` reverte isso - cada região volta a ser a sua própria imagem, com os materiais atualizados.
4. `Apply Packed Atlas` é para quando você empacotou externamente; ele revincula os materiais ao arquivo de atlas existente.

O empacotador é determinístico para entrada determinística, e é por isso que o CI o usa para goldens de igualdade de bytes.

### Animação com múltiplas ações

Cada Ação do Blender se torna uma entrada na exportação. Crie-as no [Editor de Ações](https://docs.blender.org/manual/en/latest/editors/dope_sheet/modes/index.html); o exportador respeita o intervalo de quadros de cada Ação. Strips de NLA não são consumidos - asse tudo em uma única Ação primeiro.

## Suporte a recursos

| Recurso | Status |
| - | - |
| Armadura única por cena | suportada - o caso canônico |
| Malhas parenteadas à armadura (Armature Deform) | suportadas - guiam os pesos de skinning |
| Malhas parenteadas a um único osso ([Bone parent](https://docs.blender.org/manual/en/latest/scene_layout/object/editing/parent.html)) | suportadas - anexo rígido |
| Vazios sinalizados como `is_slot` como âncoras de slot | suportados - tanto parentesco por osso quanto por objeto são respeitados |
| Grupos de vértices nomeados a partir dos ossos | suportados - a regra de correspondência exata |
| Grupos de vértices que não correspondem a nenhum osso | suportados - descartados com um aviso no console |
| Uma F-curve por canal em uma Ação | suportado - o caso canônico |
| Drivers conectados via `Drive from Bone` | suportados - sobrevivem a salvar, reabrir e desinstalar o complemento |
| [Shape keys](https://docs.blender.org/manual/en/latest/animation/shape_keys/introduction.html) em malhas de sprite | não suportadas - o exportador as ignora; o formato não tem conceito de shape-key |
| [Constraints de IK](https://docs.blender.org/manual/en/latest/animation/constraints/tracking/ik_solver.html) | auxiliar de pose só do Blender (`Toggle IK`); não exportado - asse em quadros-chave de osso para o Godot, ou reconstrua no motor. O round-trip completo está no backlog |
| Strips de NLA compondo movimento | não suportado - asse em uma única Ação primeiro; suporte de NLA-para-Ação está no backlog |

Qualquer coisa fora desta tabela não é coberta pelos fixtures de CI - armaduras vinculadas ou com sobrescrita de biblioteca, malhas multi-material, peculiaridades de gerenciamento de cor, constraints além de IK.

O caminho seguro: achate o cenário antes de rigar sobre ele. E se um fluxo de trabalho real encontrar atrito ali, registre-o para que possa virar uma spec.

## Como a validação funciona

Há duas camadas:

- Verificações **em linha** rodam a cada redesenho e são baratas: um selo de status ao lado de cada cabeçalho de subpainel e um ícone de erro ao lado de uma linha quebrada, capturando os problemas óbvios sem percorrer a cena.
- Verificações **preguiçosas** rodam sob demanda: o botão `Validate` percorre a cena inteira e lhe dá uma lista de problemas em que você pode clicar para selecionar o objeto ofensor.

Tanto `Export` quanto `Re-export` são barrados pelo validador preguiçoso - se algum problema for um `error`, a exportação aborta; avisos não bloqueiam. Os erros usuais: nenhuma armadura na cena, um sprite sem um campo obrigatório, um grupo de vértices sem osso correspondente, ou uma imagem de atlas que não pode ser encontrada.
