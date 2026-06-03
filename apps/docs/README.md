# Proscenio docs site

The Docusaurus site that serves the repo `docs/` folder: the hand-authored guides plus an interactive JSON Schema reference. See [`docs/README.md`](../../docs/README.md) for what it serves.

## Local development

```bash
pnpm install
pnpm start
```

Starts a dev server and opens a browser window; most changes hot-reload.

## Build

```bash
pnpm build
```

Generates static content into `build/`, servable by any static host. Preview the production build with `pnpm serve`.

## Deployment

Deploys to GitHub Pages via the [`docs-deploy.yml`](../../.github/workflows/docs-deploy.yml) workflow on every push to `main` that touches `docs/`, `apps/docs/`, or the dumped schemas. There is no manual `deploy` command.
