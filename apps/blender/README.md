# Proscenio — Blender addon

Blender 4.2+ addon. See repo root [AGENTS.md](../AGENTS.md) and the dev skill at [`.ai/skills/blender-addon-dev.md`](../.ai/skills/blender-addon-dev.md) before editing.

## Install for development

Symlink (Windows: directory junction) the contents of this folder into:

```text
%APPDATA%\Blender Foundation\Blender\<version>\extensions\user_default\proscenio
```

Reload via **Preferences → Get Extensions → Reload**.

## Build a release zip

```sh
blender --command extension build
```
