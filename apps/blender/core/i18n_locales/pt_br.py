"""Brazilian Portuguese (pt_BR) i18n table for the Blender addon (spec 072).

One row per translated string: ``((msgctxt, msgid), msgstr)`` where the
``msgid`` is the canonical English source. English is never a locale
module here - it is the msgid itself and stays inline in the addon
source. Rows come from the extraction catalog
(``scripts/blender/extract_i18n.py``) filled by the pt-BR content pass
(spec 072 A4): a machine-assisted first pass, human-reviewed by the team.

pt-BR orthography: full accents; keep EN technical terms (slot, atlas,
weight paint, skeleton, element) untranslated where that reads more
naturally, aportuguesados only when natural.
"""

from __future__ import annotations

from ._types import LocaleRow

#: Blender locale code. Differs from the Docusaurus BCP-47 tag ``pt-BR``.
LOCALE: str = "pt_BR"

#: Translated rows, keyed by ``(msgctxt, msgid)``. Held in sync with the source
#: catalog by the reverse-coverage test (tests/test_i18n_coverage.py); a new
#: translatable string or a stale row fails the build. Grow append-only.

ROWS: tuple[LocaleRow, ...] = (
    (
        ("*", "- all vertex groups + bound weights"),
        "- todos os grupos de vértices + pesos vinculados",
    ),
    (("*", "- the authoring strokes"), "- os traços de autoria"),
    (("*", "- the automesh / hand-drawn geometry"), "- a geometria do automesh / desenhada à mão"),
    (("*", "1 - Raw contours"), "1 - Contornos brutos"),
    (("*", "1 Raw contours"), "1 Contornos brutos"),
    (("*", "2 - Smoothed"), "2 - Suavizado"),
    (("*", "2 Smoothed"), "2 Suavizado"),
    (("*", "3 - Resampled"), "3 - Reamostrado"),
    (("*", "3 Resampled"), "3 Reamostrado"),
    (("*", "3D View Clip:"), "Recorte da vista 3D:"),
    (("*", "4 - Interior points"), "4 - Pontos interiores"),
    (("*", "4 Interior points"), "4 Pontos interiores"),
    (("*", "5 - Bridges"), "5 - Pontes"),
    (("*", "5 Bridges"), "5 Pontes"),
    (("*", "6 - Triangle fill (no interior)"), "6 - Preenchimento de triângulos (sem interior)"),
    (("*", "6 Triangle fill"), "6 Preenchimento de triângulos"),
    (("*", "About"), "Sobre"),
    (("*", "Action"), "Ação"),
    (("*", "Active"), "Ativo"),
    (("*", "Active Armature"), "Armadura ativa"),
    (("*", "Active Bone"), "Osso ativo"),
    (("*", "Active Mesh"), "Malha ativa"),
    (("*", "Active Slot"), "Slot ativo"),
    (("*", "Active Sprite"), "Sprite ativo"),
    (("*", "Active action"), "Ação ativa"),
    (("*", "Active armature"), "Armadura ativa"),
    (("*", "Active bone"), "Osso ativo"),
    (("*", "Active outliner row"), "Linha ativa do outliner"),
    (("*", "Active slot row"), "Linha ativa do slot"),
    (("*", "Active to Euler"), "Ativo para Euler"),
    (("*", "Add Selected"), "Adicionar selecionados"),
    (
        ("*", "Add to the bone selection instead of replacing it (Shift)"),
        "Adiciona à seleção de ossos em vez de substituí-la (Shift)",
    ),
    (
        ("*", "Add to the current selection instead of replacing it (Shift)"),
        "Adiciona à seleção atual em vez de substituí-la (Shift)",
    ),
    (
        ("*", "Adopt as a deformable Mesh, a rigid Sprite, or Auto-detect from the geometry"),
        "Adotar como Malha deformável, Sprite rígido, ou detectar automaticamente pela geometria",
    ),
    (("*", "Advance to the next stage"), "Avançar para o próximo estágio"),
    (
        (
            "*",
            "Advanced driver expression. 'var' is the bone channel; edit in the Drivers Editor for scaling / offsets / branching.",
        ),
        "Expressão de driver avançada. 'var' é o canal do osso; edite no Editor de Drivers para escala / deslocamentos / ramificações.",
    ),
    (("*", "Advanced expression"), "Expressão avançada"),
    (
        ("*", "After triangle_fill, before interior insertion"),
        "Depois do triangle_fill, antes da inserção interior",
    ),
    (
        (
            "*",
            "Algorithm used by Bind to Target Armature. BONE_HEAT delegates to Blender's native Parent w/ Auto Weights (recommended for sprites with bones co-planar with the picture plane). PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY are Proscenio fallbacks for edge cases (off-sprite armatures, manual paint baseline).",
        ),
        "Algoritmo usado por Vincular à armadura-alvo. BONE_HEAT delega ao Parentear com Pesos Automáticos nativo do Blender (recomendado para sprites com ossos coplanares ao plano da imagem). PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY são alternativas do Proscenio para casos extremos (armaduras fora do sprite, linha de base de pintura manual).",
    ),
    (("*", "All Bones"), "Todos os ossos"),
    (("*", "All to Euler"), "Todos para Euler"),
    (("*", "All-zero baseline for manual paint"), "Linha de base toda zero para pintura manual"),
    (
        ("*", "All-zero baseline for manual paint workflows"),
        "Linha de base toda zero para fluxos de pintura manual",
    ),
    (("*", "Alpha threshold"), "Limiar de alpha"),
    (
        (
            "*",
            "Alpha-silhouette trace resolution, an image downscale factor. 1.0 = full image (finest, slowest), 0.25 = quarter (coarser, faster); sets outline fidelity, not vertex count",
        ),
        "Resolução do traçado da silhueta de alpha, um fator de redução da imagem. 1.0 = imagem completa (mais fino, mais lento), 0.25 = um quarto (mais grosseiro, mais rápido); define a fidelidade do contorno, não a contagem de vértices",
    ),
    (("*", "Animation"), "Animação"),
    (("*", "Apply Packed Atlas"), "Aplicar atlas empacotado"),
    (("*", "Armature"), "Armadura"),
    (("*", "Armature name"), "Nome da armadura"),
    (
        ("*", "Armature whose pose bone supplies the driver value"),
        "Armadura cujo osso de pose fornece o valor do driver",
    ),
    (
        ("*", "Asset name. Empty string falls back to '<action>.<frame>' or '<armature>.<frame>'."),
        "Nome do asset. String vazia recai para '<action>.<frame>' ou '<armature>.<frame>'.",
    ),
    (("*", "Atlas"), "Atlas"),
    (("*", "Atlas packer"), "Empacotador de atlas"),
    (("*", "Attach Mesh"), "Anexar malha"),
    (("*", "Attach to Bone"), "Anexar ao osso"),
    (("*", "Attachment name"), "Nome do anexo"),
    (("*", "Authoring"), "Autoria"),
    (("*", "Authoring modal restored"), "Modal de autoria restaurado"),
    (("*", "Automesh Interactive"), "Automesh interativo"),
    (("*", "Automesh from Alpha"), "Automesh a partir do alpha"),
    (("*", "Axis"), "Eixo"),
    (("*", "Back"), "Voltar"),
    (("*", "Bake Current Pose"), "Assar pose atual"),
    (("*", "Bake IK to Keyframes"), "Assar IK em quadros-chave"),
    (("*", "Band"), "Faixa"),
    (("*", "Bind"), "Vincular"),
    (("*", "Bind falloff power"), "Potência do decaimento do vínculo"),
    (("*", "Bind max distance"), "Distância máxima do vínculo"),
    (("*", "Bind mode"), "Modo de vínculo"),
    (("*", "Bind to Bone"), "Vincular ao osso"),
    (("*", "Bind to Target Armature"), "Vincular à armadura-alvo"),
    (
        (
            "*",
            "Blender units between consecutive Y Location (Draw Order) layers. Each element sits at its draw-order number times this gap, so stacked planes never share a Y and z-fight. This only spreads planes in the 3D view - the exported draw order is the integer itself and never depends on this value. If planes still flicker, raise it or tighten the 3D view clip range in the Helpers panel. Use Re-space planes there after changing it",
        ),
        "Unidades Blender entre camadas consecutivas de Posição Y (Ordem de Desenho). Cada elemento fica no seu número de ordem de desenho vezes este intervalo, para que planos empilhados nunca compartilhem um Y e causem z-fighting. Isto só espalha os planos na vista 3D - a ordem de desenho exportada é o próprio inteiro e nunca depende deste valor. Se os planos ainda piscarem, aumente-o ou aperte a faixa de recorte da vista 3D no painel de Auxiliares. Use Reespaçar planos ali depois de alterá-lo",
    ),
    (("*", "Bone"), "Osso"),
    (("*", "Bone Heat (Blender native)"), "Bone Heat (nativo do Blender)"),
    (("*", "Bone Name"), "Nome do osso"),
    (("*", "Bone collection"), "Coleção de ossos"),
    (("*", "Bone density factor"), "Fator de densidade de ossos"),
    (("*", "Bone influence radius"), "Raio de influência do osso"),
    (("*", "Bone name prefix"), "Prefixo do nome do osso"),
    (("*", "Bone radius"), "Raio do osso"),
    (("*", "Bone the slot follows"), "Osso que o slot segue"),
    (("*", "Bone the sprite rigidly follows"), "Osso que o sprite segue rigidamente"),
    (
        (
            "*",
            "Bone this slot follows. The Godot importer parents the slot Node2D under that Bone2D so the attachments track the bone (e.g. a weapon following an arm). Bind to Bone sets this and adds a Child Of constraint that keeps the flat attachment quads in the picture plane for any bone orientation. Hand bone-parenting the Empty (Ctrl+P > Bone) also sets the followed bone and exports, but only for bones pointing into the screen - an in-plane bone tilts the quads edge-on. Empty string anchors the slot at the skeleton root.",
        ),
        "Osso que este slot segue. O importador do Godot parenteia o Node2D do slot sob aquele Bone2D para que os anexos acompanhem o osso (ex.: uma arma seguindo um braço). Vincular ao osso define isto e adiciona uma restrição Child Of que mantém os quads planos do anexo no plano da imagem para qualquer orientação do osso. Parentear o Vazio ao osso à mão (Ctrl+P > Bone) também define o osso seguido e exporta, mas apenas para ossos apontando para dentro da tela - um osso no plano inclina os quads de lado. String vazia ancora o slot na raiz do esqueleto.",
    ),
    (
        ("*", "Bone-channel value mapped to the output maximum"),
        "Valor do canal do osso mapeado para o máximo da saída",
    ),
    (
        ("*", "Bone-channel value mapped to the output maximum."),
        "Valor do canal do osso mapeado para o máximo da saída.",
    ),
    (
        ("*", "Bone-channel value mapped to the output minimum"),
        "Valor do canal do osso mapeado para o mínimo da saída",
    ),
    (
        (
            "*",
            "Bone-channel value mapped to the output minimum. The default spans negative rotation so a bone swung back no longer clamps to zero - the first-contact failure the raw 'var' default produced.",
        ),
        "Valor do canal do osso mapeado para o mínimo da saída. O padrão abrange rotação negativa para que um osso girado para trás não seja mais limitado a zero - a falha de primeiro contato que o 'var' bruto padrão produzia.",
    ),
    (
        (
            "*",
            "Bones beyond this distance contribute zero (PROXIMITY mode only). -1 = adaptive (1.5x armature deform-bone bbox extent).",
        ),
        "Ossos além desta distância contribuem com zero (somente no modo PROXIMITY). -1 = adaptativo (1.5x a extensão do bbox dos ossos de deformação da armadura).",
    ),
    (
        (
            "*",
            "Bones beyond this distance contribute zero (PROXIMITY only). -1 = adaptive (1.5x armature bbox)",
        ),
        "Ossos além desta distância contribuem com zero (somente PROXIMITY). -1 = adaptativo (1.5x o bbox da armadura)",
    ),
    (("*", "Boundary margin (edge loop)"), "Margem de borda (loop de arestas)"),
    (("*", "Brush curve preset:"), "Predefinição de curva do pincel:"),
    (("*", "Build the mesh by clicking vertices"), "Construir a malha clicando nos vértices"),
    (("*", "Bundle textures"), "Agrupar texturas"),
    (("*", "By draw order"), "Por ordem de desenho"),
    (("*", "Centered"), "Centralizado"),
    (("*", "Centered (Canvas at World Origin)"), "Centralizado (Canvas na origem do mundo)"),
    (("*", "Chain length"), "Comprimento da cadeia"),
    (("*", "Clear"), "Limpar"),
    (("*", "Clear Bone Parent"), "Limpar parentesco de osso"),
    (("*", "Clear Debug Companions"), "Limpar companheiros de debug"),
    (("*", "Clear Empty Vertex Groups"), "Limpar grupos de vértices vazios"),
    (
        (
            "*",
            "Concentric inner polylines computed via morphological erosion of the outer contour during interactive modal authoring. Higher count = more edge loops the CDT respects = more deformation control near the silhouette boundary. 0 disables inner loops",
        ),
        "Polilinhas internas concêntricas calculadas via erosão morfológica do contorno externo durante a autoria modal interativa. Contagem maior = mais loops de arestas que o CDT respeita = mais controle de deformação perto da borda da silhueta. 0 desativa os loops internos",
    ),
    (
        (
            "*",
            "Constrained Delaunay over silhouette + holes + your verts only; no automatic interior fill",
        ),
        "Delaunay Restrito sobre a silhueta + buracos + apenas seus vértices; sem preenchimento interior automático",
    ),
    (
        (
            "*",
            "Constrained Delaunay over the drawn contour + your verts only; no automatic interior fill",
        ),
        "Delaunay Restrito sobre o contorno desenhado + apenas seus vértices; sem preenchimento interior automático",
    ),
    (("*", "Contour vertices"), "Vértices do contorno"),
    (
        ("*", "Conversion ratio between Blender units and Godot pixels"),
        "Razão de conversão entre unidades Blender e pixels do Godot",
    ),
    (
        ("*", "Convert every bone in the active armature"),
        "Converter todos os ossos da armadura ativa",
    ),
    (
        ("*", "Convert just the active bone or every bone in the armature"),
        "Converter apenas o osso ativo ou todos os ossos da armadura",
    ),
    (("*", "Convert only the active pose bone"), "Converter apenas o osso de pose ativo"),
    (("*", "Create Slot"), "Criar slot"),
    (("*", "Cut margin"), "Margem de corte"),
    (("*", "Data path"), "Caminho de dados"),
    (("*", "Debug"), "Depuração"),
    (("*", "Debug Pipeline"), "Pipeline de depuração"),
    (("*", "Debug mode"), "Modo de depuração"),
    (("*", "Debug stage"), "Estágio de depuração"),
    (("*", "Default = chain connected"), "Padrão = cadeia conectada"),
    (
        ("*", "Delegate to Blender's Parent w/ Auto Weights (default)"),
        "Delegar ao Parentear com Pesos Automáticos do Blender (padrão)",
    ),
    (
        ("*", "Delegate to Blender's Parent w/ Auto Weights. Default; best for 2D rigs"),
        "Delega ao Parentear com Pesos Automáticos do Blender. Padrão; melhor para rigs 2D",
    ),
    (("*", "Dense (uniform fill)"), "Denso (preenchimento uniforme)"),
    (("*", "Density follows bones"), "Densidade segue os ossos"),
    (("*", "Density under bones"), "Densidade sob os ossos"),
    (("*", "Developer"), "Desenvolvedor"),
    (("*", "Direction"), "Direção"),
    (("*", "Display As"), "Exibir como"),
    (
        (
            "*",
            "Draw order of this element as a whole-number layer. In Blender it sets the object's Y position (this number times the Y Location spacing in the addon preferences) so stacked planes separate and do not z-fight; in Godot it sets the Sprite / Polygon draw order (z_index). Higher pushes the element further back, lower (incl. negative) pulls it forward. Reorder by editing this number, not by dragging the object in Y - a manual Y drag is flagged in validation.",
        ),
        "Ordem de desenho deste elemento como uma camada de número inteiro. No Blender ela define a posição Y do objeto (este número vezes o espaçamento de Posição Y nas preferências do addon) para que planos empilhados se separem e não causem z-fighting; no Godot ela define a ordem de desenho do Sprite / Polígono (z_index). Maior empurra o elemento mais para trás, menor (incl. negativo) o puxa para frente. Reordene editando este número, não arrastando o objeto em Y - um arraste manual em Y é sinalizado na validação.",
    ),
    (("*", "Drive from Bone"), "Dirigir a partir do osso"),
    (
        (
            "*",
            "Drive from the hand-written expression below instead of the two ranges. 'var' is the raw bone channel; edit for scaling, offsets, or branching the two-range map cannot express.",
        ),
        "Dirige a partir da expressão escrita à mão abaixo em vez das duas faixas. 'var' é o canal bruto do osso; edite para escala, deslocamentos ou ramificações que o mapa de duas faixas não consegue expressar.",
    ),
    (("*", "Driver armature"), "Armadura do driver"),
    (("*", "Driver axis"), "Eixo do driver"),
    (("*", "Driver bone"), "Osso do driver"),
    (("*", "Driver expression"), "Expressão do driver"),
    (
        (
            "*",
            "Driver expression (Advanced). 'var' is the raw bone channel. Built from the two ranges unless Advanced is on; edit in the Drivers Editor for anything the linear map cannot express.",
        ),
        "Expressão do driver (Avançado). 'var' é o canal bruto do osso. Construída a partir das duas faixas a menos que o modo Avançado esteja ativo; edite no Editor de Drivers para qualquer coisa que o mapa linear não consiga expressar.",
    ),
    (("*", "Driver target"), "Alvo do driver"),
    (
        ("*", "Drop the override - use the bind mode default"),
        "Descartar a substituição - usar o padrão do modo de vínculo",
    ),
    (
        ("*", "Each vert gets weight 1.0 in its nearest bone, 0 in others"),
        "Cada vértice recebe peso 1.0 no osso mais próximo, 0 nos demais",
    ),
    (("*", "Edit Weights"), "Editar pesos"),
    (("*", "Edit Weights modal restored"), "Modal de edição de pesos restaurado"),
    (("*", "Edit Weights:"), "Editar pesos:"),
    (("*", "Element"), "Elemento"),
    (("*", "Element type"), "Tipo de elemento"),
    (("*", "Empty"), "Vazio"),
    (
        ("*", "Empty groups hold no weights, so this is safe."),
        "Grupos vazios não retêm pesos, então isto é seguro.",
    ),
    (("*", "Envelope"), "Envelope"),
    (("*", "Errors only"), "Somente erros"),
    (("*", "Exclude from atlas"), "Excluir do atlas"),
    (("*", "Exclude from export"), "Excluir da exportação"),
    (("*", "Exit Painting Mode"), "Sair do modo de pintura"),
    (
        ("*", "Exponent for 1/dist^power (PROXIMITY only)"),
        "Expoente para 1/dist^power (somente PROXIMITY)",
    ),
    (
        (
            "*",
            "Exponent for 1/dist^power per-vert weight (PROXIMITY mode only). Higher values = tighter local influence. 2.0 (inverse square) matches Spine / DragonBones convention.",
        ),
        "Expoente para o peso por vértice 1/dist^power (somente no modo PROXIMITY). Valores maiores = influência local mais concentrada. 2.0 (quadrado inverso) segue a convenção do Spine / DragonBones.",
    ),
    (("*", "Export"), "Exportar"),
    (("*", "Export (.proscenio)"), "Exportar (.proscenio)"),
    (("*", "Export Snapshot"), "Exportar instantâneo"),
    (("*", "Expression"), "Expressão"),
    (("*", "Extend"), "Estender"),
    (("*", "Falloff Power"), "Potência de decaimento"),
    (("*", "Falloff power"), "Potência do decaimento"),
    (("*", "Favorites"), "Favoritos"),
    (("*", "Favorites only"), "Somente favoritos"),
    (
        ("*", "FeatureStatus enum value - 'godot-ready', 'blender-only', etc."),
        "Valor do enum FeatureStatus - 'godot-ready', 'blender-only', etc.",
    ),
    (("*", "Final"), "Final"),
    (
        (
            "*",
            "Flag this object as a favorite in the Proscenio outliner (the outliner subpanel). Toggle 'Show favorites only' on the panel to hide everything else; favorites keep their normal category order, they do not move to the top.",
        ),
        "Marca este objeto como favorito no outliner do Proscenio (o subpainel do outliner). Ative 'Mostrar somente favoritos' no painel para esconder todo o resto; os favoritos mantêm sua ordem normal de categoria, eles não vão para o topo.",
    ),
    (("*", "Frame"), "Quadro"),
    (
        (
            "*",
            "Frame index shown at rest pose (sprite only). Animation tracks override at runtime.",
        ),
        "Índice do quadro mostrado na pose de descanso (somente sprite). As trilhas de animação o substituem em tempo de execução.",
    ),
    (("*", "Full pipeline"), "Pipeline completo"),
    (
        ("*", "Full pipeline + clear prior debug companions"),
        "Pipeline completo + limpar companheiros de depuração anteriores",
    ),
    (("*", "Hard"), "Rígido"),
    (
        ("*", "Hard cap on the packed atlas dimensions (px). Pack fails above this."),
        "Limite rígido das dimensões do atlas empacotado (px). O empacotamento falha acima disto.",
    ),
    (("*", "Height"), "Altura"),
    (
        ("*", "Help-topic id resolved against core.help_topics.HELP_TOPICS"),
        "id do tópico de ajuda resolvido contra core.help_topics.HELP_TOPICS",
    ),
    (("*", "Helpers"), "Auxiliares"),
    (("*", "Horizontal frames"), "Quadros horizontais"),
    (
        (
            "*",
            "How `texture_region` is decided at export. Auto recomputes from UV bounds every export; Manual writes region_x/y/w/h verbatim.",
        ),
        "Como o `texture_region` é decidido na exportação. Auto recalcula a partir dos limites de UV a cada exportação; Manual grava region_x/y/w/h literalmente.",
    ),
    (
        (
            "*",
            "How much Proscenio operators report to the Info log. Errors only = just failures; Info = the default running commentary; Debug = adds the per-item pipeline traces",
        ),
        "Quanto os operadores do Proscenio reportam no log de Info. Somente erros = apenas falhas; Info = o comentário corrente padrão; Depuração = adiciona os rastreamentos de pipeline por item",
    ),
    (
        (
            "*",
            "How the hand-drawn mesh interior is filled. SIMPLE triangulates only the contour you draw plus your interior verts (sparse, Spine-like). DENSE adds the uniform interior grid (more deformable triangles).",
        ),
        "Como o interior da malha desenhada à mão é preenchido. SIMPLE triangula apenas o contorno que você desenha mais seus vértices interiores (esparso, estilo Spine). DENSE adiciona a grade interior uniforme (mais triângulos deformáveis).",
    ),
    (
        (
            "*",
            "How the mesh interior is filled. SIMPLE triangulates only the silhouette, holes, and your fold/cut/steiner verts (Spine-like sparse mesh; best for most flat 2D-skinning sprites). DENSE adds the uniform interior grid + bone-density fill (capes, hair, fine border control).",
        ),
        "Como o interior da malha é preenchido. SIMPLE triangula apenas a silhueta, os buracos e seus vértices de dobra/corte/steiner (malha esparsa estilo Spine; melhor para a maioria dos sprites planos de skinning 2D). DENSE adiciona a grade interior uniforme + preenchimento por densidade de ossos (capas, cabelo, controle fino de borda).",
    ),
    (("*", "IK chains"), "Cadeias IK"),
    (("*", "Import"), "Importar"),
    (("*", "Import Photoshop Manifest"), "Importar manifesto do Photoshop"),
    (("*", "Import Snapshot"), "Importar instantâneo"),
    (("*", "In Max"), "Entrada máx"),
    (("*", "In Min"), "Entrada mín"),
    (("*", "Incorporate as Element"), "Incorporar como elemento"),
    (("*", "Influence"), "Influência"),
    (("*", "Info"), "Info"),
    (
        (
            "*",
            "Info + the per-item pipeline traces (importer planes, automesh counters, validation issues)",
        ),
        "Info + os rastreamentos de pipeline por item (planos do importador, contadores do automesh, problemas de validação)",
    ),
    (("*", "Info + warnings + errors (default)"), "Info + avisos + erros (padrão)"),
    (("*", "Inner loop spacing"), "Espaçamento dos loops internos"),
    (("*", "Inner loops"), "Loops internos"),
    (("*", "Input max"), "Máx. de entrada"),
    (("*", "Input min"), "Mín. de entrada"),
    (("*", "Interactive trace and edit"), "Traçar e editar interativamente"),
    (("*", "Interior mode"), "Modo interior"),
    (("*", "Interior spacing"), "Espaçamento interior"),
    (("*", "Is slot anchor"), "É âncora de slot"),
    (("*", "Isolated material"), "Material isolado"),
    (
        (
            "*",
            "Keep the 4 original quad corner vertices (in the proscenio_base_sprite vertex group) as loose verts after automesh runs. OFF (default) deletes them so the mesh is clean. ON preserves them so the user can manually stitch custom UV / weight work that lived on the quad (useful when the user has hand-tweaked the base before automesh and wants to merge the work afterwards)",
        ),
        "Mantém os 4 vértices de canto do quad original (no grupo de vértices proscenio_base_sprite) como vértices soltos após o automesh rodar. OFF (padrão) os exclui para que a malha fique limpa. ON os preserva para que o usuário possa costurar manualmente trabalho de UV / peso personalizado que vivia no quad (útil quando o usuário ajustou a base à mão antes do automesh e quer mesclar o trabalho depois)",
    ),
    (
        (
            "*",
            "Keep the 4 original quad corner vertices after automesh. OFF (default) deletes them for a clean mesh; ON preserves them as loose verts for manual stitching",
        ),
        "Mantém os 4 vértices de canto do quad original após o automesh. OFF (padrão) os exclui para uma malha limpa; ON os preserva como vértices soltos para costura manual",
    ),
    (
        (
            "*",
            "Keep the figure centred around the manifest canvas centre (world origin). Useful when aligning multiple imports in a shared scene.",
        ),
        "Mantém a figura centralizada em torno do centro do canvas do manifesto (origem do mundo). Útil ao alinhar várias importações em uma cena compartilhada.",
    ),
    (
        (
            "*",
            "Keep this bone out of the Godot export - a rig helper that only makes sense in Blender (a Drive-from-Bone source, a tweak handle). Non-deform control bones (IK goals, poles) are already dropped; this pins off a bone that still deforms. The Drive-from-Bone shortcut sets it automatically on the source bone.",
        ),
        "Mantém este osso fora da exportação do Godot - um auxiliar de rig que só faz sentido no Blender (uma fonte de Dirigir a partir do osso, uma alça de ajuste). Ossos de controle que não deformam (alvos de IK, polos) já são descartados; isto desativa a exportação de um osso que ainda deforma. O atalho Dirigir a partir do osso o define automaticamente no osso de fonte.",
    ),
    (
        (
            "*",
            "Keep this sprite out of Pack Atlas entirely: it is not packed, its UVs and material are left untouched, and it ships its own texture. Use it to keep large or rarely-shared sprites out of the shared atlas.",
        ),
        "Mantém este sprite totalmente fora do Empacotar atlas: ele não é empacotado, seus UVs e material ficam intocados, e ele leva sua própria textura. Use para manter sprites grandes ou raramente compartilhados fora do atlas compartilhado.",
    ),
    (("*", "Label for this save point"), "Rótulo para este ponto de salvamento"),
    (("*", "Landed (Feet on Z=0)"), "No chão (Pés em Z=0)"),
    (("*", "Last export path"), "Último caminho de exportação"),
    (
        (
            "*",
            "Length (world units) of the stub armature's root bone. Default is 1.0. A re-import reuses the existing root in place, so this only sizes a freshly built root, never an already-imported rig.",
        ),
        "Comprimento (unidades de mundo) do osso raiz da armadura-esboço. O padrão é 1.0. Uma reimportação reutiliza a raiz existente no lugar, então isto só dimensiona uma raiz recém-construída, nunca um rig já importado.",
    ),
    (("*", "Lock to Front Orthographic"), "Travar em Frontal Ortográfica"),
    (("*", "Log level"), "Nível de log"),
    (("*", "Loops"), "Loops"),
    (("*", "Manual Mesh"), "Malha manual"),
    (("*", "Margin (px)"), "Margem (px)"),
    (("*", "Max Distance"), "Distância máxima"),
    (("*", "Max distance"), "Distância máxima"),
    (("*", "Mesh"), "Malha"),
    (("*", "Mesh Generation"), "Geração de malha"),
    (("*", "Mesh to attach to the active slot"), "Malha a anexar ao slot ativo"),
    (("*", "Message"), "Mensagem"),
    (("*", "Mode"), "Modo"),
    (
        (
            "*",
            "Multiplier for interior point density near bones. 1 = same as uniform, 2 = double, 4 = quadruple. Diminishing returns above 4.",
        ),
        "Multiplicador da densidade de pontos interiores perto dos ossos. 1 = igual ao uniforme, 2 = o dobro, 4 = o quádruplo. Retornos decrescentes acima de 4.",
    ),
    (("*", "Name"), "Nome"),
    (
        ("*", "Name of the armature object hosting the source bone"),
        "Nome do objeto de armadura que hospeda o osso de fonte",
    ),
    (
        (
            "*",
            "Name of the attachment shown by default when the scene loads. Empty string defers to the first child mesh by sorted name.",
        ),
        "Nome do anexo mostrado por padrão quando a cena carrega. String vazia recorre à primeira malha filha por nome ordenado.",
    ),
    (
        ("*", "Name of the mesh child to flag as default"),
        "Nome da malha filha a marcar como padrão",
    ),
    (
        ("*", "Name of the mesh child to show from this frame"),
        "Nome da malha filha a exibir a partir deste quadro",
    ),
    (
        ("*", "Name of the new Empty. Defaults to '<bone>.slot' or 'slot'."),
        "Nome do novo Vazio. O padrão é '<bone>.slot' ou 'slot'.",
    ),
    (
        ("*", "Name of the offending object (empty if scene-wide)"),
        "Nome do objeto problemático (vazio se for de toda a cena)",
    ),
    (
        (
            "*",
            "Name of the single bone created in the stub armature. Default is 'root'; rigs that prefer 'spine' or another identifier can override here.",
        ),
        "Nome do único osso criado na armadura-esboço. O padrão é 'root'; rigs que preferem 'spine' ou outro identificador podem substituir aqui.",
    ),
    (("*", "Next"), "Próximo"),
    (("*", "No automatic interior fill"), "Sem preenchimento interior automático"),
    (("*", "Object"), "Objeto"),
    (
        ("*", "Object Mode + meshes: slot wraps the selection"),
        "Modo de objeto + malhas: o slot envolve a seleção",
    ),
    (("*", "Object name"), "Nome do objeto"),
    (("*", "Off"), "Desligado"),
    (
        (
            "*",
            "On export, copy every referenced texture next to the .proscenio so Godot's siblings-only import resolves PSD assets that live in images/ and _spritesheets/ subfolders",
        ),
        "Na exportação, copia toda textura referenciada ao lado do .proscenio para que a importação apenas-irmãos do Godot resolva assets PSD que ficam nas subpastas images/ e _spritesheets/",
    ),
    (
        (
            "*",
            "On invoke, snap the active 3D viewport to Front Orthographic so bones land on the Y=0 picture plane. Restores the prior view on exit when the user has not orbited mid-modal.",
        ),
        "Ao invocar, encaixa a viewport 3D ativa na Frontal Ortográfica para que os ossos caiam no plano da imagem Y=0. Restaura a vista anterior ao sair quando o usuário não orbitou no meio do modal.",
    ),
    (("*", "One bone per vert, weight 1.0"), "Um osso por vértice, peso 1.0"),
    (("*", "One of 'error' or 'warning'"), "Um de 'error' ou 'warning'"),
    (("*", "Only error reports surface"), "Somente relatórios de erro aparecem"),
    (("*", "Open help"), "Abrir ajuda"),
    (("*", "Open online docs"), "Abrir a documentação online"),
    (("*", "Out Max"), "Saída máx"),
    (("*", "Out Min"), "Saída mín"),
    (
        ("*", "Outer + inner + radial bridge edges, no fill"),
        "Arestas externas + internas + de ponte radial, sem preenchimento",
    ),
    (("*", "Outliner"), "Outliner"),
    (("*", "Outliner favorite"), "Favorito do outliner"),
    (("*", "Outliner filter"), "Filtro do outliner"),
    (("*", "Output max"), "Máx. de saída"),
    (("*", "Output min"), "Mín. de saída"),
    (("*", "Pack Atlas"), "Empacotar atlas"),
    (("*", "Pack max size"), "Tamanho máx. do empacotamento"),
    (("*", "Pack padding"), "Espaçamento do empacotamento"),
    (("*", "Palette"), "Paleta"),
    (
        ("*", "Per-bone 1/distance^falloff_power normalized (Proscenio fallback)"),
        "1/distance^falloff_power por osso normalizado (alternativa do Proscenio)",
    ),
    (
        ("*", "Per-bone 1/distance^falloff_power normalized in XZ. Fallback when bone heat fails"),
        "1/distance^falloff_power por osso normalizado em XZ. Alternativa quando o bone heat falha",
    ),
    (("*", "Per-bone Soft/Hard overrides:"), "Substituições Suave/Rígido por osso:"),
    (
        ("*", "Per-bone radius from bone Custom Property"),
        "Raio por osso a partir da Propriedade Personalizada do osso",
    ),
    (
        (
            "*",
            "Pin this bone in the Skeleton panel's bone list. Toggle 'Favorites' on the Active Armature subpanel to hide every other bone; favorites keep their hierarchy order, they do not move to the top.",
        ),
        "Fixa este osso na lista de ossos do painel de Esqueleto. Ative 'Favoritos' no subpainel de Armadura ativa para esconder todos os outros ossos; os favoritos mantêm sua ordem de hierarquia, eles não vão para o topo.",
    ),
    (("*", "Pipeline"), "Pipeline"),
    (("*", "Pipeline v0.1.0"), "Pipeline v0.1.0"),
    (("*", "Pixel art"), "Pixel art"),
    (
        ("*", "Pixel-stair contours, pre-smoothing"),
        "Contornos em escada de pixels, antes da suavização",
    ),
    (
        ("*", "Pixels of padding reserved around each sprite in the packed atlas"),
        "Pixels de espaçamento reservados ao redor de cada sprite no atlas empacotado",
    ),
    (("*", "Pixels per unit"), "Pixels por unidade"),
    (
        (
            "*",
            "Pixels with alpha strictly above this value contribute to the silhouette. Default 1 includes EVERY visible pixel (even faint anti-alias edges) - the safe choice for sprite skinning where losing pixels at the boundary is unacceptable. Raise to 127 to ignore anti-alias edges (matches COA Tools 2 convention but cuts AA pixels).",
        ),
        "Pixels com alpha estritamente acima deste valor contribuem para a silhueta. O padrão 1 inclui TODOS os pixels visíveis (até bordas fracas de anti-alias) - a escolha segura para skinning de sprite onde perder pixels na borda é inaceitável. Aumente para 127 para ignorar bordas de anti-alias (segue a convenção do COA Tools 2 mas corta pixels de AA).",
    ),
    (("*", "Placement"), "Posicionamento"),
    (("*", "Pole bone"), "Osso de polo"),
    (("*", "Pole target"), "Alvo de polo"),
    (("*", "Pose Mode"), "Modo de pose"),
    (
        ("*", "Pose Mode + active bone: slot anchored to the bone"),
        "Modo de pose + osso ativo: slot ancorado ao osso",
    ),
    (
        ("*", "Pose bone transform channel feeding the driver"),
        "Canal de transformação do osso de pose que alimenta o driver",
    ),
    (
        ("*", "Pose bone whose transform feeds the driver"),
        "Osso de pose cuja transformação alimenta o driver",
    ),
    (("*", "Pose name"), "Nome da pose"),
    (("*", "Post-Laplacian contours"), "Contornos pós-Laplaciano"),
    (
        ("*", "Post-arc-length verts that enter the bmesh"),
        "Vértices pós-comprimento-de-arco que entram no bmesh",
    ),
    (("*", "Power-of-two atlas"), "Atlas em potência de dois"),
    (
        (
            "*",
            "Prefix for auto-named bones (e.g. 'def' produces 'def.000', 'def.001'). Whitespace is stripped; empty falls back to 'qbone'.",
        ),
        "Prefixo para ossos nomeados automaticamente (ex.: 'def' produz 'def.000', 'def.001'). Espaços em branco são removidos; vazio recai para 'qbone'.",
    ),
    (("*", "Preserve base quad"), "Preservar o quad base"),
    (("*", "Preserve weights on regen"), "Preservar pesos na regeneração"),
    (("*", "Preset"), "Predefinição"),
    (("*", "Preview Camera"), "Câmera de prévia"),
    (("*", "PropertyGroup not registered on this bone"), "PropertyGroup não registrado neste osso"),
    (
        ("*", "PropertyGroup not registered on this object"),
        "PropertyGroup não registrado neste objeto",
    ),
    (("*", "Proscenio IK"), "Proscenio IK"),
    (
        ("*", "Proscenio property group not registered"),
        "Grupo de propriedades do Proscenio não registrado",
    ),
    (
        ("*", "Proscenio scene properties not available"),
        "Propriedades de cena do Proscenio não disponíveis",
    ),
    (("*", "Proscenio scene props not registered"), "Props de cena do Proscenio não registradas"),
    (("*", "Proximity (1/d^p)"), "Proximidade (1/d^p)"),
    (("*", "Proximity falloff"), "Decaimento por proximidade"),
    (("*", "Quick Armature"), "Armadura Rápida"),
    (("*", "Re-export"), "Reexportar"),
    (("*", "Re-import from PSD"), "Reimportar do PSD"),
    (("*", "Re-space Planes"), "Reespaçar planos"),
    (
        ("*", "Region height (manual mode). Normalized [0,1] of atlas height."),
        "Altura da região (modo manual). Normalizada [0,1] da altura do atlas.",
    ),
    (("*", "Region mode"), "Modo de região"),
    (
        ("*", "Region origin X (manual mode). Normalized [0,1] of atlas width."),
        "Origem X da região (modo manual). Normalizada [0,1] da largura do atlas.",
    ),
    (
        ("*", "Region origin Y (manual mode). Normalized [0,1] of atlas height."),
        "Origem Y da região (modo manual). Normalizada [0,1] da altura do atlas.",
    ),
    (
        ("*", "Region width (manual mode). Normalized [0,1] of atlas width."),
        "Largura da região (modo manual). Normalizada [0,1] da largura do atlas.",
    ),
    (("*", "Regular"), "Regular"),
    (("*", "Remove Preview"), "Remover prévia"),
    (
        ("*", "Rendering path - Mesh maps to Polygon2D, Sprite maps to Sprite2D"),
        "Caminho de renderização - Malha mapeia para Polygon2D, Sprite mapeia para Sprite2D",
    ),
    (("*", "Reproject UV"), "Reprojetar UV"),
    (("*", "Reset to Last Saved Weights"), "Restaurar últimos pesos salvos"),
    (
        (
            "*",
            "Resolution of the alpha-silhouette trace, as an image downscale factor. 1.0 = full image (finest outline, slowest); 0.25 = quarter-pixel (coarser outline, faster - the default, safe for typical HD sprites). HIGHER traces a finer silhouette and costs quadratically more time. It sets outline fidelity, NOT vertex count - use Contour vertices for the outline and Interior spacing for the fill.",
        ),
        "Resolução do traçado da silhueta de alpha, como um fator de redução da imagem. 1.0 = imagem completa (contorno mais fino, mais lento); 0.25 = um quarto de pixel (contorno mais grosseiro, mais rápido - o padrão, seguro para sprites HD típicos). MAIOR traça uma silhueta mais fina e custa quadraticamente mais tempo. Define a fidelidade do contorno, NÃO a contagem de vértices - use Vértices do contorno para o contorno e Espaçamento interior para o preenchimento.",
    ),
    (
        ("*", "Revert this element to its original plane?"),
        "Reverter este elemento ao seu plano original?",
    ),
    (("*", "Revert to Plane"), "Reverter para plano"),
    (("*", "Rig UI"), "UI do rig"),
    (("*", "Root Bone Length"), "Comprimento do osso raiz"),
    (("*", "Root Bone Name"), "Nome do osso raiz"),
    (
        ("*", "Round packed atlas dimensions up to a power of two (legacy GPU optimization)"),
        "Arredonda as dimensões do atlas empacotado para cima até uma potência de dois (otimização legada de GPU)",
    ),
    (("*", "Run Smoke Test"), "Rodar smoke test"),
    (
        ("*", "Run the full pipeline AND clear any prior debug companions for the sprite"),
        "Executa o pipeline completo E limpa quaisquer companheiros de depuração anteriores do sprite",
    ),
    (
        ("*", "Run the full pipeline, no debug companions"),
        "Executa o pipeline completo, sem companheiros de depuração",
    ),
    (
        (
            "*",
            "SIMPLE triangulates only the silhouette, holes, and user verts (sparse, Spine-like). DENSE adds the uniform grid + bone-density fill. Defaults read from the Skinning panel.",
        ),
        "SIMPLE triangula apenas a silhueta, os buracos e os vértices do usuário (esparso, estilo Spine). DENSE adiciona a grade uniforme + preenchimento por densidade de ossos. Os padrões são lidos do painel de Skinning.",
    ),
    (("*", "Save Pose to Library"), "Salvar pose na biblioteca"),
    (("*", "Save Snapshot"), "Salvar instantâneo"),
    (("*", "Scope"), "Escopo"),
    (("*", "See also:"), "Veja também:"),
    (("*", "Selected"), "Selecionado"),
    (
        ("*", "Selected row in the Animation panel's action list"),
        "Linha selecionada na lista de ações do painel de Animação",
    ),
    (
        ("*", "Selected row in the Proscenio outliner UIList"),
        "Linha selecionada na UIList do outliner do Proscenio",
    ),
    (
        ("*", "Selected row in the Proscenio slots UIList"),
        "Linha selecionada na UIList de slots do Proscenio",
    ),
    (
        ("*", "Selected row in the Skeleton panel's bone list"),
        "Linha selecionada na lista de ossos do painel de Esqueleto",
    ),
    (("*", "Setup Preview"), "Configurar prévia"),
    (("*", "Severity"), "Severidade"),
    (
        (
            "*",
            "Shift the figure so its lowest point sits on world Z=0. Matches the Godot / game-engine convention of pivoting characters at the feet. An authored manifest anchor takes precedence and keeps its placement (no feet shift), so a figure with a prop below its feet does not float.",
        ),
        "Desloca a figura para que seu ponto mais baixo fique no Z=0 do mundo. Segue a convenção do Godot / motor de jogo de pivotar personagens nos pés. Uma âncora de manifesto definida tem precedência e mantém seu posicionamento (sem deslocamento dos pés), para que uma figura com um adereço abaixo dos pés não flutue.",
    ),
    (("*", "Shortcuts"), "Atalhos"),
    (("*", "Show provenance overlay"), "Mostrar sobreposição de proveniência"),
    (
        (
            "*",
            "Show the developer surface: the Diagnostics panel and the automesh Debug Pipeline subpanel. Off by default so the sidebar stays focused on the authoring workflow",
        ),
        "Mostra a superfície de desenvolvedor: o painel de Diagnósticos e o subpainel Pipeline de depuração do automesh. Desativado por padrão para que a barra lateral permaneça focada no fluxo de autoria",
    ),
    (
        (
            "*",
            "Show this element's texture with crisp nearest-neighbor sampling (Closest interpolation) instead of Blender's bilinear blur (Linear). Authoring-only viewport state - it sets the interpolation on every image-texture node of this object's materials and is not exported. Off by default; the importer leaves new art on Linear.",
        ),
        "Mostra a textura deste elemento com amostragem nítida por vizinho mais próximo (interpolação Closest) em vez do borrão bilinear do Blender (Linear). Estado de viewport apenas para autoria - define a interpolação em cada nó de imagem-textura dos materiais deste objeto e não é exportado. Desativado por padrão; o importador deixa a arte nova em Linear.",
    ),
    (("*", "Simple (sparse, Spine-like)"), "Simples (esparso, estilo Spine)"),
    (("*", "Single nearest"), "Único mais próximo"),
    (("*", "Single-nearest"), "Único mais próximo"),
    (("*", "Skeleton"), "Esqueleto"),
    (("*", "Skeleton favorite"), "Favorito do esqueleto"),
    (("*", "Slot bone"), "Osso do slot"),
    (("*", "Slot default"), "Padrão do slot"),
    (("*", "Slot name"), "Nome do slot"),
    (("*", "Slots"), "Slots"),
    (("*", "Snap increment"), "Incremento de encaixe"),
    (("*", "Snap to UV bounds"), "Encaixar nos limites de UV"),
    (("*", "Snapshot"), "Instantâneo"),
    (("*", "Soft"), "Suave"),
    (("*", "Sort by draw order"), "Ordenar por ordem de desenho"),
    (("*", "Source"), "Fonte"),
    (
        (
            "*",
            "Source-pixel margin that adds an inner edge-density loop (the silhouette eroded inward) as an extra constraint ring near the boundary. The mesh interior stays FILLED - the loop only adds silhouette edge density, it does not carve a hole. Zero (default) skips it and produces a single-contour triangulation, the common case for 2D skinning (matches Spine / DragonBones). Set > 0 for fine border deformation control (cape, hair, ribbon).",
        ),
        "Margem em pixels de origem que adiciona um loop interno de densidade de arestas (a silhueta erodida para dentro) como um anel de restrição extra perto da borda. O interior da malha permanece PREENCHIDO - o loop só adiciona densidade de arestas na silhueta, não recorta um buraco. Zero (padrão) pula isso e produz uma triangulação de contorno único, o caso comum para skinning 2D (segue Spine / DragonBones). Defina > 0 para controle fino de deformação de borda (capa, cabelo, fita).",
    ),
    (("*", "Spacing"), "Espaçamento"),
    (
        ("*", "Sprite proscenio property the driver writes to"),
        "Propriedade proscenio do sprite na qual o driver escreve",
    ),
    (
        ("*", "Spritesheet column count (sprite only)"),
        "Contagem de colunas do spritesheet (somente sprite)",
    ),
    (
        ("*", "Spritesheet row count (sprite only)"),
        "Contagem de linhas do spritesheet (somente sprite)",
    ),
    (("*", "Steiner points pre-insertion"), "Pontos de Steiner antes da inserção"),
    (("*", "Step back to the previous stage"), "Voltar ao estágio anterior"),
    (
        (
            "*",
            "Sticky destination for one-click re-export. Saved with the .blend so the document carries its export target.",
        ),
        "Destino persistente para reexportação em um clique. Salvo com o .blend para que o documento carregue seu alvo de exportação.",
    ),
    (
        ("*", "Stop after Laplacian smoothing of the raw contours"),
        "Parar após a suavização Laplaciana dos contornos brutos",
    ),
    (
        (
            "*",
            "Stop after Moore Neighbour tracing + world conversion; shows pixel-stair contours before any smoothing",
        ),
        "Parar após o traçado por Vizinhança de Moore + conversão para o mundo; mostra os contornos em escada de pixels antes de qualquer suavização",
    ),
    (
        ("*", "Stop after arc-length resampling; these are the actual verts that enter the bmesh"),
        "Parar após a reamostragem por comprimento de arco; estes são os vértices reais que entram no bmesh",
    ),
    (
        (
            "*",
            "Stop after bmesh.ops.triangle_fill; mesh shows the strip annulus before interior Steiner points are inserted",
        ),
        "Parar após bmesh.ops.triangle_fill; a malha mostra o annulus em tira antes que os pontos de Steiner interiores sejam inseridos",
    ),
    (
        (
            "*",
            "Stop after computing radial bridge offset; shows the outer + inner verts + planned bridge edges (no fill)",
        ),
        "Parar após calcular o deslocamento da ponte radial; mostra os vértices externos + internos + as arestas de ponte planejadas (sem preenchimento)",
    ),
    (
        ("*", "Stop after generating Steiner interior points (uniform grid + bone-aware density)"),
        "Parar após gerar os pontos interiores de Steiner (grade uniforme + densidade ciente dos ossos)",
    ),
    (
        (
            "*",
            "Stop the automesh pipeline at the named stage + emit a wireframe companion object into the Proscenio.Debug collection so the user can inspect intermediate output. Off / Final run the full pipeline normally; non-final stages skip the bmesh write into the active sprite",
        ),
        "Para o pipeline do automesh no estágio nomeado + emite um objeto companheiro em wireframe na coleção Proscenio.Debug para que o usuário possa inspecionar a saída intermediária. Off / Final executam o pipeline completo normalmente; estágios não-finais pulam a gravação do bmesh no sprite ativo",
    ),
    (
        ("*", "Stop the pipeline at a stage + emit a debug companion"),
        "Para o pipeline em um estágio + emite um companheiro de depuração",
    ),
    (
        (
            "*",
            "Substring filter applied to the Proscenio outliner (the outliner subpanel). Empty string shows every Proscenio-relevant object.",
        ),
        "Filtro de substring aplicado ao outliner do Proscenio (o subpainel do outliner). String vazia mostra todo objeto relevante ao Proscenio.",
    ),
    (
        (
            "*",
            "Switch to Front Orthographic on invoke and restore the previous view on exit. Uncheck to author from any view (the picture plane is still locked to Y=0).",
        ),
        "Muda para a Frontal Ortográfica ao invocar e restaura a vista anterior ao sair. Desmarque para autorar a partir de qualquer vista (o plano da imagem ainda fica travado em Y=0).",
    ),
    (("*", "Target"), "Alvo"),
    (("*", "Target value at the input maximum"), "Valor-alvo no máximo da entrada"),
    (("*", "Target value at the input minimum"), "Valor-alvo no mínimo da entrada"),
    (
        (
            "*",
            "Target vertex count for the outer contour after Laplacian smoothing + arc-length resampling. Inner contour uses half this count. Higher = smoother silhouette + more deformation control + more triangles.",
        ),
        "Contagem de vértices alvo para o contorno externo após a suavização Laplaciana + reamostragem por comprimento de arco. O contorno interno usa metade desta contagem. Maior = silhueta mais suave + mais controle de deformação + mais triângulos.",
    ),
    (
        ("*", "Target verts beyond this distance from any source vert get no weights"),
        "Vértices-alvo além desta distância de qualquer vértice de fonte não recebem pesos",
    ),
    (
        (
            "*",
            "Target verts farther than this from any source vert receive no weights (Weight Transfer). Raise it when targets sit far from the source mesh; the operator warns when a target gets zero coverage.",
        ),
        "Vértices-alvo mais distantes que isto de qualquer vértice de fonte não recebem pesos (Transferência de pesos). Aumente quando os alvos ficam longe da malha de origem; o operador avisa quando um alvo recebe cobertura zero.",
    ),
    (
        ("*", "Target-property value when the bone sits at the input maximum."),
        "Valor da propriedade-alvo quando o osso está no máximo da entrada.",
    ),
    (
        ("*", "Target-property value when the bone sits at the input minimum."),
        "Valor da propriedade-alvo quando o osso está no mínimo da entrada.",
    ),
    (("*", "Texture Region"), "Região da textura"),
    (
        (
            "*",
            "The armature every Proscenio skeleton operation targets - Quick Armature appends bones here, IK / pose helpers act on this rig, and the writer exports it. Set explicitly via the Skeleton subpanel to avoid surprises in scenes with more than one armature; if unset, the operators auto-detect a sensible target (active object > single scene armature > Proscenio.QuickRig fallback).",
        ),
        "A armadura que toda operação de esqueleto do Proscenio tem como alvo - a Armadura Rápida acrescenta ossos aqui, os auxiliares de IK / pose atuam neste rig, e o gravador a exporta. Defina explicitamente pelo subpainel de Esqueleto para evitar surpresas em cenas com mais de uma armadura; se não definida, os operadores detectam automaticamente um alvo sensato (objeto ativo > única armadura da cena > alternativa Proscenio.QuickRig).",
    ),
    (
        ("*", "The image + placement are kept. Ctrl+Z undoes it."),
        "A imagem + o posicionamento são mantidos. Ctrl+Z desfaz.",
    ),
    (
        ("*", "The proscenio.<prop> data path whose driver is removed"),
        "O caminho de dados proscenio.<prop> cujo driver é removido",
    ),
    (("*", "The snapshot to restore"), "O instantâneo a restaurar"),
    (
        ("*", "This DESTROYS the generated mesh and its weight paint:"),
        "Isto DESTRÓI a malha gerada e sua pintura de peso:",
    ),
    (("*", "Toggle"), "Alternar"),
    (("*", "Toggle this bone's selection (Ctrl)"), "Alterna a seleção deste osso (Ctrl)"),
    (("*", "Toggle this row's selection (Ctrl)"), "Alterna a seleção desta linha (Ctrl)"),
    (("*", "Topic"), "Tópico"),
    (("*", "Trace resolution"), "Resolução do traçado"),
    (
        ("*", "True after the user has run Validate at least once this session"),
        "Verdadeiro depois que o usuário executou Validar pelo menos uma vez nesta sessão",
    ),
    (("*", "Unbind from Bone"), "Desvincular do osso"),
    (
        ("*", "Uniform grid + bone-density subdivision"),
        "Grade uniforme + subdivisão por densidade de ossos",
    ),
    (
        ("*", "Uniform interior grid + bone-density subdivision (current default)"),
        "Grade interior uniforme + subdivisão por densidade de ossos (padrão atual)",
    ),
    (
        ("*", "Uniform interior grid over the drawn contour (interior spacing)"),
        "Grade interior uniforme sobre o contorno desenhado (espaçamento interior)",
    ),
    (("*", "Unpack Atlas"), "Desempacotar atlas"),
    (("*", "Use existing instead:"), "Usar o existente em vez disso:"),
    (
        ("*", "Use the raw expression instead of the two-range linear map"),
        "Usar a expressão bruta em vez do mapa linear de duas faixas",
    ),
    (("*", "Validate"), "Validar"),
    (("*", "Validation ran"), "Validação executada"),
    (("*", "Vertical frames"), "Quadros verticais"),
    (("*", "Viewport display:"), "Exibição na viewport:"),
    (
        (
            "*",
            "Weight 1.0 inside per-bone radius (read from bone Custom Property), 0 outside, then per-vert normalized",
        ),
        "Peso 1.0 dentro do raio por osso (lido da Propriedade Personalizada do osso), 0 fora, depois normalizado por vértice",
    ),
    (("*", "Weight Opacity"), "Opacidade de peso"),
    (("*", "Weight Paint"), "Pintura de peso"),
    (("*", "Weight Transfer"), "Transferência de pesos"),
    (("*", "Weight transfer max distance"), "Distância máxima da transferência de pesos"),
    (
        (
            "*",
            "When ON (default), running Automesh from Alpha on an already-bound mesh snapshots the current weights, regenerates the mesh, then reprojects the weights onto the new topology via UV anchors. OFF lets automesh wipe weights (legacy behavior) - useful when the sprite changed enough that interpolation would produce nonsense.",
        ),
        "Quando ATIVO (padrão), executar o Automesh a partir do alpha em uma malha já vinculada tira um instantâneo dos pesos atuais, regenera a malha, depois reprojeta os pesos na nova topologia via âncoras de UV. INATIVO deixa o automesh apagar os pesos (comportamento legado) - útil quando o sprite mudou o suficiente para que a interpolação produzisse algo sem sentido.",
    ),
    (
        (
            "*",
            "When ON (recommended), no-modifier drag chains the new bone to the last one (head snaps to parent's tail, matches Blender's E extrude reflex). Hold Shift to start a new root instead. When OFF, the legacy vocabulary applies: no-modifier = unparented root, Shift = chain (no connect).",
        ),
        "Quando ATIVO (recomendado), arrastar sem modificador encadeia o novo osso ao último (a cabeça encaixa na cauda do pai, seguindo o reflexo de extrusão E do Blender). Segure Shift para começar uma nova raiz em vez disso. Quando INATIVO, o vocabulário legado se aplica: sem modificador = raiz sem parenteamento, Shift = encadear (sem conectar).",
    ),
    (
        (
            "*",
            "When ON and the target armature has deform bones, add extra interior triangles near each bone segment so the mesh has more density where deformation actually happens. OFF (default) falls back to uniform interior density.",
        ),
        "Quando ATIVO e a armadura-alvo tem ossos de deformação, adiciona triângulos interiores extras perto de cada segmento de osso para que a malha tenha mais densidade onde a deformação realmente acontece. INATIVO (padrão) recai para densidade interior uniforme.",
    ),
    (
        (
            "*",
            "When ON, the Edit Weights session colors each vert by its weight source: cyan = reprojected (came from a regen), white = user paint, gray = auto seed (untouched bind output). The GPU overlay renders inside the Edit Weights modal and refreshes at stroke end.",
        ),
        "Quando ATIVO, a sessão de Editar pesos colore cada vértice pela sua fonte de peso: ciano = reprojetado (veio de uma regeneração), branco = pintura do usuário, cinza = semente automática (saída de vínculo intocada). A sobreposição de GPU renderiza dentro do modal de Editar pesos e atualiza ao fim do traço.",
    ),
    (
        (
            "*",
            "When True on an Empty object, marks it as the parent of a slot - child meshes become attachments, the writer emits a slots[] entry, and the Godot importer wires a Node2D parent + visible-toggled children.",
        ),
        "Quando Verdadeiro em um objeto Vazio, o marca como o pai de um slot - as malhas filhas se tornam anexos, o gravador emite uma entrada slots[], e o importador do Godot conecta um pai Node2D + filhos com visibilidade alternada.",
    ),
    (
        (
            "*",
            "When True, the Skeleton bone list hides every bone except those flagged via bone.proscenio.is_favorite.",
        ),
        "Quando Verdadeiro, a lista de ossos do Esqueleto esconde todo osso exceto os marcados via bone.proscenio.is_favorite.",
    ),
    (
        (
            "*",
            "When True, the outliner hides every object except those flagged via proscenio.is_outliner_favorite.",
        ),
        "Quando Verdadeiro, o outliner esconde todo objeto exceto os marcados via proscenio.is_outliner_favorite.",
    ),
    (
        (
            "*",
            "When True, the outliner lists the plane rows by their Y Location (Draw Order) - front (highest order) at the top, mirroring the Photoshop layer stack - instead of the parenting tree. The armature stays pinned to the top. Overrides the native A-Z sort while on.",
        ),
        "Quando Verdadeiro, o outliner lista as linhas de planos pela sua Posição Y (Ordem de Desenho) - a frente (maior ordem) no topo, espelhando a pilha de camadas do Photoshop - em vez da árvore de parenteamento. A armadura permanece fixada no topo. Substitui a ordenação nativa A-Z enquanto ativo.",
    ),
    (
        (
            "*",
            "When packing, keep this sprite's own material instead of linking it to the shared 'Proscenio.PackedAtlas' material. Useful for effect sprites that need their own shader (additive blend, custom fresnel, etc).",
        ),
        "Ao empacotar, mantém o material próprio deste sprite em vez de vinculá-lo ao material compartilhado 'Proscenio.PackedAtlas'. Útil para sprites de efeito que precisam de seu próprio shader (mistura aditiva, fresnel personalizado, etc).",
    ),
    (
        ("*", "Where the imported figure sits relative to the world origin"),
        "Onde a figura importada fica em relação à origem do mundo",
    ),
    (
        ("*", "Whether the Sprite2D's offset centers on its origin"),
        "Se o deslocamento do Sprite2D é centralizado em sua origem",
    ),
    (("*", "Width"), "Largura"),
    (
        (
            "*",
            "Width of the corridor gap carved by cut strokes, in world units. The stroke is offset +/- cut_margin/2 perpendicular to its tangent; the corridor between the two offset lines becomes a CDT hole, so the triangulation excludes it cleanly. Larger = wider gap between the cut sides. Clamped to a 0.01 minimum so the corridor never collapses.",
        ),
        "Largura da folga do corredor esculpida pelos traços de corte, em unidades de mundo. O traço é deslocado +/- cut_margin/2 perpendicular à sua tangente; o corredor entre as duas linhas deslocadas se torna um buraco do CDT, então a triangulação o exclui de forma limpa. Maior = folga mais larga entre os lados do corte. Limitado a um mínimo de 0.01 para que o corredor nunca colapse.",
    ),
    (
        (
            "*",
            "World-unit gap between adjacent inner loops in the authoring modal. Smaller = denser loops near the boundary; larger = single loop closer to mesh center",
        ),
        "Folga em unidades de mundo entre loops internos adjacentes no modal de autoria. Menor = loops mais densos perto da borda; maior = loop único mais próximo do centro da malha",
    ),
    (
        (
            "*",
            "World-unit grid step applied while Ctrl is held during drag. Set to 1.0 to align bones to whole world units (matches PPU=100 pixel-perfect cutout authoring).",
        ),
        "Passo de grade em unidades de mundo aplicado enquanto Ctrl é mantido durante o arraste. Defina como 1.0 para alinhar os ossos a unidades de mundo inteiras (combina com a autoria cutout pixel-perfect PPU=100).",
    ),
    (
        (
            "*",
            "World-unit radius around each bone segment within which the density-under-bones subdivision applies.",
        ),
        "Raio em unidades de mundo ao redor de cada segmento de osso dentro do qual a subdivisão de densidade sob os ossos se aplica.",
    ),
    (
        (
            "*",
            "World-unit spacing for the interior Steiner-point grid fed into bmesh.ops.triangle_fill. Lower = denser interior = more triangles that can deform under bone influence. Tune against the sprite's world-unit scale (pixels per unit in the scene props).",
        ),
        "Espaçamento em unidades de mundo para a grade interior de pontos de Steiner alimentada em bmesh.ops.triangle_fill. Menor = interior mais denso = mais triângulos que podem deformar sob a influência dos ossos. Ajuste conforme a escala em unidades de mundo do sprite (pixels por unidade nas props de cena).",
    ),
    (("*", "X"), "X"),
    (("*", "Y"), "Y"),
    (("*", "Y Location (Draw Order)"), "Posição Y (Ordem de Desenho)"),
    (("*", "Y Location spacing"), "Espaçamento da Posição Y"),
    (("*", "Zero Weights"), "Pesos zero"),
    (
        ("*", "active mesh has no image texture - add a material with a TEX_IMAGE node first"),
        "a malha ativa não tem textura de imagem - adicione primeiro um material com um nó TEX_IMAGE",
    ),
    (
        (
            "*",
            "active mesh has no image texture - add a material with a TEX_IMAGE node first, or use an automesh-able imported sprite",
        ),
        "a malha ativa não tem textura de imagem - adicione primeiro um material com um nó TEX_IMAGE, ou use um sprite importado que aceite automesh",
    ),
    (
        (
            "*",
            "active object is a sprite element - automesh is mesh-only; meshing would replace its quad. To attach a sprite to a bone, parent it with Ctrl+P > Bone instead",
        ),
        "o objeto ativo é um elemento sprite - o automesh é apenas para malhas; gerar malha substituiria seu quad. Para anexar um sprite a um osso, em vez disso parenteie-o com Ctrl+P > Bone",
    ),
    (
        (
            "*",
            "active object is a sprite element - mesh authoring is mesh-only; it would replace its quad. To attach a sprite to a bone, parent it with Ctrl+P > Bone instead",
        ),
        "o objeto ativo é um elemento sprite - a autoria de malha é apenas para malhas; isso substituiria seu quad. Para anexar um sprite a um osso, em vez disso parenteie-o com Ctrl+P > Bone",
    ),
    (("*", "active object is not a sprite element"), "o objeto ativo não é um elemento sprite"),
    (("*", "active object must be a mesh"), "o objeto ativo deve ser uma malha"),
    (("*", "active object must be a mesh element"), "o objeto ativo deve ser um elemento de malha"),
    (
        ("*", "an authoring modal is already running - finish it first"),
        "um modal de autoria já está em execução - finalize-o primeiro",
    ),
    (
        ("*", "applies only to the planar modes - Bone Heat ignores these"),
        "aplica-se somente aos modos planares - o Bone Heat os ignora",
    ),
    (("*", "armature has no pose bones"), "a armadura não tem ossos de pose"),
    (("*", "atlas: not linked in material"), "atlas: não vinculado no material"),
    (("*", "bind first to enable"), "vincule primeiro para habilitar"),
    (("*", "bone too short, skipped"), "osso curto demais, ignorado"),
    (("*", "bone: (unparented)"), "osso: (sem parenteamento)"),
    (
        (
            "*",
            "bpy.ops.poselib.create_pose_asset not available (Blender < 3.5 or pose library disabled).",
        ),
        "bpy.ops.poselib.create_pose_asset não disponível (Blender < 3.5 ou biblioteca de poses desativada).",
    ),
    (
        ("*", "could not enter Edit Mode on the QuickRig armature"),
        "não foi possível entrar no modo de edição na armadura QuickRig",
    ),
    (
        ("*", "element type is locked in Weight Paint mode"),
        "o tipo de elemento está travado no modo de pintura de peso",
    ),
    (
        ("*", "enter Pose mode to bake / save poses"),
        "entre no modo de pose para assar / salvar poses",
    ),
    (("*", "failed to create QuickRig armature"), "falha ao criar a armadura QuickRig"),
    (
        ("*", "hand-authored mesh - not a Proscenio element yet"),
        "malha feita à mão - ainda não é um elemento Proscenio",
    ),
    (("*", "island needs at least 3 points"), "a ilha precisa de pelo menos 3 pontos"),
    (("*", "issue has no object name"), "o problema não tem nome de objeto"),
    (
        ("*", "manual contour needs at least 3 points"),
        "o contorno manual precisa de pelo menos 3 pontos",
    ),
    (
        ("*", "material has no Image Texture node - cannot slice"),
        "o material não tem nó de Textura de Imagem - não é possível fatiar",
    ),
    (
        ("*", "mesh has no vertex groups - run Bind first"),
        "a malha não tem grupos de vértices - execute Vincular primeiro",
    ),
    (
        ("*", "mesh tools are mesh-only (this is a sprite)"),
        "as ferramentas de malha são apenas para malhas (isto é um sprite)",
    ),
    (("*", "modal active"), "modal ativo"),
    (("*", "must run in a 3D viewport"), "execute numa viewport 3D"),
    (
        ("*", "no Armature in scene - use Quick Armature below"),
        "nenhuma armadura na cena - use a Armadura Rápida abaixo",
    ),
    (
        ("*", "no IK chains - add one in Pose Mode"),
        "nenhuma cadeia IK - adicione uma no modo de pose",
    ),
    (("*", "no MESH objects selected"), "nenhum objeto MESH selecionado"),
    (("*", "no actions to export"), "nenhuma ação para exportar"),
    (("*", "no active Element to re-import"), "nenhum Elemento ativo para reimportar"),
    (("*", "no active armature"), "nenhuma armadura ativa"),
    (
        ("*", "no active bone - select one or use the All Bones scope"),
        "nenhum osso ativo - selecione um ou use o escopo Todos os ossos",
    ),
    (
        ("*", "no armature - pick an Active Armature in the Skeleton panel"),
        "nenhuma armadura - escolha uma Armadura ativa no painel de Esqueleto",
    ),
    (("*", "no armature found for this slot"), "nenhuma armadura encontrada para este slot"),
    (("*", "no armature found for this sprite"), "nenhuma armadura encontrada para este sprite"),
    (("*", "no armature name supplied"), "nenhum nome de armadura fornecido"),
    (
        ("*", "no armature picked - pick one in the Skeleton panel"),
        "nenhuma armadura escolhida - escolha uma no painel de Esqueleto",
    ),
    (("*", "no armature to follow"), "nenhuma armadura para seguir"),
    (("*", "no armature to parent to"), "nenhuma armadura para parentear"),
    (("*", "no atlas linked in materials"), "nenhum atlas vinculado nos materiais"),
    (
        ("*", "no bone - attachments will not follow any bone"),
        "nenhum osso - os anexos não seguirão nenhum osso",
    ),
    (
        ("*", "no bone collections - add them in Blender's Bone Collections panel"),
        "nenhuma coleção de ossos - adicione-as no painel de Coleções de Ossos do Blender",
    ),
    (("*", "no driver data path given"), "nenhum caminho de dados de driver fornecido"),
    (("*", "no empty vertex groups to clear"), "nenhum grupo de vértices vazio para limpar"),
    (("*", "no issues - ready to export"), "nenhum problema - pronto para exportar"),
    (("*", "no material on this mesh"), "nenhum material nesta malha"),
    (("*", "no mesh objects selected"), "nenhum objeto de malha selecionado"),
    (
        (
            "*",
            "no original plane recorded for this element (not a PSD import) - nothing to revert to",
        ),
        "nenhum plano original registrado para este elemento (não é uma importação de PSD) - nada para reverter",
    ),
    (
        ("*", "no rig - pick an armature in Skeleton"),
        "nenhum rig - escolha uma armadura no Esqueleto",
    ),
    (
        ("*", "no rig picked - skeleton ops will create a new Proscenio.QuickRig"),
        "nenhum rig escolhido - as operações de esqueleto criarão um novo Proscenio.QuickRig",
    ),
    (
        ("*", "no sidecar - run Bind to Target Armature first"),
        "nenhum sidecar - execute Vincular à armadura-alvo primeiro",
    ),
    (
        ("*", "no sidecar found on active mesh - run Bind to Target Armature first"),
        "nenhum sidecar encontrado na malha ativa - execute Vincular à armadura-alvo primeiro",
    ),
    (
        ("*", "no sidecar on active mesh - run Bind to Target Armature first"),
        "nenhum sidecar na malha ativa - execute Vincular à armadura-alvo primeiro",
    ),
    (("*", "no slicer to remove"), "nenhum fatiador para remover"),
    (
        ("*", "no slots yet - select meshes and Create Slot"),
        "ainda nenhum slot - selecione malhas e Criar slot",
    ),
    (("*", "no snapshot (run Bind first)"), "nenhum instantâneo (execute Vincular primeiro)"),
    (
        ("*", "no sprite meshes with source images found"),
        "nenhuma malha de sprite com imagens de origem encontrada",
    ),
    (
        (
            "*",
            "no target armature - automesh uses uniform interior density (pick an armature in the Skeleton panel for density-under-bones)",
        ),
        "nenhuma armadura-alvo - o automesh usa densidade interior uniforme (escolha uma armadura no painel de Esqueleto para densidade sob os ossos)",
    ),
    (
        ("*", "no target armature - pick one in the Skeleton panel first"),
        "nenhuma armadura-alvo - escolha uma no painel de Esqueleto primeiro",
    ),
    (
        ("*", "no weights to snapshot (mesh has no UV layer)"),
        "nenhum peso para o instantâneo (a malha não tem camada de UV)",
    ),
    (
        (
            "*",
            "no writable asset library configured. Add one in Preferences > File Paths > Asset Libraries with a path Blender can write to, then retry.",
        ),
        "nenhuma biblioteca de assets gravável configurada. Adicione uma em Preferências > Caminhos de Arquivo > Bibliotecas de Assets com um caminho no qual o Blender possa gravar, depois tente de novo.",
    ),
    (("*", "nothing to redo"), "nada para refazer"),
    (("*", "nothing to undo"), "nada para desfazer"),
    (
        ("*", "opacity 0 is not fully invisible (Blender 145603)"),
        "opacidade 0 não é totalmente invisível (Blender 145603)",
    ),
    (("*", "pick a bone for the slot to follow"), "escolha um osso para o slot seguir"),
    (("*", "pick a bone for the sprite to follow"), "escolha um osso para o sprite seguir"),
    (("*", "pick a source armature in the panel"), "escolha uma armadura de fonte no painel"),
    (
        ("*", "picked armature no longer exists - pick one again"),
        "a armadura escolhida não existe mais - escolha uma de novo",
    ),
    (("*", "place at least 3 vertices first"), "coloque pelo menos 3 vértices primeiro"),
    (
        ("*", "proscenio property group not registered"),
        "grupo de propriedades do proscenio não registrado",
    ),
    (("*", "proscenio scene props not registered"), "props de cena do proscenio não registradas"),
    (
        ("*", "rigid follow of one bone - no slot, no swap"),
        "acompanhamento rígido de um osso - sem slot, sem troca",
    ),
    (("*", "run Pack Atlas first"), "execute Empacotar atlas primeiro"),
    (("*", "run Validate to see issues"), "execute Validar para ver os problemas"),
    (("*", "scene props not registered"), "props de cena não registradas"),
    (
        ("*", "select a mesh element (Weight Paint is mesh-only)"),
        "selecione um elemento de malha (a Pintura de peso é apenas para malhas)",
    ),
    (("*", "select a mesh object to incorporate"), "selecione um objeto de malha para incorporar"),
    (("*", "select a mesh or sprite element"), "selecione um elemento de malha ou sprite"),
    (("*", "select a mesh to author"), "selecione uma malha para autorar"),
    (("*", "select a mesh to generate or edit"), "selecione uma malha para gerar ou editar"),
    (
        ("*", "select a sprite mesh as the active object"),
        "selecione uma malha de sprite como o objeto ativo",
    ),
    (
        ("*", "sidecar has no entries (legacy bind) - re-bind to populate"),
        "o sidecar não tem entradas (vínculo legado) - vincule de novo para preencher",
    ),
    (
        ("*", "sidecar/topology mismatch - re-bind to the current mesh topology"),
        "incompatibilidade entre sidecar/topologia - vincule de novo à topologia atual da malha",
    ),
    (
        ("*", "slot_bone set but inert - Bind to Bone to follow in Blender"),
        "slot_bone definido mas inerte - Vincular ao osso para seguir no Blender",
    ),
    (("*", "snapshot name cannot be empty"), "o nome do instantâneo não pode ficar vazio"),
    (
        (
            "*",
            "target rig changed since bind - prior weights reference bones this armature does not deform, so they were NOT preserved; re-bind to the current rig",
        ),
        "o rig-alvo mudou desde o vínculo - os pesos anteriores referenciam ossos que esta armadura não deforma, então NÃO foram preservados; vincule de novo ao rig atual",
    ),
    (
        ("*", "to rig a sprite, parent it to a bone: Ctrl+P > Bone"),
        "para fazer o rig de um sprite, parenteie-o a um osso: Ctrl+P > Bone",
    ),
    (
        ("*", "topology changed since bind - re-bind before saving snapshots"),
        "a topologia mudou desde o vínculo - vincule de novo antes de salvar instantâneos",
    ),
    (
        (
            "*",
            "topology changed since last snapshot - run Automesh from Alpha with preserve_on_regen ON to re-establish the snapshot",
        ),
        "a topologia mudou desde o último instantâneo - execute o Automesh a partir do alpha com preserve_on_regen ATIVO para restabelecer o instantâneo",
    ),
    (
        (
            "*",
            "topology changed since this snapshot - run Automesh from Alpha with preserve_on_regen ON to re-establish it",
        ),
        "a topologia mudou desde este instantâneo - execute o Automesh a partir do alpha com preserve_on_regen ATIVO para restabelecê-lo",
    ),
    (("*", "validation OK"), "validação OK"),
    (
        (
            "Operator",
            "Adds (or focuses) an orthographic camera sized to the scene's pixels_per_unit and render resolution. Use Numpad 0 to enter the view.",
        ),
        "Adiciona (ou foca) uma câmera ortográfica dimensionada conforme o pixels_per_unit e a resolução de render da cena. Use o Numpad 0 para entrar na vista.",
    ),
    (
        (
            "Operator",
            "Adds a driver to the active sprite's proscenio property using the armature/bone selected in the panel. Re-running on the same sprite + target property replaces the driver.",
        ),
        "Adiciona um driver à propriedade proscenio do sprite ativo usando a armadura/osso selecionado no painel. Executar de novo no mesmo sprite + propriedade-alvo substitui o driver.",
    ),
    (
        (
            "Operator",
            "Adds an IK chain to the active pose bone - an IK constraint named 'Proscenio IK' (chain length 2) wired to a control bone created at the chain tip, so the chain solves on its own - or removes both when one is already present. Hand-added constraints and retargeted ones are left untouched",
        ),
        "Adiciona uma cadeia IK ao osso de pose ativo - uma restrição IK chamada 'Proscenio IK' (comprimento de cadeia 2) ligada a um osso de controle criado na ponta da cadeia, para que a cadeia resolva sozinha - ou remove ambos quando um já está presente. Restrições adicionadas à mão e as redirecionadas ficam intocadas",
    ),
    (
        (
            "Operator",
            "Adopt this hand-authored mesh as a Proscenio element. Auto picks Sprite for a single quad and Mesh otherwise - override in the redo panel",
        ),
        "Adota esta malha feita à mão como um elemento Proscenio. O modo automático escolhe Sprite para um único quad e Malha nos demais casos - ajuste no painel de refazer",
    ),
    (
        ("Operator", "Advance to the next stage / step back, in the running Automesh modal"),
        "Avança para o próximo estágio / volta um passo, no modal do Automesh em execução",
    ),
    (("Operator", "Apply Brush Curve Preset"), "Aplicar predefinição de curva do pincel"),
    (
        ("Operator", "Apply a bone color to every bone in this collection at once"),
        "Aplica uma cor de osso a todos os ossos desta coleção de uma vez",
    ),
    (
        (
            "Operator",
            "Assigns this Animation-panel row's action to the armature picked in the Skeleton panel so the timeline plays it",
        ),
        "Atribui a ação desta linha do painel de Animação à armadura escolhida no painel de Esqueleto para que a linha do tempo a reproduza",
    ),
    (("Operator", "Automesh Step"), "Passo do automesh"),
    (
        (
            "Operator",
            "Bakes the active pose bone's IK chain to bone keyframes across the action range (visual keying) and clears the IK constraint, so the exporter reads real bone motion instead of flat fcurves. Requires Pose Mode and an IK constraint on the active bone.",
        ),
        "Assa a cadeia IK do osso de pose ativo em quadros-chave de osso por toda a faixa da ação (keying visual) e remove a restrição IK, para que o exportador leia o movimento real do osso em vez de fcurves planas. Requer o modo de pose e uma restrição IK no osso ativo.",
    ),
    (
        (
            "Operator",
            "Bind the active mesh to the Proscenio target armature (picked in the Skeleton panel). Default mode delegates to Blender's bone heat (best for 2D rigs); Proscenio's planar proximity / envelope / single-nearest / empty modes are available as F3-redo fallbacks. Surfaces 5 pre-flight diagnoses + writes a sidecar stub the reproject step consumes",
        ),
        "Vincula a malha ativa à armadura-alvo do Proscenio (escolhida no painel de Esqueleto). O modo padrão delega ao bone heat do Blender (melhor para rigs 2D); os modos planares proximity / envelope / single-nearest / empty do Proscenio ficam disponíveis como alternativas no F3-refazer. Expõe 5 diagnósticos preliminares + grava um sidecar-stub que o passo de reprojeção consome",
    ),
    (
        (
            "Operator",
            "Build a deformable annulus mesh from the active sprite's image alpha channel. Pure-Python contour walker (no OpenCV dependency) + Laplacian smoothing + arc-length resampling + bone-aware interior density when an active armature is set. Re-runs preserve the original UV-pinned quad via the proscenio_base_sprite vertex group",
        ),
        "Constrói uma malha annulus deformável a partir do canal alpha da imagem do sprite ativo. Percorredor de contorno em Python puro (sem dependência de OpenCV) + suavização Laplaciana + reamostragem por comprimento de arco + densidade interior ciente dos ossos quando uma armadura ativa está definida. Reexecuções preservam o quad original fixado por UV via o grupo de vértices proscenio_base_sprite",
    ),
    (
        (
            "Operator",
            "Bundle the current armature pose into a Pose Library asset so it shows up in the Asset Browser. Wraps Blender's poselib.create_pose_asset.",
        ),
        "Agrupa a pose atual da armadura em um asset de Biblioteca de Poses para que apareça no Navegador de Assets. Envolve o poselib.create_pose_asset do Blender.",
    ),
    (
        (
            "Operator",
            "Click-drag in the 3D viewport to draw a bone (head -> tail). Hold Shift to chain onto the previous bone. Right-click-select a bone to chain the next bone from it. Runs in Edit Mode; press Esc or Enter to finish.",
        ),
        "Clique e arraste na viewport 3D para desenhar um osso (cabeça -> cauda). Segure Shift para encadear no osso anterior. Selecione um osso com o botão direito para encadear o próximo osso a partir dele. Executa no modo de edição; pressione Esc ou Enter para finalizar.",
    ),
    (
        ("Operator", "Configure the active weight-paint brush curve to a named preset"),
        "Configura a curva do pincel de pintura de peso ativo para uma predefinição nomeada",
    ),
    (("Operator", "Copy Weights to Selected"), "Copiar pesos para os selecionados"),
    (
        (
            "Operator",
            "Copy vertex weights from the active mesh to all other selected meshes by nearest-vertex world position",
        ),
        "Copia os pesos de vértices da malha ativa para todas as outras malhas selecionadas pela posição de mundo do vértice mais próximo",
    ),
    (
        (
            "Operator",
            "Create a new slot Empty. With no mesh selected, anchors at the active pose bone. With meshes selected, wraps them as attachments under a fresh Empty parented to the active mesh's bone.",
        ),
        "Cria um novo Vazio de slot. Sem malha selecionada, ancora no osso de pose ativo. Com malhas selecionadas, as envolve como anexos sob um Vazio novo parenteado ao osso da malha ativa.",
    ),
    (
        (
            "Operator",
            "Delete every vertex group on the active mesh that has no nonzero weight. Empty groups carry no weights, so removing them is safe; a confirm lists what will be deleted first",
        ),
        "Exclui todo grupo de vértices da malha ativa que não tenha nenhum peso diferente de zero. Grupos vazios não carregam pesos, então removê-los é seguro; uma confirmação lista o que será excluído primeiro",
    ),
    (
        (
            "Operator",
            "Enter a 2D-safe weight paint context for the active mesh. Applies a weight-paint preset tuned for 2D sprites (Front Faces off, mirror from target rig), shows the provenance overlay (cyan=reprojected / white=user paint / gray=auto seed), and tags brushed verts as user_paint in the sidecar via per-stroke diff. ESC hard-exits and restores brush + bone visibility + mode + selection",
        ),
        "Entra em um contexto de pintura de peso seguro para 2D na malha ativa. Aplica uma predefinição de pintura de peso ajustada para sprites 2D (Faces Frontais desativadas, espelhamento a partir do rig-alvo), mostra a sobreposição de proveniência (ciano=reprojetado / branco=pintura do usuário / cinza=semente automática), e marca os vértices pintados como user_paint no sidecar via diff por traço. ESC força a saída e restaura pincel + visibilidade dos ossos + modo + seleção",
    ),
    (("Operator", "Export Weight Snapshot"), "Exportar instantâneo de pesos"),
    (("Operator", "Import Weight Snapshot"), "Importar instantâneo de pesos"),
    (
        (
            "Operator",
            "Include / exclude this bone from the Godot export. Exclude a rig helper that only makes sense in Blender so it does not ship as a dead Bone2D",
        ),
        "Inclui / exclui este osso da exportação do Godot. Exclua um auxiliar de rig que só faz sentido no Blender para que não seja enviado como um Bone2D morto",
    ),
    (
        (
            "Operator",
            "Inserts a keyframe on the active Proscenio IK chain's influence at the current frame - the seed of an IK/FK blend",
        ),
        "Insere um quadro-chave na influência da cadeia IK ativa do Proscenio no quadro atual - a semente de uma mistura IK/FK",
    ),
    (
        (
            "Operator",
            "Inserts a location/rotation/scale keyframe on every pose bone of the first armature in the scene at the playhead. Requires Pose Mode.",
        ),
        "Insere um quadro-chave de posição/rotação/escala em cada osso de pose da primeira armadura da cena no cabeçote de reprodução. Requer o modo de pose.",
    ),
    (
        (
            "Operator",
            "Show only the chosen attachment from the current frame (hard cut) - the slot swap the exporter projects into a Godot slot_attachment track",
        ),
        "Exibe apenas o anexo escolhido a partir do quadro atual (corte seco) - a troca de slot que o exportador projeta em uma trilha slot_attachment do Godot",
    ),
    (
        ("*", "Hide all"),
        "Ocultar tudo",
    ),
    (
        ("*", "Key the (none) state - every attachment hidden at this frame"),
        "Insere quadro-chave do estado (nenhum) - todos os anexos ocultos neste quadro",
    ),
    (
        ("*", "Override the animation the swap follows (defaults to the rig's active one)"),
        "Substitui a animação que a troca segue (o padrão é a ativa do rig)",
    ),
    (
        ("Operator", "Proscenio: Convert Slot Index to Visibility"),
        "Proscenio: Converter índice de slot em visibilidade",
    ),
    (
        (
            "Operator",
            "Convert this slot's legacy proscenio_slot_index keyframes into attachment visibility keyframes (spec 079 migration)",
        ),
        "Converte os quadros-chave legados proscenio_slot_index deste slot em quadros-chave de visibilidade dos anexos (migração da spec 079)",
    ),
    (
        (
            "Operator",
            "Load a weight snapshot JSON onto the active mesh, applying it to the live weights when the mesh topology still matches",
        ),
        "Carrega um JSON de instantâneo de pesos na malha ativa, aplicando-o aos pesos ao vivo quando a topologia da malha ainda corresponde",
    ),
    (
        (
            "Operator",
            "Locks the active Proscenio IK chain's out-of-plane rotation so the solve stays in the 2D picture plane, seeding a small bend on a straight chain so it has an elbow direction. Click again to unlock. Opt-in: the lock is hidden bone state otherwise",
        ),
        "Trava a rotação fora do plano da cadeia IK ativa do Proscenio para que a solução permaneça no plano da imagem 2D, semeando uma pequena dobra em uma cadeia reta para que ela tenha uma direção de cotovelo. Clique de novo para destravar. Opcional: caso contrário, a trava é um estado oculto do osso",
    ),
    (
        (
            "Operator",
            "Make the active slot follow a bone in Blender the way it already does in Godot: keeps the Empty object-parented and adds a Child Of constraint whose inverse cancels the bone rest, staying flat for any bone orientation. Hand bone-parenting the Empty (Ctrl+P > Bone) also exports, but only for bones pointing into the screen. If the slot already follows, Unbind first (moving a bound slot needs a rebind)",
        ),
        "Faz o slot ativo seguir um osso no Blender do jeito que já faz no Godot: mantém o Vazio parenteado por objeto e adiciona uma restrição Child Of cuja inversa cancela o descanso do osso, permanecendo plano para qualquer orientação do osso. Parentear o Vazio ao osso à mão (Ctrl+P > Bone) também exporta, mas apenas para ossos apontando para dentro da tela. Se o slot já segue, Desvincule primeiro (mover um slot vinculado requer um novo vínculo)",
    ),
    (
        (
            "Operator",
            "Make the active sprite follow a single bone as a rigid attachment: a bone parent authored keep-transform so the sprite stays put instead of jumping to the bone tail. Exports as a Sprite2D parented to that Bone2D. For a bone in the picture plane the sprite rotates with the bone rest - use a slot for a flat follow",
        ),
        "Faz o sprite ativo seguir um único osso como um anexo rígido: um parenteamento de osso feito com Manter Transformação para que o sprite fique no lugar em vez de saltar para a cauda do osso. Exporta como um Sprite2D parenteado àquele Bone2D. Para um osso no plano da imagem o sprite gira com o descanso do osso - use um slot para um acompanhamento plano",
    ),
    (
        ("Operator", "Make this attachment the slot's default visible child at scene load"),
        "Torna este anexo o filho visível padrão do slot ao carregar a cena",
    ),
    (
        (
            "Operator",
            "Manual Draw: build the mesh by clicking the silhouette vertices (LMB place / RMB drag / DEL last / ENTER apply / ESC cancel). Fully manual - separate from the automeshes; a live triangulation previews the SIMPLE mesh",
        ),
        "Desenho manual: construa a malha clicando nos vértices da silhueta (LMB coloca / RMB arrasta / DEL apaga o último / ENTER aplica / ESC cancela). Totalmente manual - separado dos automeshes; uma triangulação ao vivo pré-visualiza a malha SIMPLE",
    ),
    (
        (
            "Operator",
            "Multi-stage modal preview of the automesh pipeline. Each stage (outer contour / user outer edits / inner loops / user Steiner points / Steiner preview / apply) surfaces a GPU overlay + slider-driven re-run so the artist iterates on the mesh shape before any geometry commits. ENTER advances; BACKSPACE goes back; ESC cancels",
        ),
        "Prévia modal em múltiplos estágios do pipeline do automesh. Cada estágio (contorno externo / edições externas do usuário / loops internos / pontos de Steiner do usuário / prévia de Steiner / aplicar) expõe uma sobreposição de GPU + reexecução guiada por controle deslizante para que o artista itere na forma da malha antes que qualquer geometria seja efetivada. ENTER avança; BACKSPACE volta; ESC cancela",
    ),
    (
        ("Operator", "Open an explanation of this panel section"),
        "Abre uma explicação desta seção do painel",
    ),
    (
        (
            "Operator",
            "Override the bind mode for a single bone (SOFT=proximity falloff, HARD=single-nearest)",
        ),
        "Substitui o modo de vínculo para um único osso (SOFT=decaimento por proximidade, HARD=único mais próximo)",
    ),
    (
        (
            "Operator",
            "Pick a mesh by name and attach it to the active slot, without having to select it first",
        ),
        "Escolhe uma malha pelo nome e a anexa ao slot ativo, sem precisar selecioná-la primeiro",
    ),
    (
        (
            "Operator",
            "Pick this armature as the explicit Proscenio target so every skeleton operation (Quick Armature, IK toggle, pose helpers) writes into it",
        ),
        "Escolhe esta armadura como o alvo explícito do Proscenio para que toda operação de esqueleto (Armadura Rápida, alternância de IK, auxiliares de pose) escreva nela",
    ),
    (
        (
            "Operator",
            "Pin / unpin this bone in the Skeleton list. Pinned bones survive the 'Favorites' filter",
        ),
        "Fixa / desafixa este osso na lista de Esqueleto. Ossos fixados sobrevivem ao filtro 'Favoritos'",
    ),
    (
        (
            "Operator",
            "Pin / unpin this object in the Proscenio outliner. Pinned objects survive the 'Favorites only' filter.",
        ),
        "Fixa / desafixa este objeto no outliner do Proscenio. Objetos fixados sobrevivem ao filtro 'Somente favoritos'.",
    ),
    (
        ("Operator", "Print a sanity check to the system console"),
        "Imprime uma verificação de sanidade no console do sistema",
    ),
    (("Operator", "Proscenio: Add / Remove IK Chain"), "Proscenio: Adicionar / Remover cadeia IK"),
    (("Operator", "Proscenio: Add Slot Attachment"), "Proscenio: Adicionar anexo de slot"),
    (("Operator", "Proscenio: Apply Packed Atlas"), "Proscenio: Aplicar atlas empacotado"),
    (("Operator", "Proscenio: Attach Mesh to Slot"), "Proscenio: Anexar malha ao slot"),
    (("Operator", "Proscenio: Automesh Authoring"), "Proscenio: Autoria de automesh"),
    (("Operator", "Proscenio: Automesh from Alpha"), "Proscenio: Automesh a partir do alpha"),
    (("Operator", "Proscenio: Bake Current Pose"), "Proscenio: Assar pose atual"),
    (("Operator", "Proscenio: Bake IK to Keyframes"), "Proscenio: Assar IK em quadros-chave"),
    (
        ("Operator", "Proscenio: Bind Mesh to Target Armature"),
        "Proscenio: Vincular malha à armadura-alvo",
    ),
    (("Operator", "Proscenio: Bind Slot to Bone"), "Proscenio: Vincular slot ao osso"),
    (("Operator", "Proscenio: Clear Automesh Debug"), "Proscenio: Limpar depuração do automesh"),
    (
        ("Operator", "Proscenio: Clear Empty Vertex Groups"),
        "Proscenio: Limpar grupos de vértices vazios",
    ),
    (
        ("Operator", "Proscenio: Clear Sprite Bone Parent"),
        "Proscenio: Limpar parenteamento de osso do sprite",
    ),
    (("Operator", "Proscenio: Color Bone Collection"), "Proscenio: Colorir coleção de ossos"),
    (
        ("Operator", "Proscenio: Convert Rotation to Euler"),
        "Proscenio: Converter rotação para Euler",
    ),
    (("Operator", "Proscenio: Create Slot"), "Proscenio: Criar slot"),
    (("Operator", "Proscenio: Draw Mesh with Vertices"), "Proscenio: Desenhar malha com vértices"),
    (
        ("Operator", "Proscenio: Drive Sprite from Bone"),
        "Proscenio: Dirigir sprite a partir do osso",
    ),
    (("Operator", "Proscenio: Edit Weights"), "Proscenio: Editar pesos"),
    (("Operator", "Proscenio: Export (.proscenio)"), "Proscenio: Exportar (.proscenio)"),
    (("Operator", "Proscenio: Feature Status"), "Proscenio: Status de recursos"),
    (("Operator", "Proscenio: Help"), "Proscenio: Ajuda"),
    (
        ("Operator", "Proscenio: Import Photoshop Manifest"),
        "Proscenio: Importar manifesto do Photoshop",
    ),
    (("Operator", "Proscenio: Incorporate as Element"), "Proscenio: Incorporar como elemento"),
    (
        ("Operator", "Proscenio: Key IK Influence"),
        "Proscenio: Inserir quadro-chave da influência IK",
    ),
    (
        ("Operator", "Proscenio: Keyframe Slot Attachment"),
        "Proscenio: Inserir quadro-chave do anexo de slot",
    ),
    (("Operator", "Proscenio: Pack Atlas"), "Proscenio: Empacotar atlas"),
    (("Operator", "Proscenio: Parent Sprite to Bone"), "Proscenio: Parentear sprite ao osso"),
    (("Operator", "Proscenio: Preview Camera"), "Proscenio: Câmera de prévia"),
    (("Operator", "Proscenio: Quick Armature"), "Proscenio: Armadura Rápida"),
    (("Operator", "Proscenio: Re-export"), "Proscenio: Reexportar"),
    (("Operator", "Proscenio: Re-import Element"), "Proscenio: Reimportar elemento"),
    (("Operator", "Proscenio: Re-space Planes"), "Proscenio: Reespaçar planos"),
    (("Operator", "Proscenio: Remove Driver"), "Proscenio: Remover driver"),
    (("Operator", "Proscenio: Remove Preview Material"), "Proscenio: Remover material de prévia"),
    (("Operator", "Proscenio: Reproject UV"), "Proscenio: Reprojetar UV"),
    (("Operator", "Proscenio: Revert to Plane"), "Proscenio: Reverter para plano"),
    (("Operator", "Proscenio: Save Pose to Library"), "Proscenio: Salvar pose na biblioteca"),
    (("Operator", "Proscenio: Select Bone"), "Proscenio: Selecionar osso"),
    (("Operator", "Proscenio: Select Bone Collection"), "Proscenio: Selecionar coleção de ossos"),
    (("Operator", "Proscenio: Select Issue Object"), "Proscenio: Selecionar objeto do problema"),
    (("Operator", "Proscenio: Select Outliner Object"), "Proscenio: Selecionar objeto do outliner"),
    (("Operator", "Proscenio: Select Slot"), "Proscenio: Selecionar slot"),
    (("Operator", "Proscenio: Set Active Action"), "Proscenio: Definir ação ativa"),
    (("Operator", "Proscenio: Set Slot Default"), "Proscenio: Definir padrão do slot"),
    (("Operator", "Proscenio: Setup Preview Material"), "Proscenio: Configurar material de prévia"),
    (("Operator", "Proscenio: Smoke Test"), "Proscenio: Teste de fumaça"),
    (
        ("Operator", "Proscenio: Snap region to UV bounds"),
        "Proscenio: Encaixar região nos limites de UV",
    ),
    (("Operator", "Proscenio: Toggle Bone Export"), "Proscenio: Alternar exportação de osso"),
    (("Operator", "Proscenio: Toggle Bone Favorite"), "Proscenio: Alternar favorito de osso"),
    (
        ("Operator", "Proscenio: Toggle IK In-Plane Lock"),
        "Proscenio: Alternar trava no plano do IK",
    ),
    (
        ("Operator", "Proscenio: Toggle Outliner Favorite"),
        "Proscenio: Alternar favorito do outliner",
    ),
    (
        ("Operator", "Proscenio: Toggle Relative Parenting"),
        "Proscenio: Alternar parenteamento relativo",
    ),
    (("Operator", "Proscenio: Unbind Slot from Bone"), "Proscenio: Desvincular slot do osso"),
    (("Operator", "Proscenio: Unpack Atlas"), "Proscenio: Desempacotar atlas"),
    (("Operator", "Proscenio: Use Armature"), "Proscenio: Usar armadura"),
    (("Operator", "Proscenio: Validate"), "Proscenio: Validar"),
    (
        ("Operator", "Re-parent the selected mesh as a child of the active slot Empty"),
        "Reparenteia a malha selecionada como filha do Vazio de slot ativo",
    ),
    (
        (
            "Operator",
            "Re-projects the active mesh's UVs with a deterministic planar projection (U follows X, V follows Z for a picture-plane mesh) so the texture lines up after vertex edits without rotating or mirroring the layout. Active object only.",
        ),
        "Reprojeta os UVs da malha ativa com uma projeção planar determinística (U segue X, V segue Z para uma malha no plano da imagem) para que a textura se alinhe após edições de vértices sem rotacionar ou espelhar o layout. Somente o objeto ativo.",
    ),
    (
        ("Operator", "Re-run the writer using the last export path - no file dialog"),
        "Reexecuta o gravador usando o último caminho de exportação - sem diálogo de arquivo",
    ),
    (
        (
            "Operator",
            "Read a Photoshop manifest (the photoshop importer v1) and stamp one quad mesh per layer, plus a stub armature for posing",
        ),
        "Lê um manifesto do Photoshop (o importador do photoshop v1) e carimba uma malha quad por camada, mais uma armadura-esboço para posar",
    ),
    (
        (
            "Operator",
            "Reads <blend>.atlas.json, rewrites every sprite's UVs to address the packed atlas, and (unless material_isolated is set on the object) links the sprite to the shared 'Proscenio.PackedAtlas' material. Undoable - Ctrl+Z reverts.",
        ),
        "Lê <blend>.atlas.json, reescreve os UVs de cada sprite para endereçar o atlas empacotado, e (a menos que material_isolated esteja definido no objeto) vincula o sprite ao material compartilhado 'Proscenio.PackedAtlas'. Reversível - Ctrl+Z desfaz.",
    ),
    (
        (
            "Operator",
            "Reads the active mesh's UV bounds and writes them into the manual region fields. Use this to seed manual mode with the current auto value.",
        ),
        "Lê os limites de UV da malha ativa e os grava nos campos de região manual. Use isto para semear o modo manual com o valor automático atual.",
    ),
    (
        (
            "Operator",
            "Reapply this named snapshot's weights to the active mesh. Cancels when the mesh topology changed since the snapshot was taken",
        ),
        "Reaplica os pesos deste instantâneo nomeado à malha ativa. Cancela quando a topologia da malha mudou desde que o instantâneo foi tirado",
    ),
    (
        (
            "Operator",
            "Rebuild the original imported quad with its texture and drop the generated mesh - the automesh / hand-drawn geometry, the weights, and the authoring strokes are cleared. The escape hatch to start this element's mesh over (PSD-imported mesh elements only)",
        ),
        "Reconstrói o quad importado original com sua textura e descarta a malha gerada - a geometria do automesh / desenhada à mão, os pesos e os traços de autoria são limpos. A saída de emergência para recomeçar a malha deste elemento (somente elementos de malha importados de PSD)",
    ),
    (
        (
            "Operator",
            "Refresh only the active Element from its source manifest entry, leaving every other Element untouched. Same-bounds keeps painted weights; a resized layer reprojects them",
        ),
        "Atualiza apenas o Elemento ativo a partir de sua entrada no manifesto de origem, deixando todos os outros Elementos intocados. Mesmos limites mantém os pesos pintados; uma camada redimensionada os reprojeta",
    ),
    (
        (
            "Operator",
            "Remove every wireframe debug companion (raw contours / smoothed / resampled / interior points / bridges / triangle fill) for the active sprite. Companions live in the Proscenio.Debug collection",
        ),
        "Remove todo companheiro de depuração em wireframe (contornos brutos / suavizado / reamostrado / pontos interiores / pontes / preenchimento de triângulos) do sprite ativo. Os companheiros ficam na coleção Proscenio.Debug",
    ),
    (
        (
            "Operator",
            "Remove the SpriteFrameSlicer node + drivers; re-link the ImageTexture directly so the material renders the full atlas again.",
        ),
        "Remove o nó SpriteFrameSlicer + drivers; revincula o ImageTexture diretamente para que o material renderize o atlas completo de novo.",
    ),
    (
        ("Operator", "Removes this bone driver from the active sprite's proscenio property"),
        "Remove este driver de osso da propriedade proscenio do sprite ativo",
    ),
    (("Operator", "Reset to Last Saved Weights"), "Restaurar últimos pesos salvos"),
    (("Operator", "Restore Weight Snapshot"), "Restaurar instantâneo de pesos"),
    (
        (
            "Operator",
            "Restores every sprite mesh to its pre-Apply state - original UVs, original material, original region_mode. Reads a snapshot stored as a Custom Property + a duplicated UV layer (`<name>.pre_pack`). Survives .blend reload (Ctrl+Z does not).",
        ),
        "Restaura cada malha de sprite ao seu estado anterior ao Aplicar - UVs originais, material original, region_mode original. Lê um instantâneo armazenado como uma Propriedade Personalizada + uma camada de UV duplicada (`<name>.pre_pack`). Sobrevive ao recarregamento do .blend (o Ctrl+Z não).",
    ),
    (
        (
            "Operator",
            "Reverts paint edits since the last Bind or Automesh regen, restoring the weight snapshot saved at that time. Does NOT trigger automesh regen - if topology has changed since the snapshot, the operator cancels with a hint to re-run automesh with preserve_on_regen ON",
        ),
        "Reverte edições de pintura desde o último Vincular ou regeneração do Automesh, restaurando o instantâneo de pesos salvo naquele momento. NÃO dispara a regeneração do automesh - se a topologia mudou desde o instantâneo, o operador cancela com uma dica para reexecutar o automesh com preserve_on_regen ATIVO",
    ),
    (("Operator", "Save Weight Snapshot"), "Salvar instantâneo de pesos"),
    (
        (
            "Operator",
            "Save the current vertex weights as a named restore point. Named snapshots are unbounded and survive .blend save/reload",
        ),
        "Salva os pesos de vértices atuais como um ponto de restauração nomeado. Instantâneos nomeados são ilimitados e sobrevivem ao salvar/recarregar do .blend",
    ),
    (
        (
            "Operator",
            "Select and activate this slot so its attachments show in the Active Slot subpanel",
        ),
        "Seleciona e ativa este slot para que seus anexos apareçam no subpainel de Slot ativo",
    ),
    (
        ("Operator", "Selects and activates the object that the issue refers to"),
        "Seleciona e ativa o objeto ao qual o problema se refere",
    ),
    (
        ("Operator", "Selects every bone assigned to this bone collection in the viewport"),
        "Seleciona todo osso atribuído a esta coleção de ossos na viewport",
    ),
    (
        (
            "Operator",
            "Selects the bone for this Skeleton-panel row in the viewport. Shift extends the selection, Ctrl toggles the bone",
        ),
        "Seleciona o osso desta linha do painel de Esqueleto na viewport. Shift estende a seleção, Ctrl alterna o osso",
    ),
    (
        (
            "Operator",
            "Selects the object for this outliner row. Shift extends the selection, Ctrl toggles the row",
        ),
        "Seleciona o objeto desta linha do outliner. Shift estende a seleção, Ctrl alterna a linha",
    ),
    (("Operator", "Set Bone Mode"), "Definir modo do osso"),
    (
        (
            "Operator",
            "Set every Proscenio element's Y to its draw-order layer times the Y Location spacing preference. Applies a changed spacing and snaps planes dragged off their layer back into place",
        ),
        "Define o Y de cada elemento Proscenio para sua camada de ordem de desenho vezes a preferência de espaçamento de Posição Y. Aplica um espaçamento alterado e encaixa de volta no lugar os planos arrastados para fora de sua camada",
    ),
    (
        (
            "Operator",
            "Set the bone rotation mode to XYZ Euler (Blender converts the stored rotation). Drive-from-Bone reads rotation as XYZ, so a Quaternion bone drives wrong - this is the one-click fix",
        ),
        "Define o modo de rotação do osso para XYZ Euler (o Blender converte a rotação armazenada). Dirigir a partir do osso lê a rotação como XYZ, então um osso Quaternion dirige errado - esta é a correção em um clique",
    ),
    (
        (
            "Operator",
            "Slice the spritesheet in the viewport via shader nodes + drivers. Switch to Material Preview mode (Z-key) to see the active cell.",
        ),
        "Fatia o spritesheet na viewport via nós de shader + drivers. Mude para o modo Pré-visualização de Material (tecla Z) para ver a célula ativa.",
    ),
    (
        (
            "Operator",
            "Stop the active slot following a bone: removes the Proscenio Child Of constraint or a hand-authored bone parent (whichever it uses) and clears slot_bone, leaving the Empty object-parented and inert",
        ),
        "Para o slot ativo de seguir um osso: remove a restrição Child Of do Proscenio ou um parenteamento de osso feito à mão (o que estiver em uso) e limpa slot_bone, deixando o Vazio parenteado por objeto e inerte",
    ),
    (
        (
            "Operator",
            "Stop the active sprite following a bone: drops the bone parent and leaves the sprite unparented at the same position, ready to re-parent or attach to a slot",
        ),
        "Para o sprite ativo de seguir um osso: descarta o parenteamento de osso e deixa o sprite sem parenteamento na mesma posição, pronto para reparentear ou anexar a um slot",
    ),
    (
        (
            "Operator",
            "Toggle Relative Parenting on this bone - the child follows the parent's local transform instead of its rest offset. A pose flag, not a geometry edit",
        ),
        "Alterna o parenteamento relativo neste osso - o filho segue a transformação local do pai em vez de seu deslocamento de descanso. Um sinalizador de pose, não uma edição de geometria",
    ),
    (
        (
            "Operator",
            "Walks every sprite mesh, collects its source image, packs them with MaxRects-BSSF, and writes <blend>.atlas.png + <blend>.atlas.json. Run Apply Packed Atlas afterwards to rewrite UVs and materials.",
        ),
        "Percorre cada malha de sprite, coleta sua imagem de origem, as empacota com MaxRects-BSSF, e grava <blend>.atlas.png + <blend>.atlas.json. Execute Aplicar atlas empacotado em seguida para reescrever UVs e materiais.",
    ),
    (
        (
            "Operator",
            "Walks the scene, checks every sprite against the armature, verifies atlas files. Errors block export.",
        ),
        "Percorre a cena, verifica cada sprite contra a armadura, confere os arquivos de atlas. Erros bloqueiam a exportação.",
    ),
    (
        ("Operator", "Write the active mesh's weight snapshot to a JSON file"),
        "Grava o instantâneo de pesos da malha ativa em um arquivo JSON",
    ),
    (
        ("Operator", "Write the active scene to a Proscenio JSON file"),
        "Grava a cena ativa em um arquivo JSON do Proscenio",
    ),
    # Spec 079 PR2 - Active Slot swap authoring + target-animation override.
    (
        ("*", "(empty: follows the active animation)"),
        "(vazio: segue a animação ativa)",
    ),
    (("*", "(none) / Hide All"), "(nenhum) / Ocultar todos"),
    (
        (
            "*",
            "Animation a new slot-swap keyframe targets. Empty (default) follows the rig's active animation, so authoring the swap needs no extra step; set a name here to bind the swap into that animation instead (spec 079 D3).",
        ),
        "Animação que um novo quadro-chave de troca de slot mira. Vazio (padrão) segue a animação ativa da armadura, então autorar a troca não requer passo extra; defina um nome aqui para vincular a troca àquela animação (spec 079 D3).",
    ),
    (
        ("*", "Keyframe swap (show only at current frame):"),
        "Quadro-chave de troca (exibir apenas no quadro atual):",
    ),
    (("*", "Show Only"), "Exibir apenas"),
    (("*", "Target anim"), "Animação-alvo"),
    (("*", "Target animation"), "Animação-alvo"),
)
