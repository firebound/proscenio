# UI feedback (defer)

Coisas que **funcionam** mas poderiam melhorar - UX polish, copy, layout,
defaults. Não são bugs (não vão para `[!]` no backlog-manual-testing.md), são
melhorias de qualidade. Eventualmente viram issues / spec próprio.

Formato livre. Quando tiver massa crítica de itens, agrupa por área e
promove pro backlog.

## Cross-panel / general

- Drag-and-drop reorder de subpanels (Blender nativo + outros plugins permitem) - aplicar onde der.

## Active Sprite panel

- Mostrar nome do mesh selecionado no header do panel: "Active Sprite: <obj_name>" em vez de só "Active Sprite".
- `Initial frame` field deveria ser clamped em `[0, hframes*vframes-1]` (hoje aceita qualquer int). Pode causar confusão - usuário digita 99 sem feedback de que só existem 4 frames. Idem `frame` field se editado fora desse range. UI atual: `min=0` está, `max` falta (ou usa `soft_max`).
- `Initial frame` label confunde no contexto de animação. Quando usuário keyframa o field, ele NÃO é "initial" - é THE frame value sendo animado. Renomear label pra `Frame` (mais simples, alinha com Sprite2D do Godot). Description pode manter "frame index at rest pose; animation tracks override at runtime" - explica o duplo papel sem polluir a label. File: `apps/blender/properties/object_props.py:124`.
- `Drive from Bone` - expression default `var` é misleading pra o caso `Frame index`. Bone rotation em radianos típica varia `[-pi, pi]`, mas frame range é `[0, hframes*vframes-1]`. Expression `var` faz negativos clamparem em 0 e valores acima de N-1 clamparem no max - usuário rotaciona bone e parece que driver não funciona.
- **Expression como string crua é hostil** pra usuário não-programador: `var * 0.5 + 0.3` parece números mágicos. Usuário tem que entender que `var` = rotação em radianos e fazer álgebra mental pra mapear `[bone_min, bone_max]` em `[prop_min, prop_max]`. Animator não pensa nisso - pensa em "quando bone rotaciona deste jeito, sprite mostra essa faixa".
- **Proposta UX:** substituir Expression por 2 ranges editáveis:
  - "Bone rotation range" - 2 sliders / fields: `from -90°` to `+90°`
  - "Sprite property range" - 2 sliders: `from 0` to `3` (pra Frame index, com default = full range; pra Region X, default = `0` to `1`)
  - Auto-genera expression linear: `(var - bone_min) / (bone_max - bone_min) * (prop_max - prop_min) + prop_min`
  - Modo "Advanced" colapsável que expõe a string crua pra power users que querem expressões custom (não-lineares, branching, etc).
- **Bonus:** preview HUD na panel mostrando "agora bone está em 0.78 rad (45°) → property = 2 (de 0..3)" enquanto rotaciona.
- `Drive from Bone` debug é dolorido. Pra inspecionar driver value live precisa abrir Drivers Editor em outra janela / area, e ao mover seleção pra entrar em Pose Mode, perde o foco no fcurve no Drivers Editor (precisa re-clicar nele). Alternativas pro Active Sprite panel:
  - Quando driver existe em `proscenio.<target>`, mostrar inline: "Driver from `<armature>:<bone>.<axis>` - value: 0.78 rad (45°) → frame: 3".
  - Quick action button "Inspect Driver" abre uma popup compacta com expression, variable value, current driver result.
  - Botão "Reset Driver" (apaga + recria) pra iterar em expressions sem mexer no Drivers Editor.
- **Mesh <-> Pose Mode swap dolorido**: pra animar drivers, usuário precisa selecionar bone em Pose Mode na armature → active object muda → Active Sprite panel some (porque depende do mesh estar active). Não há jeito visual fácil de "ver os campos do sprite" enquanto manipula o bone. Sugestões:
  - Mostrar `Sprite watched: <obj>` no header do Drive from bone box quando active object é armature/pose bone que tem driver alimentando algum `proscenio.*` de outro mesh.
  - Pin / sticky panel mode - usuário marca `Active Sprite: locked to <obj>` e o painel para de seguir active object.
  - Side-by-side debug HUD: pequeno overlay no viewport com `frame: 2` / `region_x: 0.45` enquanto bone rotaciona.

- **`Centered` vs origin do PS - clarificar / documentar.** `centered` (`object_props.py:104`, `name="Centered"`, "Whether the Sprite2D's offset centers on its origin") só existe pro element_type `sprite`, NÃO pro `mesh`: Polygon2D não tem conceito de "centered" (os vertices carregam a posição). Confunde porque a origem do objeto vem do `[origin]` do PS - `centered` (pivot do Sprite2D no Godot) e origin (pivot do objeto vindo do PS) são coisas separadas. Documentar a distinção no help do Active Sprite e considerar se `centered` deveria ser derivado da origin importada em vez de toggle manual. (A questão "sprite que não é quad / travar ferramentas mesh-only" virou entrada em backlog.md "Element-type gating".)

## Active Slot panel

- **Falta overview de todos os slots na cena.** Active Slot só mostra UM slot por vez (o ativo na seleção). Pra ver "quais slots existem? quem é parent de quem? onde estão?", usuário precisa caçar os Empties no outliner um por um. Sugestões:
  - Subpanel novo `Slots` (ou seção dentro de `Outliner` panel) listando todos os Empties com `is_slot=True`, mostrando nome + parent (bone/object/unparented) + número de attachments.
  - Click numa linha = seleciona o slot Empty + foca câmera nele.
- **Path A vs Path B unclear:** "Create Slot" no Skeleton panel parece o mesmo botão pros 2 fluxos, mas comportamento depende do contexto (modo + seleção). Usuário não sabe qual modo usar pra qual resultado. Sugestões:
  - Disable button + tooltip "select a bone in pose mode OR meshes in object mode" quando contexto inválido.
  - Hint inline antes do botão: "Pose Mode + bone selected: BONE-parented slot. Object Mode + N meshes: OBJECT slot wrapping selection".
- **Mesh repositioning quando vira attachment de slot novo é confuso.** Path B reparenteia meshes sem feedback visual ("ué, por que minha espada pulou pra outro canto da cena?"). Idealmente o operator deve preservar world position SEMPRE (bug em backlog-bugs-found.md), e o panel deve mostrar transform delta se inevitável.
- **Slot vinculado a quê?** Quando slot é criado sem bone (Path B sem seed parented a bone), Empty fica solto na cena - usuário não sabe que precisa parentear depois. Active Slot panel mostra "bone: (unparented)" mas nem todos vão entender o significado. Sugestão: warning amarelo no panel "slot has no parent - attachments will not follow any bone" + botão "Parent to Bone..." para fix rápido.

## Slots panel (lista de slots do projeto)

- **Lista de slots fora do padrão das outras listas.** O painel Slots (spec 022) lista cada slot Empty via `col.row()` + botão por linha (`panels/slots.py:62-74`), enquanto Outliner e Skeleton usam `template_list` (UIList nativo com filtro / scroll / multi-seleção). Padronizar a lista de slots pro mesmo UIList deixa a UI consistente. (A queixa antiga "Falta overview de todos os slots na cena" já foi atendida por este painel - ele lista todos os slots; o que falta agora é o widget bater com o resto.)
- **Animar qual slot está ativo - UX implícita.** Dá pra animar a troca de attachment hoje: o slot system emite tracks `slot_attachment` (visibility toggle por attachment), e a action `swing` do slot_swap faz exatamente isso flipando club / sword. Mas não há botão "keyframe active attachment" - o autor precisa saber keyframar visibility / `slot_default` na mão. Considerar um affordance de autoring pra keyframar a troca de slot direto do painel. (Driver de slot a partir de bone virou entrada própria em backlog.md.)

## Mesh Generation panel (spec 022)

- **"Mesh resolution" é um nome deceptivo.** O field (`scene_props.py:84`, `name="Mesh resolution"`) é um fator de downscale 0..1 da imagem pro contour walker: valor MENOR = imagem menor processada porém MAIS vertices na malha final (a própria description já diz "Lower values produce more vertices"). "Resolution" sugere o oposto (número maior = mais resolução). Renomear pra refletir a relação invertida (ex: "Detail", "Coarseness", "Downscale factor") ou inverter a escala pra "maior = mais denso". Default atual 0.25; user sugere 0.5.
- **`Density follows bones` pode vir OFF por padrão.** `automesh_density_under_bones` (`scene_props.py:175`) + o operator default ON. O caso comum não precisa de densidade extra sob bones; ligar sob demanda. Trocar default pra OFF.
- **`Interior spacing` isolado dos outros valores.** O layout (`mesh_generation.py:_draw_automesh_alpha`) separa: resolution / alpha / margin / contour, [sep], preserve_base_quad, [sep], (dense) interior_spacing / density / bone_radius / bone_factor. User quer `interior_spacing` agrupado junto dos primeiros valores numéricos, não isolado no bloco dense.
- **"Preserve weights on regen" fica escondido longe de onde age.** O toggle vive em Weight Paint > Snapshot, mas afeta o Automesh (regen de malha aqui no Mesh Generation) E a geração de pesos. Rodar Automesh from Alpha / Interactive sem ver esse estado é obtuso - o usuário não sabe se o regen vai preservar ou apagar a pintura. Surfacar o estado nos pontos de interesse: readout no subpanel Automesh ("Weights: preserved on regen" / warn "Weights: NOT preserved - regen vai apagar a pintura") e idealmente espelhar o próprio toggle ali. No Bind, deixar claro que o snapshot é o que alimenta o preserve.

## Weight Paint panel (spec 022)

- **Automesh Interactive: "modal" não diz nada pro usuário.** O subpanel mostra label "Multi-stage modal preview" + botão "Automesh (modal)" (`mesh_generation.py:175,187`). "modal" é jargão de implementação do Blender, irrelevante pro autor. Trocar por copy orientada à ação (ex: "Automesh (interactive)" / "Edit step-by-step").
- **Bind não mostra qual armature é o alvo.** O painel-pai Weight Paint mostra "Picker: <name>", mas o subpanel Bind (e a box "Per-bone Soft/Hard overrides", que lista wrist / palm / fingertip) não repete o nome - fácil de perder quando o foco é o subpanel. Mostrar o armature alvo no header do Bind ou da box de overrides.
- **Edit Weights herda o display de weight paint padrão do Blender (ruim pra malha plana).** Em malhas / polígonos planos 2D, o override de cor full-mesh do weight paint nativo (gradiente azul->vermelho cobrindo tudo) esconde a textura e dificulta enxergar o que se pinta (imagem 1 do user). Alternativas: (a) trazer a textura por cima / lado a lado da pintura de peso; (b) achar modo nativo do Blender que exiba melhor em malha plana; (c) se nada nativo servir, referência = weight paint do Spine: mantém a textura visível + mostra os vertices com peso como círculos coloridos. Candidato a spec própria (display de weight paint 2D).
- **Per-bone Soft/Hard: vários problemas.** (a) Não dá pra LIMPAR um override de volta pro default - `operators/skinning/set_bone_mode.py` só seta SOFT ou HARD, sem opção "(default)"; uma vez clicado, fica preso num dos dois. (b) Os overrides são INERTES no modo BONE_HEAT, que é o default - ver bug em backlog-bugs-found.md; só valem em PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY. (c) "Soft/Hard" traduz mal o que acontece: SOFT = família proximity-falloff, HARD = família single-nearest, e o override só flipa o bone entre essas 2 famílias (não expõe os 5 algoritmos de bind). Renomear pra algo claro (ex: "Blend / Rigid" ou "Falloff / Nearest") + tooltip explicando. (d) O botão "Bind to Picker Armature" vem ANTES da box de overrides; ordem lógica = Mode -> overrides por-bone -> Bind (a ação que consome tudo). Mover o botão pro fim.
- **Sidecar IO: Import não aplica nos pesos vivos.** `operators/skinning/sidecar_io.py` `import_sidecar` só grava o CP `proscenio_weight_sidecar`; pra empurrar pros vertex groups vivos precisa rodar "Reset to Last Saved Weights" depois (e isso aborta se a topologia mudou - hash check). O fluxo Import -> Reset não é óbvio. Documentar / encadear, ou fazer o Import já aplicar quando a topologia bate.
- **"Snapshot" e "Sidecar IO" não parecem relacionados (e "sidecar" é jargão interno).** São a mesma coisa: Sidecar IO é o Export / Import do snapshot pra arquivo. Unificar sob "snapshot" (user prefere): renomear o subpanel "Sidecar IO" pra "Snapshot Export/Import" (ou fundir os 2 botões dentro do subpanel Snapshot) + trocar os labels dos operators ("Export / Import Weight Sidecar" -> "Export / Import Snapshot"). "sidecar" fica só interno (CP key, schema), nunca user-facing.
- **Weight Transfer: `max_distance` só no F9.** O raio de busca (default 0.5 world units) é prop de redo F9, não aparece no painel - usuário não vê nem ajusta. Surfacar no subpanel Weight Transfer. (Falta de warning pra targets fora do alcance virou bug em backlog-bugs-found.md.)

## Skeleton panel

- Visualização atual está ruim:
  - Click no bone na lista deveria selecionar o bone no Blender (3D viewport / pose mode)
  - Ou permitir rename inline
- Hoje o panel é só inspect read-only, não serve de muito
- **Warning "2 armatures - writer uses the first only" precisa contexto.** (Update 2026-06-10: o picker de armature shippou no Skeleton panel, mas o writer segue exportando `armatures[0]` e ignorando o picker - virou bug próprio em `backlog-bugs-found.md`; aqui resta só o polish do texto do warning.) Quando cena tem 2+ armatures, o panel mostra warning mas:
  - "the first" sem indicar QUAL armature está sendo usada - usuário tem que adivinhar pela scene order.
  - Sem botão pra trocar a armature ativa do panel.
  - Sugestões: (a) mostrar nome da armature usada no warning: `2 armatures present - writer uses 'atlas_pack.armature'`. (b) Dropdown selector no panel pra escolher qual armature trabalhar (Scene PG `active_armature_name`). (c) Sincronizar com active object se for armature, fallback pra scene order só se nenhuma armature ativa.

## Toggle IK / IK workflow

- **Toggle IK cria constraint sem target.** Operator (`authoring_ik.py:49-55`) só insere `IK` constraint vazia na pose bone selecionada - não wira `target` nem `subtarget`. INFO bar avisa "set the target manually" mas usuário precisa caçar Properties > Bone Constraints > Target dropdown. Para um helper de autoring, sugestão:
  - Operator pode receber `target_object` + `target_bone` como props F9; default usa controller bone irmão (heurística simples) ou um Empty auto-criado no tail do chain.
  - Alternativa low-friction: tras de Toggle IK, abrir popup pedindo target (single dialog) antes de criar.
- **Sem bake-action gate no Export.** IK é purely authoring (BLENDER_ONLY em feature_status); writer lê FCurves diretamente. Se o usuário anima APENAS o controlador (terminal bone via IK) sem fazer `Pose > Animation > Bake Action` antes do export, os bones intermediários NÃO ganham keyframes → Godot recebe pose torta. Sugestões:
  - Validator: warning quando uma action keyframa bones com IK constraint ativa mas a chain anterior não tem keyframes. (Cheirar via cross-referencing fcurves vs bone parent chain + IK influence > 0.)
  - Botão "Bake Action (visual)" no Animation panel próximo ao action selector, wrapper de `bpy.ops.nla.bake` com defaults certos (visual_keying=True, clear_constraints=False, bake_types={'POSE'}).
  - Doc explícito no help_topics.py `toggle_ik` ou criar topic dedicado "ik_workflow" explicando: autor IK → bake antes do export.
- **Sem IK/FK switch.** Rigify-style runtime switching (custom property + drivers + snap ops) seria muito útil pra animação complexa, mas é spec-on-paper - por hoje, usuário pode só toggle IK on/off via panel, não trocar mid-animation. Documentar limitação até feature pousar (não tá no roadmap atual).

## Quick Armature operator

- **(quick-armature first-cut polish) Preview line cortada visualmente quando cursor passa por baixo de panel/header/toolbar.** Apos fix do region overlay filter (operator nao processa eventos sob N-panel/header/toolbar), preview line continua sendo desenhada matematicamente cheia ate cursor real - mas Blender pinta panels POR CIMA do GPU draw handler, mascarando trechos da linha. Visualmente parece "corte". Tradeoff aceito: clicks em panel area nao criam bones (correto). Polish proposto:
  - **A. Clamp visual no boundary do canvas-livre.** No MOUSEMOVE, se cursor entra zona de overlay, projeta `_cursor_world` pra borda mais proxima do retangulo canvas-menos-overlays. Linha para visualmente na borda do panel em vez de sumir sob ele.
  - **B. Indicacao por cor.** Linha muda pra cinza/vermelho `(0.6, 0.6, 0.6, 0.7)` quando cursor sobre overlay zone. Sinaliza "click aqui = no-op" sem precisar matematica de clamp.
  - **C. Ambos.** Clamp + cor diferente.
  - Status 2026-06-10: opcao B SHIPPED (linha vermelha + tooltip quando cursor fora do canvas, `_overlay.py`). Resta A (clamp visual no boundary) se demanda surgir.

## Outliner panel

- Recursos OK no geral, ainda enxuto
- Falta hierarquia / árvore indentada (armature > slots > attachments, meshes parented a bones) - hoje é lista plana. Mesma pegada do pedido do Skeleton panel (hierarquia indentada estilo outliner nativo).
- Favoritos: útil, manter
- Alinhamento dos nomes das meshes está centralizado - horrível. **Regra geral pra todas as listas: alinhar à esquerda**.

## Animation panel

- (a testar)

## Atlas panel

- **Faltam controles de packing comparado a TexturePacker / Spine.** Proscenio hoje expõe só `pack_padding_px`, `pack_max_size`, `pack_pot`. Spine / TexturePacker oferecem (em ordem decrescente de utilidade):
  - **Strip whitespace X/Y + Alpha threshold:** corta pixels transparentes em volta de cada sprite antes de empacotar. Reduz drasticamente tamanho do atlas com sprites de fundo transparente (típico em 2D cutout).
  - **Rotation:** permite girar sprites 90 graus pra packing mais denso. Trade-off: runtime precisa rotacionar UVs.
  - **Min width/height + Square + Divisible by 4:** restrições de shape do atlas (alguns GPUs antigos exigem POT ou divisível por 4; mobile às vezes prefere square).
  - **Edge padding vs Duplicate padding:** edge replica borda do sprite no padding pra evitar bleeding (linhas brancas em zoom-out por bilinear sampling pegando o vizinho). Crítico pra atlas bem feito.
  - **Premultiply alpha + Bleed:** alpha workflow correto pra blending sem halos.
  - **Scale + multi-resolution suffixes (`@2x`):** gera atlas em múltiplas resoluções (HD/SD) numa só passada.
  - **Pretty print JSON:** debug-friendly manifest output.
  - **Pages (multi-atlas):** quando sprites não cabem num único atlas, gera page1/page2/... automaticamente.
  - **Filter min/mag + Wrap X/Y:** metadata runtime (Linear vs Nearest, ClampToEdge vs Repeat) que vai pro manifest.

  Hoje todos esses defaultam ao implícito (no whitespace strip, no rotation, no bleed). Pra um pipeline de produção 2D, vários desses são *table stakes*. Não precisa de tudo de uma vez; priorizar **Edge padding + Strip whitespace** primeiro (maior impacto visual + tamanho).
- **Falta visibility sobre PPU (pixels per unit) através do pipeline.** Hoje PPU vive como Scene-prop / parâmetro CLI no writer (`pixels_per_unit=100`), mas:
  - PSD manifest tem `pixels_per_unit` no schema - vira *implicit* depois que o importer carrega.
  - Blender não tem UI mostrando o PPU efetivo da scene (usuário tem que olhar Export panel ou CLI).
  - Atlas pack hoje preserva pixel resolution 1:1 (sprite 32x32 vira slot 32x32 no atlas), então PPU se mantém. **Mas:** se no futuro adicionar `Scale` (0.5x, 2x, multi-res), a relação PPU vs atlas pixel quebra silenciosamente.
  - **Sugestão:** Atlas panel mostrar header com `Source PPU: 100 / Atlas PPU: 100 (1.0x)` quando packed. Se um dia `Scale` for adicionado, vira `Atlas PPU: 50 (0.5x scale)` com warning amarelo "world position bookkeeping needed". Idem mostrar PPU no Export panel + ler PPU do PSD manifest no importer (warning se mismatch).
- **Atlas image picker label** mostra `atlas_pack_workbench.atlas.png` (filename do atlas packed) - útil. Mas se o Pack ainda não rodou, mostra `sprite_1.png` (primeiro discovered). Sugestão: header explícito tipo `Discovered source atlas: <name>` vs `Packed atlas: <name>` pra deixar claro qual é qual estado.
- **Visibility sobre estado de pack/unpack por objeto está ausente.** Setup pode ser híbrido (alguns objetos packed, outros não, ou múltiplos atlases na mesma cena). Hoje:
  - O botão `Unpack Atlas` aparece sempre que QUALQUER objeto da scene tem snapshot, mesmo se o objeto selecionado não está packed. Comportamento `scene_has_pre_pack_snapshot(scene)` em `_paths.py:61-63`.
  - Sem indicador per-objeto "este sprite está packed em `<atlas X>`" no Active Sprite panel.
  - Sem lista global de atlases ativos na cena (quantos atlases foram packed? qual cada sprite usa?).
  - **Sugestão:** novo subpanel ou sub-box "Packed atlases" no Atlas panel, listando: `<atlas_name>: N sprite(s) - Pack date / Apply state`. Filtrar por seleção quando relevante. Per-sprite no Active Sprite: mostrar badge `packed in: <atlas_name>` quando objeto tem snapshot.
- **Material identity é por nome (string), não por pointer.** Documentar limitação no Atlas panel UI (ou no help popup): "Renaming materials between Apply and Unpack will silently break restoration. Use Unpack first, then rename." Idealmente Proscenio expõe rename op próprio que atualiza snapshot junto, mas é overkill - documentação na UI já reduz pegadinha. Bug em backlog-bugs-found.md detalha o fix técnico.
- **MaxRects-BSSF heurística é greedy, não global-optimal.** Pro fixture atlas_pack (9 sprites 32x32, padding=2), o packer escolheu layout 7+2 colunas (footprint ~74x252) ao invés de 3x3 grid ótimo (108x108). Não afeta atlas size final (sempre 256 por start_size minimum), só density visual. Improvement possível: tentar múltiplas heurísticas (BSSF + BLSF + AreaFit) e escolher menor resultado. Prioridade baixa.
- **Atlas não shrinka pra fit tight; start_size 256 hardcoded.** `apps/blender/core/atlas_packer.py:82` - `size = max(start_size, ...)`. Independente de quantos sprites tem, atlas mínimo é 256x256. Pra fixtures pequenas, atlas tem 80%+ de waste. Sugestão: expor `start_size` como Scene PG (default 256, configurável). Ou modo "shrink to fit" - pós-pack, recalcula bounding box dos placements e gera atlas no tamanho exato. Trade-off: pior pra reuso de atlas entre runs (size flutua) mas melhor pra storage.

## Materials panel (proposed - doesn't exist yet)

Sem panel dedicado pra inspeção / configuração de materials. Hoje usuário caça pelos materiais no Shader Editor ou Properties > Material per-objeto. Sugestão: novo subpanel **Materials** com:

- **Inspeção:** lista materials da cena (ou filtrada por seleção). Mostra: nome, qtd users, qtd Image Texture nodes, image filepath(s).
- **Cross-material quick config:** botões que aplicam a todos / seleção / regex:
  - **Interpolation toggle:** Closest / Linear / Cubic / Smart - aplica a TODOS Image Texture nodes dos materials selecionados. Resolve o caso "import Photoshop traz tudo Linear, eu quero Closest pixel-art".
  - **Blend mode toggle:** Opaque / Clip / Hashed / Blend - aplica a TODOS materials. Crítico: importer hoje seta `HASHED` por default, que renderiza dither stipple em pixels semi-transparentes. Pixel art quer `CLIP` (binary cutoff). Bulk toggle resolve.
  - **Extension mode:** Repeat / Extend / Clip - mesmo padrão.
  - **Alpha mode:** Straight / Premultiplied.
  - **Alpha threshold slider:** 0..1, default 0.5 - visível para `CLIP` blend mode.
  - **Mipmaps on/off**, **Anisotropic filtering** (futuro).
- **Bulk image path fix:** detectar broken image filepaths + botão "Repair" que abre file picker pra resolver missing texture.
- **Material report:** quantos materials únicos, quantos compartilham mesma imagem (atlas candidates), quantos com `material_isolated=True`.

**Motivação:** Proscenio assume convenções (Closest, edge-padding, pixel-art conventions) mas não força nem expõe controle. Usuário tem que conhecer Blender deep pra ajustar. Panel dedicado dá autonomia + visibilidade.

**Alternativa low-effort se panel completo for overkill:** adicionar uma seção "Material setup" no Active Sprite panel com checkbox `Pixel art` - quando ligado, seta Closest interpolation + nearest filter no Image Texture node do material ativo. Toggle one-click pra caso comum.

## Pipeline cross-tool

- **Per-asset PPU end-to-end (gap real).** Pipeline atual usa **um único PPU global** (Scene PG, default 100). Schema PSD manifest tem campo `pixels_per_unit` mas:
  - Importer PSD não respeita por-layer / por-asset.
  - Writer Blender exporta sempre com PPU global.
  - Godot import respeita PPU mas o que receber é o global.
  - **Consequência:** dois personagens entregues em pixels diferentes (1280px vs 1920px) viram meshes de tamanhos diferentes no Blender (12.8m vs 19.2m com PPU=100), violando "same in-game height" mesmo que o artista intencionalmente trabalhou nesses pixels pra ter mesmo detail level.
  - **Workaround hoje:** artista normaliza assets pra mesma resolução antes do pipeline; OR designer manualmente escala meshes no Blender pós-import.
  - **Solução certa (futuro):** PSD manifest carrega `pixels_per_unit` per-layer (ou per-asset group); importer Blender escala mesh proporcionalmente na criação (`world_size = px / asset_ppu`); writer exporta per-mesh world_size derivada do per-asset PPU; Godot import usa world_size direto sem assumir global. Atlas pack pode opcionalmente downsample o maior pra resolução do menor (Spine Scale-style) com warning sobre detail loss.
  - Discussão completa rolou na sessão de manual testing 1.10 (10-mai-2026).
- **Quirk: JSX export hardcoda PPU=100, perdendo o valor original no roundtrip.** `apps/photoshop/proscenio_export.jsx:54` (`var DEFAULT_PIXELS_PER_UNIT = 100`). PSD não tem campo nativo "pixels per unit" pra game world (DPI é coisa de impressão, separado). Quando o roundtrip volta pro Blender com manifest em PPU=100 mas canvas dimensionado pra PPU=1000 original, meshes vêm exatamente 10x maiores. Verificado em sessão 1.17 (11-mai-2026): doll.blend canonical bbox 0.77x1.67m vs. imported_from_photoshop.blend bbox 7.74x16.67m. **Não é bug crítico** - quirk previsível de workflow PS roundtrip; user escala 0.1x manual após reimport ou re-aplica scale apply. **Fix preferido (futuro):** opção A - proscenio_import.jsx salva `pixels_per_unit` em XMP custom field do PSD (`app.activeDocument.info.transmissionReference`); proscenio_export.jsx lê de volta. Opções B (sidecar JSON) e C (layer name encoded) também possíveis, menor robustez. Implementação deferida.

## Validation panel

- **Click em issue de objeto hidden seleciona no outliner mas viewport não reflete.** Comportamento Blender padrão, mas confuso pro usuário que clica achando que vai ver o offending object destacado. Sugestão: `proscenio.select_issue_object` operator deve também `hide_viewport=False` + frame view na target (View > Frame Selected). Workaround: usuário precisa unhide manual antes da seleção fazer sentido visual.

## Export panel

- (a testar)

## Help / status badges

- Help panel completamente inútil e ilegível como tá - substituir por botão único que abre popup
- **See-also references nos popups de help: refs LOCAIS não são clickáveis.** (Parcial pós-spec-023: refs `http(s)` já renderizam como `wm.url_open` + botão "Open online docs"; restam os see-also de path local - `specs/`, `examples/` - como labels puros.) Sugestões (em ordem de impacto):
  - **A. wm.path_open operator:** envolver cada ref num `layout.operator("wm.path_open")` com `filepath=<abspath>` - abre arquivo/pasta no app default do OS. Funciona pra `STATUS.md`, pastas de exemplo (abre file manager) etc. Mínimo viável.
  - **B. wm.url_open** se ref começa com `http`. Mistura A+B detectando prefixo.
  - **C. Copy to clipboard button** próximo de cada ref - alternativa baixa-fricção.
  - **D. Ícone visual:** se decidir não fazer A/B, ao menos trocar ícone URL no header da seção pra algo menos clicky (DOT, INFO), pra não enganar.

## Diagnostics panel

- Agregar com Help → "Help & Diagnostics" panel único
