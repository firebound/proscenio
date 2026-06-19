# Backlog

Entry point to where not-yet-shipped work is tracked. It routes to the per-domain homes so a reader finds the right one without re-deriving the layout, and it carries the QA-walk issue queue until each issue is routed into a home or into a numbered spec.

## Where work lives

- **Locked calls** - [`decisions.md`](decisions.md). Architectural and per-feature decisions that are settled (ADR-light: the call, the rationale, the revisit trigger).
- **Held behind a trigger** - [`gated.md`](gated.md). Real value, built only when a written demand signal fires.
- **Sequenced second-stage** - [`deferred.md`](deferred.md). Real value waiting its turn, usually to ride a related change so its cost is shared.
- **Declined** - [`dropped.md`](dropped.md). Value below cost, kept with its reasoning so a pruned item is never re-litigated.
- **Per-domain product homes** - [`backlog-ui-feedback.md`](backlog-ui-feedback.md) (UI polish), [`backlog-bugs-found.md`](backlog-bugs-found.md) (still-broken bugs), [`backlog-code-quality.md`](backlog-code-quality.md) (type/lint health), [`backlog-ik-ergonomics.md`](backlog-ik-ergonomics.md) (IK authoring), [`backlog-blender-6.md`](backlog-blender-6.md) (Blender 6 forward-compat), [`backlog-godot-importer.md`](backlog-godot-importer.md) (Godot import builders), [`backlog-photoshop.md`](backlog-photoshop.md) (Photoshop plugin), [`backlog-docs.md`](backlog-docs.md) (doc/help-text coverage). The last three were carved from the 2026-06-15 QA Companion audit; each is sized for a future area STUDY, not per-issue tracking.
- **Closed-PR review sweep** - [`backlog-coderabbit-nitpicks.md`](backlog-coderabbit-nitpicks.md). The 2026-06-18 harvest of CodeRabbit nitpicks/quick-wins across all 135 closed PRs, validated against current `main` (most flagged items were already fixed by the restructure and dropped). One report pending routing into the per-domain homes above.

## Fila da sprint

A maioria das issues de UI/UX dos walks pós-spec-036 foi promovida em 2026-06-18 para [spec 049](049-blender-ui-polish/STUDY.md) (10 itens now-able) e [spec 050](050-blender-authoring-design/STUDY.md) (3 decisões de autoria travadas). O `show-provenance-overlay` toggle inerte saiu de [`backlog-bugs-found.md`](backlog-bugs-found.md) no mesmo movimento (agora no spec 049). Voltaram/sobraram dois itens:

### Blender · Skeleton

- **qa-quickarm-interaction-revision** `[feature]` - Revisar o vocabulário de interação do modal do Quick Armature: os taps de modificador (Shift/Ctrl/etc.) são ruins e precisam ser repensados, e o esquema de chords está saturado (Shift/Alt/Ctrl/X/Z ocupados). No esquema revisto, incluir o pick-parent na viewport (hit-testing de ponta de bone para reparentar mid-sketch) - há demanda. **`DECIDIR (STUDY):`** o novo vocabulário de interação (o que substitui os taps) antes de encaixar o pick-parent. Absorve o antigo `qa-pick-parent-viewport`. (Tirado do spec 050 em 2026-06-18: a redesign de interação precisa de mais tempo de decisão.)

### Blender · Sprite (PS -> Blender -> Godot)

- **sprite-origin-cleanup** `[bug]` `[quick win]` - O `[origin]` do PS vira pivô só pra SPRITE (o import põe a `location` no ponto -> o writer deriva `Sprite2D.offset` -> a Godot aplica `centered`+`offset`). Pra MESH é no-op downstream: Polygon2D não tem pivô, os verts são assados em absoluto/bone-local e o import compensa a geometria, então a origin se cancela. Acertos: (1) tornar `[origin]` sprite-only (o PS não emite pra camada mesh, ou o validador avisa); (2) remover o toggle `centered` manual (vestigial, acoplado ao offset, fica sempre `true`); (3) teste de round-trip `[origin]` PS -> pivô Sprite2D. (Saiu do spec 050 em 2026-06-18 - não era decisão de design.)

Formato para novas issues, por app → painel: `**slug** [cat] - descrição` + refs de código (`arquivo:linha`, id de teste `BL-…` do [`checklist/blender.md`](../tools/qa-companion/checklist/blender.md)). Categorias: `[bug]` `[ui]` `[feature]` `[code]`; marcadores `[teste FAIL]`, `[quick win]`. **`DECIDIR (STUDY):`** marca pergunta de design em aberto - resolver no STUDY, não no palpite. Fluxo: issue → STUDY → implementar (este arquivo não é spec).

## Itens spec-sized (não cabem numa sprint de polish)

Cada um é grande o bastante para virar spec próprio; estão aqui só para não se perderem.

- **materials-panel** `[feature]` - (Reaberto em 2026-06-16: a spec 036 avaliou e descartou, mas o item foi mantido aqui a pedido. O racional do descarte - path-repair duplica o "Find Missing Files" nativo, e o resto é superfície especulativa - precisa ser respondido no STUDY próprio antes de construir.) Painel dedicado para inspeção/configuração de materials (hoje o usuário caça no Shader Editor ou em Properties > Material por objeto). Conteúdo proposto: inspeção (lista de materials com nome, users, Image Texture nodes, filepath); quick config cross-material aplicável a todos/seleção/regex (Interpolation Closest/Linear/Cubic/Smart; Blend mode Opaque/Clip/Hashed/Blend - o importer hoje seta `HASHED` por default, que faz dither stipple em pixels semi-transparentes, e pixel art quer `CLIP`; Extension; Alpha mode; Alpha threshold; Mipmaps/Anisotropic); bulk image-path fix ("Repair" com file picker); material report (únicos, compartilhando imagem, `material_isolated=True`). **`DECIDIR (STUDY):`** escopo - painel completo vs a alternativa low-effort (checkbox "Pixel art" no Active Sprite que seta Closest + nearest filter no material ativo).
- **skin-coordination** `[feature]` - Conjuntos de attachment nomeados entre slots (estilo "skin" do Spine): um switch troca um attachment por slot em vários slots de uma vez. Superfície de coordenação de três apps (schema + writer + selector de runtime no Godot), apoiada na camada de runtime que o plugin importer-only do Godot deliberadamente não tem. **`DECIDIR (STUDY):`** forma - `skins[]` de primeira classe depende do format-migration-path; a forma aditiva via generated-animations não depende, mas tem semântica de runtime frágil a overrides.

## Quick wins já em homes de backlog (ponteiros)

Issues simples/baratas que já vivem num home de backlog; **permanecem lá** e aqui ficam só como ponteiro para a fila.

- **docs-no-hard-wrap-rule** `[code]` `[quick win]` - Codificar a regra no-hard-wrap em [`.ai/conventions/docs.md`](../.ai/conventions/docs.md) ("prosa é uma linha por parágrafo/bullet; deixar o editor soft-wrap; nunca hand-wrap markdown ou parágrafos de comentário"); o reflow em si segue oportunista. → [`backlog-code-quality.md`](backlog-code-quality.md). cf. `tooltip-copy-revision`.
