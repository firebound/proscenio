# Spec 063: SonarCloud analysis pipeline - TODO

Ordered: the config fix lands first so the issue list reflects the intended scope, then coverage, then triage. The route decision in the STUDY gates PR 1 and PR 2.

## PR 1 - analysis configuration (pending route call)

- [ ] Fix `sonar.projectKey` to `firebound_proscenio` (the live key) in `sonar-project.properties`.
- [ ] Make `sonar.exclusions` recursive (`scripts/**/*.out` and so on, not the top-level-only `scripts/*.out`). `sonar-project.properties:90-92`.
- [ ] Route A: set the Python version in the SonarCloud UI, add `apps/docs/**` and `tools/qa-companion/**` to `sonar.exclusions`, and stop here (coverage stays impossible).
- [ ] Route B (recommended): add a `sonarsource/sonarcloud-github-action` step that runs after the build with `node_modules` installed and coverage generated, and disable Automatic Analysis in the UI so the two modes do not both run.

## PR 2 - coverage wiring (Route B only)

- [ ] Add a CI job that runs the in-Blender coverage pass and the pytest `--cov-append` pass, merges with `coverage xml`, then runs `pnpm -C apps/photoshop run test:coverage`.
- [ ] Invoke the SonarCloud scanner so `reportPaths` resolve against the repo root (mind the Docker mount-path note in the properties file).
- [ ] Add a `new_coverage` condition to the quality gate.
- [ ] Verify the combined Python report lifts the bpy-bound writer and exporter lines as the properties comment claims.

## PR 3 - issue triage (after the config fix)

- [ ] Triage the 1 BLOCKER, 11 CRITICAL, 14 BUG, and 9 VULNERABILITY issues, plus the 6 security hotspots: each gets fixed, suppressed with justification (`sonar.issue.ignore.multicriteria`, mirrored in `.vscode/settings.json` per the existing convention), or confirmed out-of-scope.
- [ ] Capture the disposition so the next reader does not re-triage.
- [ ] The 159 MINOR smells are a separate opportunistic pass, not a blocking sweep.
