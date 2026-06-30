# UI feedback (defer)

Coisas que **funcionam** mas poderiam melhorar - UX polish, copy, layout,
defaults. Não são bugs (não vão para `bugs-found.md`), são
melhorias de qualidade. Eventualmente viram issues / spec próprio.

Formato livre. Quando tiver massa crítica de itens, agrupa por área e
promove pro backlog.

A reconciliação de 2026-06-11 removeu os itens já trabalhados (resolvidos saíram; adiados / gated / dropados foram pro [`deferred.md`](../deferred.md), [`gated.md`](../gated.md), [`dropped.md`](../dropped.md)).

2026-06-16: os três grupos que restavam aqui (Element panel, Outliner panel, Materials panel proposal) foram promovidos para [`backlog`](index.md#fila-da-sprint). O arquivo segue vivo como bucket de novo polish de UI/help surfaces que aparecer.

## Itens abertos (2026-06-27)

- **interactive-cheatsheet-cross-tool** [ui] [quick win] - Aplicar o padrão de cheatsheet em painel colapsável do spec 069 (Quick Armature) nas outras duas ferramentas interativas. O padrão: `layout.panel(default_closed=True)` + `emit_chord_layout` no `body`, gated no flag de sessão viva do modal (ex. `_modal_running`). Alvos: Automesh authoring (`apps/blender/operators/automesh/automesh_authoring.py` - hoje só tem `_draw_modal_indicator`, caixa simples, sem o chord mirror completo) e Edit Weights (`apps/blender/operators/skinning/edit_weights.py` - sem mirror de painel). Canônico do padrão: `.ai/conventions/code.md` "Interactive-tool gesture cheatsheet"; referência: a memória do cheatsheet das 3 ferramentas interativas. Cuidado: o spec 066 (#162) reescreveu o chord scheme do automesh (Tab-cycle), então ler o estado atual de `_status_bar.py` do automesh antes de espelhar. (O Manual Mesh do spec 070 já tem o mirror colapsável; sobram Automesh authoring + Edit Weights.)
