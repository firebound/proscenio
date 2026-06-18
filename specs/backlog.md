# Backlog

Entry point to where not-yet-shipped work is tracked. It routes to the per-domain homes so a reader finds the right one without re-deriving the layout, and it carries the QA-walk issue queue until each issue is routed into a home or into a numbered spec.

## Where work lives

- **Locked calls** - [`decisions.md`](decisions.md). Architectural and per-feature decisions that are settled (ADR-light: the call, the rationale, the revisit trigger).
- **Held behind a trigger** - [`gated.md`](gated.md). Real value, built only when a written demand signal fires.
- **Sequenced second-stage** - [`deferred.md`](deferred.md). Real value waiting its turn, usually to ride a related change so its cost is shared.
- **Declined** - [`dropped.md`](dropped.md). Value below cost, kept with its reasoning so a pruned item is never re-litigated.
- **Per-domain product homes** - [`backlog-ui-feedback.md`](backlog-ui-feedback.md) (UI polish), [`backlog-bugs-found.md`](backlog-bugs-found.md) (still-broken bugs), [`backlog-code-quality.md`](backlog-code-quality.md) (type/lint health), [`backlog-ik-ergonomics.md`](backlog-ik-ergonomics.md) (IK authoring), [`backlog-blender-6.md`](backlog-blender-6.md) (Blender 6 forward-compat), [`backlog-godot-importer.md`](backlog-godot-importer.md) (Godot import builders), [`backlog-photoshop.md`](backlog-photoshop.md) (Photoshop plugin), [`backlog-docs.md`](backlog-docs.md) (doc/help-text coverage). The last three were carved from the 2026-06-15 QA Companion audit; each is sized for a future area STUDY, not per-issue tracking.

## Fila da sprint

Issues nomeadas para a próxima sprint/spec, por app → painel. Formato: `**slug** [cat] - descrição` + refs de código (`F-xx` do audit, agora em [`backlog-docs.md`](backlog-docs.md) / [`backlog-bugs-found.md`](backlog-bugs-found.md), `arquivo:linha`, id de teste `BL-…` do [`checklist/blender.md`](../tools/qa-companion/checklist/blender.md)). Categorias: `[bug]` `[ui]` `[feature]` `[code]`; marcadores `[teste FAIL]`, `[quick win]`.

**`DECIDIR (STUDY):`** marca pergunta de design em aberto - resolver no STUDY, não no palpite. Fluxo: issue → STUDY → implementar (este arquivo não é spec).

### Blender · Global chrome

- _Feito na spec 036:_ `status-badge-tooltip-scope` (a legenda não cita mais `TOOL_SETTINGS`) + as três help-strings que mentiam. A spec 036 corrigiu só as strings erradas, NÃO a concisão/qualidade da cópia - o resto fica nos dois itens abaixo (feedback do walk pós-merge).
- **tooltip-copy-revision** `[ui]` - Revisar a cópia dos textos de help/tooltip: hoje longos e com informação dispersa. O `?` do painel explica o painel no geral; subpanels explicam o seu específico sem vazar. Cortar verborragia, conferir precisão.
- **help-popup-text-width** `[ui]` - O popup do `?` não ocupa toda a largura: o conteúdo é hand-wrapped em linhas curtas renderizadas por `layout.label` (que não faz wrap), então fica numa coluna estreita com margem direita vazia (img do walk). Reflow o conteúdo pra largura do popup (ou dimensionar o popup pelo conteúdo). Liga a `tooltip-copy-revision` + `docs-no-hard-wrap-rule`.
- **proscenio-list-cross-deselect** `[ui]` - Selecionar um item numa lista do Proscenio não limpa o highlight de active-row das OUTRAS listas: seleciono um bone no Skeleton, depois um element no Outliner, e o bone segue destacado na lista anterior (confuso). Cada lista tem seu `active_*_index` independente; sincronizar pro objeto/bone realmente ativo (estende o identity-sync do outliner da 043). Verificado no walk pós-merge.
- **native-list-standardization** `[ui]` - Padronizar as listas de todos os painéis no estilo outliner nativo do Blender: foldable items / accordion em hierarquia clara, busca nativa, marcações custom por painel. Caso concreto que resta: `wpaint-override-list-scroll` (a lista de slots já migrou para `template_list` na pruned 046; o `outliner-hierarchy-tree` foi dropado - ver [`dropped.md`](dropped.md): UIList do Blender não tem árvore nativa em Python).
- **list-multiselect** `[feature]` - Seleção múltipla (Shift/Ctrl) por lista, conforme o que o clique significa: multi nas listas que mapeiam seleção real do Blender, single nas que são "escolher um". O Outliner já entregou multi (extend/toggle por `event.shift`/`event.ctrl`); resta a seleção de bones do Skeleton e o set-em-lote nos overrides per-bone do Weight Paint, que dependem do componente de lista ainda não construído (cf. `wpaint-override-list-scroll`). Trava técnica: o `template_list` só tem um `active_index`, então multi exige estado de selecionado por item + marcador custom (o highlight múltiplo é aproximação, não nativo).

### Blender · Outliner

- **proscenio-y-depth-layers** `[feature]` - Controle de profundidade em Y dos objetos (meshes e sprites) para evitar z-fight entre planos após o import do Photoshop; ex.: organizar em "camadas" estilo Photoshop, com uma distância aplicada conforme a profundidade. **`DECIDIR (STUDY):`** mecanismo (auto pela ordem de camada do PS vs manual) e se isso entra no schema/export ou é só authoring no Blender.

### Blender · Element

- **incorporate-blender-mesh-as-element** `[feature]` - Botão para incorporar uma malha criada no Blender como elemento do fluxo do Proscenio, quando o ativo for um objeto do Blender. **`DECIDIR (STUDY):`** o que "incorporar" seta (`element_type`, props default, material) e quais pré-condições.
- **element-driver-management** `[ui]` - Lista de todos os "drive from bone" do elemento, permitindo excluir / alterar / adicionar vários; hoje só substitui e é impossível remover um driver pelo painel. (distinto do gated `sticky-panel`, que é o painel fixo durante a edição de pose)
- **sprite-centered-vs-origin-doc** `[ui]` - **`DECIDIR (STUDY):`** `centered` (`object_props.py:104`, só existe para `sprite`) deve derivar da origin importada do `[origin]` do PS ou continuar toggle manual? (A linha de help que documenta a distinção `centered` vs origin já está na spec 036; aqui resta só a pergunta de design.)
- **element-header-active-name** `[ui]` - Header do painel Element mostrar "Element: <nome>" do objeto ativo, no MESMO padrão do header de Skeleton (bl_label vazio + draw_header com threshold de largura). A spec 036 entregou isso como readout no CORPO (uma linha com o nome no Active Mesh/Sprite), mas o pedido era o header; corrigir pro padrão Skeleton e remover o readout do corpo. (feedback do walk pós-merge)
- _Feito na spec 036:_ `reproject-uv-purpose-clarity`, `sprite-frame-clamp`, `sprite-frame-label-rename`. `texture-region-hide-for-mesh` (F-18) foi DROPADO - premissa falsa, Texture Region é funcional pra mesh (`resolve_region` honra a região manual + Snap-to-UV é mesh-only). O gated `atlas-region-helper` continua em [`gated.md`](gated.md).

### Blender · Skeleton

- **qa-rotation-mode** `[feature]` - Escolha de rotation-mode no Quick Armature (Euler-Y vs quaternion) + safe swap. O export já está correto dos dois jeitos (o writer colapsa ambos via `_quat_to_screen_angle`), então o valor é só clareza de autoria. **`DECIDIR (STUDY):`** o safe-swap pode quebrar animações silenciosamente se errado - validar a estratégia antes de implementar.
- **qa-quickarm-interaction-revision** `[feature]` - Revisar o vocabulário de interação do modal do Quick Armature: os taps de modificador (Shift/Ctrl/etc.) são ruins e precisam ser repensados, e o esquema de chords está saturado (Shift/Alt/Ctrl/X/Z ocupados). No esquema revisto, incluir o pick-parent na viewport (hit-testing de ponta de bone para reparentar mid-sketch) - há demanda. A "saturação de chords" não é bloqueio, é o escopo. **`DECIDIR (STUDY):`** o novo vocabulário de interação (o que substitui os taps) antes de encaixar o pick-parent. Absorve o antigo `qa-pick-parent-viewport`.

### Blender · Mesh Generation

- **automesh-shared-params-surfacing** `[ui]` - Elevar/reorganizar os parâmetros que hoje só vivem no subpanel Automesh-from-Alpha mas afetam também o Automesh Interactive. Findings F-47 e F-48.

### Blender · Weight Paint

- **wpaint-override-list-scroll** `[ui]` - A lista de override per-bone fica gigantesca e empurra todo o resto do Bind para baixo; usar a lista padrão do projeto ou, no mínimo, uma scrollbar. Caso concreto de `native-list-standardization`.
- **wpaint-named-snapshots** `[ui]` - Snapshots nomeados / save points com escolha de para onde voltar; o snapshot atual é confuso (não dá pra saber se volta para antes ou depois da pintura). Findings F-55/F-66.

## Itens spec-sized (não cabem numa sprint de polish)

Cada um é grande o bastante para virar spec próprio; estão aqui só para não se perderem.

- **materials-panel** `[feature]` - (Reaberto em 2026-06-16: a spec 036 tinha avaliado e dropado, mas o item foi mantido aqui a pedido; a 036 foi atualizada para refletir isso. O racional do drop - path-repair duplica o "Find Missing Files" nativo, e o resto é superfície especulativa - precisa ser respondido no STUDY próprio antes de construir.) Painel dedicado para inspeção/configuração de materials (hoje o usuário caça no Shader Editor ou em Properties > Material por objeto). Conteúdo proposto: inspeção (lista de materials com nome, users, Image Texture nodes, filepath); quick config cross-material aplicável a todos/seleção/regex (Interpolation Closest/Linear/Cubic/Smart; Blend mode Opaque/Clip/Hashed/Blend - o importer hoje seta `HASHED` por default, que faz dither stipple em pixels semi-transparentes, e pixel art quer `CLIP`; Extension; Alpha mode; Alpha threshold; Mipmaps/Anisotropic); bulk image-path fix ("Repair" com file picker); material report (únicos, compartilhando imagem, `material_isolated=True`). **`DECIDIR (STUDY):`** escopo - painel completo vs a alternativa low-effort (checkbox "Pixel art" no Active Sprite que seta Closest + nearest filter no material ativo).
- **skin-coordination** `[feature]` - Conjuntos de attachment nomeados entre slots (estilo "skin" do Spine): um switch troca um attachment por slot em vários slots de uma vez. Superfície de coordenação de três apps (schema + writer + selector de runtime no Godot), apoiada na camada de runtime que o plugin importer-only do Godot deliberadamente não tem. **`DECIDIR (STUDY):`** forma - `skins[]` de primeira classe depende do format-migration-path; a forma aditiva via generated-animations não depende, mas tem semântica de runtime frágil a overrides.

## Quick wins já em homes de backlog (ponteiros)

Issues simples/baratas que já vivem num home de backlog; **permanecem lá** e aqui ficam só como ponteiro para a fila.

- **sprite-frame-preview-help-orphan** `[bug]` `[quick win]` - Na spec 036 (PR 1): re-wirar o `?` órfão do topic `sprite_frame_preview` (junto com o `pose_library`) + um teste de cobertura reversa que prende a família inteira de topics. Fecha o item 1.13/9 do checklist.
- **docs-no-hard-wrap-rule** `[code]` `[quick win]` - Codificar a regra no-hard-wrap em [`.ai/conventions/docs.md`](../.ai/conventions/docs.md) ("prosa é uma linha por parágrafo/bullet; deixar o editor soft-wrap; nunca hand-wrap markdown ou parágrafos de comentário"); o reflow em si segue oportunista. → [`backlog-code-quality.md`](backlog-code-quality.md). cf. `tooltip-copy-revision`.
