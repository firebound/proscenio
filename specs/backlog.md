# Backlog

Ponto de entrada para onde o trabalho ainda-não-entregue é rastreado. Roteia para os homes certos para que um leitor ache o lugar sem re-derivar o layout.

## Onde o trabalho vive

- **Specs planejados** - [`_index.md`](_index.md). A onda de drenagem de backlog de 2026-06-20 roteou os backlogs por-domínio (bugs, Godot importer, Photoshop, IK, docs, code-quality, blender-6, sonarqube e a varredura de nitpicks do CodeRabbit) para specs temáticos focados (051-063), cada um STUDY-first. Os arquivos `backlog-*.md` por-domínio agora são ponteiros finos para os specs que os absorveram.
- **Locked calls** - [`decisions.md`](decisions.md). Decisões arquiteturais e por-feature já travadas (ADR-light: a decisão, o racional, o gatilho de revisão).
- **Held behind a trigger** - [`gated.md`](gated.md). Valor real, construído só quando um sinal de demanda escrito dispara.
- **Sequenced second-stage** - [`deferred.md`](deferred.md). Valor real esperando a vez, geralmente para pegar carona numa mudança relacionada e dividir o custo.
- **Declined** - [`dropped.md`](dropped.md). Valor abaixo do custo, mantido com o racional para um item podado nunca ser re-litigado.
- **Buckets vivos (recebem achados novos)** - [`backlog-bugs-found.md`](backlog-bugs-found.md) (bugs ainda-quebrados de teste manual), [`backlog-ui-feedback.md`](backlog-ui-feedback.md) (polish de UI), [`backlog-code-quality.md`](backlog-code-quality.md) (saúde de tipo/lint, com a baseline de auditoria preservada). Esvaziados na drenagem de 2026-06-20; seguem abertos para o que walk novo achar.

## Fila da sprint

O grosso das issues de UI/UX dos walks pós-spec-036 virou as specs 049 e 050 em 2026-06-18 (ver [`_index.md`](_index.md)). A onda de drenagem de 2026-06-20 transformou o resto dos backlogs abertos nos specs 051-063. Nada está pendente de roteamento na fila no momento.

Formato para novas issues, por app → painel: `**slug** [cat] - descrição` + refs de código (`arquivo:linha`, id de teste `BL-…` do [`checklist/blender.md`](../tools/qa-companion/checklist/blender.md)). Categorias: `[bug]` `[ui]` `[feature]` `[code]`; marcadores `[teste FAIL]`, `[quick win]`. **`DECIDIR (STUDY):`** marca pergunta de design em aberto - resolver no STUDY, não no palpite. Fluxo: issue → STUDY → implementar (este arquivo não é spec).

## Itens que viraram specs na drenagem de 2026-06-20

Os itens spec-sized e a issue que tinha voltado para a fila agora têm spec próprio (ver [`_index.md`](_index.md)):

- **materials-panel** -> spec 057 materials-panel. O STUDY respondeu o racional de descarte do spec 036 (o painel completo segue fora; só o caso pixel-art tem dor real) e corrigiu a premissa do texto antigo: o default problemático do importer é a interpolação de textura não-setada (`Linear`, que borra pixel art), não o blend mode `HASHED` - o importer roteia todo modo para `BLEND`.
- **skin-coordination** -> spec 059 skin-coordination. Forma `skins[]` de primeira classe gated atrás de `format-migration-path` e da janela do spec 037; a forma aditiva via `Slot` é a ponte pré-gate. Gated/sequenciado, não pronto para construir.
- **qa-quickarm-interaction-revision** -> spec 058 quick-armature-interaction-redesign. Redesign do vocabulário de interação do modal (esquema mode-layer recomendado) + pick-parent na viewport; absorve o antigo `qa-pick-parent-viewport`.
- **docs-no-hard-wrap-rule** -> spec 054 code-review-cleanup. Codificar a regra no-hard-wrap em [`.ai/conventions/docs.md`](../.ai/conventions/docs.md).
