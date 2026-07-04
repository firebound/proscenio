# Godot: envolva e jogue

O Godot importa o `.proscenio` para uma cena nativa; o seu trabalho é envolver essa cena para que o seu próprio trabalho sobreviva às reexportações.

## Importe o .proscenio

Um `.proscenio` é apenas JSON - ele nomeia suas texturas por nome de arquivo (o atlas, quaisquer PNGs por sprite, os spritesheets compostos), então ele não viaja sozinho.

_Importe_: copie o `.proscenio` **e os PNGs que ele nomeia** para uma única pasta no seu projeto Godot. Eles devem ficar lado a lado, sem subpastas - o importador resolve cada textura por nome de arquivo relativo ao `.proscenio`.

O Godot então o importa como uma cena, assada no cache de importação (você nunca a vê ou edita como um arquivo). O resultado são nós Godot simples que rodam mesmo com o plugin desinstalado.

Instanciá-lo dá a você:

```text
<root> (Node2D)
├── Skeleton2D
│   ├── Bone2D ...        the rig
│   ├── Polygon2D ...     cutout sprites (skinned ones deform via bone weights)
│   ├── Sprite2D ...      sprite_frame sprites (hframes/vframes grid)
│   └── Node2D ...        slots (visibility-toggled attachment children)
└── AnimationPlayer       one library: bone_transform, sprite_frame, slot tracks
```

Sprites `Polygon2D` com skinning carregam `Polygon2D.skeleton` + arrays de pesos por osso, então eles deformam com o rig; os rígidos são filhos do seu `Bone2D`. Sprites `Sprite2D` fatiam o seu `region_rect` por `hframes` / `vframes`. Slots seguram seus anexos e uma trilha alterna qual deles fica visível.

## Envolva a cena gerada {#wrap-the-generated-scene}

A reimportação **regenera por completo** a cena importada, então qualquer coisa alterada dentro dela é perdida. Mantenha todo o seu trabalho em uma cena wrapper que instancia o `.proscenio`:

```text
res://characters/<character>/
├── <character>.proscenio   from Blender; you instance this
├── <character>.atlas.png   plus every PNG the .proscenio names, same folder
├── <character>.tscn        yours - instances <character>.proscenio
└── <character>.gd          your script, on the wrapper root
```

1. _Instancie o personagem_: no seu próprio `<character>.tscn`, instancie `<character>.proscenio` (o Godot trata o `.proscenio` importado como um `PackedScene`).

2. _Construa sobre o wrapper_: scripts, efeitos, colisores e jogabilidade vivem todos no wrapper, nunca dentro da cena importada. Acesse os nós importados a partir do wrapper - por exemplo, reproduza uma animação importada:

```gdscript
@onready var anim: AnimationPlayer = $Character/AnimationPlayer

func _ready() -> void:
    anim.play("idle")
```

Efeitos e colisores seguem um osso com um `RemoteTransform2D`; sobrescritas de material ou visibilidade por sprite vão no `_ready`. O [fluxo de trabalho do Godot](../02-advanced/03-godot.md) tem o conjunto completo de receitas (IA, efeitos, colisores, sobrescritas de shader, eventos de animação, animações personalizadas) e as compensações entre wrapper e editable children.

> [!WARNING]
> **Nunca edite a cena importada diretamente.** Ela é regenerada a cada reexportação do Blender, então mudanças dentro dela são perdidas. Sempre construa sobre o wrapper.

Fixtures de referência: [`examples/authored/doll/`](../../../examples/authored/doll/) é a vitrine abrangente; [`examples/generated/blink_eyes/`](../../../examples/generated/blink_eyes/) isola o caminho `sprite_frame`, e [`examples/generated/shared_atlas/`](../../../examples/generated/shared_atlas/) isola o caminho de atlas fatiado. Consulte o [fluxo de trabalho do Godot](../02-advanced/03-godot.md) para o comportamento do importador em detalhes.
