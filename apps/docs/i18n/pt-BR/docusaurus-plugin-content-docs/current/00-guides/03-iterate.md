# Iterando pelo loop

Isto é um loop, não um tiro único. Uma edição repercute nas três ferramentas, e hoje cada salto é uma reexportação / reimportação deliberada - ainda **não** há link ao vivo.

Digamos que você repinte o PNG de uma camada no Photoshop. Para vê-lo na cena Godot em execução:

1. *Reexporte do Photoshop*: o manifesto + PNGs.

2. *Reimporte no Blender*: aponte para o manifesto de novo. Idempotente para o trabalho no nível do objeto - seu rig, parentesco, slots, configurações por sprite e pesos pintados são preservados (uma camada de posicionamento alterado reconstrói o quad mas reprojeta seus pesos do sidecar; só a densidade do Automesh volta ao normal, então reajuste a densidade depois). A única coisa que quebra a preservação é renomear uma camada no PSD: isso orfana o plano antigo (com pesos e tudo) e carimba um em branco, a menos que você reaponte a tag dele primeiro. Consulte [o contrato de reimportação](02-advanced/01-photoshop.md#re-importing-after-psd-edits).

3. *Reexporte do Blender*: `Re-export` reutiliza o caminho fixado, sem diálogo.

4. *Reimporte no Godot*: automático ao focar o editor. O Godot regenera o personagem importado do zero - a cena assada é totalmente sobrescrita, então qualquer coisa editada *dentro* dela é perdida. É exatamente por isso que o seu trabalho vive em uma cena **wrapper** separada que instancia o personagem: o `.tscn` / `.gd` do wrapper fica intocado pela reimportação. Consulte [o contrato do Godot](02-advanced/03-godot.md#the-contract).

Quatro passos, nenhum dos quais descarta o seu trabalho a jusante - porque tudo fica em lugares que a regeneração não toca: seus pesos viajam no sidecar no Blender, e o seu código de jogo viaja no wrapper no Godot. Essa é a propriedade em torno da qual o pipeline inteiro é construído.

## O que ainda não é automatizado

Cada salto acima é manual de propósito - ainda não há hot reload através das fronteiras entre ferramentas. A maior lacuna é um link ao vivo Blender <-> Godot; esse e as outras direções ainda não construídas estão detalhados em [Adiado](../01-project/04-deferred.md).

## Ajuda e feedback

- Encontrou um bug ou quer um recurso? Abra uma issue: [issues do Proscenio](https://github.com/firebound/proscenio/issues).
- Quer contribuir? Consulte [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
- O aprofundamento por ferramenta vive nos guias de fluxo de trabalho: [Photoshop](02-advanced/01-photoshop.md), [Blender](02-advanced/02-blender.md), [Godot](02-advanced/03-godot.md).
