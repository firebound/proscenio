# Arquitetura

Como Proscenio é construído: os três plugins, os sistemas dentro de cada um, os dados que eles movem e onde estão a complexidade e o risco. Leia isto antes de mexer em qualquer coisa estrutural.

Os três plugins nunca chamam uns aos outros - Photoshop, Blender e Godot cada um entrega um arquivo ao próximo, ligados apenas por um formato versionado compartilhado. Cada seção abaixo cobre as entranhas de um plugin; para o fluxo de ponta a ponta, comece pelo [passo a passo básico](../00-guides/01-basic/index.md).

## Photoshop - plugin [UXP](https://developer.adobe.com/photoshop/uxp/2022/) ([React](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/))

Transforma um PSD em camadas num manifesto mais PNGs que o Blender consegue importar.

O código é organizado em camadas de forma limpa: `api/` isola a API da Adobe e concentra os efeitos colaterais (ler e escrever arquivos, chamar a API do Photoshop), enquanto `lib/` guarda a lógica de domínio pura e testável, mantida livre de plataforma.

| Sistema | O que faz | Arquivos principais |
| --- | --- | --- |
| [**Adaptador de documento**](../../apps/photoshop/src/api/adapt-document.ts) | Converte o documento e as camadas da API do Photoshop no seu próprio modelo `Layer`. Atua como fronteira, de modo que o resto do código nunca toca diretamente na API da Adobe. | `api/adapt-document.ts` |
| [**Sistema de tags**](../../apps/photoshop/src/lib/tag-parser.ts) | Lê e escreve marcadores entre colchetes no nome da camada (`[ignore]`, `[merge]`, `[spritesheet]`, `[folder]`, `[scale]`, `[origin]` e outros). É assim que o artista dirige a exportação sem sair do Photoshop. | `lib/tag-parser`, `tag-writer`, `tag-tree`; `api/layer-rename` |
| [**Planner**](../../apps/photoshop/src/lib/planner.ts) | O coração da exportação: percorre a árvore de camadas e produz o manifesto (cada camada vira uma entrada `mesh` ou `sprite`), a lista de PNGs a escrever, os avisos e o que foi pulado. Resolve a ordem de desenho (z-order), os grupos `[merge]`, a detecção automática de spritesheet, o pivô e a escala. | `lib/planner.ts`, `lib/manifest.ts` |
| [**Validação e I/O do manifesto**](../../apps/photoshop/src/api/manifest-validator.ts) | Valida o manifesto com o [ajv](https://ajv.js.org/) (um validador de JSON Schema em tempo de execução) **antes** que qualquer coisa seja escrita em disco, de modo que um manifesto inválido nunca chega ao Blender. Além do leitor e do escritor de JSON. | `api/manifest-validator` (ajv), `manifest-reader`, `manifest-writer` |
| [**Exportação de PNG**](../../apps/photoshop/src/api/png-writer.ts) | Renderiza a região de cada camada para um PNG, lendo a bounding box a partir da seleção do Photoshop. | `api/png-writer`, `png-placer`, `ps-selection`, `ps-selection-bounds` |
| [**Orquestração (exportar / importar)**](../../apps/photoshop/src/api/export-flow.ts) | Amarra tudo. Exportação: adapta o documento, monta o plano, valida e então escreve PNGs + manifesto dentro de um único modal do Photoshop ([`executeAsModal`](https://developer.adobe.com/photoshop/uxp/2022/ps_reference/media/executeasmodal/)); o manifesto só é salvo se **todos** os PNGs tiverem sucesso, então ele nunca aponta para arquivos ausentes. A importação faz o inverso: a partir de um manifesto mais PNGs, ela **reconstrói um PSD do zero**. | `api/export-flow`, `import-flow` |
| [**UI e questões transversais**](../../apps/photoshop/src/panels) | Os painéis (Exporter, Tags, Validate, Debug) com suas seções e hooks reativos, além das partes de apoio: metadados [XMP](https://developer.adobe.com/xmp/docs/) (para que os pixels por unidade sobrevivam ao round trip), uma pasta de saída persistente e a migração da convenção legada de camada `_name` para `[ignore]`. | `panels/**`, `hooks/**`, `api/xmp`, `api/folder-storage`, `*/legacy-migration` |

## Blender - addon Python

O addon registra três grupos: `properties`, `operators` e `panels`.

**Antes dos sistemas, o armazenamento de dados.** Cada objeto carrega um `ProscenioObjectProps` (acessado como `Object.proscenio`) e a cena carrega um `ProscenioSceneProps`. Esses são [*PropertyGroups*](https://docs.blender.org/api/current/bpy.types.PropertyGroup.html) - a estrutura tipada do Blender para armazenar dados em objetos. Cada campo também é espelhado para uma [*Custom Property*](https://docs.blender.org/manual/en/latest/files/custom_properties.html) crua (um par chave/valor solto no objeto), porque a Custom Property é mais resiliente: ela sobrevive ao addon ser desativado e é um alvo estável para drivers de animação. O espelhamento é feito por `hydrate` / `cp_keys` / `pg_cp_fallback`.

| Sistema | O que faz | Operadores / core |
| --- | --- | --- |
| [**Automesh**](../../apps/blender/core/automesh) | Constrói a malha do sprite a partir do alpha da imagem: detecta a silhueta e então triangula o interior com [CDT](https://en.wikipedia.org/wiki/Constrained_Delaunay_triangulation) (constrained Delaunay triangulation - uma malha de triângulos que respeita o contorno). Tem um modo de autoria interativo (um modal) com um overlay de GPU onde o artista edita o contorno, adiciona pontos e corta. A lógica de geometria é **pura** (`core/automesh`, sem Blender) e mantida separada da ponte que toca o [bmesh](https://docs.blender.org/api/current/bmesh.html) (`core/bpy_helpers/automesh`), e é por isso que ela pode ser testada fora do Blender. | `automesh`, `automesh_authoring`, `bind_mesh` |
| [**Skinning (pintura de peso)**](../../apps/blender/core/skinning) | Vincula os vértices da malha aos ossos. Faz o vínculo inicial por proximidade no plano, tem um modal de pintura de peso com um preset apropriado para 2D e mantém um **sidecar** - um JSON paralelo que registra a procedência de cada peso (pintado à mão, reprojetado, gerado automaticamente) e sobrevive a uma regeneração da malha. Inclui copiar pesos entre sprites e instantâneo/restauração. | `edit_weights`, `brush_preset`, `copy_weights_to_selected`, `restore_weight_snapshot`, `sidecar_io`; `core/skinning` |
| [**Quick Armature**](../../apps/blender/operators/armature/quick_armature.py) | Um modal para desenhar a cadeia de ossos por extrusão na viewport, travado no plano XZ na vista frontal ortográfica. A matemática da cadeia é pura e testada à parte. | `armature/quick_armature`; `core/armature/quick_armature_math` |
| [**Sistema de slots**](../../apps/blender/operators/slot) | Grupos de troca de sprite (por exemplo, trocar uma mão fechada por uma aberta). Cria o slot, anexa os attachments e tem um shader de prévia. | `slot/create`, `slot/attachment`, `slot/preview_shader`; `core/slot_emit` |
| [**Empacotamento de atlas**](../../apps/blender/operators/atlas_pack) | Empacota, desempacota e aplica regiões de UV num único atlas de textura. | `atlas_pack/*`; `core/atlas_packer` |
| [**Importação de PSD**](../../apps/blender/importers/photoshop) | Consome o manifesto do Photoshop mais os PNGs e constrói os planos (quads Polygon2D) e, opcionalmente, a armadura. | `import_photoshop`; `importers/photoshop/{planes,armature}`; `core/psd_manifest` |
| [**Exportação para Godot**](../../apps/blender/exporters/godot) | Descobre a armadura, os sprites e o atlas na cena (`scene_discovery`), chama um builder por aspecto (`build_skeleton`, `build_sprite`, `build_slots_for_scene`, `build_animations`, `build_slot_animations`) e monta um `ProscenioDocument` que vira o arquivo `.proscenio`. | `export_flow`; `exporters/godot/writer/*` |
| [**Autoria de animação**](../../apps/blender/operators/driver.py) | Atalhos de rigging e animação: "drive from bone" (um driver ligando o quadro de um sprite a um osso), toggle IK/FK por osso, uma biblioteca de poses (em cima do sistema nativo do Blender), uma câmera de prévia ortográfica e um auxiliar de IK. | `driver`, `set_bone_mode`, `pose_library`, `authoring_camera`, `authoring_ik` |
| [**Apoio**](../../apps/blender/core/validation) | Autoria de UV (bounds), o seletor de armadura, auxiliares de seleção, validação, despacho de ajuda e utilitários (relato de erros, espelhamento, estado da viewport). | `uv_authoring`, `skeleton_target`, `selection`, `help_dispatch`; `core/validation`, `core/{report,mirror,viewport_state,...}` |

## Godot - plugin de editor (GDScript)

Pequeno e focado: um único plugin de importação mais cinco builders.

| Componente | O que faz |
| --- | --- |
| [**Plugin de importação**](../../apps/godot/addons/proscenio/importer.gd) (`importer.gd`) | Um [`EditorImportPlugin`](https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html) - o Godot o executa sempre que um `.proscenio` entra no projeto. Ele lê o JSON como um Resource tipado (`ProscenioDocument.from_dict`), checa o `format_version`, constrói a árvore de nós e a salva como uma cena `.scn`. A ordem importa: esqueleto, depois atlas, depois **slots antes dos sprites** (para que os sprites possam ser parenteados sob o nó de slot), depois sprites, depois animação. |
| [**Os cinco builders**](../../apps/godot/addons/proscenio/builders) | Cada um constrói uma fatia da cena, e **cada um só trata daquilo que reconhece**: ele lê o campo `type` em cada sprite no JSON, processa os que são seus e ignora o resto - não há herança nem polimorfismo, apenas funções chamadas em sequência. São eles: `SkeletonBuilder` ([Skeleton2D](https://docs.godotengine.org/en/stable/classes/class_skeleton2d.html) + [Bone2D](https://docs.godotengine.org/en/stable/classes/class_bone2d.html)), `SlotBuilder` (os nós de slot), `PolygonBuilder` ([Polygon2D](https://docs.godotengine.org/en/stable/classes/class_polygon2d.html) com pesos, para sprites `polygon`), `SpriteFrameBuilder` ([Sprite2D](https://docs.godotengine.org/en/stable/classes/class_sprite2d.html) com uma grade de quadros, para sprites `sprite_frame`) e `AnimationBuilder` (preenche o [AnimationPlayer](https://docs.godotengine.org/en/stable/classes/class_animationplayer.html) com os tipos de track que ele suporta - `bone_transform`, `sprite_frame`, `slot_attachment`; o schema também define uma track `visibility`, mas o importador ainda não a consome). |
| [**node_name_util**](../../apps/godot/addons/proscenio/builders/node_name_util.gd) | Nomeação de nós à prova de colisão. A reimportação sobrescreve a cena gerada por inteiro; as edições do usuário sobrevivem através do padrão de cena-wrapper, não de um diff/merge. |
| [**Plugin + schema_bindings**](../../apps/godot/addons/proscenio/plugin.gd) | `plugin.gd` registra o plugin de importação no editor; `schema_bindings/` é a camada de leitura tipada gerada a partir do schema. |

## O que se sustenta bem

Algumas decisões merecem destaque, porque moldam todo o resto:

- **Um modelo de dados, não três.** Ambas as pontas falam o schema diretamente - o Blender escreve tipado, o Godot lê tipado - então não há um dicionário solto se desviando nas bordas. Um campo muda em um lugar e flui para os três apps.

- **No Blender, a matemática é mantida separada do próprio Blender.** A geometria por trás do automesh e do skinning vive em Python puro, sem imports de `bpy`, e apenas uma ponte fina de fato conversa com o Blender. Essa separação é o que permite testar a maior parte dela sem nunca abrir o app.

- **No Photoshop, as camadas se mantêm honestas.** A API da Adobe é tocada em um só lugar, a lógica de planejamento e de tags é pura e fácil de testar, os efeitos colaterais ficam isolados em `io/`, e o manifesto é validado antes que qualquer coisa chegue ao disco.

## Onde pisar com cuidado

Não são bugs - apenas os pontos que carregam mais complexidade, onde mudanças merecem cuidado extra:

- **O Blender carrega o maior peso.** É o maior dos três por larga margem, e seus dois sistemas mais intrincados são a ferramenta interativa de autoria de automesh e o trabalho de procedência do skinning - ambos guardam muito estado vivo e se apoiam no Blender em tempo de execução, então são mais difíceis de cobrir com testes. Regressões tendem a aparecer aqui primeiro.

- **O armazenamento duplo é sutil.** Espelhar cada configuração entre uma PropertyGroup tipada e uma Custom Property crua é o que torna os dados resilientes, mas também é o acoplamento mais delicado do addon (manter os dois em sincronia, undo, timing de carregamento). Simplificá-lo está no roadmap.

- **O round trip do Photoshop é uni-direcional em espírito.** O plugin consegue reconstruir um PSD a partir de um manifesto, mas esse ciclo PSD-para-PSD não é perfeito pixel a pixel (pequeno desvio de pivô e de pixels por unidade, ambos rastreados). Isso é aceitável na prática: a exportação existe para alimentar o Blender, não para reconstruir o Photoshop.

- **O Godot lê uma versão de formato.** O importador mira a versão atual do `.proscenio` e não migra arquivos mais antigos - intencional enquanto o formato ainda está se assentando, e revisitado quando existir uma segunda versão.

- **A convenção do plano-imagem XZ.** Proscenio faz autoria e exportação no plano XZ, com Y como eixo de profundidade, porque o fluxo de recorte 2D vive na vista Frontal Ortográfica do Blender, onde uma projeção com Y para cima colapsa os ossos no plano do chão. Toda coordenada que cruza para a exportação - transforms de osso, posições de malha, eixos de driver - segue isso. Código que toca o writer, os drivers, o automesh ou o Quick Armature deve manter a convenção, ou a cena do Godot sai espelhada ou achatada.

- **A ordem dos campos está travada nos goldens.** Os modelos pydantic declaram seus campos na ordem em que o writer os emite, de modo que `model_dump_json(exclude_unset=True)` reproduz os fixtures golden versionados byte a byte. Isso é uma restrição de teste, não parte do contrato de transmissão - um consumidor de JSON não se importa com a ordem das chaves - então reordenar os campos de um modelo ou inserir um no meio da estrutura desvia os goldens e faz falhar os testes de correspondência versionada até que sejam regerados.
