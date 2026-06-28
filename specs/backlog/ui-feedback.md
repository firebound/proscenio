# UI feedback (defer)

Coisas que **funcionam** mas poderiam melhorar - UX polish, copy, layout,
defaults. Não são bugs (não vão para `bugs-found.md`), são
melhorias de qualidade. Eventualmente viram issues / spec próprio.

Formato livre. Quando tiver massa crítica de itens, agrupa por área e
promove pro backlog.

A reconciliação de 2026-06-11 removeu os itens já trabalhados (resolvidos saíram; adiados / gated / dropados foram pro [`deferred.md`](../deferred.md), [`gated.md`](../gated.md), [`dropped.md`](../dropped.md)).

2026-06-16: os três grupos que restavam aqui (Element panel, Outliner panel, Materials panel proposal) foram promovidos para [`backlog`](index.md#fila-da-sprint). O arquivo segue vivo como bucket de novo polish de UI/help surfaces que aparecer.

## Itens abertos (2026-06-27)

- **interactive-cheatsheet-cross-tool** [ui] [quick win] - Aplicar o padrão de cheatsheet em painel colapsável do spec 069 (Quick Armature) nas outras duas ferramentas interativas. O padrão: `layout.panel(default_closed=True)` + `emit_chord_layout` no `body`, gated no flag de sessão viva do modal (ex. `_modal_running`). Alvos: Automesh authoring (`apps/blender/operators/automesh/automesh_authoring.py` - hoje só tem `_draw_modal_indicator`, caixa simples, sem o chord mirror completo) e Edit Weights (`apps/blender/operators/skinning/edit_weights.py` - sem mirror de painel). Canônico do padrão: `.ai/conventions/code.md` "Interactive-tool gesture cheatsheet"; referência: a memória do cheatsheet das 3 ferramentas interativas. Cuidado: o spec 066 (#162) reescreveu o chord scheme do automesh (Tab-cycle), então ler o estado atual de `_status_bar.py` do automesh antes de espelhar.

- **mesh-pen-authoring** [feature] `DECIDIR (STUDY):` - Um modo NOVO de **criar** malha do zero com uma pen tool estilo Illustrator/Spine: o primeiro clique larga o primeiro vért e o contorno cresce ponto a ponto até fechar o loop, triangulando numa malha SIMPLE (não dense). Duas partes que são uma feature só: (1) **criar do zero** sem precisar de element/import/alpha-trace antes (hoje o contour pen do spec 066 só edita o `output.outer` de uma mesh element JA existente, dentro do modal Automesh Interactive que é gated em `element_type == "mesh"` e termina no APPLY - não cria do nada); (2) **re-editar persistente** - voltar numa malha ja aplicada e adicionar/mover pontos depois (o 066 é sessão one-shot). Reusa a click-pen machine + a triangulação do 066, mas o ponto de entrada e o ciclo de vida mudam. Decisões de design: a ferramenta cria o element + a mesh a partir do contorno desenhado (qual `element_type`, qual textura/material inicial)? a re-entrada recarrega o outline/pontos anteriores (persistir o estado de autoria no objeto) ou edita a geometria viva do `Polygon2D`? como compõe com weights/slots/drivers ja presentes? Refs: `apps/blender/operators/automesh/automesh_authoring.py` (a click-pen machine + `AuthoringStage` OUTER/EDIT_OUTLINE/EDIT_INTERIOR_POINTS), `apps/blender/operators/incorporate.py` (criação de element), spec 066 (mesh-generation-interaction).

- **mesh-revert-to-plane** [feature] `DECIDIR (STUDY):` - Revert de um clique de um element gerado pelo Proscenio de volta ao plane original importado com textura (desfaz tudo que o Proscenio fez - automesh, skinning, dados de element - restaurando o quad simples + o material de imagem). Distinto do re-import por PSD (spec 067, que RE-RODA o automesh): aqui o destino é o quad plano, não uma malha re-gerada. Decisão de design: restaurar de um snapshot do plane original guardado, ou reconstruir um quad a partir da textura + bounds do element? O que acontece com weights / slots / drivers / parenting no revert (avisar e limpar, ou bloquear). Refs: `apps/blender/operators/incorporate.py`, `apps/blender/importers/photoshop/planes.py`, contrato de re-import (specs 055 / 067).
