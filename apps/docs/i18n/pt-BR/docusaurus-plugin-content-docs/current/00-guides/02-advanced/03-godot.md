# Godot

O guia aprofundado do lado do Godot: como adicionar scripts, efeitos, colisores, áudio e jogabilidade a um personagem Proscenio sem perder esse trabalho na próxima reimportação. Para a versão rápida, consulte o [passo a passo básico](../01-basic/03-godot.md).

## O contrato {#the-contract}

A reexportação do Blender **regenera o personagem importado do zero** - qualquer coisa editada dentro dele é perdida. Então você nunca o edita diretamente: você mantém todo o seu trabalho em uma cena separada, sua, o **wrapper**, que instancia o personagem. (Por que regenerar em vez de mesclar? Consulte [Por que não simplesmente mesclar?](#why-not-just-merge).)

## Como o `.proscenio` vira uma cena

O `.proscenio` não é um arquivo de cena que você abre e edita - ele é uma **fonte de importação**, do mesmo jeito que um `.png` é. Você o solta no seu projeto Godot (com os PNGs que ele nomeia ao lado, já que o `.proscenio` é JSON que se refere às suas texturas por nome de arquivo), e o [sistema de importação](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/import_process.html) do Godot roda o [`EditorImportPlugin`](https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html) do Proscenio. Esse plugin **assa uma [`PackedScene`](https://docs.godotengine.org/en/stable/classes/class_packedscene.html)** - o esqueleto montado, os sprites e as animações - no cache de importação oculto do Godot (`.godot/imported/`), não como um arquivo irmão. A cena assada é regenerada a cada reimportação, que é exatamente por que ela não é sua para editar.

No dock do FileSystem o `.proscenio` ainda aparece como uma única cena que você pode instanciar - assim como um `.glb` importado. Você constrói o seu jogo [instanciando](https://docs.godotengine.org/en/stable/getting_started/step_by_step/instancing.html)-o dentro de uma cena sua: o wrapper.

## O wrapper

O wrapper é um `.tscn` simples que você possui e versiona. Sua raiz é o seu nó com o seu script; o personagem importado é instanciado como filho. Tudo que você adiciona - scripts, IA, efeitos, colisores - vive no wrapper, nunca dentro do personagem instanciado. (O layout de pastas em disco está no [passo a passo básico](../01-basic/03-godot.md#wrap-the-generated-scene).)

Uma reimportação regenera a cena assada; seu `.tscn` e `.gd` ficam intocados. Este é o mesmo padrão de instanciar-um-asset-importado que você já usa para um modelo `.glb`: edite ao redor dele, nunca dentro dele. (As receitas abaixo usam um personagem `hero` inventado - troque pelos seus próprios nomes; os caminhos de nós são ilustrativos.)

## Padrão wrapper vs Editable Children

O Godot lhe dá duas formas de personalizar uma subcena instanciada: o wrapper, ou o [Editable Children](https://docs.godotengine.org/en/stable/getting_started/step_by_step/instancing.html) embutido do Godot (que expõe os nós internos de uma instância para sobrescritas no lugar). Veja como eles se comparam:

| Preocupação | Padrão wrapper | Editable Children |
| - | - | - |
| Um osso renomeado no Blender | parcial - os [NodePaths](https://docs.godotengine.org/en/stable/classes/class_nodepath.html) do wrapper quebram, mas um grep e uma edição os corrigem | não - a sobrescrita é orfanada silenciosamente |
| Um sprite adicionado ou removido no `.proscenio` | tranquilo - o wrapper não é afetado | não - a sobrescrita pode cair no nó errado ou sumir |
| A forma da saída do exportador evoluindo | tranquilo - os caminhos de código do wrapper ainda resolvem | não - os caminhos de sobrescrita apontam para uma camada que não existe mais |
| Ver suas personalizações | claro - tudo está no `.tscn` e `.gd` do wrapper, arquivos versionados à parte | oculto - as sobrescritas vivem dentro do `.tscn` como um diff contra a subcena |
| Conflito com um padrão regenerado | determinístico - o wrapper se aplica no `_ready`, a última escrita vence | indefinido - a ordem entre o padrão da subcena e o diff externo é opaca |
| Comportamento de reimportação | limpo - a cena regenera e o wrapper nem pestaneja | reconciliar-ou-descartar - o Godot reaplica as sobrescritas e descarta silenciosamente as que não se encaixam mais |
| Plugin desinstalado | seguro - o wrapper é um `.tscn` simples | a saída ainda funciona, mas o caminho de criação vira ler-modificar-escrever |
| Melhor para | a maior parte do trabalho de dev de jogos sobre um personagem importado | um ajuste de último recurso numa subcena que nunca muda |
| Pior para | scripts por osso e sobrescritas por sprite (use composição e um loop de `_ready`) | qualquer coisa que reexporta com frequência ou espera que o schema cresça |

O padrão wrapper é a opção padrão. O Editable Children funciona em casos estreitos e estáveis, mas não sobrevive ao loop de iteração para o qual o resto do pipeline foi construído.

## Receitas

### IA, comportamento e máquinas de estado

Coloque o script na raiz do wrapper (`Hero.gd`) e acesse a cena importada com referências [`@onready`](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html#onready-annotation):

```gdscript
extends Node2D
@onready var skeleton: Skeleton2D = $hero/Skeleton2D
@onready var anim: AnimationPlayer = $hero/AnimationPlayer
# ... game logic, signals, state machine, input handling
```

Isto sobrevive à reimportação completamente. Só quebra se um osso ou sprite que você referencia for renomeado no Blender - e isso falha ruidosamente em tempo de execução.

### Efeitos que seguem um osso

Adicione o efeito sob o wrapper e escravize a transformação dele a um osso com um [`RemoteTransform2D`](https://docs.godotengine.org/en/stable/classes/class_remotetransform2d.html):

```text
Hero.tscn
├── hero (instance)
├── HandTrail (GPUParticles2D)
└── HandFollower (RemoteTransform2D)
    remote_path = ../hero/Skeleton2D/torso/arm/hand
```

O `RemoteTransform2D` copia a transformação do osso para o efeito a cada quadro. Ele pertence ao wrapper, então é seguro à reimportação.

### Colisores e hitboxes em um osso

Mesma ideia dos efeitos: adicione um [`Area2D`](https://docs.godotengine.org/en/stable/classes/class_area2d.html) (ou um [`CharacterBody2D`](https://docs.godotengine.org/en/stable/classes/class_characterbody2d.html) para uma hitbox sólida) sob o wrapper, mais um `RemoteTransform2D` escravizado ao osso. Mantenha o tratamento de sinais e a configuração de layer / mask no `Hero.gd`.

### Uma sobrescrita de material ou shader em um sprite

Aplique-a em tempo de execução no `_ready` - não use Editable Children para isso:

```gdscript
func _ready() -> void:
    var head_sprite := $hero/Skeleton2D/torso/head/head_sprite as Polygon2D
    head_sprite.material = preload("res://shaders/glow.tres")
    head_sprite.modulate = Color.RED
```

É seguro à reimportação porque a sobrescrita é código, não um diff estrutural armazenado.

### Eventos de animação (deixas de som, ganchos de jogabilidade em um quadro)

O caso de atrito. Até o schema ganhar um tipo de trilha `event`, a solução alternativa é um segundo [`AnimationPlayer`](https://docs.godotengine.org/en/stable/classes/class_animationplayer.html) no wrapper, contendo animações espelho cujas trilhas chamam métodos no `Hero.gd`, reproduzidas em sincronia com a importada:

```text
Hero.tscn
├── hero (instance)              imported AnimationPlayer plays the visuals
└── EventPlayer (AnimationPlayer) wrapper-owned, plays method tracks
```

```gdscript
func play_idle() -> void:
    $hero/AnimationPlayer.play("idle")
    $EventPlayer.play("idle_events")  # mirror: method tracks for sound cues
```

O espelho corresponde à duração e ao tempo da animação importada, mas carrega apenas [trilhas Call Method](https://docs.godotengine.org/en/stable/tutorials/animation/animation_track_types.html#call-method-track). Você o cria uma vez e o mantém em sincronia à mão - o que fica verboso além de um punhado de eventos.

### Sobrescritas em massa por sprite

Guie-as a partir de um dicionário de configuração no wrapper, em um loop de `_ready`:

```gdscript
@export var sprite_overrides: Dictionary = {
    "head_sprite": {"modulate": Color.RED},
    "torso_sprite": {"z_index": 5},
}

func _ready() -> void:
    for sprite_name in sprite_overrides:
        var node := find_child(sprite_name, true, false)
        if node:
            for prop in sprite_overrides[sprite_name]:
                node.set(prop, sprite_overrides[sprite_name][prop])
```

Verboso mas estável; só quebra se um sprite for renomeado no Blender.

### Suas próprias animações ao lado das importadas

O `AnimationPlayer` importado contém as animações criadas no Blender em uma [biblioteca de animações](https://docs.godotengine.org/en/stable/tutorials/animation/introduction.html) sob a chave padrão (`""`). Para adicionar as suas próprias:

1. Adicione um `AnimationPlayer` separado ao wrapper (digamos `UserAnimations`).
2. Crie suas animações em uma biblioteca nomeada nele (digamos `"user"`).
3. Dispare a partir do `Hero.gd`: `imported_player.play("idle")` ou `user_player.play("user/death_special")`.

A biblioteca importada é regenerada a cada reimportação; a sua biblioteca pertence ao wrapper e o lado da importação nunca a toca.

## Casos extremos e custos conhecidos

- **Um osso renomeado no Blender** quebra qualquer `NodePath` do wrapper que usava o nome antigo. Trate renomeações como uma operação entre ferramentas: renomeie no Blender, depois faça um grep no wrapper pelo nome antigo.
- **Um sprite adicionado ou removido no `.proscenio`**: um sprite removido quebra qualquer código do wrapper que o enderece (ruidoso em tempo de execução); um sprite adicionado fica visível mas inerte até você escolher endereçá-lo.
- **Muitos eventos de animação** ficam dolorosos além de cerca de dez por animação com a solução alternativa do `AnimationPlayer`-espelho. Esse é o sinal para promover o tipo de trilha `event` de ideia a spec.
- **Nenhum link ao vivo entre Blender e Godot hoje.** Cada reexportação do Blender significa uma reimportação no Godot. Está estacionado como uma ideia de longo prazo; fechá-lo provavelmente reabre a regra de não-GDExtension.

## Por que não simplesmente mesclar? {#why-not-just-merge}

Sobrescrita total mais um wrapper foi escolhida em vez de mesclar a saída do Blender nas suas edições. Uma mesclagem baseada em marcadores foi rejeitada: o schema não tem IDs estáveis, então renomear um osso perderia silenciosamente os seus scripts anexados. Um híbrido (sobrescrever por padrão, mesclagem opcional) fica adiado até a composição por wrapper se provar genuinamente insuficiente. A abordagem atual não precisa de nenhum código de mesclagem, permanece segura quando o plugin é desinstalado, e é Godot idiomático.

A maioria dos pontos de dor - efeitos, IA, materiais, colisores - tem uma receita de wrapper acima. Os dois que ainda mordem, eventos de animação e um link ao vivo, são melhor resolvidos por specs dedicadas do que por lógica de mesclagem.
