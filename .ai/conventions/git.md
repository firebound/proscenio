# Git: branches, workflow, commits, PRs, review

How work is branched, committed, reviewed, and merged. Part of the [agent and contributor reference](../README.md).

## Branches

```text
feat/<slug>                   # Feature
fix/<slug>                    # Bug fix
docs/<slug>                   # Documentation only
refactor/<slug>               # Refactor without behavior change
chore/<slug>                  # Maintenance, tooling, configs
test/<slug>                   # Tests only
ci/<slug>                     # Workflow changes
```

Prefix vocabulary matches [Conventional Commits](https://www.conventionalcommits.org/). When the work implements a numbered spec under `specs/`, embed the number after the prefix as a stable search token: `feat/spec-<NNN>-<slug>`. The spec infix is a navigation aid, not a hard gate - omit it when the work is component-wide rather than spec-driven.

Examples: `feat/spec-<NNN>-<slug>` (numbered spec), `feat/photoshop-ui`, `fix/blender-bugs`, `chore/install-dev`.

Reference issues in the commit body (`Refs: #42`), not in the branch name. Keep branch names readable.

## Workflow

- `main` holds planning artifacts (spec studies and TODOs, backlogs) and small chores. Planning docs land directly on `main` because they cross PR boundaries and inform parallel work.
- Implementation work lives on a topic branch (typically `feat/spec-<NNN>-<slug>` or `fix/<slug>`) and merges back via PR.
- Commit gradually as work progresses. The merge can squash if the PR scope warrants it, but the branch history is the audit trail while work is in flight. A long PR benefits from many small commits; a tight bugfix is fine as one.

## Commits

### Grouping

- One commit per cohesive unit of work.
- Do not mix components in a single commit unless the change is a schema bump (which crosses by design).
- Prefer short subjects; use the body only when the *why* is non-obvious.

### Format

Conventional Commits:

```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Use for |
| --- | --- |
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Refactor without behavior change |
| `style` | Formatting, whitespace, no behavior change |
| `perf` | Performance improvement |
| `test` | Tests |
| `chore` | Maintenance, tooling, configs |
| `ci` | CI workflow changes |

### Scopes

Scope is the area touched. Use the smallest label that lets a reader locate the change. Recommended top-level scopes:

| Scope | Area |
| --- | --- |
| `blender` | Blender addon |
| `godot` | Godot plugin |
| `photoshop` | Photoshop UXP plugin |
| `schema` | Cross-component JSON schemas |
| `specs` | Planning specs |
| `ci` | CI workflows |
| `repo` | Root meta (license, configs, dotfiles) |

Sub-scopes like `photoshop/runtime` or `fixtures/doll` are allowed when they aid navigation. Keep them kebab-case, short, and consistent across a PR. Avoid one-off feature names as scopes unless they refer to a long-lived module.

### Examples

```text
feat(blender): add Photoshop JSON importer
fix(godot): flip Y on bone transform tracks
feat(schema): bump format_version to 2 for cubic interpolation
chore(repo): pin ruff version
```

## Pull requests

### Title

Same format as the commit subject:

```text
feat(blender): add Photoshop JSON importer
```

### Description

1. What changed - short summary.
2. Why - motivation if non-obvious.
3. How to test - concrete steps, including which Blender / Godot / Photoshop version.
4. Schema impact - if `format_version` bumped, link to the migration note.

### Template

```markdown
## What changed
<!-- one or two sentences -->

## Why
<!-- only if non-obvious -->

## How to test
<!-- concrete steps -->

## Checklist
- [ ] Per-language lint and format pass
- [ ] Per-language typecheck passes
- [ ] Tests pass for the affected app
- [ ] Schemas validate against examples and fixtures
- [ ] If `format_version` changed, migration documented
```

## Code review

What to review:

1. Correctness - does it do what the PR claims?
2. Boundary discipline - Photoshop knows nothing of Blender; Blender knows nothing of Godot internals; Godot reads only the exported document. Cross-component contracts go through the schema, not through shared code.
3. Schema fidelity - producer output and consumer input both match the schema.
4. No GDExtension creep - the Godot side stays pure GDScript with built-in nodes only.
5. Reload safety - Blender addon `register()` / `unregister()` symmetry, no leaked classes.
6. Test coverage - non-trivial logic gets a fixture or a unit test.
7. Cohesion and size - if a file or function has grown past the comfortable reading window, consider splitting before merging.

What not to review:

- Code style - formatters handle it.
- Personal preferences when a convention already chose.
- Formatting - covered by the editor and lint hooks.
