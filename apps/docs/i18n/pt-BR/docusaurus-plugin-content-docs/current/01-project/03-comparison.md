# Comparação de ferramentas

Como Proscenio se posiciona ao lado de outros pipelines de recorte 2D / animação de personagem e opções nativas de engine.

## Matriz de recursos

`yes` = entregue, `partial` = incompleto ou encapsulado, `no` = ausente ou fora de escopo, `-` = não aplicável. Notas entre parênteses após a palavra de status a qualificam.

As colunas são ordenadas por quão diretamente cada uma se compara a Proscenio: os rivais de destaque primeiro - Spine, o 2D nativo do Godot, o 2D Animation first-party do Unity e o Moho - depois as outras suítes e plugins de engine. A exportação de jogo com esqueleto vivo do Moho (glTF) é recente (Moho 14.4, fim de 2025); versões anteriores assam apenas sprite sheets ou vídeo.

| Recurso | Proscenio | Spine | Godot nativo | Unity 2D Animation | Moho | COA Tools 2 | Live2D | DragonBones | Souperior (plugin do Godot) | Puppet2D (plugin do Unity) | AnyPortrait (plugin do Unity) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Licença** | GPL-3.0 | pago | aberto | proprietário | pago (Debut / Pro) | GPL | pago (camada gratuita) | aberto | MIT | pago (Asset Store) | pago (Asset Store) |
| **Engine alvo** | apenas Godot 4 | múltiplas (~20 runtimes) | Godot 4 | Unity | múltiplas via glTF (14.4+) | Godot (quebrado), genérico | Cubism viewer + SDK AE/Unity | múltiplas (Cocos, Unity, Phaser…) | Godot 4 (nós modificadores de Skeleton2D) | Unity | Unity |
| **Saída é cena nativa da engine** | yes (`.scn` com nós core) | no (requer runtime) | yes | yes | no (intercâmbio glTF) | no (requer runtime) | no (requer SDK) | no (requer runtime) | yes (usa modificações de Skeleton2D) | yes (GameObjects do Unity) | partial (componente de runtime do AnyPortrait) |
| **Seguro à desinstalação do plugin** | yes | no | - | - | - | no | no | no | no (os nós de IK SÃO o plugin) | no (requer scripts de runtime) | no (requer runtime do AnyPortrait) |
| **Ferramenta de autoria** | Blender + Photoshop | editor do Spine | editor do Godot | editor do Unity + PSD Importer | editor do Moho + PSD | Blender + PSD/GIMP/Krita | Cubism + PSD | DragonBones Pro + PSD | editor do Godot | editor do Unity + janelas do Puppet2D | editor do Unity + janela do AnyPortrait (in-engine) |
| **Ingestão de PSD** | yes (UXP + schema de manifesto) | yes | no | yes (2D PSD Importer) | yes (Pro) | yes (multi-DCC) | yes | yes | no (apenas rigging) | no (sprites do Unity) | yes (importação de PSD em camadas) |
| **Esqueleto + ossos** | yes | yes | yes (Skeleton2D) | yes (Sprite Skinning) | yes (Smart Bones) | yes | - | yes | yes (opera sobre Skeleton2D) | yes | yes |
| **Malha de polígonos + pesos por vértice** | yes | yes (FFD) | yes (Polygon2D) | yes | partial (vínculo de ossos, vetor primeiro) | yes | partial (baseado em deformer) | yes | no (apenas do lado dos ossos) | yes (deformação de malha por pontos de controle) | yes (deformação de malha) |
| **Células de spritesheet (`hframes` / `vframes`)** | yes (Sprite2D) | yes | yes (Sprite2D) | yes | no (apenas sequência de PNG) | yes | - | yes | no | no | partial (apenas exportação) |
| **Sistema de slot / troca de sprite** | yes | yes | no | partial (Sprite Library / Resolver) | yes (Switch Layers) | yes | - | yes | no | partial | yes |
| **Coordenação de skins (grupo de slots)** | no (desdobramento candidato) | yes | no | partial (categorias da Sprite Library) | partial | no | - | yes | no | no | partial |
| **Cinemática inversa** | partial (encapsula o nativo do Blender) | yes (ferramenta de pose) | yes (SkeletonModification2D, experimental) | yes (IK Manager 2D) | yes | partial | - | yes | yes (IK + LookAt, recurso principal) | yes (cadeias de IK) | yes |
| **Path constraints** | no | yes | partial (PathFollow2D) | no | partial (Follow Path) | no | - | no | no | no | no |
| **Física de ossos** | no (backlog) | yes | no | no (apenas comunidade) | yes (Bone Dynamics, Pro) | no | yes (pêndulo, não baseado em ossos) | no | yes (jiggle) | no | yes (jiggle / dinâmica) |
| **Eventos de animação / tracks de método** | no (backlog) | yes | yes (AnimationPlayer) | yes (Animation Events) | no | no | partial | yes | yes (herda o AnimationPlayer do Godot) | yes (AnimationClip do Unity) | yes |
| **Preservação de curvas Bezier na exportação** | no (formato v2) | yes | yes | yes | no (assado na exportação) | yes (via Blender) | - | yes | yes (herda o Godot) | yes (nativo do Unity) | yes |
| **Empacotamento de atlas (rotação, fatiamento)** | partial (sem rotação) | yes | partial (manual) | yes (Sprite Atlas) | no | yes | yes | yes | no | yes (Unity) | yes |
| **Múltiplos atlas por personagem** | no (formato v2) | yes | - | yes | no | yes | yes | yes | - | yes (Unity) | yes |
| **Re-rig não destrutivo no meio da edição** | partial (o wrapper sobrevive, pesos/chaves não) | partial (skins ajudam) | - | partial | partial | partial | yes | partial | yes (vive no Godot) | partial | partial |
| **Prévia = paridade com runtime** | no (Blender ≠ Godot) | yes (runtime no editor) | yes (mesma engine) | yes (mesma engine) | partial (glTF) | no | yes (Cubism viewer) | yes | yes (mesma engine) | yes (mesma engine) | yes (mesma engine) |
| **Hot reload ao salvar** | partial (apenas do lado do Godot) | yes | yes | yes | - | partial | yes | yes | yes | yes | yes |
| **Auto-rig / templates / presets** | no | partial (ferramenta de pose) | no | partial (comunidade) | yes (Character Wizard) | partial | yes (presets de física) | partial | no | yes (auto-rig de bípede) | partial (templates) |
| **Malha a partir de contorno (automesh)** | yes (traçado de alpha) | yes | no | yes (Auto Geometry) | no (manual) | yes | yes (geração automática de malha) | partial | no | no (pontos de controle manuais) | yes (auto-mesh a partir do sprite) |
| **Tipagem forte no pipeline inteiro** | yes (mypy strict + GDScript tipado + TypeScript strict) | - | - | - | - | no | - | - | - | - | - |
| **Schema de exportação versionado (aberto)** | yes (JSON Schema 2020-12, 5 verificações) | proprietário | - | - | partial (glTF) | no | proprietário | proprietário | - | - | proprietário |

## Resumo de posicionamento

Cada ferramenta abaixo é lida do lado do Proscenio: *Vitória* onde Proscenio mira ser melhor, *Derrota* onde é pior, *Empate* onde se igualam.

- **Spine**
  - *Vitória:* gratuito e aberto (GPL); `.scn` nativo da engine sem biblioteca de runtime; seguro à desinstalação do plugin; um contrato de exportação aberto e fortemente tipado (o formato do Spine é proprietário).
  - *Derrota:* exportação multi-runtime; física de ossos, path constraints, coordenação de skins; Bezier preservado através da exportação; prévia no editor fiel ao runtime; loop de iteração mais apertado.
  - *Empate:* esqueleto, malha + pesos, slots, spritesheets, automesh - ambos cobrem o núcleo de recorte.

- **Godot nativo (sem plugin)**
  - *Vitória:* toda a camada de autoria - ingestão de PSD, rigging no Blender, automesh, slots - mais um contrato de exportação tipado; com o Godot pelado, você constrói tudo isso à mão no editor.
  - *Derrota:* nenhum salto de exportação, paridade de prévia na mesma engine, eventos nativos do `AnimationPlayer` e curvas Bezier.
  - *Empate:* a saída é idêntica - Proscenio emite exatamente o `Skeleton2D` + `Polygon2D` + `AnimationPlayer` do Godot.

- **Unity 2D Animation + PSD Importer**
  - *Vitória:* aberto e gratuito vs. a stack proprietária do Unity; o maduro conjunto de ferramentas de rig + animação do Blender; contrato aberto e tipado.
  - *Derrota:* fluxo de trabalho de engine única (sem salto de exportação), prévia na mesma engine, IK em runtime, empacotamento de atlas completo, eventos de animação e um ecossistema amplo.
  - *Empate:* quase paridade de recursos no núcleo de recorte - rig de PSD, automesh Auto Geometry, malha + pesos, esqueleto - através de uma engine diferente. (O sistema de slots do Proscenio é mais completo que a Sprite Library parcial do Unity.)

- **Moho**
  - *Vitória:* cena Godot nativa da engine + contrato tipado; automesh (o Moho abandonou o auto-trace na v13); um runtime livre de plugin; gratuito e aberto.
  - *Derrota:* a profundidade de autoria do Moho - Smart Bones, física de bone-dynamics, IK maduro, Character Wizard, biblioteca de conteúdo - um app completo versus um plugin fino.
  - *Empate:* PSD-para-rig, esqueleto + deformação dirigida por ossos, trocas de slot / switch-layer.
  - Nota: a exportação de jogo com esqueleto vivo do Moho (glTF) só chegou na 14.4 (fim de 2025) e é genérica + com perdas; versões mais antigas assam apenas sprite sheets ou vídeo.

- **COA Tools 2**
  - *Vitória:* uma exportação para Godot funcional e tipada (o importador do COA não tem manutenção); automesh em Python puro sem o bloqueio de instalação do `cv2`; rigor de schema + CI.
  - *Derrota:* ingestão multi-DCC - o COA lê PSD, GIMP e Krita; Proscenio é somente PSD hoje.
  - *Empate:* Blender como host de autoria, automesh, esqueleto + malha + slots.

- **Live2D**
  - *Vitória:* encaixe em runtime de jogo, recorte baseado em esqueleto, saída aberta e nativa da engine.
  - *Derrota:* rigs de deformer com ilustração em primeiro lugar, animação facial dirigida por parâmetros, física e presets maduros.
  - Nota: uma forma de arte diferente, não um rival direto - os dois mal se sobrepõem.

- **DragonBones**
  - *Vitória:* saída Godot nativa da engine (sem lib de runtime); schema aberto e tipado; automesh mais forte (o do DragonBones é tosco); mantido ativamente (o editor do DragonBones está parado desde ~2021).
  - *Derrota:* amplitude multi-runtime; coordenação de skins; animação exportada mais rica (IK em runtime, eventos, Bezier).
  - *Empate:* aberto e gratuito, esqueleto + malha + pesos, slots.

- **Souperior (plugin do Godot)**
  - *Vitória:* Proscenio faz a autoria do personagem inteiro - PSD, malha, slots - o que o Souperior não consegue.
  - *Derrota:* o Souperior adiciona IK / LookAt / jiggle in-engine mais ricos que o Proscenio, que não exporta constraints.
  - Nota: complementar, não concorrente - importe com Proscenio, refine com Souperior; os dois se empilham.

- **Puppet2D (plugin do Unity)**
  - *Vitória:* ingestão de PSD, variantes de spritesheet, um sistema de slots, automesh, saída aberta + nativa da engine - o Puppet2D (Unity pago) não tem nenhuma dessas.
  - *Derrota:* o auto-rig de bípede e o IK em runtime do Puppet2D; o ecossistema do Unity.
  - *Empate:* rigging esquelético com deformação de malha - através de uma engine diferente.

- **AnyPortrait (plugin do Unity)**
  - *Vitória:* cena nativa da engine + contrato aberto (o AnyPortrait precisa do seu componente de runtime em tempo de execução); gratuito e aberto.
  - *Derrota:* a autoria mais rica de ferramenta única do AnyPortrait - física de ossos, blend modes, IK maduro.
  - *Empate:* importação de PSD, malha + pesos, ossos, automesh, slots - um núcleo comparável em recursos, através de uma engine diferente.

## Paradigmas

Paradigmas de QoL entre ferramentas que a comunidade celebra, e onde Proscenio se posiciona em cada eixo.

### Adotados

- **Preservação da arte de origem.** As camadas do PSD sobrevivem até o Blender via o manifesto; os dados do Blender sobrevivem até o Godot via o padrão de cena-wrapper. A reimportação nunca destrói wrappers autorados pelo usuário. (Live2D, Spine e COA todos vendem isso.)

- **Saída nativa da engine.** O `.scn` gerado usa apenas nós core do Godot. A desinstalação do plugin é um teste rígido, não uma esperança. (Diferencial vs. Spine, DragonBones, importador Godot do CT2.)

- **Manipulação direta no DCC.** A autoria herda a pintura de peso, o dopesheet, o NLA e os drivers já existentes do Blender. Proscenio adiciona atalhos (Quick Armature, Drive from Bone), não modos proprietários. (O CT2 vende isso como "sem modos proprietários".)

- **Contrato versionado como fonte única de verdade.** Os aumentos de versão do schema são explícitos, validados em 5 verificações, e forçam migração. (Herdado da prática de engenharia de dados; raro entre pipelines de DCC.)

- **Tipagem forte de ponta a ponta.** Python `mypy --strict`, GDScript `untyped_declaration=2`, TypeScript `strict`. (Paradigma ausente da arte anterior.)

- **Sem fricção de dependências.** Cada plugin roda sobre o que já vem junto - um painel UXP, um addon do Blender com wheels do pydantic embutidas, um importador em GDScript - sem instalação de `cv2` / numpy e sem precisar de acesso ao PyPI. (O requisito de OpenCV do COA Tools 2 é o conto de advertência.)

### Parcialmente adotados

- **Iteração não destrutiva.** O wrapper sobrevive; pesos e chaves não sobrevivem a um re-rig hoje. (O RubberHose e as skins do Spine colocam a régua mais alta.)

- **Autoria na velocidade de um rascunho.** Automesh, Quick Armature e Create Slot reduzem a fricção; a exportação ainda custa três cliques (Validate → Export → copiar). (O bone-draw do COA é o alvo de referência.)

- **Eficiência de atlas.** O empacotador de atlas está entregue, ainda sem empacotamento com rotação, sem múltiplos atlas. (Spine e DragonBones lideram aqui.)

- **Investimento em onboarding.** Popups de `?` no painel e ajuda por tópico já chegaram. Tutoriais, personagens de referência e fixtures de vitrine ainda são escassos. (O investimento do Live2D em amostras e lições é o ponto mais alto.)

### Não adotados

Paradigmas deliberadamente fora da pista do Proscenio (a justificativa de roadmap para esses vive em [Adiado](04-deferred.md)):

- **Prévia com paridade de runtime** - a prévia do Blender não é o runtime do Godot; fechar essa lacuna provavelmente precisa de um live link.

- **Auto-rig / templates dirigidos por parâmetros** - a topologia de rig fica a cargo do usuário.

- **Rigs de deformer dirigidos por parâmetros (paradigma Live2D)** - uma forma de arte diferente, não uma lacuna de roadmap.

- **Re-rig no meio da animação (paradigma RubberHose)** - o formato assa o rig nas tracks hoje.
