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

Open `apps/godot/` in Godot 4.3 or newer. The plugin is auto-enabled in `project.godot`.

Before opening for the first time (or after `git pull` that touches `examples/`), sync the canonical fixtures into the project so the wrapper scenes and `.proscenio` files become reachable from `res://`:

```sh
python scripts/godot/sync_fixtures.py
```

The script links each `examples/<tier>/<name>/<name>.expected.proscenio` -> `apps/godot/examples/<name>/<name>.proscenio`, plus the wrapper `.tscn`/`.gd` and texture PNGs. It tries symlinks first, falls back to hardlinks (Windows without Developer Mode), and finally to plain copies if neither is available. Output dirs (`apps/godot/examples/<name>/`) are gitignored -- never commit them.

The Godot dev project sees the synced fixtures under `res://examples/<name>/` -- wrapper TSCNs reference paths under that prefix. `addons/proscenio/` (the plugin source) and `tests/` (GUT + type-B importer fixtures) live at the project root as usual.

Cross-platform notes:

- **Linux / macOS:** symlinks work out of the box. Edits in `examples/` propagate live to `apps/godot/`.
- **Windows with Developer Mode ON** (Settings > Privacy & security > For developers): same as Linux/macOS.
- **Windows without Developer Mode:** falls back to hardlinks. Edits propagate, but if `git pull` replaces a source file the hardlink becomes stale -- re-run the sync.
- **Cross-volume (rare):** the script copies. Re-run after any source edit.

## Run tests

```sh
godot --headless --path godot-plugin -s addons/gut/gut_cmdln.gd
```

GUT must be installed in the project for this to work.
