# Proscenio — Godot plugin

Godot 4.3+ editor plugin. See repo root [AGENTS.md](../AGENTS.md) and the dev skill at [`.ai/skills/godot-plugin-dev.md`](../.ai/skills/godot-plugin-dev.md) before editing.

## Structure

```text
godot-plugin/
├── project.godot          # dev project for testing the addon
├── addons/proscenio/      # the actual addon — what ships
└── tests/                 # GUT tests
```

When you ship the plugin, only `addons/proscenio/` goes in the zip.

## Run the dev project

Open `godot-plugin/` in Godot 4.3 or newer. The plugin is auto-enabled in `project.godot`.

## Run tests

```sh
godot --headless --path godot-plugin -s addons/gut/gut_cmdln.gd
```

GUT must be installed in the project for this to work.
