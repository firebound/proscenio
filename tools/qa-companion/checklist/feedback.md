# Feature feedback

Panel-level product feedback gathered during the walk - not test results.
Each entry normalizes into a backlog file later (ui/remove -> ui-feedback,
bug -> bugs-found, code -> code-quality, perf -> perf, note -> general).

## BL · Global chrome (test once - applies to every panel)
- ui: Seria interessante se a tootlip das status badges apenas mostrassem o que realmente elas representam. Hoje, clicar em qualquer badge mostra o texto inteiro (que inclusive está desatualizado, TOOL_SETTINGS não é utilizado mais para representar que só funciona no blender).
- ui: As tooltips estão com quebras de linhas  entre as frases em que o texto ocupa menos espaço que a tooltip permite.
- ui: Todas as tooltips precisam ter os textos revistos: as ? nos paineis devem explicar o painel em si de forma geral, sendo que subpanels agrupam as funcionalidades específicas e precisam de uma explicação mais detalhada, sem "vazar" entre os subpanels a menos que extritamente necessário.
- ui: no geral, cada lista de itens nos paineis está de um jeito... o ideal seria, se possível: reproduzir o outliner padrão do blender com foldable items numa hierarquia clara (accordion), usar a busca nativa sempre, e fazer as marcações custom sempre que necessário (de acordo com cada painel)

## BL · Outliner panel
- ui: a identação do outliner deve seguir o padrão de hierarquias: alinhado à esquerda, agrupamento claro entre as hierarquias (armature > bone > slot > mesh), nem que seja ASCII, mas seria bom que fosse seguindo o padrão do outliner do blender, com foldable items etc
- ui: duas search bars é completamente inadimissível, devemos usar apenas a search bar nativa do blender, o toggle de favorito pode ser uma checkbox com texto inline
- ui: falta alguma forma de controlar a profundidade em Y dos objetos do proscenio, principalmente mesher e sprites para não acontecer zfight entre os planos após serem importados do photoshop... talvez algo simples como definir uma distância e organizar os objetos em "camadas" (igual do photoshop), aplicando essa distância quanto mais fundo na camada estiverem... algo assim (aceito sugestões)
- bug: quando seleciono um objeto na 3d view direto, o painel de outliner continua mostrando o objeto anterior selecionado
- bug: a lista está mostrando elementos excluídos (unused data blocks): após criar armatures com quick mesh ou no próprio blender e ou voltar com ctrl z ou deletá-las, elas continuam aparecendo no outliner, mas dão erro ao selecioná-las: Python: Traceback (most recent call last): File "C:\Users\Danilo\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default\proscenio\operators\selection.py", line 56, in execute if select_named_or_warn(self, context, self.obj_name) is None: ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ File "C:\Users\Danilo\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default\proscenio\core\bpy_helpers\_shared\select.py", line 112, in select_named_or_warn select_only(context, obj) ~~~~~~~~~~~^^^^^^^^^^^^^^ File "C:\Users\Danilo\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default\proscenio\core\bpy_helpers\_shared\select.py", line 34, in select_only obj.select_set(True) ~~~~~~~~~~~~~~^^^^^^ RuntimeError: Error: Object 'doll_tagged.rig' cannot be selected because it is not in View Layer 'ViewLayer'!

## BL · Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV)
- ui: não está claro como é possível criar objetos no blender e incorporá-los como elementos ao fluxo do proscenio... acho que precisa de um botão pra isso quando for um objeto do blender (malha)
- ui: no cabeçalho do "Element" é interessante ter dois pontos seguido do nome pra deixar mais claro que é o elemento ativo
- ui: no Element panel não existe opção de remover ou adicionar vários drivers, apenas substituir... talvez fosse interessante ter uma lista de todos os drivers from bones que um elemento possui e permitir iterar entre eles (excluir completamente, alterar ou adicionar novos)
- ui: impossível remover um driver pelo painel de element
- ui: Possível bug de unidade no sprite manual: os campos são normalizados [0,1] (object_props.py:121-156), mas Sprite2D.region_rect é em pixels, e o builder usa os valores crus (sprite_builder.gd:58) sem multiplicar pelo tamanho da textura (o mesh_builder multiplica, o sprite não). Uma region manual [0,0,0.5,0.5] viraria Rect2(0,0,0.5,0.5) = meio pixel. Vale verificar - parece divergência real.
- ui: pro tipo mesh (que vira poly 2d na godot) o subpanel de Texture Region tecnicamente não deveria fazer nada e, se for o caso, pode ser oculto quando estiver trabalhando em mesh

## BL · Slots panel + slot operators
- ui: a gestão dos slots é horrível: impossível adicionar meshes ou bones em slots já existentes: o certo seria uma forma de dar attach de alguma forma, ou selecionar de uma lista ou com o picker... o comportamento atual pede que eu selecione o slot > selectione bone ou mesh... isso é simplesmente IMPOSSÍVEL já que a seleção é uma só... o blender possui "subseleção", mas ainda seria uma gambiarra pra dar uma volta no problema
- ui: a UI do painel de slots parece meio poluída, a lista de slots podia ser um outliner seguindo o padrão das outras listas desse projeto (outliner, armature), com busca nativa... a quantidade de anexos é interessante mas o ícone de link não faz sentido
- ui: os avisos de "empty slot" e "slot has no mesh children" significam a mesma coisa, não precisa do segundo
- ui: a lista de attachments do active slot também deve seguir o mesmo padrão dos outros outliners / listas desse projeto

## BL · Skeleton panel: armature picker, bone list, pose helpers, Quick Armature, IK, authoring camera, pose library
- ui: seguindo a sugestão do element, é interessante mostrar o nome da armature sendo trabalhada ("Skeleton: <nome>")
- ui: no quick armature, esc e enter fazem a mesma coisa (aplicam a armature)... se for proposital é ok mas pode ser uma instrução só no header
- ui: falta marcar como "disconnected" nos bones que são children de outros (já aparece "connected" caso sejam)
- ui: as instruções no viewport-header são desnecessárias, devem ser removidas (nada mais tá fazendo isso)
- ui: o subpanel "Armature" pode se chamar "Active Armature", pra manter a consistencia

## BL · Mesh Generation panel: automesh one-click + interactive modal + debug pipeline
- ui: não está claro que o automesh from alpha e o automesh interactive usam alguns dos parâmetros que estão localizados apenas no subpanel de automesh from alpha... se for o caso, é necessário elevar os parametros ou, pelo menos, reorganizar melhor os subpanels...

## BL · Weight Paint panel: five bind modes, Edit Weights modal, brush preset, copy weights, sidecar IO, snapshot restore
- ui: a lista de override per bone fica gigantesca e empurra tudo do bind pra baixo, o ideal seria uma lista parecida com o padrão do projeto ou, no mínimo, uma barra de rolagem
- ui: o botão de "edit weights" deveria virar "exit paiting mode" caso o usuário entre no modo de weight paint
- ui: Não, isso é um gap de UI - não é design intencional bom.  O que tá acontecendo:  O operator tem 3 props no redo (F9): bind_init_mode, falloff_power, max_distance (bind_mesh.py:49-87). As 3 são persistentes: existem como scene props (bind_init_mode, bind_falloff_power, bind_max_distance) e o operator as semeia no invoke (bind_mesh.py:107-109). Mas o painel só desenha uma delas - o bind_init_mode ("Mode", weight_paint.py:174). falloff_power e max_distance nunca são desenhados. Resultado: tu só consegue ajustar falloff/max distance por execução no F9; o valor sticky (scene prop) não tem como ser setado pela UI.  Dois agravantes que confirmam ser gap, não intenção:  Inconsistência: a feature de transfer/copy weights DESENHA o max distance dela no painel (weight_transfer_max_distance, weight_paint.py:150). O bind não. Contexto: falloff_power e max_distance só importam no modo Proximity (é o 1/dist^power com cutoff de distância). Bone Heat (default), Single-nearest, Envelope, Empty ignoram. O certo seria o painel mostrar os dois condicionalmente quando Mode = Proximity - hoje somem em todos os modos. Então: esperado, não. É pra logar. Item de UI: "expor bind falloff power + max distance no painel, condicional ao modo Proximity (hoje só no F9)". Quer que eu registre no backlog, ou tu prefere flaggear o painel Weight Paint pela aba Feedback (teu fluxo)?
- ui: o snapshot é super confuso de usar, eu fiz uma pintura de peso e não tenho certeza se o snapshot vai voltar para "antes dela" ou "depois dela"... talvez fosse interessante o usuário ter mais agência nisso, tipo salvar snapshots nomeados mesmo e escolher quando / pra onde quer voltar... o auto snapshot é interessante mas "automático sem clareza"... talvez seja mais útil se for acompanhado de algo que o usuário realmente tenha agência (como save points)
- ui: sair do modo de weight paint através dos controles do blender não está encerrando o edit weights do proscenio, aparentemente.... as marcações / cores continuam
- ui: no painel de weight paint eu gostaria de um atalho para limpar todos os vertex groups com pesos vazios, com um aviso do que será detelato, se possível

## BL · Animation panel (read-only action summary)
- ui: o Animation panel deveria seguir o padrão do projeto: todos usam a armature definida no skeleton como base, se não há, avisa
