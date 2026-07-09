# Estado da release v1 do Proscenio

Projeto feature-complete e estável. Este documento rastreia o que já foi feito no passe de release-prep e o que ainda falta pra cortar a tag `v1.0.0`.

## Feito neste passe (na main)

- **Versão padronizada com fonte única.** `VERSION` (raiz) = `1.0.0` é canônico; `scripts/maintenance/sync_version.py` propaga pros 4 manifests (Blender, Godot `plugin.cfg`, UXP `manifest.json`, `package.json`). CI falha em divergência (`--check`); `release.yml` recusa tag que discorde de `VERSION`.
- **README** - removido o aviso "proof of concept / not for production".
- **CHANGELOG** - seção `1.0.0` adicionada.
- **Docs** - removida a admoestação "Placeholder pages" (en+pt); doc órfã `09-manual-mesh` linkada no índice do addon (en+pt); `onBrokenLinks`/`onBrokenMarkdownLinks` -> `throw` (build validado limpo nos dois locais).
- **Spec 077** podada (pasta removida, índice marcado shipped/PR #186).
- **qa-companion** - referência a `findings.md` (inexistente) corrigida no README.
- **release.yml** - empacotamento do addon trocado de `zip` cru por `blender --command extension validate` + `extension build` (com secção `[build]` no manifest excluindo tests/dev). Validado local: build OK, 273 files, 15 wheels, tests/pyproject fora.
- **ruff** - pin alinhado: hook pre-commit e CI ambos em `0.15.20`.
- **Sonar/Dependabot** - scan pulado em PR de Dependabot (some o falso-vermelho); fix definitivo anotado no backlog.

## Falta pra tag v1 (bloqueadores reais)

1. **Feature do spec 079 (per-animation slot swaps)** - em andamento por outro agente; entra na v1. A tag espera ela mergear.
2. **`doll-roundtrip-remeasure`** - re-medir o desvio de 1px + PPU=100 na volta PSD->Blender pela via UXP atual. **Não automatizável aqui** (precisa rodar Photoshop UXP + Blender interativo). Único item com gatilho escrito "antes da primeira tag `v*`".
3. **Cortar a tag `v1.0.0`** - depois de 1 e 2. `release.yml` já builda os 3 bundles e valida tag==VERSION.

## Sem defeito de código, mas dívida de QA manual

- **10 regressões do QA Companion NÃO são bugs.** Triadas: cada uma teve o texto-esperado reescrito após specs de UI-restructure já shipadas (panel-restructure, draw-order-authoring, spec 036 PR3, element-reimport). O código implementa o comportamento novo (verificado: reproject é planar, `smart_uv_project` sumiu; `select_issue_object` existe pós-decomposição). Status `regressed` = PASS gravado obsoleto, precisa **re-walk humano na GUI** - não conserto.
- Walk manual majoritariamente pendente (~215 itens). Testes automatizados verdes (170+); o passe humano é dívida de cobertura, não trava código. Decisão de gate é tua.

## Fora de escopo v1 (features deferidas de propósito)

Exportadores Krita/GIMP (spec 038), skins estilo Spine (059), compat Blender 6 (062), e toda a lista de `specs/gated.md` + `specs/deferred.md`.

## Verificar

- Repo `github.com/firebound/proscenio` já é **público**? Todo link de install da doc resolve lá.
- 6 PRs de Dependabot abertas (dev-deps) travadas pelo check obrigatório do Sonar; mergear com admin ou pôr `SONAR_TOKEN` no store do Dependabot (ver backlog).
