# Backlog

Ponto de entrada para onde o trabalho ainda-não-entregue é rastreado. Roteia para os homes certos para que um leitor ache o lugar sem re-derivar o layout.

## Onde o trabalho vive

- **Specs planejados** - [`_index.md`](../_index.md). A onda de drenagem de backlog de 2026-06-20 roteou os backlogs por-domínio (bugs, Godot importer, Photoshop, IK, docs, code-quality, blender-6, sonarqube e a varredura de nitpicks do CodeRabbit) para specs temáticos focados (051-063), cada um STUDY-first. Os ponteiros finos `backlog-*.md` por-domínio que sobravam foram removidos em 2026-06-21; recupere os originais do histórico git (os specs que os absorveram estão no índice).
- **Locked calls** - [`decisions.md`](../decisions.md). Decisões arquiteturais e por-feature já travadas (ADR-light: a decisão, o racional, o gatilho de revisão).
- **Held behind a trigger** - [`gated.md`](../gated.md). Valor real, construído só quando um sinal de demanda escrito dispara.
- **Sequenced second-stage** - [`deferred.md`](../deferred.md). Valor real esperando a vez, geralmente para pegar carona numa mudança relacionada e dividir o custo.
- **Declined** - [`dropped.md`](../dropped.md). Valor abaixo do custo, mantido com o racional para um item podado nunca ser re-litigado.
- **Buckets vivos (recebem achados novos)** - [`ui-feedback.md`](ui-feedback.md) (polish de UI), [`code-quality.md`](code-quality.md) (saúde de tipo/lint, com a baseline de auditoria preservada), [`code-audit/`](code-audit/index.md) (smells estruturais de `apps/blender` - god modules, código mal colocado, DRY, código morto, qualidade de teste - da auditoria multi-agente de 2026-06-28, verificada adversarialmente; arquivos temáticos + refutados). Esvaziados na drenagem de 2026-06-20; seguem abertos para o que walk novo achar. (Bugs de teste manual ainda-quebrados usam o nome `bugs-found.md`, recriado do histórico git quando aparecer o primeiro - vazio, foi removido.)

## Fila da sprint

O grosso das issues de UI/UX dos walks pós-spec-036 virou as specs 049 e 050 em 2026-06-18 (ver [`_index.md`](../_index.md)). A onda de drenagem de 2026-06-20 transformou o resto dos backlogs abertos nos specs 051-063. Nada está pendente de roteamento na fila no momento.

Formato para novas issues, por app → painel: `**slug** [cat] - descrição` + refs de código (`arquivo:linha`, id de teste `BL-…` do [`checklist/blender.md`](../../tools/qa-companion/checklist/blender.md)). Categorias: `[bug]` `[ui]` `[feature]` `[code]`; marcadores `[teste FAIL]`, `[quick win]`. **`DECIDIR (STUDY):`** marca pergunta de design em aberto - resolver no STUDY, não no palpite. Fluxo: issue → STUDY → implementar (este arquivo não é spec).
