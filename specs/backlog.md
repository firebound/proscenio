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

- **status-badge-tooltip-scope** `[ui]` - A tooltip de uma status badge deve mostrar só o que aquela badge representa; hoje qualquer badge abre o texto inteiro da legenda, ainda desatualizado (menciona `TOOL_SETTINGS`, que não representa mais "só funciona no Blender"). Finding F-116.
- **tooltip-copy-revision** `[ui]` - Revisar o texto de todas as tooltips: o `?` do painel explica o painel no geral; subpanels explicam suas funcionalidades específicas, sem vazar entre subpanels salvo estritamente necessário. (As quebras de linha indevidas em tooltips são o repro de `docs-no-hard-wrap-rule`, nos quick wins abaixo.)
- **native-list-standardization** `[ui]` - Padronizar as listas de todos os painéis no estilo outliner nativo do Blender: foldable items / accordion em hierarquia clara, busca nativa, marcações custom por painel. Caso concreto que resta: `wpaint-override-list-scroll` (a lista de slots já migrou para `template_list` na pruned 046; o `outliner-hierarchy-tree` foi dropado - ver [`dropped.md`](dropped.md): UIList do Blender não tem árvore nativa em Python).
- **list-multiselect** `[feature]` - Seleção múltipla (Shift/Ctrl) por lista, conforme o que o clique significa: multi nas listas que mapeiam seleção real do Blender, single nas que são "escolher um". O Outliner já entregou multi (extend/toggle por `event.shift`/`event.ctrl`); resta a seleção de bones do Skeleton e o set-em-lote nos overrides per-bone do Weight Paint, que dependem do componente de lista ainda não construído (cf. `wpaint-override-list-scroll`). Trava técnica: o `template_list` só tem um `active_index`, então multi exige estado de selecionado por item + marcador custom (o highlight múltiplo é aproximação, não nativo).

### Blender · Outliner

- **proscenio-y-depth-layers** `[feature]` - Controle de profundidade em Y dos objetos (meshes e sprites) para evitar z-fight entre planos após o import do Photoshop; ex.: organizar em "camadas" estilo Photoshop, com uma distância aplicada conforme a profundidade. **`DECIDIR (STUDY):`** mecanismo (auto pela ordem de camada do PS vs manual) e se isso entra no schema/export ou é só authoring no Blender.

### Blender · Element

- **incorporate-blender-mesh-as-element** `[feature]` - Botão para incorporar uma malha criada no Blender como elemento do fluxo do Proscenio, quando o ativo for um objeto do Blender. **`DECIDIR (STUDY):`** o que "incorporar" seta (`element_type`, props default, material) e quais pré-condições.
- **element-header-active-name** `[ui]` - Header do painel mostrar `: <nome>` do elemento ativo ("Active Sprite: <obj_name>"), deixando claro que é o ativo.
- **element-driver-management** `[ui]` - Lista de todos os "drive from bone" do elemento, permitindo excluir / alterar / adicionar vários; hoje só substitui e é impossível remover um driver pelo painel. (distinto do gated `sticky-panel`, que é o painel fixo durante a edição de pose)
- **texture-region-hide-for-mesh** `[ui]` - Ocultar o subpanel Texture Region quando o tipo for mesh (Polygon2D não usa). Finding F-18.
- **reproject-uv-purpose-clarity** `[ui]` - O propósito de Reproject UV / UV bounds / Texture Region não está claro (a projeção funciona). cf. o bug aberto em [`backlog-bugs-found.md`](backlog-bugs-found.md) ("Reproject UV: UV resultante rotacionada/flipada") e o gated `atlas-region-helper` (mesmo território de UV/region authoring).
- **sprite-frame-clamp** `[ui]` - Clampar `Initial frame` em `[0, hframes*vframes-1]` (hoje aceita qualquer int; `min=0` existe, falta `max`/`soft_max`). Idem o campo `frame`. `object_props.py:124`.
- **sprite-frame-label-rename** `[ui]` - Renomear a label `Initial frame` para `Frame` (em animação, quando keyframado, não é "initial" - é o frame value sendo animado; alinha com o Sprite2D do Godot). Manter a description atual. `object_props.py:124`.
- **sprite-centered-vs-origin-doc** `[ui]` - `centered` (`object_props.py:104`) só existe para `sprite`, não `mesh`; confunde com a origin vinda do `[origin]` do PS (são pivots separados). Documentar a distinção no help do Active Sprite. **`DECIDIR (STUDY):`** `centered` deve derivar da origin importada ou continuar toggle manual?

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

- **sprite-frame-preview-help-orphan** `[bug]` `[quick win]` - O help topic `sprite_frame_preview` é orphan (sem entry point na UI); re-wirar o botão `?` nos `_draw_*.py` das sub-boxes (`draw_subbox_header` ficou sem callers após o restructure #96). Fecha o item 1.13/9 do checklist. → [`backlog-bugs-found.md`](backlog-bugs-found.md).
- **docs-no-hard-wrap-rule** `[code]` `[quick win]` - Codificar a regra no-hard-wrap em [`.ai/conventions/docs.md`](../.ai/conventions/docs.md) ("prosa é uma linha por parágrafo/bullet; deixar o editor soft-wrap; nunca hand-wrap markdown ou parágrafos de comentário"); o reflow em si segue oportunista. → [`backlog-code-quality.md`](backlog-code-quality.md). cf. `tooltip-copy-revision`.
