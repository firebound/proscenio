# Docs do Proscenio

Este é um índice de documentação de nível superior que combina guias de fluxo de trabalho escritos à mão com uma referência interativa de JSON Schema, para que o leitor possa ir de "como o pipeline funciona" a "o que cada campo de um documento `.proscenio` significa" sem sair deste diretório.

## Guias de fluxo de trabalho

- [Primeiros passos](00-guides/00-getting-started/index.md): pré-requisitos, onde obter cada plugin e o formato do loop de ponta a ponta.
- [Passo a passo básico](00-guides/01-basic/index.md): o loop de ponta a ponta, uma página por ferramenta.
- [Fluxo de trabalho avançado](00-guides/02-advanced/index.md): mergulhos mais profundos nos recursos de cada ferramenta e como eles se encaixam.

## Documentação do projeto

- [Arquitetura do projeto](01-project/01-architecture.md): os objetivos de design, o fluxo de dados e como as ferramentas e os formatos se encaixam.
- [Comparação do pipeline](01-project/03-comparison.md): Proscenio contra outras stacks de autoria 2D (Spine, DragonBones, COA Tools).
- [Adiado / fora de escopo](01-project/04-deferred.md): a justificativa para recursos explicitamente fora da iteração atual.

## Ferramentas

Referência de alto nível, ao nível de intenção, para cada app do pipeline:

- [Hub de ferramentas](02-tools/index.md): a referência de alto nível, ao nível de intenção, para cada app do pipeline.
- [Addon do Blender](02-tools/blender-addon/index.md): o addon de autoria - malha, rig, pesos, slots, atlas, exportação.
- [Plugin do Photoshop](02-tools/photoshop-plugin/index.md): marque com tags e exporte um PSD em camadas para um manifesto mais PNGs.
- [Plugin do Godot](02-tools/godot-plugin/index.md): reimporte um `.proscenio` para uma cena nativa do Godot.

## Referência de schema

Referência interativa para ambos os formatos de transmissão, agrupada por recurso e renderizada ao vivo a partir dos JSON Schemas pelo viewer do site de docs, de modo que sempre reflete os modelos:

- [Referência de schema](content/README.md): ponto de entrada para ambos os formatos.
- [Personagem Proscenio](content/proscenio/document.mdx): o documento `.proscenio`: esqueleto, elementos, slots, animação.
- [Manifesto PSD](content/psd-manifest/manifest.mdx): o manifesto que o importador do Blender lê a partir da exportação do Photoshop.

Os JSON Schemas são despejados a partir da fonte de verdade pydantic em [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/). Regenere os schemas e os bindings após editar os modelos:

```pwsh
uv run python -m proscenio_codegen all
```

Isso emite os artefatos de JSON Schema, os bindings de Resource do Godot e os bindings de TypeScript (ou execute `schemas` / `godot` / `ts` individualmente). A própria referência de schema não precisa de passo de regeneração: o viewer lê os schemas despejados diretamente.

## Onde vive a fonte de verdade

| Superfície                                     | Arquivo / pacote                                                                        |
| ---------------------------------------------- | --------------------------------------------------------------------------------------- |
| Modelos de formato de transmissão (.proscenio + manifesto PSD) | [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/)     |
| Emissores de codegen (schemas / Godot / TS)    | [`packages/codegen/src/proscenio_codegen/`](../packages/codegen/src/proscenio_codegen/) |
| Addon do Blender                               | [`apps/blender/`](../apps/blender/)                                                     |
| Plugin UXP do Photoshop                        | [`apps/photoshop/`](../apps/photoshop/)                                                 |
| Plugin importador do Godot                     | [`apps/godot/`](../apps/godot/)                                                         |

## Site de docs

O site de docs é um app Docusaurus em [`apps/docs/`](../apps/docs/) que serve esta pasta `docs/` como sua raiz de conteúdo.

Execute-o com `pnpm --dir apps/docs start` para desenvolvimento, ou `pnpm --dir apps/docs build` para um bundle de produção.

Ele é publicado no GitHub Pages em [firebound.github.io/proscenio](https://firebound.github.io/proscenio/) via [`docs-deploy.yml`](../.github/workflows/docs-deploy.yml), a cada push para `main` que toca em `docs/`, `apps/docs/` ou nos schemas despejados.
