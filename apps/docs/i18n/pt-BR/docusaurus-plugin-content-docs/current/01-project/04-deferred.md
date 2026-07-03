# Adiado

O panorama geral. Cada item abaixo é uma *iniciativa guarda-chuva* que se encaixa conceitualmente em Proscenio, mas não está comprometida com um roadmap. Quando o trabalho começa, o guarda-chuva se desdobra em uma ou mais specs numeradas.

Este arquivo é intencionalmente grosseiro. Itens de granularidade mais fina (operadores isolados, entradas da matriz de CI, polimento do repo, desdobramentos adiados de specs já entregues) ficam em `specs/backlog/index.md` com suas próprias condições de disparo.

## Aceleração da autoria

Tire o artista do modo "comece a partir de um quad de 4 vértices" e leve-o em direção a "desenhe uma forma, obtenha uma malha pronta para rig".

- **Presets de subdivisão procedural de malha.** Subdivisão de quad em densidade baixa / média / alta para que o usuário não comece do zero.
- **Templates de auto-rig.** Presets humanoide, quadrúpede, boneco - "crie a armadura com a nomenclatura de ossos que o writer espera". Menos ambicioso que um auto-rig completo; mais como um passo de onboarding de um clique.

## Expressividade de animação

Igualar o que as ferramentas de recorte estabelecidas (Spine, DragonBones, CT2) entregam de fábrica.

- **Preservação de curvas Bezier.** Manipuladores de tangente de entrada / saída por chave no schema, para que a fidelidade das curvas do Blender chegue byte a byte ao Godot.
- **Mistura de interpolação por chave.** Chaves `linear` / `constant` / `cubic` misturadas na mesma track.
- **Eventos de animação / tracks de método.** Deixas sonoras, spawns de partículas, ganchos de gameplay - mapeiam para as tracks de método do `AnimationPlayer` do Godot. Remove a gambiarra do `AnimationPlayer` espelhado.
- **Re-rig não destrutivo no meio da edição.** Hoje o wrapper sobrevive à reimportação, mas os pesos e as chaves não sobrevivem a um re-rig da armadura subjacente. Cobertura parcial provavelmente chega junto com a preservação de Bezier + remapeamento de chaves.

## Topologia de rig e física

O lado de runtime de "o que um personagem pode fazer".

- **Coordenação de skins.** "Skin" no estilo Spine que agrupa N attachments de slot sob uma variante nomeada; um único switch troca a fantasia inteira.
- **Física de ossos, path constraints, transform constraints.** Constraints de runtime no estilo Spine. Requer uma extensão de formato e demanda concreta.

## Extensões de formato

Cada uma adiciona campos opcionais aos schemas e a lógica de consumo correspondente.

- **Múltiplos atlas por personagem.** Atlas único hoje; futuro `atlas_pages[]` indexado por sprite.
- **Sprite de máscara, blend modes, modulação de cor animável.** Máscara alpha por sprite, cor `modulate` animável, `z_index` animável.

## Alcance cross-DCC

O schema do manifesto PSD é agnóstico a DCC por design.

- **Exportadores Krita / GIMP.** Emitir um manifesto conforme a partir de outro DCC; o importador do Blender não precisa de mudanças.
- **Live link Blender ↔ Godot.** Hot reload através da fronteira do DCC. Provavelmente dispara a reconsideração da GDExtension.
