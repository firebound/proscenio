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
- ui: talvez uma alternativa para esse painel seria um filtro custom no outliner nativo do blender, isso é possível?

## BL · Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV)
- ui: não está claro como é possível criar objetos no blender e incorporá-los como elementos ao fluxo do proscenio... acho que precisa de um botão pra isso quando for um objeto do blender (malha)
- ui: no cabeçalho do "Element" é interessante ter dois pontos seguido do nome pra deixar mais claro que é o elemento ativo
- ui: no Element panel não existe opção de remover ou adicionar vários drivers, apenas substituir... talvez fosse interessante ter uma lista de todos os drivers from bones que um elemento possui e permitir iterar entre eles (excluir completamente, alterar ou adicionar novos)
- ui: impossível remover um driver pelo painel de element

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
