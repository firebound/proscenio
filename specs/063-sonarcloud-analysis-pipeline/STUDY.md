# Spec 063: SonarCloud analysis pipeline

SonarCloud analyses this repository via Automatic Analysis (the GitHub App), not a CI-based scanner, so most of `sonar-project.properties` is inert: the project key is wrong, the Python-version key is dropped, coverage never reaches the gate, and the scan walks trees that are not in the intended sources. On top of the plumbing, 248 open issues have never been triaged. This spec fixes the analysis pipeline so the gate measures the intended surface, wires coverage, then triages the issue set.

Scaffolded ahead of its STUDY. The plumbing carries one real route decision (stay on Automatic Analysis and trim it, or switch to CI-based analysis), and the triage is sequenced after the config fix so the issue count is honest first.

## Scope

- Decide the analysis route and apply it: trim Automatic Analysis, or switch to a CI-based scanner.
- Wire coverage so the Python and JavaScript reports reach SonarCloud and a new-code coverage gate condition can exist.
- Triage the open issues in severity order, marking each as a fix, a justified suppression, or out-of-scope.

## Open questions (resolve before coding)

- Route A (stay on Automatic Analysis and trim it) versus Route B (CI-based scanner). Route A is cheap but coverage stays impossible because Automatic Analysis does not build the project. Route B makes the whole properties file authoritative and is the prerequisite for coverage. The backlog recommends Route B; confirm the trade before committing, since Route B adds a CI job and the two modes must not both run.
- Triage threshold: fix-versus-suppress for the high-severity set, and how much of the 159 MINOR smells to take in the first pass versus leave opportunistic.

## Sources

Drains [`backlog-sonarqube.md`](../backlog-sonarqube.md) (all three entries) and the non-recursive `sonar.exclusions` item from [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md). Behavioral fixes that emerge from triage route to the matching bug backlog; type and lint shaped ones to [`backlog-code-quality.md`](../backlog-code-quality.md).
